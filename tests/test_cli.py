import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from f5_waf_toolkit.client import F5ApiError
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
                    "--ip-intelligence",
                    "--inspect-responses",
                    "--learning-mode",
                    "automatic",
                    "--signature-accuracy",
                    "medium",
                    "--checklist-output",
                    str(Path(directory) / "checklist.md"),
                ]
            )

            self.assertEqual(result, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("easy-app", text)
            self.assertIn("Java", text)
            self.assertIn("200101552", text)
            self.assertIn("ip-intelligence", text)
            self.assertIn("responseCheck", text)
            self.assertIn("minimumAccuracyForAutoAddedSignatures", text)
            self.assertTrue((Path(directory) / "checklist.md").exists())

    def test_lab_dvwa_writes_fixed_environment_files(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = Path(directory) / "policy.json"
            checklist = Path(directory) / "checklist.md"
            result = main(
                [
                    "lab",
                    "dvwa",
                    "--output",
                    str(policy),
                    "--checklist-output",
                    str(checklist),
                ]
            )

            self.assertEqual(result, 0)
            self.assertIn("dvwa-rapid-policy-v2", policy.read_text(encoding="utf-8"))
            self.assertIn("192.168.137.211", checklist.read_text(encoding="utf-8"))

    def test_policy_upload_apply_posts_unwrapped_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            policy_file = Path(directory) / "policy.json"
            policy_file.write_text(
                '{"policy":{"name":"demo","enforcementMode":"transparent"}}',
                encoding="utf-8",
            )
            with patch("f5_waf_toolkit.config.F5Config.require_credentials"), patch.dict(
                "os.environ",
                {"F5_HOST": "https://bigip.example.com", "F5_USERNAME": "admin", "F5_PASSWORD": "secret"},
            ), patch("f5_waf_toolkit.cli.F5Client.create_policy") as create_policy:
                create_policy.return_value = {"name": "demo"}

                result = main(["policy", "upload", str(policy_file), "--apply"])

            self.assertEqual(result, 0)
            create_policy.assert_called_once_with({"name": "demo", "enforcementMode": "transparent"})

    def test_policy_upload_prints_bigip_error_body(self):
        with tempfile.TemporaryDirectory() as directory:
            policy_file = Path(directory) / "policy.json"
            policy_file.write_text(
                '{"policy":{"name":"demo","enforcementMode":"transparent"}}',
                encoding="utf-8",
            )
            body = '{"code":400,"message":"bad policy","kind":":resterrorresponse"}'
            with patch("f5_waf_toolkit.config.F5Config.require_credentials"), patch.dict(
                "os.environ",
                {"F5_HOST": "https://bigip.example.com", "F5_USERNAME": "admin", "F5_PASSWORD": "secret"},
            ), patch("f5_waf_toolkit.cli.F5Client.create_policy") as create_policy, patch(
                "sys.stderr"
            ) as stderr:
                create_policy.side_effect = F5ApiError(400, "400 Bad Request", body)

                result = main(["policy", "upload", str(policy_file), "--apply"])

            self.assertEqual(result, 1)
            output = "".join(str(call.args[0]) for call in stderr.write.call_args_list if call.args)
            self.assertIn("BIG-IP response:", output)
            self.assertIn("bad policy", output)

    def test_logging_profile_create_dry_run(self):
        result = main(["logging", "profile", "create", "--name", "waf_detect_only"])

        self.assertEqual(result, 0)

    def test_logging_profile_create_apply_posts_payload(self):
        with patch("f5_waf_toolkit.config.F5Config.require_credentials"), patch.dict(
            "os.environ",
            {"F5_HOST": "https://bigip.example.com", "F5_USERNAME": "admin", "F5_PASSWORD": "secret"},
        ), patch("f5_waf_toolkit.cli.F5Client.create_security_log_profile") as create_profile:
            create_profile.return_value = {"name": "waf_detect_only"}

            result = main(["logging", "profile", "create", "--name", "waf_detect_only", "--apply"])

        self.assertEqual(result, 0)
        payload = create_profile.call_args.args[0]
        self.assertEqual(payload["name"], "waf_detect_only")
        self.assertEqual(payload["application"][0]["filter"][0]["values"], ["illegal-including-staged-signatures"])


if __name__ == "__main__":
    unittest.main()
