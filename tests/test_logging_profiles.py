import unittest

from f5_waf_toolkit.logging_profiles import (
    build_application_security_logging_profile,
    build_tmsh_create_logging_profile_command,
)


class LoggingProfileTests(unittest.TestCase):
    def test_builds_staged_signature_logging_profile(self):
        profile = build_application_security_logging_profile("waf_detect_only")

        self.assertEqual(profile["name"], "waf_detect_only")
        self.assertEqual(profile["application"][0]["localStorage"], "enabled")
        self.assertEqual(profile["application"][0]["remoteStorage"], "none")
        self.assertEqual(
            profile["application"][0]["filter"],
            [
                {
                    "key": "request-type",
                    "values": ["illegal-including-staged-signatures"],
                }
            ],
        )

    def test_builds_tmsh_create_command(self):
        profile = build_application_security_logging_profile("waf_detect_only")

        command = build_tmsh_create_logging_profile_command(profile)

        self.assertIn("tmsh create security log profile waf_detect_only", command)
        self.assertIn("application add", command)
        self.assertIn("illegal-including-staged-signatures", command)


if __name__ == "__main__":
    unittest.main()
