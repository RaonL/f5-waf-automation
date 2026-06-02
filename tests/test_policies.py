import unittest

from f5_waf_toolkit.policies import convert_asm_to_awaf, validate_policy


class PolicyTests(unittest.TestCase):
    def test_validate_policy_accepts_minimal_valid_policy(self):
        errors = validate_policy(
            {
                "policy": {
                    "name": "demo",
                    "enforcementMode": "transparent",
                    "blockingSettings": {"violations": [{"name": "VIOL_XSS"}]},
                }
            }
        )

        self.assertEqual(errors, [])

    def test_validate_policy_rejects_missing_name(self):
        errors = validate_policy({"policy": {"enforcementMode": "blocking"}})

        self.assertIn("policy.name must be a non-empty string", errors)

    def test_convert_asm_to_awaf_blocks_when_target_is_blocking(self):
        converted = convert_asm_to_awaf(
            {
                "asmPolicy": {
                    "name": "legacy",
                    "blockingSettings": {"violations": [{"name": "VIOL_SQL_INJECTION"}]},
                },
                "awafTarget": {"name": "modern", "enforcementMode": "blocking"},
            }
        )

        self.assertEqual(converted["policy"]["name"], "modern")
        self.assertIs(converted["policy"]["blockingSettings"]["violations"][0]["block"], True)


if __name__ == "__main__":
    unittest.main()
