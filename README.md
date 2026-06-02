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
2. BIG-IP에 적용
3. WAF 로그 확인
4. 오탐을 줄이도록 정책 조정
5. 충분히 확인한 뒤 `blocking` 모드 정책으로 전환

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
