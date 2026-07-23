import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from cartopy.mpl.geoaxes import GeoAxes

from cavapy.cava_plot import plot_spatial_map


class TestSpatialPlotting(unittest.TestCase):
    def test_spatial_map_renders_with_constrained_layout(self):
        data = xr.DataArray(
            np.arange(50, dtype=float).reshape(2, 5, 5),
            dims=("time", "latitude", "longitude"),
            coords={
                "time": np.array(
                    ["1991-01-01", "1992-01-01"], dtype="datetime64[D]"
                ),
                "latitude": np.linspace(30.0, 32.0, 5),
                "longitude": np.linspace(72.0, 74.0, 5),
            },
            name="tasmax",
            attrs={"units": "°C"},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "spatial-map.png"
            with patch.object(GeoAxes, "add_feature", return_value=None):
                fig = plot_spatial_map(
                    data,
                    time_period=(1991, 1992),
                    save_path=save_path,
                )
                fig.canvas.draw()

            self.assertEqual(
                fig.get_layout_engine().__class__.__name__, "ConstrainedLayoutEngine"
            )
            self.assertTrue(all(ax.get_position().width > 0 for ax in fig.axes))
            title_bounds = fig.axes[0].title.get_window_extent(
                fig.canvas.get_renderer()
            ).bounds
            self.assertTrue(np.isfinite(title_bounds).all())
            self.assertTrue(save_path.is_file())
            image = plt.imread(save_path)
            self.assertGreater(image.shape[1], image.shape[0])
            plt.close(fig)


if __name__ == "__main__":
    unittest.main()
