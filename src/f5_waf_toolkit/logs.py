from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

FIELDS = [
    "timestamp",
    "client_ip",
    "method",
    "uri",
    "violation",
    "support_id",
    "policy_name",
    "severity",
]


def normalize_log_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": event.get("timestamp") or event.get("event_timestamp"),
        "client_ip": event.get("ip_client") or event.get("clientIp") or event.get("client_ip"),
        "method": event.get("http_method") or event.get("method"),
        "uri": event.get("uri") or event.get("request_uri"),
        "violation": event.get("violation") or event.get("violation_name"),
        "support_id": event.get("support_id") or event.get("supportId"),
        "policy_name": event.get("policy_name") or event.get("policyName"),
        "severity": event.get("severity") or event.get("severity_string"),
    }


def parse_jsonl_to_csv(input_path: str | Path, output_path: str | Path) -> int:
    rows = []
    with Path(input_path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                event = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
            if isinstance(event, dict):
                rows.append(normalize_log_event(event))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
