# DVWA에 AWAF Rapid Deployment 적용 가이드

이 문서는 **F5 AWAF와 DVWA 서버가 이미 구축되어 있고, DVWA가 BIG-IP LTM Virtual Server 뒤에서 정상 서비스되는 상태**를 기준으로 합니다.

구축 자체는 다루지 않습니다. 실제 AWAF를 적용하는 시점부터 시작합니다.

## 고정 환경

이 가이드는 아래 환경을 기준으로 합니다.

| 항목 | 값 |
| --- | --- |
| F5 BIG-IP 관리 IP | `192.168.137.125` |
| 구성 방식 | One-arm |
| DVWA Real Server IP | `192.168.137.113` |
| Virtual Server | `dvwa_vs` |
| VIP | `192.168.137.211:80` |
| 기존 WAF Policy | `waf_pol` |
| 새 WAF Policy | `dvwa-rapid-policy-v2` |

## 0. 시작 전 확인

아래 항목이 먼저 되어 있어야 합니다.

| 항목 | 확인 방법 |
| --- | --- |
| DVWA 서버 동작 | `192.168.137.113`으로 직접 접속 가능 |
| Pool 구성 | `Local Traffic > Pools`에서 DVWA 서버 member가 up |
| Virtual Server 구성 | `Local Traffic > Virtual Servers`에서 `dvwa_vs`가 up |
| LB 경유 접속 | 브라우저에서 `http://192.168.137.211/` 또는 DVWA 경로 접속 가능 |
| HTTP Profile | DVWA VS에 HTTP profile 연결 |

기존 Virtual Server에 local traffic policy가 이미 붙어 있다면, AWAF 정책 연결 전에 현재 정책이 어떤 용도인지 먼저 확인하세요.

## 1. DVWA용 탐지 모드 정책 만들기

DVWA는 보통 Apache, PHP, MySQL 기반으로 구성하므로 server technology를 같이 지정합니다.

가장 쉬운 방법:

```powershell
f5-waf lab dvwa
```

직접 옵션을 지정하는 방법:

```powershell
f5-waf quickstart --name dvwa-rapid-policy-v2 --type web --mode transparent --learning-mode manual --signature-accuracy high --server-tech Apache --server-tech PHP --server-tech MySQL --deployment-scenario existing --virtual-server dvwa_vs --logging-profile waf_detect_only --checklist-output out\dvwa-awaf-checklist.md --output out\dvwa-rapid-policy-v2.json
```

이 명령은 두 파일을 만듭니다.

| 파일 | 용도 |
| --- | --- |
| `out\dvwa-rapid-policy-v2.json` | BIG-IP에 올릴 AWAF 정책 초안 |
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
f5-waf policy validate out\dvwa-rapid-policy-v2.json
```

정상 결과:

```text
OK: out\dvwa-rapid-policy-v2.json is a valid AWAF policy document.
```

## 3. BIG-IP에 정책 업로드

먼저 dry-run으로 확인합니다.

```powershell
f5-waf policy upload out\dvwa-rapid-policy-v2.json
```

실제 업로드:

```powershell
$env:F5_HOST="https://192.168.137.125"
$env:F5_USERNAME="<username>"
$env:F5_PASSWORD="<password>"
f5-waf policy upload out\dvwa-rapid-policy-v2.json --apply
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
| Policy | `dvwa-rapid-policy-v2` |
| Log Profile | `waf_detect_only` 또는 테스트용 logging profile |

저장 후 `Update`를 누릅니다.

정책이 Virtual Server에 붙지 않으면 트래픽이 AWAF를 지나가지 않으므로 학습과 로그가 쌓이지 않습니다.

## 4-1. 기존 `waf_pol`이 이미 연결되어 있는 경우

같은 Virtual Server에 AWAF 정책을 두 개 동시에 활성 연결할 수는 없습니다.

지금처럼 `waf_pol`이 이미 `dvwa_vs`에 연결되어 있다면, 새 정책을 하나 더 만든 뒤 `dvwa_vs`의 Application Security Policy를 새 정책으로 교체합니다.

기존 정책은 삭제하지 않아도 됩니다. Virtual Server에서 연결만 빠지면 더 이상 `dvwa_vs` 트래픽에는 적용되지 않습니다.

권장 절차:

1. 기존 상태 기록
   - Policy: `waf_pol`
   - Enforcement Mode: `Transparent`
   - Virtual Server: `dvwa_vs`
2. 새 정책 생성
   - 예: `dvwa-rapid-policy-v2`
3. 새 정책 업로드
4. BIG-IP GUI에서 `dvwa_vs`로 이동
5. `Security` 탭에서 Application Security Policy는 `Enabled` 유지
6. Policy 값을 `waf_pol`에서 `dvwa-rapid-policy-v2`로 변경
7. Logging Profile이 연결되어 있는지 확인
8. `Update` 클릭
9. Event Logs에서 새 정책 이름으로 로그가 쌓이는지 확인

새 정책 생성 예시:

```powershell
f5-waf quickstart --name dvwa-rapid-policy-v2 --type web --mode transparent --learning-mode manual --signature-accuracy high --server-tech Apache --server-tech PHP --server-tech MySQL --deployment-scenario existing --virtual-server dvwa_vs --logging-profile waf_detect_only --checklist-output out\dvwa-v2-checklist.md --output out\dvwa-rapid-policy-v2.json
```

