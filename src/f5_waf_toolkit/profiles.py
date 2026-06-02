from __future__ import annotations

from typing import Any

WEB_VIOLATIONS = [
    "VIOL_HTTP_PROTOCOL_VIOLATION",
    "VIOL_EVASION",
    "VIOL_SQL_INJECTION",
    "VIOL_XSS",
]

API_VIOLATIONS = [
    "VIOL_JSON_MALFORMED",
    "VIOL_PARAMETER_VALUE_METACHAR",
    "VIOL_OPEN_API_VIOLATION",
]

IP_INTELLIGENCE_CATEGORIES = [
    "Anonymous Proxy",
    "BotNets",
    "Denial of Service",
    "Infected Sources",
    "Phishing Proxies",
    "Scanners",
    "Spam Sources",
    "Tor Proxies",
    "Web Attacks",
    "Windows Exploits",
]

DVWA_LAB = {
    "f5_mgmt_ip": "192.168.137.125",
    "topology": "one-arm",
    "server_ip": "192.168.137.113",
    "virtual_server": "dvwa_vs",
    "vip": "192.168.137.211",
    "vip_port": 80,
    "policy_name": "dvwa-rapid-policy-v2",
    "logging_profile": "waf_detect_only",
    "server_technologies": ["Apache", "PHP", "MySQL"],
}


def build_easy_policy(
    name: str,
    app_type: str = "web",
    mode: str = "transparent",
    staging: bool = True,
    server_technologies: list[str] | None = None,
    disabled_signature_ids: list[int] | None = None,
    disallowed_geolocations: list[str] | None = None,
    ip_intelligence: bool = False,
    trust_xff: bool = False,
    xff_headers: list[str] | None = None,
    data_guard: bool = True,
    inspect_responses: bool = False,
    learning_mode: str = "manual",
    signature_accuracy: str = "high",
) -> dict[str, Any]:
    if app_type not in {"web", "api"}:
        raise ValueError("type must be web or api")
    if mode not in {"transparent", "blocking"}:
        raise ValueError("mode must be transparent or blocking")
    if learning_mode not in {"manual", "automatic", "fully-automatic"}:
        raise ValueError("learning mode must be manual, automatic, or fully-automatic")
    if signature_accuracy not in {"high", "medium", "low"}:
        raise ValueError("signature accuracy must be high, medium, or low")

    violations = API_VIOLATIONS if app_type == "api" else WEB_VIOLATIONS
    builder_mode = "automatic" if learning_mode == "fully-automatic" else learning_mode
    technologies = server_technologies or []
    signatures = disabled_signature_ids or []
    geolocations = disallowed_geolocations or []
    headers = xff_headers or []
    policy: dict[str, Any] = {
        "policy": {
            "name": name,
            "type": "security",
            "applicationLanguage": "utf-8",
            "enforcementMode": mode,
            "template": {
                "name": "POLICY_TEMPLATE_API_SECURITY"
                if app_type == "api"
                else "POLICY_TEMPLATE_RAPID_DEPLOYMENT"
            },
            "blocking-settings": {
                "violations": [
                    {
                        "name": violation,
                        "alarm": True,
                        "block": mode == "blocking",
                        "learn": True,
                    }
                    for violation in violations
                ]
            },
            "signature-sets": [
                {
                    "name": "Generic Detection Signatures",
                    "alarm": True,
                    "block": mode == "blocking",
                    "learn": True,
                }
            ],
            "signature-settings": {
                "signatureStaging": staging,
                "placeSignaturesInStaging": staging,
                "minimumAccuracyForAutoAddedSignatures": signature_accuracy,
                "attackSignatureFalsePositiveMode": "detect-and-allow" if staging else "detect",
            },
            "server-technologies": [
                {
                    "serverTechnologyName": technology,
                }
                for technology in technologies
            ],
            "signatures": [
                {
                    "signatureId": signature_id,
                    "enabled": False,
                    "performStaging": staging,
                }
                for signature_id in signatures
            ],
            "filetypes": [
                {
                    "name": "*",
                    "type": "wildcard",
                    "allowed": True,
                    "performStaging": staging,
                    "responseCheck": inspect_responses,
                }
            ],
            "policy-builder-filetype": {
                "learnExplicitFiletypes": "never",
            },
            "policy-builder-parameter": {
                "learnExplicitParameters": "never",
                "parameterLearningLevel": "global",
            },
            "policy-builder-url": {
                "learnExplicitUrls": "never",
            },
            "policy-builder-cookie": {
                "learnExplicitCookies": "never",
            },
            "policy-builder-server-technologies": {
                "enableServerTechnologiesDetection": True,
            },
            "policy-builder": {
                "learningMode": builder_mode,
                "fullyAutomatic": learning_mode == "fully-automatic",
                "learnFromResponses": inspect_responses,
            },
            "general": {
                "enforcementReadinessPeriod": 7,
                "maskCreditCardNumbersInRequest": True,
                "trustXff": trust_xff,
                "customXffHeaders": headers,
            },
            "data-guard": {
                "enabled": data_guard,
                "creditCardNumbers": True,
                "maskData": True,
                "lastCcnDigitsToExpose": 4,
                "usSocialSecurityNumbers": False,
            },
            "disallowed-geolocations": [
                {
                    "countryName": country,
                }
                for country in geolocations
            ],
            "description": "Generated by f5-waf quickstart. Review and tune before production.",
        }
    }

    if ip_intelligence:
        policy["policy"]["ip-intelligence"] = {
            "enabled": True,
            "ipIntelligenceCategories": [
                {
                    "category": category,
                    "alarm": True,
                    "block": mode == "blocking",
                }
                for category in IP_INTELLIGENCE_CATEGORIES
            ],
        }

    if app_type == "api":
        policy["policy"]["apiProtection"] = {
            "enableJsonValidation": True,
            "enableXmlValidation": False,
            "enforceContentType": True,
            "validateParameters": True,
        }

    return policy


