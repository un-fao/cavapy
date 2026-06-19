"""CAVA Python package for retrieving and visualizing climate data."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cavapy")
except PackageNotFoundError:
    __version__ = "0+unknown"

from .cavapy import get_climate_data
from .cava_plot import plot_spatial_map, plot_time_series
from .cava_config import (
    VALID_DOMAINS,
    VALID_GCM,
    VALID_RCM,
    VALID_RCPS,
    VALID_VARIABLES,
)

__all__ = [
    "get_climate_data",
    "plot_spatial_map",
    "plot_time_series",
    "VALID_DOMAINS",
    "VALID_GCM",
    "VALID_RCM",
    "VALID_RCPS",
    "VALID_VARIABLES",
]
