"""코디 색 자동 검사 보고서.

    python scripts/color_plan_report.py              # 12명 × 90일
    python scripts/color_plan_report.py --days 30 --out /tmp/report.json

화면에 코디를 다시 켜기 전에 이 보고서의 release_ready 가 True 여야 한다.
"""
import argparse
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "backend"))

from fashion_v2.color_plan.report import evaluate, measure, simulate  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-11-01")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--out")
    args = ap.parse_args()
    metrics = measure(simulate(dt.date.fromisoformat(args.start), args.days))
    report = dict(metrics=metrics, checks=evaluate(metrics))
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
