import tempfile
import unittest
from pathlib import Path

from f5_waf_toolkit.logs import parse_jsonl_to_csv


class LogTests(unittest.TestCase):
    def test_parse_jsonl_to_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "events.jsonl"
            output = Path(directory) / "events.csv"
            source.write_text(
                '{"timestamp":"2026-06-02T00:00:00Z","ip_client":"192.0.2.1","http_method":"GET","uri":"/","violation_name":"VIOL_XSS"}\n',
                encoding="utf-8",
            )

            count = parse_jsonl_to_csv(source, output)
            text = output.read_text(encoding="utf-8")

        self.assertEqual(count, 1)
        self.assertIn("client_ip", text)
        self.assertIn("192.0.2.1", text)


if __name__ == "__main__":
    unittest.main()
