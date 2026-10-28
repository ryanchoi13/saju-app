"""Capture deterministic recommendation output and local timing.

Run this script from the repository checkout being measured:
    python /path/to/benchmark_recommendation_maintenance.py /tmp/result.json

Requires the app's Python dependencies. Uses fictional profiles and no account
storage or network requests. Timing of the full response uses the current day;
the output digest uses only fixed dates. Run sequentially, without other tests.
"""

import hashlib
import json
import statistics
import sys
import time
from datetime import date, time as clock, timedelta
from pathlib import Path

# Deliberately import the checkout under comparison, not this script's parent.
sys.path.insert(0, str(Path.cwd()))

import main
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic.overall import select_overall_domains
from app.engine.services.ranked_menu import build_rankings
from fashion_v2.svg_recommendation import build_svg_catalog_contexts
from fashion_v2.daily_colors import all_daily_pairs, outfit_color

DAILY_PAIRS = [(outfit_color(a), outfit_color(b)) for a, b in all_daily_pairs()]


def capture():
    digest = hashlib.sha256()

    def record(value):
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        digest.update(encoded.encode())
        digest.update(b'\n')

    for gender in ('male', 'female'):
        for season in ('spring', 'summer', 'autumn', 'winter'):
            for a, b in DAILY_PAIRS:
                record(build_svg_catalog_contexts(gender, season, a, b, age=50))

    profiles = [('male', 1990, 5, 15), ('female', 1985, 10, 20),
                ('male', 1970, 3, 1), ('female', 2009, 7, 12)]
    births = [BirthInput(name='검토', gender=g, birth_date=date(y, m, d), birth_time=clock(10, 30))
              for g, y, m, d in profiles]
    weights = [{e: 4} for e in '木火土金水'] + [{}, {'木': -2, '水': -4}, {'木': 2, '火': 2, '金': -1}]
    offsets = (0, 1, 2, 30, 90, 180, 270)
    scopes = ('natal', 'luck_cycle', 'annual', 'monthly', 'daily')
    day_zero = date(2026, 9, 16)
    for birth in births:
        for offset in offsets:
            day = day_zero + timedelta(days=offset)
            for weight in weights:
                record(build_rankings(birth, day, weight, '土', 'medium'))
            core = calculate_myeongri_core(birth, target_date=day)
            for scope in scopes:
                record(select_overall_domains(core, scope))

    tasks = {
        'fashion_all_daily_pairs': lambda: [
            build_svg_catalog_contexts('female', 'autumn', a, b, age=50)
            for a, b in DAILY_PAIRS
        ],
        'menu_four_profiles': lambda: [
            build_rankings(b, day_zero, {'土': 4}, '土', 'medium') for b in births
        ],
        'full_four_profiles': lambda: [
            main.get_saju_pillars_and_analysis(
                '성능검사', b.gender, b.birth_date.year, b.birth_date.month,
                b.birth_date.day, 'solar', 5
            ) for b in births
        ],
    }
    timings = {}
    for name, task in tasks.items():
        task()
        samples = []
        for _ in range(9):
            start = time.perf_counter()
            task()
            samples.append((time.perf_counter() - start) * 1000)
        timings[name] = {'median_ms': statistics.median(samples), 'samples_ms': samples}

    return {
        'counts': {
            'fashion_looks': len(DAILY_PAIRS) * 2 * 4 * 6,
            'menu_rankings': len(births) * len(offsets) * len(weights),
            'overall_scopes': len(births) * len(offsets) * len(scopes),
        },
        'sha256': digest.hexdigest(),
        'timing': timings,
        'scope': 'local_cpu_no_network_or_database',
    }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python benchmark_recommendation_maintenance.py OUTPUT.json')
    result = json.dumps(capture(), indent=2)
    Path(sys.argv[1]).write_text(result, encoding='utf-8')
    print(result)
