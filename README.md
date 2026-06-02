# F5 WAF 쉽게 설정하기

F5 BIG-IP Advanced WAF(AWAF)를 매번 복잡한 JSON과 API 문서부터 보지 않고, 간단한 명령으로 정책 초안을 만들고 검증하고 적용하기 위한 저장소입니다.

목표는 단순합니다.

- 웹 서비스인지 API 서비스인지 고릅니다.
- 처음에는 관찰 모드(`transparent`)로 시작합니다.
- 문제가 없으면 차단 모드(`blocking`)로 바꿉니다.
- 업로드 전에는 항상 dry-run으로 확인합니다.

## 가장 쉬운 사용법

설치:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

웹 서비스용 WAF 정책 초안 만들기:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --output out\my-web-app-policy.json
```

서버 기술까지 지정해서 탐지용 정책 만들기:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --server-tech Java --server-tech MySQL --output out\my-web-app-policy.json
```

Virtual Server 연결과 로깅 프로파일 확인용 체크리스트까지 같이 만들기:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --server-tech Java --server-tech MySQL --virtual-server my_web_vs --logging-profile waf_detect_only --checklist-output out\my-web-app-checklist.md --output out\my-web-app-policy.json
```

API 서비스용 WAF 정책 초안 만들기:

```powershell
f5-waf quickstart --name my-api --type api --mode transparent --output out\my-api-policy.json
```

정책 파일 검증:

```powershell
f5-waf policy validate out\my-web-app-policy.json
```

BIG-IP에 보내기 전 미리보기:

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

## 추천 운영 흐름

처음부터 차단하지 말고 아래 순서로 진행하는 것을 권장합니다.

1. `transparent` 모드로 정책 생성
2. 백엔드 기술을 알면 `--server-tech`로 지정
3. BIG-IP에 적용
4. WAF 로그와 Traffic Learning 제안 확인
5. 오탐을 줄이도록 정책 조정
6. 충분히 확인한 뒤 `blocking` 모드 정책으로 전환

탐지 모드에서도 중요한 설정은 아래와 같습니다.

| 설정 | 추천값 | 이유 |
| --- | --- | --- |
| Enforcement Mode | `transparent` | 처음에는 차단하지 않고 탐지/로그 중심으로 운영 |
| Signature Staging | 켜짐 | 새 시그니처로 인한 오탐을 줄이기 위해 관찰 기간 확보 |
| Alarm | 켜짐 | 위반 이벤트를 로그와 리포트에서 확인 |
| Block | 꺼짐 | 탐지 모드에서는 사용자 요청을 막지 않음 |
| Server Technologies | 애플리케이션에 맞게 지정 | Java, MySQL, IIS 같은 기술별 공격 시그니처를 더 정확히 적용 |
| Data Guard | 켜짐 | 신용카드 번호 같은 민감 정보가 로그/화면에 노출되는 것을 줄임 |
| Policy Builder | wildcard 중심 | Rapid Deployment의 단순 운영 흐름 유지 |
| Logging Profile | 별도 적용 | 정책이 실제로 요청을 보고 있는지 로그로 확인 |

## Rapid Deployment 기준으로 생성되는 주요 값

`quickstart`는 Rapid Deployment를 쉽게 시작하기 위해 아래 값을 정책에 넣습니다.

| 항목 | 생성값 |
| --- | --- |
| Template | `POLICY_TEMPLATE_RAPID_DEPLOYMENT` |
| Type | `security` |
| Application Language | `utf-8` |
| Enforcement Mode | 기본 `transparent` |
| Signature Staging | 켜짐 |
| Signature Set | `Generic Detection Signatures` |
| Data Guard | 켜짐, 신용카드 번호 마스킹 |
| Enforcement Readiness Period | 7일 |
| File Type/URL/Parameter/Cookie Learning | 명시 엔티티 학습 `never`, wildcard 중심 |

## 추가 보안 옵션

Geo 차단 탐지:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --disallow-country "American Samoa" --output out\my-web-app-policy.json
```

IP Intelligence를 탐지 모드로 켜기:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --ip-intelligence --output out\my-web-app-policy.json
```

BIG-IP 앞단에 신뢰 가능한 프록시가 있고 X-Forwarded-For를 써야 할 때:

```powershell
f5-waf quickstart --name my-web-app --type web --mode transparent --trust-xff --xff-header X-Forwarded-For --output out\my-web-app-policy.json
```

`--trust-xff`는 신뢰 가능한 프록시 뒤에 BIG-IP가 있을 때만 사용하세요. 클라이언트가 헤더를 직접 조작할 수 있는 구조에서는 켜면 안 됩니다.

차단 모드 정책 생성:

```powershell
f5-waf quickstart --name my-web-app --type web --mode blocking --output out\my-web-app-blocking-policy.json
```

## 명령어 요약

| 명령 | 설명 |
| --- | --- |
| `f5-waf quickstart` | 쉬운 옵션만으로 WAF 정책 초안 생성 |
| `f5-waf policy validate` | 정책 JSON 검증 |
| `f5-waf policy upload` | 정책 업로드, 기본값은 dry-run |
| `f5-waf logs parse` | WAF JSONL 로그를 CSV로 변환 |
| `f5-waf asm convert` | 단순 ASM 정책 조각을 AWAF 정책 초안으로 변환 |

`quickstart`에서 자주 쓰는 옵션:

| 옵션 | 설명 |
| --- | --- |
| `--type web` | 일반 웹 애플리케이션 |
| `--type api` | JSON API 중심 애플리케이션 |
| `--mode transparent` | 탐지 모드 |
| `--mode blocking` | 차단 모드 |
| `--server-tech Java` | 서버 기술 지정. 여러 번 사용 가능 |
| `--disable-signature-id 200101552` | 특정 공격 시그니처 비활성화. 검토 후 사용 |
| `--disallow-country "Country"` | Geo 차단 국가 추가 |
| `--ip-intelligence` | IP Intelligence 카테고리를 alarm 중심으로 추가 |
| `--trust-xff` | 신뢰 가능한 프록시 환경에서 XFF 신뢰 |
| `--checklist-output file.md` | VS 연결, 로깅, Traffic Learning 확인용 체크리스트 생성 |
| `--no-staging` | 시그니처 staging 비활성화. 최초 적용에는 비추천 |

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
