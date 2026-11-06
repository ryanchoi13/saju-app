"""원국 보완 오행(primary)이 억부 방향과 어긋나는 사용자 비율. 무작위 출생 N명."""
import os as _os, sys as _sys
ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
DATA = _os.path.join(ROOT, 'docs', 'engine')
OUT = _os.environ.get('RESEARCH_OUT', '/tmp')
_sys.path[:0] = [ROOT, _os.path.join(ROOT, 'backend'), _os.path.dirname(_os.path.abspath(__file__))]

import sys, os, random, datetime as dt, json
from collections import Counter
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.element_balance import natal_balance, GENERATES, GENERATED_BY, CONTROLS, CONTROLLED_BY

N = int(sys.argv[1]) if len(sys.argv) > 1 else 600
rng = random.Random(11)
stats = Counter(); examples = []
for _ in range(N):
    y = rng.randint(1960, 2004); m = rng.randint(1, 12); d = rng.randint(1, 28); h = rng.randint(0, 23)
    core = calculate_myeongri_core(BirthInput(name="x", gender=rng.choice(["male", "female"]), birth_date=dt.date(y, m, d),
                                              calendar_type="solar", is_leap_month=False, birth_time=dt.time(h, 0),
                                              time_unknown=False), target_date=dt.date(2026, 11, 5))
    nb = natal_balance(core)
    dm = core.natal_facts.pillars["day"].stem_element
    st = str(core.synthesis.strength_state or "undetermined")
    p = nb["primary"]
    if st in {"strong", "extremely_strong"}:
        bucket = "strong"; bad = p in {dm, GENERATED_BY[dm]}
    elif st in {"weak", "extremely_weak"}:
        bucket = "weak"; bad = p in {GENERATES[dm], CONTROLS[dm], CONTROLLED_BY[dm]}
    else:
        bucket = "undetermined"; bad = None
    stats[bucket] += 1
    if bad: stats[bucket + "_contradict"] += 1
    if bad is not None and nb["scores"][nb["ranking"][0]] == nb["scores"][nb["ranking"][1]]:
        stats[bucket + "_tie_top2"] += 1
    if bad and len(examples) < 5:
        examples.append(dict(birth=f"{y}-{m:02d}-{d:02d} {h}시", dm=dm, strength=st, primary=p,
                             scores=nb["scores"], comp=nb["composition"]))
print(json.dumps(dict(n=N, stats=stats, examples=examples), ensure_ascii=False, indent=1))
