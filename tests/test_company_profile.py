import unittest

from dcfs.integration.company_profile import CompanyProfileError, load_company_profile, validate_company_profile


class CompanyProfileTests(unittest.TestCase):
    def test_load_default_profile(self):
        profile = load_company_profile()

        self.assertEqual(profile["id"], "factory_simulator_corrugados")
        self.assertGreater(profile["machines"], 0)

    def test_validate_profile_requires_fields(self):
        with self.assertRaises(CompanyProfileError):
            validate_company_profile({"id": "missing_fields"})


if __name__ == "__main__":
    unittest.main()
