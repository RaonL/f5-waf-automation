from __future__ import annotations

from typing import Any

from .config import F5Config


class F5Client:
    def __init__(self, config: F5Config) -> None:
        self.config = config

    def create_policy(self, policy: dict[str, Any]) -> dict[str, Any]:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("Install project dependencies before using --apply: python -m pip install -e .") from exc

        self.config.require_credentials()
        url = f"{self.config.host}/mgmt/tm/asm/policies"
        response = requests.post(
            url,
            auth=(self.config.username, self.config.password),
            json=policy,
            timeout=self.config.timeout,
            verify=self.config.verify_tls,
        )
        response.raise_for_status()
        if not response.content:
            return {"status": response.status_code}
        return response.json()
