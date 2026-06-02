from __future__ import annotations

import re
import shlex
from typing import Any

REQUEST_TYPE_VALUES = {
    "blocked": "blocked",
    "illegal": "illegal",
    "illegal-including-staged": "illegal-including-staged-signatures",
    "all": "all",
}

SAFE_PROFILE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def build_application_security_logging_profile(
    name: str,
    description: str = "Illegal requests, and requests",
    request_type: str = "illegal-including-staged",
    response_logging: str = "none",
) -> dict[str, Any]:
    if request_type not in REQUEST_TYPE_VALUES:
        allowed = ", ".join(sorted(REQUEST_TYPE_VALUES))
        raise ValueError(f"request type must be one of: {allowed}")
    if response_logging not in {"none", "illegal", "all"}:
        raise ValueError("response logging must be none, illegal, or all")

    return {
        "name": name,
        "partition": "Common",
        "description": description,
        "application": [
            {
                "name": "asm",
                "localStorage": "enabled",
                "remoteStorage": "none",
                "logicOperation": "or",
                "responseLogging": response_logging,
                "filter": [
                    {
                        "key": "request-type",
                        "values": [
                            REQUEST_TYPE_VALUES[request_type],
                        ],
                    }
                ],
            }
        ],
    }


def require_safe_profile_name(name: str) -> None:
    if not SAFE_PROFILE_NAME.fullmatch(name):
        raise ValueError("logging profile name may contain only letters, numbers, dot, underscore, or hyphen")


def build_tmsh_create_logging_profile_command(profile: dict[str, Any]) -> str:
    name = str(profile["name"])
    require_safe_profile_name(name)
    application = profile["application"][0]
    filters = application["filter"]
    request_type = filters[0]["values"][0]
    if request_type not in REQUEST_TYPE_VALUES.values():
        raise ValueError("unsupported logging profile request type")

    response_logging = application.get("responseLogging", "none")
    if response_logging not in {"none", "illegal", "all"}:
        raise ValueError("unsupported logging profile response logging value")

    description = str(profile.get("description", ""))
    return (
        "tmsh create security log profile "
        f"{name} "
        f"description {shlex.quote(description)} "
        "application add { asm { "
        "local-storage enabled "
        "remote-storage none "
        "logic-operation or "
        f"response-logging {response_logging} "
        "filter add { request-type { "
        f"values add {{ {request_type} }} "
        "} } "
        "} }"
    )
