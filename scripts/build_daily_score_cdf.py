"""오늘의 운세 길흉 점수 — 모집단 raw 분위수 매듭(RAW_CDF) 생성.

무작위 출생(1950~2005, 0~23시, 성별 무작위, seed 20261024) N명에 대해 원국을 한 번 계산하고,
60갑자 일진을 모두 한 번씩 돌려 raw 점수(타이브레이크 키)를 모은다. 일진은 60일 주기라 60갑자 × N 이
1년 365일 × N 과 같은 분포다(월운 지지가 끼는 삼합·방합만 2026-01~03 월운으로 고정된다).

사용:  cd backend && python ../scripts/build_daily_score_cdf.py [N] [--knots 41]
출력:  app/engine/services/daily_score.py 의 RAW_CDF 상수에 붙일 파이썬 튜플 + 단계 분포 검산.
억부(용신) 설정은 daily_score.YONG_W·yong_direction 을 그대로 따른다 — 가중치를 바꾸면 이 표도 다시 만든다.
"""
from __future__ import annotations

import collections
import random
import statistics
import sys
import time as clock
from datetime import date, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.engine.core.models import BirthInput                       # noqa: E402
from app.engine.orchestrator import calculate_myeongri_core        # noqa: E402
from app.engine.services import daily_score as ds                  # noqa: E402

SEED = 20261024
START = date(2026, 1, 1)          # 60갑자가 한 바퀴 도는 구간의 첫날


def sample_births(n: int) -> list[BirthInput]:
    rng = random.Random(SEED)
    span = (date(2005, 12, 31) - date(1950, 1, 1)).days
    out = []
    for i in range(n):
        birth = date(1950, 1, 1) + timedelta(days=rng.randint(0, span))
        out.append(BirthInput(name=f"p{i}", gender=rng.choice(["male", "female"]), birth_date=birth,
                              birth_time=time(rng.randint(0, 23), 0), time_unknown=False))
    return out


def population_keys(births: list[BirthInput]) -> tuple[list[float], list[int], collections.Counter]:
    keys, raws, strength = [], [], collections.Counter()
    for birth in births:
        core = calculate_myeongri_core(birth, target_date=START)
        strength[ds.yong_direction(core) or "none"] += 1
        for i in range(60):
            day = START + timedelta(days=i)
            items = ds.score_items(core, ds.day_ganji(day), day)
            keys.append(ds.raw_score(items))
            raws.append(sum(w for _, w in items))
    return sorted(keys), raws, strength


def knots_from(keys: list[float], count: int) -> tuple[tuple[float, float], ...]:
    n = len(keys)
    out = []
    for j in range(count):
        f = j / (count - 1)
        k = keys[min(n - 1, int(f * n))] if f < 1 else keys[-1]
        out.append((round(f, 4), round(k, 2)))
    return tuple(out)


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1000
    count = int(sys.argv[sys.argv.index("--knots") + 1]) if "--knots" in sys.argv else 41
    t0 = clock.time()
    births = sample_births(n)
    keys, raws, strength = population_keys(births)
    elapsed = clock.time() - t0
    knots = knots_from(keys, count)

    print(f"# N = {n}명 × 60갑자 = {len(keys):,}건, 억부 W={ds.YONG_W} (strong/weak만), {elapsed:.1f}s")
    print(f"# raw 평균 {statistics.mean(raws):.2f} 표준편차 {statistics.pstdev(raws):.2f} 범위 {min(raws)}~{max(raws)}")
    print(f"# strength: {dict(strength)}")
    print("RAW_CDF: tuple[tuple[float, float], ...] = (")
    for i in range(0, len(knots), 4):
        print("    " + " ".join(f"({f}, {k})," for f, k in knots[i:i + 4]))
    print(")")

    dist = collections.Counter(ds.grade(ds.display_score(k, knots)) for k in keys)
    print("# 단계 분포(검산):", {g: f"{100 * dist[g] / len(keys):.1f}%" for g in ds.GRADES})
    print("# 목표: 나쁨 15 / 주의 20 / 보통 30 / 좋음 20 / 아주 좋음 15")


if __name__ == "__main__":
    main()
