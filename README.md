# F5 WAF 쉽게 설정하기

F5 BIG-IP ASM/AWAF에서 Rapid Deployment Policy를 쉽게 시작하기 위한 CLI 도구입니다.

목표는 복잡한 WAF JSON을 직접 처음부터 쓰는 것이 아니라, 몇 가지 옵션만으로 탐지 모드 정책 초안을 만들고, BIG-IP GUI에서 확인해야 할 항목까지 체크리스트로 남기는 것입니다.

## 기준 문서

이 저장소의 기본 흐름은 아래 문서를 기준으로 잡았습니다.

- F5 공식 BIG-IP ASM 12.1 Getting Started: Using Rapid Deployment
- F5 공식 BIG-IP ASM 13.0 Getting Started: Using Rapid Deployment to Create a Security Policy
- F5 Agility Lab: transparent rapid deployment policy, logging profile, log validation
- TechClick Rapid Deployment setup: Rapid Deployment 생성 및 Signature Staging
- LinkedIn Rapid Deployment ASP 요약: signature staging, generic signatures, wildcard 중심 학습, Data Guard

## 빠른 시작

설치:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

웹 서비스 탐지 모드 정책 생성:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --output out\my-web-app-policy.json
```

서버 기술까지 지정:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --server-tech Java --server-tech MySQL --output out\my-web-app-policy.json
```

정책 JSON과 BIG-IP 적용 체크리스트를 같이 생성:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --server-tech Java --server-tech MySQL --virtual-server my_web_vs --logging-profile waf_detect_only --checklist-output out\my-web-app-checklist.md --output out\my-web-app-policy.json
```

API 서비스 정책 생성:

```powershell
f5-waf quickstart --name my-api --type api --mode transparent --output out\my-api-policy.json
```

정책 검증:

```powershell
f5-waf policy validate out\my-web-app-policy.json
```

BIG-IP 업로드 dry-run:

```powershell
f5-waf policy upload out\my-web-app-policy.json
```

실제 적용:

```powershell
$env:F5_HOST="https://bigip.example.com"
$env:F5_USERNAME="automation-user"
$env:F5_PASSWORD="secret"
f5-waf policy upload out\my-web-app-policy.json --apply
```

## Rapid Deployment 기본값

`quickstart`는 Rapid Deployment 흐름에 맞춰 아래 값을 생성합니다.

| 항목 | 생성값 |
| --- | --- |
| Policy Template | `POLICY_TEMPLATE_RAPID_DEPLOYMENT` |
| Policy Type | `security` |
| Application Language | `utf-8` |
| Enforcement Mode | 기본 `transparent` |
| Enforcement Readiness Period | `7`일 |
| Signature Staging | 켜짐 |
| Signature Set | `Generic Detection Signatures` |
| Data Guard | 켜짐, 신용카드 번호 마스킹 |
| File Type/URL/Parameter/Cookie Learning | 명시 엔티티 학습 `never`, wildcard 중심 |

F5 공식 12.1 문서 기준으로 Rapid Deployment는 HTTP compliance, mandatory HTTP headers, information leakage, illegal HTTP methods, response codes, cookie RFC compliance, attack signatures, evasion technique, disallowed geolocation, disallowed users/sessions/IPs, request length, disallowed file upload content, character conversion failure, modified ASM cookies 등을 기본 보안 검사로 포함합니다.

## 탐지 모드에서 중요한 설정

| 설정 | 추천값 | 이유 |
| --- | --- | --- |
| Enforcement Mode | `transparent` | 처음에는 차단하지 않고 로그/학습 중심으로 운영 |
| Signature Staging | 켜짐 | 신규/업데이트 시그니처가 바로 차단되지 않도록 관찰 기간 확보 |
| Alarm | 켜짐 | 위반 이벤트를 로그와 리포트에서 확인 |
| Block | 꺼짐 | 탐지 단계에서는 사용자 요청을 막지 않음 |
| Server Technologies | 애플리케이션에 맞게 지정 | Java, MySQL, IIS 같은 기술별 시그니처 적용 |
| Data Guard | 켜짐 | 민감 정보가 로그/화면에 노출되는 것을 줄임 |
| Logging Profile | 별도 적용 | WAF가 실제 요청을 보고 있는지 확인 |

## 추가 옵션

응답에도 공격 시그니처 검사 적용:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --inspect-responses --output out\my-web-app-policy.json
```

