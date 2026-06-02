from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PolicyValidationError(ValueError):
    """Raised when a policy document is not suitable for upload."""


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise PolicyValidationError("JSON document must be an object.")
    return data


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def validate_policy(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = data.get("policy")
    if not isinstance(policy, dict):
        return ["Missing required object: policy"]

    name = policy.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("policy.name must be a non-empty string")

    enforcement_mode = policy.get("enforcementMode")
    if enforcement_mode not in {"transparent", "blocking"}:
        errors.append("policy.enforcementMode must be transparent or blocking")

    template = policy.get("template", {})
    if template and not isinstance(template, dict):
        errors.append("policy.template must be an object when provided")

    blocking = policy.get("blocking-settings", policy.get("blockingSettings", {}))
    violations = blocking.get("violations", []) if isinstance(blocking, dict) else []
    if violations and not isinstance(violations, list):
        errors.append("policy.blockingSettings.violations must be a list")

    for index, violation in enumerate(violations):
        if not isinstance(violation, dict):
            errors.append(f"violation #{index + 1} must be an object")
            continue
        if not violation.get("name"):
            errors.append(f"violation #{index + 1} is missing name")

    return errors


def require_valid_policy(data: dict[str, Any]) -> None:
    errors = validate_policy(data)
    if errors:
        raise PolicyValidationError("; ".join(errors))


def convert_asm_to_awaf(data: dict[str, Any]) -> dict[str, Any]:
    asm_policy = data.get("asmPolicy", {})
    awaf_target = data.get("awafTarget", {})
    violations = asm_policy.get("blockingSettings", {}).get("violations", [])

    converted_violations = []
    for violation in violations:
        name = violation.get("name") if isinstance(violation, dict) else None
        if name:
            converted_violations.append(
                {
                    "name": name,
                    "alarm": bool(violation.get("alarm", True)),
                    "block": awaf_target.get("enforcementMode", "blocking") == "blocking",
                }
            )

    return {
        "policy": {
            "name": awaf_target.get("name") or f"{asm_policy.get('name', 'asm')}-awaf",
            "applicationLanguage": awaf_target.get("applicationLanguage", "utf-8"),
            "enforcementMode": awaf_target.get("enforcementMode", "transparent"),
            "template": {"name": awaf_target.get("template", "POLICY_TEMPLATE_RAPID_DEPLOYMENT")},
            "blockingSettings": {"violations": converted_violations},
            "signatureSettings": {"signatureStaging": awaf_target.get("signatureStaging", True)},
            "description": awaf_target.get(
                "description",
                "Generated from a simplified ASM fragment. Review before applying.",
            ),
        }
    }
