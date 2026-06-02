# F5 AWAF Rapid Deployment 쉽게 적용하기

이 저장소는 **F5 AWAF와 DVWA 서버가 이미 준비되어 있고, DVWA가 BIG-IP LTM Virtual Server 뒤에 붙어 있는 상태**에서 AWAF 정책을 쉽게 생성하고 적용하기 위한 도구입니다.

즉, 아래는 이미 끝났다고 가정합니다.

- DVWA 서버 구축 완료
- BIG-IP Pool에 DVWA 서버 등록 완료
- BIG-IP Virtual Server 생성 완료
- 브라우저에서 Virtual Server 주소로 DVWA 접속 확인 완료

이 저장소는 그 다음 단계인 **AWAF 정책 생성, Virtual Server에 연결, 로그 확인, 탐지 모드 운영, 차단 모드 전환**을 도와줍니다.

## 바로 쓰는 명령

설치:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

DVWA용 탐지 모드 정책 생성:

```powershell
f5-waf quickstart --name dvwa-rapid-policy --type web --mode transparent --learning-mode manual --signature-accuracy high --server-tech Apache --server-tech PHP --server-tech MySQL --deployment-scenario existing --virtual-server dvwa_vs --logging-profile waf_detect_only --checklist-output out\dvwa-awaf-checklist.md --output out\dvwa-rapid-policy.json
```

정책 검증:

```powershell
f5-waf policy validate out\dvwa-rapid-policy.json
```

BIG-IP 업로드 dry-run:

```powershell
f5-waf policy upload out\dvwa-rapid-policy.json
```

실제 업로드:

```powershell
$env:F5_HOST="https://<big-ip-mgmt-ip>"
$env:F5_USERNAME="<username>"
$env:F5_PASSWORD="<password>"
f5-waf policy upload out\dvwa-rapid-policy.json --apply
```

## 실제 적용 순서

자세한 절차는 아래 문서를 보세요.

[DVWA에 AWAF Rapid Deployment 적용 가이드](docs/dvwa-awaf-apply-guide.md)

이미 `waf_pol` 같은 기존 정책이 `dvwa_vs`에 연결되어 있어도 새 정책을 만들 수 있습니다. 같은 Virtual Server에 정책 두 개를 동시에 활성 연결하는 것은 아니며, `dvwa_vs`의 Policy 값을 기존 정책에서 새 정책으로 교체합니다. 기존 정책은 삭제하지 말고 보존해두면 문제가 생겼을 때 바로 되돌릴 수 있습니다.

요약하면 순서는 이렇습니다.

1. `quickstart`로 DVWA용 Rapid Deployment 정책 JSON 생성
2. `policy validate`로 정책 검증
3. BIG-IP에 정책 업로드
4. BIG-IP GUI에서 DVWA Virtual Server에 Application Security Policy 연결
5. Logging Profile 연결
6. DVWA 정상 접속 테스트
7. SQL Injection 같은 테스트 요청 발생
8. Security Event Log와 Traffic Learning 확인
9. 오탐 튜닝 후 Apply Policy
10. 충분히 관찰한 뒤 Blocking 전환 검토

## 탐지 모드 기본값

처음 적용은 운영 영향을 줄이기 위해 아래 값을 기본으로 권장합니다.

| 항목 | 권장값 |
| --- | --- |
| Policy Template | Rapid Deployment |
| Enforcement Mode | `transparent` |
| Learning Mode | `manual` |
| Signature Accuracy | `high` |
| Signature Staging | enabled |
| Server Technologies | `Apache`, `PHP`, `MySQL` |
| Data Guard | enabled |
| Logging | violations 중심, 테스트 기간에는 all requests 가능 |

## 차단 테스트용 정책

랩에서 SQL Injection이 실제로 차단되는지 바로 보고 싶다면 아래처럼 만들 수 있습니다.

```powershell
f5-waf quickstart --name dvwa-blocking-policy --type web --mode blocking --no-staging --signature-accuracy low --server-tech Apache --server-tech PHP --server-tech MySQL --output out\dvwa-blocking-policy.json
```

주의: 이 설정은 테스트/랩 검증용입니다. 실제 서비스 첫 적용은 `transparent + staging on + high accuracy`를 권장합니다.

## 참고 문서

- F5 공식 BIG-IP ASM 12.1 Getting Started: Rapid Deployment
- F5 공식 BIG-IP ASM 13.0 Getting Started: Rapid Deployment
- F5 Agility Lab WAF
- RAYKA AWAF 첫 보안 정책 생성
- TechClick Rapid Deployment setup

## 테스트

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```
