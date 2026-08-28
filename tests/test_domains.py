import unittest

from cavapy.cava_config import VALID_DOMAINS
from cavapy.cava_validation import CORDEX_DOMAIN_EXTENTS, _validate_cordex_domain


# One realistic country bounding box per domain: (xlim, ylim).
IN_DOMAIN_BBOXES = {
    "AFR-22": ((-0.2, 1.8), (6.1, 11.2)),  # Togo
    "EUR-22": ((-5.1, 9.6), (41.3, 51.1)),  # France
    "NAM-22": ((-125.0, -66.9), (24.4, 49.4)),  # contiguous United States
    "AUS-22": ((112.9, 153.7), (-43.7, -10.6)),  # Australia
    "SAM-22": ((-73.9, -34.7), (-33.8, 5.3)),  # Brazil
    "CAM-22": ((-85.9, -82.5), (8.0, 11.2)),  # Costa Rica
    "SEA-22": ((102.1, 109.5), (8.4, 23.4)),  # Vietnam
    "WAS-22": ((68.1, 97.4), (6.5, 35.5)),  # India
    "CAS-22": ((73.5, 134.8), (18.1, 53.6)),  # China
    "EAS-22": ((129.4, 145.8), (31.0, 45.5)),  # Japan
}


class TestCordexDomainValidation(unittest.TestCase):
    def test_every_domain_accepts_a_realistic_country_bbox(self):
        for domain, (xlim, ylim) in IN_DOMAIN_BBOXES.items():
            dataset = "CORDEX-CORE-BC" if domain == "EAS-22" else "CORDEX-CORE"
            with self.subTest(domain=domain):
                _validate_cordex_domain(xlim, ylim, domain, dataset)

    def test_domain_table_covers_all_valid_domains(self):
        for domain in VALID_DOMAINS:
            self.assertIn(domain, CORDEX_DOMAIN_EXTENTS)

    def test_eas22_rejected_for_non_bias_corrected_dataset(self):
        xlim, ylim = IN_DOMAIN_BBOXES["EAS-22"]
        with self.assertRaisesRegex(ValueError, "CORDEX-CORE-BC"):
            _validate_cordex_domain(xlim, ylim, "EAS-22", "CORDEX-CORE")

    def test_out_of_domain_bbox_suggests_containing_domain(self):
        xlim, ylim = IN_DOMAIN_BBOXES["EUR-22"]
        with self.assertRaisesRegex(ValueError, "EUR-22"):
            _validate_cordex_domain(xlim, ylim, "AFR-22", "CORDEX-CORE")

    def test_unknown_domain_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not recognized"):
            _validate_cordex_domain((0.0, 1.0), (0.0, 1.0), "XYZ-22", "CORDEX-CORE")


if __name__ == "__main__":
    unittest.main()
