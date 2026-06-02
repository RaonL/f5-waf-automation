from __future__ import annotations

from typing import Any

REQUEST_TYPE_VALUES = {
    "blocked": "blocked",
    "illegal": "illegal",
    "illegal-including-staged": "illegal-including-staged-signatures",
    "all": "all",
}


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
