# Step-by-Step: DVWA에 새 AWAF 정책 적용

이 문서는 그대로 따라 하는 실습 순서입니다.

## 환경

| 항목 | 값 |
| --- | --- |
| F5 관리 IP | `192.168.137.125` |
| 구성 | One-arm |
| DVWA 서버 Real IP | `192.168.137.113` |
| Virtual Server | `dvwa_vs` |
| VIP | `192.168.137.211:80` |
| 현재 연결된 정책 | `waf_pol` |
| 새로 만들 정책 | `dvwa-rapid-policy-v2` |

## Step 0. 현재 상태 확인

브라우저에서 DVWA가 열리는지 확인합니다.

```text
http://192.168.137.211/dvwa/
```

BIG-IP GUI에서 현재 정책을 확인합니다.

```text
Security > Application Security > Security Policies > Policy List
```

현재 상태:

```text
Policy: waf_pol
Enforcement Mode: Transparent
Virtual Server: dvwa_vs
```

`waf_pol`은 삭제하지 않습니다. 새 정책 적용 후 문제가 있으면 다시 `waf_pol`로 되돌립니다.

## Step 1. 도구 설치

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Step 2. 새 DVWA용 정책 생성

```powershell
f5-waf lab dvwa
```

생성되는 파일:

```text
out/dvwa-rapid-policy-v2.json
out/dvwa-awaf-checklist.md
```

이 정책은 처음에는 차단하지 않는 탐지 모드입니다.

```text
Enforcement Mode: transparent
Learning Mode: manual
Signature Accuracy: high
Signature Staging: enabled
Server Technologies: Apache, PHP, MySQL
```

## Step 3. 정책 파일 검증

```powershell
f5-waf policy validate out\dvwa-rapid-policy-v2.json
```

정상 결과:

```text
OK: out\dvwa-rapid-policy-v2.json is a valid AWAF policy document.
```

## Step 4. BIG-IP 접속 정보 설정

```powershell
$env:F5_HOST="https://192.168.137.125"
$env:F5_USERNAME="<BIG-IP 사용자>"
$env:F5_PASSWORD="<BIG-IP 비밀번호>"
```

## Step 5. 업로드 전 dry-run

```powershell
f5-waf policy upload out\dvwa-rapid-policy-v2.json
```

`dry_run: true`가 보이면 아직 BIG-IP에는 변경을 보내지 않은 상태입니다.

## Step 6. BIG-IP에 새 정책 업로드

```powershell
f5-waf policy upload out\dvwa-rapid-policy-v2.json --apply
```

업로드 후 GUI에서 새 정책이 보이는지 확인합니다.

```text
Security > Application Security > Security Policies > Policy List
```

확인할 정책:

```text
dvwa-rapid-policy-v2
```

## Step 7. Logging Profile 생성

네가 GUI에서 만든 것과 같은 목적의 Application Security Logging Profile을 생성합니다.

```powershell
f5-waf logging profile create --name waf_detect_only
```

dry-run payload를 확인한 뒤 실제 생성합니다.

```powershell
f5-waf logging profile create --name waf_detect_only --apply
```

기본 request type은 아래 GUI 항목에 해당합니다.

```text
Illegal requests, and requests that include staged attack signature or staged threat campaigns or Potential False Positive signature
```

생성 후 GUI에서 확인합니다.

```text
Security > Event Logs > Logging Profiles
```

확인할 값:

```text
Profile Name: waf_detect_only
Application Security: Enabled
Storage Destination: Local Storage
Request Type: Illegal requests, and requests that include staged attack signature...
```

## Step 8. dvwa_vs에 새 정책 연결

BIG-IP GUI에서 이동합니다.

```text
Local Traffic > Virtual Servers > Virtual Server List > dvwa_vs > Security
```

아래처럼 변경합니다.

| 항목 | 값 |
| --- | --- |
| Application Security Policy | `Enabled` |
| Policy | `dvwa-rapid-policy-v2` |
| Log Profile | `waf_detect_only` 또는 staged signatures가 보이는 profile |

`Update`를 누릅니다.

주의: `Application Security Policy`를 `Disabled`로 바꾸는 것이 아닙니다. 기존 `waf_pol`을 새 `dvwa-rapid-policy-v2`로 교체하는 것입니다.

