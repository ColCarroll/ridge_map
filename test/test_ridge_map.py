from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
import pytest

from ridge_map import RidgeMap


# We monkeypatch srtm in conftest.py, and here
# we make sure not to request google fonts
@pytest.fixture(scope="function")
def mapper():
    return RidgeMap(font=FontProperties())


def test_default_plot(mapper):
    mapper.plot_map()


def test_gradient_plot(mapper):
    mapper.plot_map(line_color=plt.get_cmap("viridis"))


def test_elevation_plot(mapper):
    mapper.plot_map(line_color=plt.get_cmap("viridis"), kind="elevation")

