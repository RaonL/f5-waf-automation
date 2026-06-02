import unittest

from f5_waf_toolkit.profiles import build_easy_policy


class ProfileTests(unittest.TestCase):
    def test_web_policy_defaults_to_transparent(self):
        policy = build_easy_policy("portal")

        self.assertEqual(policy["policy"]["name"], "portal")
        self.assertEqual(policy["policy"]["enforcementMode"], "transparent")
        self.assertFalse(policy["policy"]["blockingSettings"]["violations"][0]["block"])

    def test_api_policy_adds_api_protection(self):
        policy = build_easy_policy("api", app_type="api", mode="blocking")

        self.assertEqual(policy["policy"]["template"]["name"], "POLICY_TEMPLATE_API_SECURITY")
        self.assertTrue(policy["policy"]["apiProtection"]["enableJsonValidation"])
        self.assertTrue(policy["policy"]["blockingSettings"]["violations"][0]["block"])

    def test_policy_includes_server_technologies_and_signature_exceptions(self):
        policy = build_easy_policy(
            "portal",
            server_technologies=["Java", "MySQL"],
            disabled_signature_ids=[200101552],
        )

        self.assertEqual(
            policy["policy"]["server-technologies"],
            [
                {"serverTechnologyName": "Java"},
                {"serverTechnologyName": "MySQL"},
            ],
        )
        self.assertEqual(
            policy["policy"]["signatures"],
            [
                {
                    "signatureId": 200101552,
                    "enabled": False,
                    "performStaging": True,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
