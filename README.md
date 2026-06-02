# F5 WAF Automation Toolkit

This is an upgraded, safe-by-default starter repository for automating F5 BIG-IP Advanced WAF and ASM migration workflows.

It is intentionally not a direct copy of the reference examples. The scripts have been reorganized into a reusable Python CLI with validation, dry-run behavior, environment-based configuration, test coverage, and GitHub Actions CI.

## What is included

- `f5-waf policy validate`: validate AWAF policy JSON before upload.
- `f5-waf policy upload`: upload a policy to BIG-IP ASM/AWAF, with dry-run enabled by default.
- `f5-waf asm convert`: convert a simplified ASM export fragment into an AWAF policy draft.
- `f5-waf logs parse`: normalize JSON-lines WAF logs into CSV for analysis.
- Example policies and log files under `examples/`.
- Unit tests under `tests/`.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
f5-waf --help
```

Validate an example policy:

```powershell
f5-waf policy validate examples\policies\baseline-awaf-policy.json
```

Preview an upload without changing BIG-IP:

```powershell
f5-waf policy upload examples\policies\baseline-awaf-policy.json
```

Apply the upload only when you are ready:

```powershell
$env:F5_HOST="https://bigip.example.com"
$env:F5_USERNAME="automation-user"
$env:F5_PASSWORD="secret"
f5-waf policy upload examples\policies\baseline-awaf-policy.json --apply
```

Parse WAF logs:

```powershell
f5-waf logs parse examples\logs\waf-events.jsonl out\waf-events.csv
```

Convert a simplified ASM fragment:

```powershell
f5-waf asm convert examples\policies\asm-fragment.json out\converted-awaf-policy.json
```

Run tests:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

## Safety defaults

- Policy upload runs as dry-run unless `--apply` is provided.
- TLS verification is enabled by default.
- Credentials are read from environment variables, not hardcoded.
- Policy JSON is validated before upload.
- The CLI fails fast on malformed files and missing required policy fields.

## Environment variables

Copy `.env.example` into your own secret store or terminal profile. Do not commit real credentials.

| Variable | Purpose | Default |
| --- | --- | --- |
| `F5_HOST` | BIG-IP base URL | required for upload |
| `F5_USERNAME` | BIG-IP username | required for upload |
| `F5_PASSWORD` | BIG-IP password | required for upload |
| `F5_VERIFY_TLS` | `true` or `false` | `true` |
| `F5_TIMEOUT` | HTTP timeout in seconds | `30` |

## Repository setup

```powershell
git init
git add .
git commit -m "Initial F5 WAF automation toolkit"
```

Then create a new empty GitHub repository and push this project as its first commit.
