"""
Quick delivery test for email and SMS providers configured in .env.

Usage:
  python Backend/test_delivery.py --email you@example.com
  python Backend/test_delivery.py --sms +911234567890
  python Backend/test_delivery.py --email you@example.com --sms +911234567890
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from notifications import send_email, send_sms


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", help="Target email for test message")
    parser.add_argument("--sms", help="Target phone for test SMS (E.164 format, e.g. +911234567890)")
    args = parser.parse_args()

    if not args.email and not args.sms:
        print("Pass at least one: --email or --sms")
        return 1

    failures = 0

    if args.email:
        ok = send_email(
            args.email,
            "TaskPrioritize Test Reminder",
            "This is a real delivery test from TaskPrioritize backend.",
        )
        print(f"EMAIL => {'SUCCESS' if ok else 'FAILED'}")
        if not ok:
            failures += 1

    if args.sms:
        ok = send_sms(args.sms, "TaskPrioritize test reminder SMS.")
        print(f"SMS => {'SUCCESS' if ok else 'FAILED'}")
        if not ok:
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