되돌리기가 필요하면 같은 화면에서 Policy 값을 다시 `waf_pol`로 바꾸면 됩니다.

기존 정책을 완전히 비활성화하고 싶다면:

```text
Local Traffic > Virtual Servers > dvwa_vs > Security
```

위 화면에서 Application Security Policy를 `Disabled`로 바꾸면 해당 Virtual Server에서는 AWAF가 적용되지 않습니다. 다만 이 경우 새 정책도 적용되지 않으므로, 보통은 `Disabled`가 아니라 **정책 교체**를 사용합니다.

## 5. 정상 트래픽 확인

브라우저에서 DVWA에 접속합니다.

```text
http://192.168.137.211/dvwa/
```

로그인 후 DVWA 메뉴를 몇 개 클릭합니다.

확인 위치:

```text
Security > Event Logs > Application > Requests
```

탐지 모드라면 정상 요청은 차단되지 않아야 합니다.

## 5-1. 일본 벤더 교육자료 기준 추가 확인

일본 벤더 AWAF v17.1 교육자료의 흐름에서는 Guided Configuration으로 WAF 정책을 만들 때 아래 값을 확인합니다.

| 항목 | 값 |
| --- | --- |
| Enforcement Mode | `Transparent` |
| Policy Type | `Generic` |
| Server Technologies | `Apache`, `MySQL`, `PHP` |
| Assign Policy | `Use Existing`으로 기존 `dvwa_vs` 선택 |
| Logging Profile | illegal requests 또는 staged attack signatures가 보이는 profile |

정책 적용 후 아래도 확인합니다.

- `Security > Application Security > Policy Building > Learning and Blocking Settings`
- Attack Signatures의 `Enable Signature Staging` 체크
- Policy의 Attack Signatures 화면에서 signature 상태가 `Staging`인지 확인
- Staging은 공격을 탐지해도 block하지 않고 Manual Traffic Learning으로 학습 제안을 만드는 상태
- 필요하면 staged signatures가 Event Logs에 보이도록 별도 Logging Profile 생성

## 6. SQL Injection 테스트

DVWA에서 보안 레벨을 낮게 설정한 뒤 SQL Injection 메뉴로 이동합니다.

예시 입력:

```text
'or 1=1 #
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

## 7-1. Staging 해제 흐름

탐지 로그가 정상적으로 쌓이고 오탐을 검토했다면 signature staging을 해제할 수 있습니다.

GUI 기준:

```text
Security > Application Security > Security Policies > Policies List > dvwa-rapid-policy-v2 > Attack Signatures
```

절차:

1. `Enforce all Staged Signatures` 선택
2. signature 상태가 `Enforced`로 바뀌는지 확인
3. `Apply Policy` 클릭
4. SQL Injection 테스트 재수행
5. Event Logs에서 `Alarm Learn` 상태 확인

Blocking 전환 전에는 이 단계를 거쳐 staging 상태를 명확히 확인하는 것이 좋습니다.

## 8. 차단 모드 전환 전 확인

최소 며칠간 아래를 확인합니다.

- 정상 로그인/조회/검색/폼 제출이 문제 없는지
- Event Log에 반복 오탐이 없는지
- Traffic Learning 제안을 검토했는지
- 필요한 정책 변경 후 Apply Policy 했는지
- 운영팀이 Support ID 기준으로 로그를 찾을 수 있는지
- Attack Signatures 상태가 Staging인지 Enforced인지
- Logging Profile이 staged signature 로그를 보여주는지

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

## 11. 오탐 튜닝 예시

오탐이 특정 파라미터에서 반복되면 무조건 전체 signature를 끄지 말고, 가능한 좁은 범위에서 예외를 둡니다.

예시 흐름:

1. Event Logs에서 오탐이 발생한 parameter 이름 확인
2. `Security > Application Security > Parameters > Parameters List`
3. 해당 parameter 생성 또는 수정
4. 필요 시 Parameter Value Type을 조정
5. 특정 signature ID만 해당 parameter에서 disable
6. `Apply Policy`
7. 정상 요청 재검증

일본 벤더 자료에서는 예시 signature ID로 `200002835`를 사용해 parameter 단위 비활성화를 설명합니다. 실제 환경에서는 반드시 Event Log에 나온 signature ID를 기준으로 처리하세요.

## 12. 추가로 검토할 보안 기능

| 기능 | 설명 | 주의 |
| --- | --- | --- |
| Threat Campaigns | 실제 공격 캠페인 기반의 복합 조건 signature | Learn 없이 Alarm/Block 중심 |
| Signature Update | 최신 공격 대응을 위해 운영 테스트 전에 업데이트 권장 | 업데이트된 signature는 staging 정책 확인 |
| Geolocation Enforcement | 접속 계획이 없는 국가 차단 | 차단 전 업무 영향 확인 |
| IP Intelligence | 알려진 악성 IP 평판 기반 탐지/차단 | 별도 구독 라이선스 필요 |
| Blocking Page Customization | 차단 응답 페이지 문구 변경 | 변경 후 Apply Policy |

## 장애 시 되돌리기

문제가 생기면 가장 빠른 되돌리기는 Virtual Server에서 Application Security Policy를 비활성화하거나 이전 정책으로 되돌리는 것입니다.

```text
Local Traffic > Virtual Servers > dvwa_vs > Security
```

운영 환경에서는 변경 전/후 스크린샷, 정책 백업, 적용 시간, 담당자를 기록해두는 것을 권장합니다.
