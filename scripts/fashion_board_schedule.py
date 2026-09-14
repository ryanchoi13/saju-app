#!/usr/bin/env python3
"""Emit one idempotent GitHub-issue payload for the fashion production cycle."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fashion_v2.production_schedule import production_plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, choices=("monthly", "seasonal"))
    parser.add_argument("--today", type=date.fromisoformat)
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = json.dumps(production_plan(args.event, args.today).as_dict(), ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
    else:
        print(payload)


if __name__ == "__main__":
    main()
