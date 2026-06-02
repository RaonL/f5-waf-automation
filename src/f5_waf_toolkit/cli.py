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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="f5-waf")
    subcommands = parser.add_subparsers(dest="command", required=True)

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
