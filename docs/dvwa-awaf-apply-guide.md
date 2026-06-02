# DVWA에 AWAF Rapid Deployment 적용 가이드

이 문서는 **F5 AWAF와 DVWA 서버가 이미 구축되어 있고, DVWA가 BIG-IP LTM Virtual Server 뒤에서 정상 서비스되는 상태**를 기준으로 합니다.

구축 자체는 다루지 않습니다. 실제 AWAF를 적용하는 시점부터 시작합니다.

## 0. 시작 전 확인

아래 항목이 먼저 되어 있어야 합니다.

| 항목 | 확인 방법 |
| --- | --- |
| DVWA 서버 동작 | DVWA 서버 IP로 직접 접속 가능 |
| Pool 구성 | `Local Traffic > Pools`에서 DVWA 서버 member가 up |
| Virtual Server 구성 | `Local Traffic > Virtual Servers`에서 DVWA VS가 up |
| LB 경유 접속 | 브라우저에서 VS 주소로 DVWA 접속 가능 |
| HTTP Profile | DVWA VS에 HTTP profile 연결 |

기존 Virtual Server에 local traffic policy가 이미 붙어 있다면, AWAF 정책 연결 전에 현재 정책이 어떤 용도인지 먼저 확인하세요.

## 1. DVWA용 탐지 모드 정책 만들기

DVWA는 보통 Apache, PHP, MySQL 기반으로 구성하므로 server technology를 같이 지정합니다.

```powershell
f5-waf quickstart --name dvwa-rapid-policy --type web --mode transparent --learning-mode manual --signature-accuracy high --server-tech Apache --server-tech PHP --server-tech MySQL --deployment-scenario existing --virtual-server dvwa_vs --logging-profile waf_detect_only --checklist-output out\dvwa-awaf-checklist.md --output out\dvwa-rapid-policy.json
```

이 명령은 두 파일을 만듭니다.

| 파일 | 용도 |
| --- | --- |
| `out\dvwa-rapid-policy.json` | BIG-IP에 올릴 AWAF 정책 초안 |
| `out\dvwa-awaf-checklist.md` | GUI에서 확인할 적용 체크리스트 |

생성되는 정책은 처음부터 차단하지 않습니다.

- Enforcement Mode: `transparent`
- Learning Mode: `manual`
- Signature Accuracy: `high`
- Signature Staging: enabled
- Generic Detection Signatures enabled
- Data Guard enabled
- Apache/PHP/MySQL server technology 지정

## 2. 정책 JSON 검증

```powershell
f5-waf policy validate out\dvwa-rapid-policy.json
```

정상 결과:

```text
OK: out\dvwa-rapid-policy.json is a valid AWAF policy document.
```

## 3. BIG-IP에 정책 업로드

먼저 dry-run으로 확인합니다.

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

업로드 후 BIG-IP GUI의 아래 메뉴에서 정책이 보이는지 확인합니다.

```text
Security > Application Security > Security Policies > Policy List
```

## 4. DVWA Virtual Server에 AWAF 정책 연결

BIG-IP GUI에서 진행합니다.

```text
Local Traffic > Virtual Servers > Virtual Server List > dvwa_vs
```

`Security` 탭에서 아래처럼 설정합니다.

| 항목 | 값 |
| --- | --- |
| Application Security Policy | Enabled |
| Policy | `dvwa-rapid-policy` |
| Log Profile | `waf_detect_only` 또는 테스트용 logging profile |

저장 후 `Update`를 누릅니다.

정책이 Virtual Server에 붙지 않으면 트래픽이 AWAF를 지나가지 않으므로 학습과 로그가 쌓이지 않습니다.

## 5. 정상 트래픽 확인

브라우저에서 DVWA에 접속합니다.

```text
http://<dvwa-virtual-server-ip>/dvwa/
```

로그인 후 DVWA 메뉴를 몇 개 클릭합니다.

확인 위치:

```text
Security > Event Logs > Application > Requests
```

탐지 모드라면 정상 요청은 차단되지 않아야 합니다.

## 6. SQL Injection 테스트

DVWA에서 보안 레벨을 낮게 설정한 뒤 SQL Injection 메뉴로 이동합니다.

예시 입력:

```text
%' or 1='1
```

탐지 모드 정책에서는 요청이 차단되지 않을 수 있습니다. 대신 Event Logs에 SQL Injection signature 또는 violation이 남아야 합니다.

확인 위치:

```text
Security > Event Logs > Application > Requests
Security > Application Security > Policy Building > Traffic Learning
```

## 7. Traffic Learning 확인

Traffic Learning에서 제안을 확인합니다.

| 상황 | 처리 |
| --- | --- |
| 정상 요청인데 violation 발생 | false positive 가능성 검토 후 제안 수락 |
| 명확한 공격 요청 | 제안 수락하지 않음 |
| 반복 오탐 | server technology, signature staging, 예외 정책 검토 |

변경 후에는 반드시 `Apply Policy`를 눌러야 반영됩니다.

## 8. 차단 모드 전환 전 확인

최소 며칠간 아래를 확인합니다.

- 정상 로그인/조회/검색/폼 제출이 문제 없는지
- Event Log에 반복 오탐이 없는지
- Traffic Learning 제안을 검토했는지
- 필요한 정책 변경 후 Apply Policy 했는지
- 운영팀이 Support ID 기준으로 로그를 찾을 수 있는지

## 9. 차단 모드 정책 만들기

탐지 기간이 끝난 뒤 차단 모드 정책을 새로 생성하거나 기존 정책을 수정합니다.

```powershell
f5-waf quickstart --name dvwa-blocking-policy --type web --mode blocking --learning-mode manual --signature-accuracy high --server-tech Apache --server-tech PHP --server-tech MySQL --output out\dvwa-blocking-policy.json
```

랩에서 바로 차단을 확인하려면 아래처럼 signature staging을 끌 수 있습니다.

```powershell
f5-waf quickstart --name dvwa-lab-blocking-policy --type web --mode blocking --no-staging --signature-accuracy low --server-tech Apache --server-tech PHP --server-tech MySQL --output out\dvwa-lab-blocking-policy.json
```

주의: `blocking + --no-staging + low`는 테스트 공격 차단 확인에는 좋지만, 실제 서비스 첫 적용에는 오탐 위험이 큽니다.

## 10. 차단 확인

차단 모드 정책을 Virtual Server에 연결한 뒤 SQL Injection 테스트를 다시 수행합니다.

기대 결과:

- 브라우저에서 차단 페이지 또는 요청 실패 확인
- Event Logs에서 blocked 상태 확인
- Support ID 확인 가능
- 매칭된 attack signature 확인 가능

## 장애 시 되돌리기

문제가 생기면 가장 빠른 되돌리기는 Virtual Server에서 Application Security Policy를 비활성화하거나 이전 정책으로 되돌리는 것입니다.

```text
Local Traffic > Virtual Servers > dvwa_vs > Security
```

운영 환경에서는 변경 전/후 스크린샷, 정책 백업, 적용 시간, 담당자를 기록해두는 것을 권장합니다.
