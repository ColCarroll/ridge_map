import codecs
import os
import re
from setuptools import setup, find_packages

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
README_FILE = os.path.join(PROJECT_ROOT, "README.md")
VERSION_FILE = os.path.join(PROJECT_ROOT, "ridge_map", "__init__.py")


def get_long_description():
    with codecs.open(README_FILE, "rt") as buff:
        return buff.read()


def get_version():
    lines = open(VERSION_FILE, "rt").readlines()
    version_regex = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in lines:
        mo = re.search(version_regex, line, re.M)
        if mo:
            return mo.group(1)
    raise RuntimeError("Unable to find version in %s." % (VERSION_FILE,))


setup(
    name="ridge_map",
    version=get_version(),
    description="1d lines, 3d maps",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Colin Carroll",
    author_email="colcarroll@gmail.com",
    url="https://github.com/ColCarroll/ridge_map",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(exclude=["test"]),
    install_requires=["SRTM.py", "numpy", "matplotlib", "scikit-image>=0.14.2"],
    include_package_data=True,
)