## Step 9. Logging Profile 연결 확인

일본 벤더 교육자료 기준으로 staging 로그를 보려면 staged attack signatures가 Event Logs에 보여야 합니다.

확인 위치:

```text
Security > Event Logs > Logging Profiles
Security > Overview > Summary
```

초기 실습에서는 아래 유형이 보이면 좋습니다.

```text
Illegal requests
Requests that include staged attack signatures
Potential False Positive signatures
```

## Step 10. Signature Staging 확인

```text
Security > Application Security > Policy Building > Learning and Blocking Settings
```

확인:

```text
Enable Signature Staging: checked
```

정책의 Attack Signatures 화면에서도 상태를 확인합니다.

```text
Security > Application Security > Security Policies > Policies List > dvwa-rapid-policy-v2 > Attack Signatures
```

기대 상태:

```text
Status: Staging
```

## Step 11. 정상 접속 테스트

브라우저에서 DVWA에 접속합니다.

```text
http://192.168.137.211/dvwa/
```

DVWA 로그인 후 몇 개 메뉴를 클릭합니다.

탐지 모드이므로 정상 요청이 차단되면 안 됩니다.

## Step 12. SQL Injection 테스트

DVWA에서 Security Level을 `Low`로 설정합니다.

```text
DVWA Security > Security Level > Low
```

SQL Injection 메뉴에서 아래 값을 입력합니다.

```text
'or 1=1 #
```

탐지 모드에서는 요청이 차단되지 않을 수 있습니다. 대신 로그와 학습 제안이 남아야 합니다.

## Step 13. Event Logs 확인

```text
Security > Event Logs > Application > Requests
```

확인할 것:

```text
SQL Injection 관련 signature 또는 violation
Staged 상태
Support ID
Policy 이름: dvwa-rapid-policy-v2
```

## Step 14. Traffic Learning 확인

```text
Security > Application Security > Policy Building > Traffic Learning
```

확인할 것:

```text
Attack signature detected
Related Suggestions
```

명확한 공격 요청은 수락하지 않습니다. 정상 요청 오탐만 검토합니다.

## Step 15. Apply Policy

정책 변경이나 학습 제안 반영 후에는 반드시 누릅니다.

```text
Apply Policy
```

## Step 16. Staging 해제

탐지 로그와 오탐 검토가 끝나면 staging을 해제합니다.

```text
Security > Application Security > Security Policies > Policies List > dvwa-rapid-policy-v2 > Attack Signatures
```

절차:

```text
Enforce all Staged Signatures
Apply Policy
```

다시 SQL Injection 테스트를 하고 Event Logs에서 `Alarm Learn` 상태를 확인합니다.

## Step 17. Blocking 모드 전환

```text
Security > Application Security > Security Policies > Policies List > dvwa-rapid-policy-v2 > General Settings
```

변경:

```text
Enforcement Mode: Blocking
Save
Apply Policy
```

## Step 18. 차단 확인

다시 SQL Injection 테스트를 합니다.

```text
'or 1=1 #
```

기대 결과:

```text
요청 차단
Event Logs에서 Block Alarm Learn 확인
Support ID 확인
매칭된 attack signature 확인
```

## Step 19. 되돌리기

문제가 생기면 `dvwa_vs`의 Policy를 다시 기존 정책으로 바꿉니다.

```text
Local Traffic > Virtual Servers > Virtual Server List > dvwa_vs > Security
```

변경:

```text
Policy: waf_pol
Update
```

가장 빠르게 AWAF를 빼야 한다면 `Application Security Policy`를 `Disabled`로 바꿀 수 있습니다. 다만 이 경우 새 정책뿐 아니라 AWAF 자체가 해당 VS에서 빠집니다.

## 부록. 랩에서 바로 차단 테스트용 정책 만들기

처음부터 차단을 빠르게 보고 싶을 때만 사용합니다.

```powershell
f5-waf lab dvwa --name dvwa-lab-blocking-policy --mode blocking --no-staging --signature-accuracy low --output out\dvwa-lab-blocking-policy.json --checklist-output out\dvwa-lab-blocking-checklist.md
```

이 설정은 실습 확인용입니다. 운영 첫 적용에는 `transparent + staging enabled + high accuracy`가 더 안전합니다.
