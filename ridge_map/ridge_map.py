"""3D maps with 1D lines."""

from urllib.request import urlopen
from tempfile import NamedTemporaryFile

from matplotlib.collections import LineCollection
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
from skimage.filters import rank
from skimage.morphology import footprint_rectangle
from skimage.util import img_as_ubyte
from scipy.ndimage import rotate

import srtm


class FontManager:
    """Utility to load fun fonts from https://fonts.google.com/ for matplotlib.

    Find a nice font at https://fonts.google.com/, and then get its corresponding URL
    from https://github.com/google/fonts/

    Use like:

    fm = FontManager()
    fig, ax = plt.subplots()

    ax.text("Good content.", fontproperties=fm.prop, size=60)
    """

    def __init__(
        self,
        github_url="https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf",  # pylint: disable=line-too-long
    ):
        """
        Lazily download a font.

        Parameters
        ----------
        github_url : str
            Can really be any .ttf file, but probably looks like
            "https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf" # pylint: disable=line-too-long
        """
        self.github_url = github_url
        self._prop = None

    @property
    def prop(self):
        """Get matplotlib.font_manager.FontProperties object that sets the custom font."""
        if self._prop is None:
            with NamedTemporaryFile(delete=False, suffix=".ttf") as temp_file:
                # pylint: disable=consider-using-with
                temp_file.write(urlopen(self.github_url).read())
                self._prop = fm.FontProperties(fname=temp_file.name)
        return self._prop


