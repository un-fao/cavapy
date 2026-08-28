import importlib
import unittest
from unittest.mock import patch


class TestVariables(unittest.TestCase):
    def test_tas_is_supported(self):
        import cavapy
        from cavapy.cava_config import VARIABLES_MAP

        cavapy_module = importlib.import_module("cavapy.cavapy")

        with (
            patch.object(cavapy_module, "_show_startup_announcements", lambda: None),
            patch.object(cavapy_module, "_validate_urls", lambda *args, **kwargs: None),
            patch.object(
                cavapy_module,
                "_geo_localize",
                lambda *args, **kwargs: {"xlim": (0.0, 1.0), "ylim": (0.0, 1.0)},
            ),
            patch.object(
                cavapy_module,
                "process_worker",
                lambda *args, variable=None, **kwargs: f"processed:{variable}",
            ),
        ):
            self.assertIn("tas", cavapy.VALID_VARIABLES)
            self.assertEqual(VARIABLES_MAP["tas"], "t2m")

            data = cavapy.get_climate_data(
                country="Togo",
                variables=["tas", "pr"],
                cordex_domain="AFR-22",
                rcp="rcp26",
                gcm="MPI",
                rcm="REMO",
                years_up_to=2030,
                dataset="CORDEX-CORE-BC",
                num_processes=1,
            )

        self.assertEqual(data, {"tas": "processed:tas", "pr": "processed:pr"})

    def test_main_api_forwards_buffer_to_bbox_localization(self):
        import cavapy

        cavapy_module = importlib.import_module("cavapy.cavapy")
        calls = []

        def fake_geo_localize(country, xlim, ylim, buffer, cordex_domain, obs, dataset):
            calls.append(
                {
                    "country": country,
                    "xlim": xlim,
                    "ylim": ylim,
                    "buffer": buffer,
                    "cordex_domain": cordex_domain,
                    "obs": obs,
                }
            )
            return {"xlim": (8.0, 13.0), "ylim": (-2.0, 3.0)}

        with (
            patch.object(cavapy_module, "_show_startup_announcements", lambda: None),
            patch.object(cavapy_module, "_validate_urls", lambda *args, **kwargs: None),
            patch.object(cavapy_module, "_geo_localize", fake_geo_localize),
            patch.object(
                cavapy_module,
                "process_worker",
                lambda *args, variable=None, **kwargs: f"processed:{variable}",
            ),
        ):
            cavapy.get_climate_data(
                country=None,
                xlim=(10.0, 11.0),
                ylim=(0.0, 1.0),
                buffer=2,
                variables=["tas"],
                cordex_domain="AFR-22",
                rcp="rcp26",
                gcm="MPI",
                rcm="REMO",
                years_up_to=2030,
                dataset="CORDEX-CORE-BC",
                num_processes=1,
            )

        self.assertEqual(calls[0]["buffer"], 2)
