"""오늘의 행운 색 실측: 가상 사용자 × 일수. 실제 엔진(todays_lucky_tones)을 그대로 쓴다."""
import os as _os, sys as _sys
ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
DATA = _os.path.join(ROOT, 'docs', 'engine')
OUT = _os.environ.get('RESEARCH_OUT', '/tmp')
_sys.path[:0] = [ROOT, _os.path.join(ROOT, 'backend'), _os.path.dirname(_os.path.abspath(__file__))]

import sys, os, json, random, datetime as dt
from collections import Counter
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.daily import build_daily_fortune
from fashion_v2.daily_colors import todays_lucky_tones

N_USERS = int(sys.argv[1]) if len(sys.argv) > 1 else 40
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 90
START = dt.date(2026, 11, 5)
rng = random.Random(7)
users = []
while len(users) < N_USERS:
    y = rng.randint(1960, 2004); m = rng.randint(1, 12); d = rng.randint(1, 28)
    users.append((rng.choice(["male", "female"]), (y, m, d), rng.choice([None] + list(range(24)))))

rows = []
for gender, (y, m, d), hour in users:
    for i in range(DAYS):
        day = START + dt.timedelta(days=i)
        core = calculate_myeongri_core(BirthInput(
            name="검사", gender=gender, birth_date=dt.date(y, m, d), calendar_type="solar",
            is_leap_month=False, birth_time=dt.time(hour, 0) if hour is not None else None,
            time_unknown=hour is None), target_date=day)
        f = build_daily_fortune(core, "검사", day, current_hour=8, account_key=None, include_menu=False)
        L = todays_lucky_tones(core, f, day.toordinal(), y * 372 + m * 31 + d)
        p = core.timing.daily["pillar"]
        rows.append(dict(user=f"{gender}-{y}{m:02d}{d:02d}-{hour}", day=day.isoformat(),
                         ganji=p.get("ganji"), stem_el=p["stem_element"],
                         lucky=f["lucky_element"], natal=f.get("natal_balance_element"),
                         ea=L["element_a"], eb=L["element_b"], a=L["tone_a"]["name"], b=L["tone_b"]["name"],
                         src=L["basis"]["source"], tg=bool(L["tongguan"])))
json.dump(rows, open(_os.path.join(OUT, 'lucky_rows.json'), 'w'), ensure_ascii=False)

by = {}
for r in rows: by.setdefault(r["user"], []).append(r)
same_el = sum(r["ea"] == r["eb"] for r in rows) / len(rows)
src = Counter(r["src"] for r in rows)
swap = rep_set = 0; pairs = 0
top_share = []; natal_in_cards = []
for u, rs in by.items():
    for x, y2 in zip(rs, rs[1:]):
        pairs += 1
        if {x["a"], x["b"]} == {y2["a"], y2["b"]}: rep_set += 1
    els = Counter([r["ea"] for r in rs] + [r["eb"] for r in rs])
    top_share.append(els.most_common(1)[0][1] / (2 * len(rs)))
    nat = rs[0]["natal"]
    natal_in_cards.append(sum(nat in (r["ea"], r["eb"]) for r in rs) / len(rs))
top_share.sort(); natal_in_cards.sort()
print(json.dumps(dict(
    rows=len(rows), users=len(by),
    basis_source=src,
    same_element_pair_rate=round(same_el, 3),
    same_color_set_next_day_rate=round(rep_set / pairs, 3),
    top_element_share_per_user=dict(min=round(top_share[0], 2), median=round(top_share[len(top_share)//2], 2), max=round(top_share[-1], 2)),
    natal_element_in_cards_per_user=dict(min=round(natal_in_cards[0], 2), median=round(natal_in_cards[len(natal_in_cards)//2], 2), max=round(natal_in_cards[-1], 2)),
), ensure_ascii=False, indent=1))
