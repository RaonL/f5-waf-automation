import unittest

from f5_waf_toolkit.cli import main


class CliTests(unittest.TestCase):
    def test_policy_validate_command_passes(self):
        result = main(["policy", "validate", "examples/policies/baseline-awaf-policy.json"])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
