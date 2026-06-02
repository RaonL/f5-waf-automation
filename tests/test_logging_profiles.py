import unittest

from f5_waf_toolkit.logging_profiles import build_application_security_logging_profile


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


if __name__ == "__main__":
    unittest.main()
