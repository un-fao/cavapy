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
