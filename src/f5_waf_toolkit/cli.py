from __future__ import annotations

import argparse
import json
import sys

from .client import F5Client
from .config import F5Config
from .logs import parse_jsonl_to_csv
from .policies import (
    PolicyValidationError,
    convert_asm_to_awaf,
    load_json,
    require_valid_policy,
    validate_policy,
    write_json,
)
from .profiles import DVWA_LAB, build_dvwa_lab_policy, build_easy_policy, build_rollout_checklist


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="f5-waf")
    subcommands = parser.add_subparsers(dest="command", required=True)

    quickstart = subcommands.add_parser("quickstart", help="Create a simple WAF policy from a few options.")
    quickstart.add_argument("--name", required=True, help="Policy name, usually the application name.")
    quickstart.add_argument("--type", choices=["web", "api"], default="web", help="Application type.")
    quickstart.add_argument(
        "--mode",
        choices=["transparent", "blocking"],
        default="transparent",
        help="Start with transparent for monitoring, blocking for enforcement.",
    )
    quickstart.add_argument("--output", required=True, help="Output policy JSON file.")
    quickstart.add_argument(
        "--server-tech",
        action="append",
        default=[],
        help="Backend technology to tune attack signatures. Can be used multiple times, for example: --server-tech Java --server-tech MySQL",
    )
    quickstart.add_argument(
        "--disable-signature-id",
        action="append",
        type=int,
        default=[],
        help="Disable a specific attack signature ID in the generated policy. Can be used multiple times.",
    )
    quickstart.add_argument(
        "--disallow-country",
        action="append",
        default=[],
        help="Add a disallowed geolocation country name. Can be used multiple times.",
    )
    quickstart.add_argument(
        "--ip-intelligence",
        action="store_true",
        help="Enable IP Intelligence categories in alarm mode for transparent policies.",
    )
    quickstart.add_argument(
        "--trust-xff",
        action="store_true",
        help="Trust X-Forwarded-For. Use only when BIG-IP is behind a trusted proxy.",
    )
    quickstart.add_argument(
        "--xff-header",
        action="append",
        default=[],
        help="Custom trusted XFF header. Can be used multiple times.",
    )
    quickstart.add_argument(
        "--no-data-guard",
        action="store_true",
        help="Disable Data Guard in the generated policy.",
    )
    quickstart.add_argument(
        "--inspect-responses",
        action="store_true",
        help="Apply attack signatures to responses as well as requests.",
    )
    quickstart.add_argument(
        "--learning-mode",
        choices=["manual", "automatic", "fully-automatic"],
        default="manual",
        help="Learning mode. Manual is safest for first rollout.",
    )
    quickstart.add_argument(
        "--signature-accuracy",
        choices=["high", "medium", "low"],
        default="high",
        help="Minimum accuracy for auto-added signatures. Low is stricter but can create more false positives.",
    )
    quickstart.add_argument(
        "--log-scope",
        choices=["violations", "all-requests", "all-requests-and-responses"],
        default="violations",
        help="Logging scope note for the generated checklist.",
    )
    quickstart.add_argument(
        "--deployment-scenario",
        choices=["existing", "new", "unassigned"],
        default="existing",
        help="Deployment scenario for the generated checklist.",
    )
    quickstart.add_argument(
        "--virtual-server",
        default="",
        help="Virtual Server name for the generated rollout checklist.",
    )
    quickstart.add_argument(
        "--logging-profile",
        default="waf_detect_only",
        help="Logging profile name for the generated rollout checklist.",
    )
    quickstart.add_argument(
        "--checklist-output",
        help="Optional Markdown checklist for BIG-IP GUI steps such as VS assignment and logging profile.",
    )
    quickstart.add_argument(
        "--no-staging",
        action="store_true",
        help="Disable signature staging. Keep staging enabled for first rollout.",
    )
    quickstart.set_defaults(func=cmd_quickstart)

    lab = subcommands.add_parser("lab", help="Use built-in lab presets.")
    lab_commands = lab.add_subparsers(dest="lab_command", required=True)
    dvwa = lab_commands.add_parser("dvwa", help="Create policy and checklist for the fixed DVWA one-arm lab.")
    dvwa.add_argument("--name", default=DVWA_LAB["policy_name"], help="Policy name.")
    dvwa.add_argument(
        "--mode",
        choices=["transparent", "blocking"],
        default="transparent",
        help="Use transparent for first rollout, blocking for enforcement tests.",
    )
    dvwa.add_argument(
        "--no-staging",
        action="store_true",
        help="Disable signature staging. Use only for lab blocking tests.",
    )
    dvwa.add_argument(
        "--signature-accuracy",
        choices=["high", "medium", "low"],
        default="high",
        help="Minimum accuracy for auto-added signatures.",
    )
    dvwa.add_argument("--output", default="out/dvwa-rapid-policy-v2.json", help="Output policy JSON file.")
    dvwa.add_argument("--checklist-output", default="out/dvwa-awaf-checklist.md", help="Output checklist file.")
    dvwa.set_defaults(func=cmd_lab_dvwa)

    policy = subcommands.add_parser("policy")
    policy_commands = policy.add_subparsers(dest="policy_command", required=True)

    validate = policy_commands.add_parser("validate")
    validate.add_argument("policy_file")
    validate.set_defaults(func=cmd_policy_validate)

    upload = policy_commands.add_parser("upload")
    upload.add_argument("policy_file")
    upload.add_argument("--apply", action="store_true", help="Upload to BIG-IP. Without this flag, run dry-run.")
    upload.set_defaults(func=cmd_policy_upload)

    asm = subcommands.add_parser("asm")
    asm_commands = asm.add_subparsers(dest="asm_command", required=True)
    convert = asm_commands.add_parser("convert")
    convert.add_argument("input_file")
    convert.add_argument("output_file")
    convert.set_defaults(func=cmd_asm_convert)

    logs = subcommands.add_parser("logs")
    log_commands = logs.add_subparsers(dest="log_command", required=True)
    parse = log_commands.add_parser("parse")
    parse.add_argument("input_file")
    parse.add_argument("output_file")
    parse.set_defaults(func=cmd_logs_parse)

    return parser


