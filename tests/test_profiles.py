import unittest

from f5_waf_toolkit.profiles import build_easy_policy, build_rollout_checklist


class ProfileTests(unittest.TestCase):
    def test_web_policy_defaults_to_transparent(self):
        policy = build_easy_policy("portal")

        self.assertEqual(policy["policy"]["name"], "portal")
        self.assertEqual(policy["policy"]["enforcementMode"], "transparent")
        self.assertFalse(policy["policy"]["blocking-settings"]["violations"][0]["block"])
        self.assertEqual(policy["policy"]["policy-builder-filetype"]["learnExplicitFiletypes"], "never")
        self.assertTrue(policy["policy"]["data-guard"]["enabled"])

    def test_api_policy_adds_api_protection(self):
        policy = build_easy_policy("api", app_type="api", mode="blocking")

        self.assertEqual(policy["policy"]["template"]["name"], "POLICY_TEMPLATE_API_SECURITY")
        self.assertTrue(policy["policy"]["apiProtection"]["enableJsonValidation"])
        self.assertTrue(policy["policy"]["blocking-settings"]["violations"][0]["block"])

    def test_policy_includes_server_technologies_and_signature_exceptions(self):
        policy = build_easy_policy(
            "portal",
            server_technologies=["Java", "MySQL"],
            disabled_signature_ids=[200101552],
            disallowed_geolocations=["American Samoa"],
            ip_intelligence=True,
            trust_xff=True,
            xff_headers=["X-Forwarded-For"],
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
        self.assertEqual(policy["policy"]["disallowed-geolocations"], [{"countryName": "American Samoa"}])
        self.assertTrue(policy["policy"]["ip-intelligence"]["enabled"])
        self.assertTrue(policy["policy"]["general"]["trustXff"])

    def test_rollout_checklist_includes_operational_steps(self):
        checklist = build_rollout_checklist("portal", "portal_vs", "waf_detect_only")

        self.assertIn("portal_vs", checklist)
        self.assertIn("Logging Profile", checklist)
        self.assertIn("Traffic Learning", checklist)


if __name__ == "__main__":
    unittest.main()