Geo 차단 국가 추가:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --disallow-country "American Samoa" --output out\my-web-app-policy.json
```

IP Intelligence를 alarm 중심으로 추가:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --ip-intelligence --output out\my-web-app-policy.json
```

신뢰 가능한 프록시 뒤에서 X-Forwarded-For 사용:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --trust-xff --xff-header X-Forwarded-For --output out\my-web-app-policy.json
```

`--trust-xff`는 BIG-IP 앞단 프록시가 신뢰 가능한 경우에만 사용하세요. 클라이언트가 XFF 헤더를 직접 조작할 수 있는 구조에서는 켜면 안 됩니다.

## BIG-IP GUI 체크리스트에서 확인할 것

공식 12.1 문서 기준으로 Rapid Deployment 생성 시 Deployment Scenario를 고르게 됩니다.

- Existing Virtual Server: 기존 VS에 정책 연결
- New Virtual Server: 새 VS와 pool을 같이 생성
- Do not associate with Virtual Server: 정책만 만들고 나중에 VS 연결

기존 Virtual Server를 사용할 때는 HTTP profile이 있어야 하며, local traffic policy가 이미 연결되어 있으면 먼저 구성을 확인해야 합니다. 정책을 VS에 연결하지 않으면 트래픽이 ASM을 지나가지 않으므로 학습이 시작되지 않습니다.

체크리스트 생성:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --deployment-scenario existing --virtual-server my_web_vs --logging-profile waf_detect_only --checklist-output out\my-web-app-checklist.md --output out\my-web-app-policy.json
```

## 운영 순서

1. `transparent` 모드로 정책 생성
2. 백엔드 기술을 알면 `--server-tech`로 지정
3. 필요 시 `--inspect-responses`, `--ip-intelligence`, `--disallow-country` 추가
4. BIG-IP에 적용
5. Logging Profile을 적용하고 Event Logs를 확인
6. Traffic Learning 제안을 검토
7. 오탐이 반복되는 항목을 튜닝하고 Apply Policy
8. 최소 7일 이상 관찰 후 `blocking` 전환 검토

## 명령어 요약

| 명령 | 설명 |
| --- | --- |
| `f5-waf quickstart` | 쉬운 옵션으로 WAF 정책 초안 생성 |
| `f5-waf policy validate` | 정책 JSON 검증 |
| `f5-waf policy upload` | 정책 업로드, 기본값은 dry-run |
| `f5-waf logs parse` | WAF JSONL 로그를 CSV로 변환 |
| `f5-waf asm convert` | 단순 ASM 정책 조각을 AWAF 정책 초안으로 변환 |

`quickstart` 주요 옵션:

| 옵션 | 설명 |
| --- | --- |
| `--type web` | 일반 웹 애플리케이션 |
| `--type api` | JSON API 중심 애플리케이션 |
| `--mode transparent` | 탐지 모드 |
| `--mode blocking` | 차단 모드 |
| `--server-tech Java` | 서버 기술 지정, 여러 번 사용 가능 |
| `--inspect-responses` | 응답에도 공격 시그니처 검사 적용 |
| `--disable-signature-id 200101552` | 특정 공격 시그니처 비활성화 |
| `--disallow-country "Country"` | Geo 차단 국가 추가 |
| `--ip-intelligence` | IP Intelligence 카테고리를 alarm 중심으로 추가 |
| `--trust-xff` | 신뢰 가능한 프록시 환경에서 XFF 신뢰 |
| `--deployment-scenario existing` | 체크리스트용 배포 시나리오 |
| `--checklist-output file.md` | VS 연결, 로깅, Traffic Learning 체크리스트 생성 |
| `--no-staging` | 시그니처 staging 비활성화, 최초 적용에는 비추천 |

## 환경변수

실제 업로드할 때만 필요합니다. 실제 계정 정보는 절대 커밋하지 마세요.

| 변수 | 설명 |
| --- | --- |
| `F5_HOST` | BIG-IP 주소 |
| `F5_USERNAME` | BIG-IP 사용자 이름 |
| `F5_PASSWORD` | BIG-IP 비밀번호 |
| `F5_VERIFY_TLS` | TLS 인증서 검증 여부, 기본값 `true` |
| `F5_TIMEOUT` | 요청 제한 시간, 기본값 `30`초 |

## 테스트

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```