class RidgeMap:
    """Main class for interacting with art.

    Keeps state around so no servers are hit too often.
    """

    def __init__(self, bbox=(-71.928864, 43.758201, -70.957947, 44.465151), font=None):
        """Initialize RidgeMap.

        Parameters
        ----------
        bbox : list-like of length 4
            In the form (long, lat, long, lat), describing the
            (bottom_left, top_right) corners of a box.
            http://bboxfinder.com is a useful way to find these tuples.
        font : matplotlib.font_manager.FontProperties
            Optional, a custom font to use. Defaults to Cinzel Regular.
        """
        self.bbox = bbox
        self._srtm_data = srtm.get_data()
        if font is None:
            font = FontManager().prop
        self.font = font
        self.ax = None

    @property
    def lats(self):
        """Left and right latitude of bounding box."""
        return (self.bbox[1], self.bbox[3])

    @property
    def longs(self):
        """Bottom and top longitude of bounding box."""
        return (self.bbox[0], self.bbox[2])

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def get_elevation_data(
        self,
        num_lines=80,
        elevation_pts=300,
        viewpoint_angle=0,
        crop=False,
        interpolation=0,
        lock_resolution=False,
    ):
        """Fetch elevation data and return a numpy array.

        Parameters
        ----------
        num_lines : int
            Number of horizontal lines to draw
        elevation_pts : int
            Number of points on each line to request. There's some limit to
            this that srtm enforces, but feel free to go for it!
        viewpoint_angle : int (default 0)
            The angle in degrees from which the map will be visualised.
        crop : bool
            If the corners are cropped when rotating
        interpolation : int in [0, 5]
            The level of interpolation. Can smooth out sharp edges, especially
            when rotating. Above 1 tends to lead to an all NaN graph.
        lock_resolution : bool
            Locks the resolution during rotation, ensuring consistent rotation
            deltas but producing potential scaling artifacts. These artifacts
            can be reduced by setting num_lines = elevation_pts.

        Returns
        -------
        np.ndarray
        """
        if (
            45 < (viewpoint_angle % 360) < 135 or 225 < (viewpoint_angle % 360) < 315
        ) and not lock_resolution:
            num_lines, elevation_pts = elevation_pts, num_lines

        values = self._srtm_data.get_image(
            (elevation_pts, num_lines), self.lats, self.longs, 5280, mode="array"
        )
        values = rotate(
            values, angle=viewpoint_angle, reshape=not crop, order=interpolation
        )

        return values

    def preprocess(
        self, *, values=None, water_ntile=10, lake_flatness=3, vertical_ratio=40
    ):
        """Get map data ready for plotting.

        You can do this yourself, and pass an array directly to plot_map. This
        gathers all nan values, the lowest `water_ntile` percentile of elevations,
        and anything that is flat enough, and sets the values to `nan`, so no line
        is drawn. It also exaggerates the vertical scale, which can be nice for flat
        or mountainy areas.

        Parameters
        ----------
        values : np.ndarray
            An array to process, or fetch the elevation data lazily here.
        water_ntile : float in [0, 100]
            Percentile below which to delete data. Useful for coasts or rivers.
            Set to 0 to not delete any data.
        lake_flatness : int
            How much the elevation can change within 3 squares to delete data.
            Higher values delete more data. Useful for rivers, lakes, oceans.
        vertical_ratio : float > 0
            How much to exaggerate hills. Kind of arbitrary. 40 is reasonable,
            but try bigger and smaller values!

        Returns
        -------
        np.ndarray
            Processed data.
        """
        if values is None:
            values = self.get_elevation_data()
        nan_vals = np.isnan(values)

        values[nan_vals] = np.nanmin(values)
        values = (values - np.min(values)) / (np.max(values) - np.min(values))

        is_water = values < np.percentile(values, water_ntile)
        is_lake = (
            rank.gradient(img_as_ubyte(values), footprint_rectangle((3, 3)))
            < lake_flatness
        )

        values[nan_vals] = np.nan
        values[np.logical_or(is_water, is_lake)] = np.nan
        values = vertical_ratio * values[-1::-1]  # switch north and south
        return values

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def plot_annotation(
        self,
        label="Mount Washington",
        coordinates=(-71.3173, 44.2946),
        x_offset=-0.25,
        y_offset=-0.045,
        label_size=30,
        annotation_size=8,
        color=None,
        background=True,
        ax=None,
    ):
        """Plot an annotation to an existing map.

        It is recommended to call this function only after calling map_plot()

        Parameters
        ----------
        label : string
            Label to place on the map. Use an empty string for no label.
        coordinates : (float, float)
            The coordinates of the annotation as Longitude, Latitude
        x_offset : float
            Where to position the label relative to the annotation horizontally
        y_offset : float
            Where to position the label relative to the annotation vertically
        label_size : int
            fontsize of the label
        annotation_size : int
            Size of the annotation marking
        label_color : string or None
            Color for the label. If None, then uses label_color of map
        background : bool
            If there is a background or not
        ax : matplotlib Axes
            You can pass your own axes, but probably best not to

        Returns
        -------
        matplotlib.Axes
        """
        if ax is None and self.ax is None:
            raise ValueError(
                "No axes found: Either plot_map() beforehand or pass an matplotlib.Axes value "
                "to the function."
            )
        if ax is None:
            ax = self.ax

        highest_zorder = max(text.zorder for text in ax.texts) if ax.texts else 1

        rel_coordinates = (
            (coordinates[0] - self.longs[0]) / (self.longs[1] - self.longs[0]),
            (coordinates[1] - self.lats[0]) / (self.lats[1] - self.lats[0]),
        )

        annotation_color = "black"
        if color:
            annotation_color = color
        elif ax.texts[0].get_color():
            annotation_color = ax.texts[0].get_color()

        ax.text(
            rel_coordinates[0] + x_offset,
            rel_coordinates[1] + y_offset,
            label,
            fontproperties=self.font,
            size=label_size,
            color=annotation_color,
            transform=ax.transAxes,
            bbox=(
                {"facecolor": ax.get_facecolor(), "alpha": 1, "linewidth": 1}
                if background
                else None
            ),
            verticalalignment="bottom",
            zorder=highest_zorder,
        )

        ax.plot(
            *rel_coordinates,
            "o",
            color=annotation_color,
            transform=ax.transAxes,
            ms=annotation_size,
            zorder=highest_zorder,
        )

        self.ax = ax
        return ax

    # pylint: disable=too-many-arguments,too-many-locals
    def plot_map(
        self,
        values=None,
        label="The White\nMountains",
        label_color=None,
        label_x=0.62,
        label_y=0.15,
        label_verticalalignment="bottom",
        label_size=60,
        line_color="black",
        kind="gradient",
        linewidth=2,
        background_color=(0.9255, 0.9098, 0.9255),
        size_scale=20,
        ax=None,
    ):
        """Plot the map.

        Lots of nobs, and they're all useful to sometimes turn.

        Parameters
        ----------
        values : np.ndarray
            Array of elevations to plot. Defaults to the elevations at the provided
            bounding box.
        label : string
            Label to place on the map. Use an empty string for no label.
        label_color : string or None
            Color for the label. If None, then uses line_color
        label_x : float in [0, 1]
            Where to position the label horizontally
        label_y : float in [0, 1]
            Where to position the label vertically
        label_verticalalignment: "top" or "bottom"
            Whether the label_x and label_y refer to the top or bottom left corner
            of the label text box
        label_size : int
            fontsize of the label
        line_color : string or callable
            colors for the map. A callable will be fed the scaled index in [0, 1]
        kind : {"gradient" | "elevation"}
            If you provide a colormap to `line_color`, "gradient" colors by the line index, and
            "elevation" colors by the actual elevation along the line.
        linewidth : float
            Width of each line in the map
        background_color : color
            For the background of the map and figure
        scale_size : float
            If you are printing this, make this number bigger.
        ax : matplotlib Axes
            You can pass your own axes!

        Returns
        -------
        matplotlib.Axes
        """
        if kind not in {"gradient", "elevation"}:
            raise TypeError("Argument `kind` must be one of 'gradient' or 'elevation'")
        if values is None:
            values = self.preprocess()

        if ax is None:
            ratio = (self.lats[1] - self.lats[0]) / (self.longs[1] - self.longs[0])
            _, ax = plt.subplots(figsize=(size_scale, size_scale * ratio))

        x = np.arange(values.shape[1])
        norm = plt.Normalize(np.nanmin(values), np.nanmax(values))
        for idx, row in enumerate(values):
            y_base = -6 * idx * np.ones_like(row)
            y = row + y_base
            if callable(line_color) and kind == "elevation":
                points = np.array([x, y]).T.reshape((-1, 1, 2))
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                lines = LineCollection(
                    segments, cmap=line_color, zorder=idx + 1, norm=norm
                )
                lines.set_array(row)
                lines.set_linewidth(linewidth)
                ax.add_collection(lines)
            else:
                if callable(line_color) and kind == "gradient":
                    color = line_color(idx / values.shape[0])
                else:
                    color = line_color

                ax.plot(x, y, "-", color=color, zorder=idx, lw=linewidth)
            ax.fill_between(x, y_base, y, color=background_color, zorder=idx)

        if label_color is None:
            if callable(line_color):
                label_color = line_color(0.0)
            else:
                label_color = line_color

        ax.text(
            label_x,
            label_y,
            label,
            color=label_color,
            transform=ax.transAxes,
            fontproperties=self.font,
            size=label_size,
            verticalalignment=label_verticalalignment,
            bbox={"facecolor": background_color, "alpha": 1, "linewidth": 0},
            zorder=len(values) + 10,
        )

        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_facecolor(background_color)

        self.ax = ax
        return ax
