# F5 WAF 자동화 툴킷

F5 BIG-IP Advanced WAF(AWAF)와 ASM 마이그레이션 작업을 더 안전하고 반복 가능하게 처리하기 위한 자동화 스타터 저장소입니다.

이 저장소는 참고 예제를 그대로 복사한 것이 아니라, 실제 환경에서 바로 손볼 수 있도록 Python CLI 구조로 재구성했습니다. 정책 검증, 기본 dry-run 업로드, 환경변수 기반 설정, 로그 변환, ASM to AWAF 변환, 테스트, GitHub Actions CI를 포함합니다.

## 포함된 기능

- `f5-waf policy validate`: AWAF 정책 JSON 업로드 전 유효성 검증
- `f5-waf policy upload`: BIG-IP ASM/AWAF 정책 업로드, 기본값은 dry-run
- `f5-waf asm convert`: 단순화된 ASM 정책 조각을 AWAF 정책 초안으로 변환
- `f5-waf logs parse`: JSON-lines 형식 WAF 로그를 CSV로 정규화
- `examples/` 아래 예제 정책과 로그 파일
- `tests/` 아래 기본 단위 테스트

## 빠른 시작

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
f5-waf --help
```

예제 정책 검증:

```powershell
f5-waf policy validate examples\policies\baseline-awaf-policy.json
```

BIG-IP에 변경을 보내지 않고 업로드 미리보기:

```powershell
f5-waf policy upload examples\policies\baseline-awaf-policy.json
```

실제 업로드 실행:

```powershell
$env:F5_HOST="https://bigip.example.com"
$env:F5_USERNAME="automation-user"
$env:F5_PASSWORD="secret"
f5-waf policy upload examples\policies\baseline-awaf-policy.json --apply
```

WAF 로그 CSV 변환:

```powershell
f5-waf logs parse examples\logs\waf-events.jsonl out\waf-events.csv
```

ASM 정책 조각을 AWAF 정책 초안으로 변환:

```powershell
f5-waf asm convert examples\policies\asm-fragment.json out\converted-awaf-policy.json
```

테스트 실행:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

## 안전 기본값

- 정책 업로드는 `--apply`를 명시하지 않으면 dry-run으로만 실행됩니다.
- TLS 인증서 검증은 기본적으로 켜져 있습니다.
- 계정 정보는 코드에 하드코딩하지 않고 환경변수에서 읽습니다.
- 정책 JSON은 업로드 전에 먼저 검증합니다.
- 파일 형식이 잘못됐거나 필수 정책 필드가 빠지면 즉시 실패합니다.

## 환경변수

`.env.example`을 참고해서 터미널 프로필, 비밀 관리 도구, CI Secret 등에 값을 넣으세요. 실제 계정 정보는 절대 커밋하지 마세요.

| 변수 | 용도 | 기본값 |
| --- | --- | --- |
| `F5_HOST` | BIG-IP 기본 URL | 업로드 시 필수 |
| `F5_USERNAME` | BIG-IP 사용자 이름 | 업로드 시 필수 |
| `F5_PASSWORD` | BIG-IP 비밀번호 | 업로드 시 필수 |
| `F5_VERIFY_TLS` | TLS 인증서 검증 여부, `true` 또는 `false` | `true` |
| `F5_TIMEOUT` | HTTP 요청 제한 시간(초) | `30` |

## 저장소 설정

새 GitHub 저장소에 처음 올릴 때는 아래 명령을 사용합니다.

```powershell
git init
git add .
git commit -m "Initial F5 WAF automation toolkit"
git remote add origin https://github.com/<사용자또는조직>/<저장소>.git
git push -u origin main
```

이미 이 저장소를 클론한 상태라면 `git pull`, 수정, 테스트, 커밋, 푸시 순서로 작업하면 됩니다.