def build_rollout_checklist(
    policy_name: str,
    virtual_server: str = "",
    logging_profile: str = "waf_detect_only",
    deployment_scenario: str = "existing",
    inspect_responses: bool = False,
    mode: str = "transparent",
    staging: bool = True,
    learning_mode: str = "manual",
    signature_accuracy: str = "high",
    log_scope: str = "violations",
    environment: dict[str, Any] | None = None,
) -> str:
    target = virtual_server or "<virtual-server-name>"
    scenario_text = {
        "existing": "Existing Virtual Server",
        "new": "New Virtual Server",
        "unassigned": "Do not associate with Virtual Server",
    }[deployment_scenario]
    response_text = "Enabled" if inspect_responses else "Disabled"
    staging_text = "Enabled" if staging else "Disabled"
    lab_note = ""
    if mode == "blocking" and not staging:
        lab_note = "- Blocking + Signature Staging Disabled 구성은 차단 테스트가 빠르지만 운영 첫 적용에는 신중하게 사용한다.\n"
    environment_block = ""
    if environment:
        environment_block = f"""## 0. 고정 랩 환경

| 항목 | 값 |
| --- | --- |
| F5 BIG-IP 관리 IP | `{environment.get("f5_mgmt_ip", "")}` |
| 구성 방식 | `{environment.get("topology", "")}` |
| DVWA Real Server IP | `{environment.get("server_ip", "")}` |
| Virtual Server | `{environment.get("virtual_server", "")}` |
| VIP | `{environment.get("vip", "")}:{environment.get("vip_port", "")}` |
| Server Technologies | `{", ".join(environment.get("server_technologies", []))}` |

"""
    return f"""# {policy_name} WAF 적용 체크리스트

{environment_block}
## 1. 정책 생성

- Rapid Deployment Policy 기반으로 정책을 생성한다.
- Deployment Scenario: `{scenario_text}`
- Enforcement Mode: `{mode}`
- Learning Mode: `{learning_mode}`
- Signature Accuracy: `{signature_accuracy}`
- Application Language는 UTF-8로 둔다.
- Enforcement Readiness Period는 기본 7일로 둔다.
- Signature Staging: `{staging_text}`
- Apply Signatures to Responses: `{response_text}`
{lab_note}

## 2. Virtual Server 연결

- 대상 Virtual Server: `{target}`
- 기존 Virtual Server를 사용할 경우 HTTP profile이 있어야 한다.
- 기존 Virtual Server에 local traffic policy가 이미 연결되어 있으면 먼저 구조를 확인한다.
- Virtual Server에 연결하지 않고 정책만 만들면 트래픽이 지나가기 전까지 학습이 시작되지 않는다.
- Security 탭에서 Application Security Policy가 Enabled인지 확인한다.
- 생성한 정책 `{policy_name}`이 연결되어 있는지 확인한다.

## 3. Logging Profile

- Application Security Logging Profile 이름: `{logging_profile}`
- Logging Scope: `{log_scope}`
- 탐지 초기에는 로그가 남는지 확인한다. 문제 분석 기간에는 all requests, 운영 상시에는 violations only가 더 가볍다.
- 운영 환경에서는 모든 요청/응답 로깅이 성능에 영향을 줄 수 있으므로 필요한 기간에만 사용한다.

## 4. 검증

- 정상 사용자가 주요 화면/API를 호출한다.
- Security > Event Logs > Application > Requests에서 로그가 쌓이는지 확인한다.
- Traffic Learning 제안을 검토한다.
- 오탐이 반복되는 항목은 정책 튜닝 후 Apply Policy 한다.

## 5. 차단 전환

- 최소 7일 이상의 Enforcement Readiness 기간을 두고 로그를 검토한다.
- 오탐이 충분히 줄어든 뒤 Blocking 모드 정책으로 전환한다.
- 차단 전환 후에도 Support ID 기준으로 로그를 모니터링한다.
"""


def build_dvwa_lab_policy(
    name: str = DVWA_LAB["policy_name"],
    mode: str = "transparent",
    staging: bool = True,
    learning_mode: str = "manual",
    signature_accuracy: str = "high",
) -> dict[str, Any]:
    return build_easy_policy(
        name=name,
        app_type="web",
        mode=mode,
        staging=staging,
        server_technologies=list(DVWA_LAB["server_technologies"]),
        learning_mode=learning_mode,
        signature_accuracy=signature_accuracy,
    )
