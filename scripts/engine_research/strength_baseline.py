"""정답 원국 세트(strength-answer-set.csv)로 현재 엔진의 강약 판정을 채점한다.
간지만 있는 고전 명조는 같은 네 기둥이 나오는 양력 날짜·시각을 찾아 엔진에 넣는다."""
import os as _os, sys as _sys
ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
DATA = _os.path.join(ROOT, 'docs', 'engine')
OUT = _os.environ.get('RESEARCH_OUT', '/tmp')
_sys.path[:0] = [ROOT, _os.path.join(ROOT, 'backend'), _os.path.dirname(_os.path.abspath(__file__))]

import sys, os, csv, datetime as dt, json
from collections import Counter
from lunar_python import Solar
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core

HOUR_FOR = {b: h for b, h in zip("子丑寅卯辰巳午未申酉戌亥", (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22))}

# 날짜 → (연, 월, 일) 간지 표를 한 번 만든다(정오 기준, 절입일 경계는 시각으로 다시 확인)
index = {}
d = dt.date(1801, 1, 1)
while d < dt.date(2100, 1, 1):
    ec = Solar.fromYmdHms(d.year, d.month, d.day, 12, 0, 0).getLunar().getEightChar()
    index.setdefault((ec.getYear(), ec.getMonth(), ec.getDay()), []).append(d)
    d += dt.timedelta(days=1)

def engine_verdict(y, m, d_, h):
    for day in index.get((y, m, d_), []):
        hour = HOUR_FOR[h[1]] + 1   # 시지 가운데쯤(진태양시 보정 여유)
        core = calculate_myeongri_core(BirthInput(name="x", gender="male", birth_date=day, calendar_type="solar",
                                                  is_leap_month=False, birth_time=dt.time(hour % 24, 0),
                                                  time_unknown=False), target_date=day + dt.timedelta(days=400))
        p = core.natal_facts.pillars
        got = (p["year"].ganji, p["month"].ganji, p["day"].ganji, p["hour"].ganji)
        if got == (y, m, d_, h):
            return str(core.synthesis.strength_state), day, hour
    return None, None, None

def bucket(v):
    if v in ("신강", "극신강"): return "strong"
    if v in ("신약", "극신약"): return "weak"
    return "other"

rows = list(csv.DictReader(open(sys.argv[1], encoding='utf-8-sig')))
out = []; c = Counter()
for r in rows:
    state, day, hour = engine_verdict(r['year'], r['month'], r['day'], r['hour'])
    gold = bucket(r['verdict']); special = bool(r['special_structure'].strip())
    eng = "strong" if state in ("strong", "extremely_strong") else "weak" if state in ("weak", "extremely_weak") else ("notfound" if state is None else "undetermined")
    out.append(dict(id=r['id'], pillars=f"{r['year']} {r['month']} {r['day']} {r['hour']}", gold=r['verdict'], special=r['special_structure'],
                    engine=state, date=str(day), hit=(eng == gold)))
    if special or gold == "other":
        c['excluded'] += 1; continue
    c['scored'] += 1; c[f'engine_{eng}'] += 1
    if eng == gold: c['correct'] += 1
    elif eng in ("strong", "weak"): c['wrong_direction'] += 1
json.dump(out, open(_os.path.join(OUT, 'strength_baseline_' + _os.path.basename(sys.argv[1]) + '.json'), 'w'), ensure_ascii=False, indent=1)
print(dict(c))
for o in out:
    print(o['id'], o['pillars'], '정답', o['gold'], '| 엔진', o['engine'], o['special'] or '')
