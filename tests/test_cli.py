import unittest
import tempfile
from pathlib import Path

from f5_waf_toolkit.cli import main


class CliTests(unittest.TestCase):
    def test_policy_validate_command_passes(self):
        result = main(["policy", "validate", "examples/policies/baseline-awaf-policy.json"])

        self.assertEqual(result, 0)

    def test_quickstart_writes_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "policy.json"
            result = main(
                [
                    "quickstart",
                    "--name",
                    "easy-app",
                    "--type",
                    "web",
                    "--mode",
                    "transparent",
                    "--output",
                    str(output),
                    "--server-tech",
                    "Java",
                    "--disable-signature-id",
                    "200101552",
                ]
            )

            self.assertEqual(result, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("easy-app", text)
            self.assertIn("Java", text)
            self.assertIn("200101552", text)


if __name__ == "__main__":
    unittest.main()