def cmd_quickstart(args: argparse.Namespace) -> int:
    policy = build_easy_policy(
        name=args.name,
        app_type=args.type,
        mode=args.mode,
        staging=not args.no_staging,
        server_technologies=args.server_tech,
        disabled_signature_ids=args.disable_signature_id,
        disallowed_geolocations=args.disallow_country,
        ip_intelligence=args.ip_intelligence,
        trust_xff=args.trust_xff,
        xff_headers=args.xff_header,
        data_guard=not args.no_data_guard,
        inspect_responses=args.inspect_responses,
        learning_mode=args.learning_mode,
        signature_accuracy=args.signature_accuracy,
    )
    require_valid_policy(policy)
    write_json(args.output, policy)
    print(f"Wrote easy WAF policy: {args.output}")
    if args.checklist_output:
        checklist = build_rollout_checklist(
            args.name,
            args.virtual_server,
            args.logging_profile,
            args.deployment_scenario,
            args.inspect_responses,
            args.mode,
            not args.no_staging,
            args.learning_mode,
            args.signature_accuracy,
            args.log_scope,
        )
        with open(args.checklist_output, "w", encoding="utf-8") as handle:
            handle.write(checklist)
        print(f"Wrote rollout checklist: {args.checklist_output}")
    print("Next: review it, then run policy upload without --apply for a dry-run.")
    return 0


def cmd_lab_dvwa(args: argparse.Namespace) -> int:
    staging = not args.no_staging
    policy = build_dvwa_lab_policy(
        name=args.name,
        mode=args.mode,
        staging=staging,
        signature_accuracy=args.signature_accuracy,
    )
    require_valid_policy(policy)
    write_json(args.output, policy)
    checklist = build_rollout_checklist(
        args.name,
        DVWA_LAB["virtual_server"],
        DVWA_LAB["logging_profile"],
        "existing",
        False,
        args.mode,
        staging,
        "manual",
        args.signature_accuracy,
        "violations",
        DVWA_LAB,
    )
    with open(args.checklist_output, "w", encoding="utf-8") as handle:
        handle.write(checklist)
    print(f"Wrote DVWA lab policy: {args.output}")
    print(f"Wrote DVWA lab checklist: {args.checklist_output}")
    print(
        f"Target: F5 {DVWA_LAB['f5_mgmt_ip']}, "
        f"VS {DVWA_LAB['virtual_server']} {DVWA_LAB['vip']}:{DVWA_LAB['vip_port']}, "
        f"server {DVWA_LAB['server_ip']}"
    )
    return 0


def cmd_policy_validate(args: argparse.Namespace) -> int:
    data = load_json(args.policy_file)
    errors = validate_policy(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.policy_file} is a valid AWAF policy document.")
    return 0


def cmd_policy_upload(args: argparse.Namespace) -> int:
    data = load_json(args.policy_file)
    require_valid_policy(data)
    policy_name = data["policy"]["name"]

    if not args.apply:
        print(json.dumps({"dry_run": True, "policy": policy_name}, indent=2))
        print("No changes sent. Re-run with --apply to upload.")
        return 0

    config = F5Config.from_env()
    result = F5Client(config).create_policy(data)
    print(json.dumps(result, indent=2))
    return 0


def cmd_asm_convert(args: argparse.Namespace) -> int:
    data = load_json(args.input_file)
    converted = convert_asm_to_awaf(data)
    require_valid_policy(converted)
    write_json(args.output_file, converted)
    print(f"Wrote converted AWAF policy: {args.output_file}")
    return 0


def cmd_logs_parse(args: argparse.Namespace) -> int:
    count = parse_jsonl_to_csv(args.input_file, args.output_file)
    print(f"Wrote {count} normalized WAF log rows: {args.output_file}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, RuntimeError, ValueError, PolicyValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
