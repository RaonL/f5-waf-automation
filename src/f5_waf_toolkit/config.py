from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class F5Config:
    host: str
    username: str
    password: str
    verify_tls: bool = True
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "F5Config":
        host = os.getenv("F5_HOST", "").rstrip("/")
        username = os.getenv("F5_USERNAME", "")
        password = os.getenv("F5_PASSWORD", "")
        timeout = float(os.getenv("F5_TIMEOUT", "30"))

        return cls(
            host=host,
            username=username,
            password=password,
            verify_tls=_env_bool("F5_VERIFY_TLS", True),
            timeout=timeout,
        )

    def require_credentials(self) -> None:
        missing = [
            name
            for name, value in {
                "F5_HOST": self.host,
                "F5_USERNAME": self.username,
                "F5_PASSWORD": self.password,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
