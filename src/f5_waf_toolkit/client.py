from __future__ import annotations

from typing import Any

from .config import F5Config


class F5ApiError(RuntimeError):
    def __init__(self, status_code: int, message: str, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


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
        if response.status_code >= 400:
            body = response.text.strip()
            raise F5ApiError(
                response.status_code,
                f"{response.status_code} {response.reason} for url: {url}",
                body,
            )
        if not response.content:
            return {"status": response.status_code}
        return response.json()

    def create_security_log_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("Install project dependencies before using --apply: python -m pip install -e .") from exc

        self.config.require_credentials()
        url = f"{self.config.host}/mgmt/tm/security/log/profile"
        response = requests.post(
            url,
            auth=(self.config.username, self.config.password),
            json=profile,
            timeout=self.config.timeout,
            verify=self.config.verify_tls,
        )
        if response.status_code >= 400:
            body = response.text.strip()
            raise F5ApiError(
                response.status_code,
                f"{response.status_code} {response.reason} for url: {url}",
                body,
            )
        if not response.content:
            return {"status": response.status_code}
        return response.json()
