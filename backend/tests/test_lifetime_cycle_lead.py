"""평생 풀이 대운 — 별명 제목을 빼고, 첫 문장이 '무엇의 10년이고 결론은 어느 쪽인가'를 말한다 (2026-11-02)."""
import random
import re
import unittest
from datetime import date, time

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic import build_service_query
from app.engine.services import lifetime_v3_copy as copy
from app.engine.services.annual_copy import find_banned
from app.engine.services.lifetime import _split_cycles
from app.engine.services.lifetime_v3 import build_lifetime_v3

TARGET = date(2026, 11, 2)


def _html(birth, clock, gender="male"):
    core = calculate_myeongri_core(
        BirthInput(name="t", gender=gender, birth_date=birth, birth_time=clock, time_unknown=False), target_date=TARGET)
    q = build_service_query(core, "lifetime_overall")
    past, now, future = _split_cycles(q["timing"]["luck_cycles"])
    return build_lifetime_v3(core, "t", past=past, now=now, future=future, current_selection=None,
                             climate=q["synthesis"]["climate_state"].get("state"),
                             strength=q["synthesis"].get("strength_state"))["html"]


def _leads(html):
    text = re.sub(r"<[^>]*>", "\n", html)
    return [m.group(1) for m in re.finditer(r"([^\n.]*10년(?:입니다|이었습니다|으로 넘어갑니다))\.", text)]


class CycleLeadTests(unittest.TestCase):
    def test_jungoh_now_cycle(self):
        html = _html(date(1978, 3, 13), time(11, 0))
        self.assertIn("<h4>지금 · 48~57세 · 庚申</h4>", html)
        self.assertIn("바깥의 기준과 부딪치는 일이 잦지만, 만만치 않은 일을 해내며 자리가 커지는 10년입니다.", html)
        self.assertNotIn("만만찮은 숙제", html)
        self.assertNotIn("들어오는 기운", html)

    def test_every_cycle_has_one_lead_and_no_label(self):
        rng = random.Random(3)
        cons_bank = {v[i] for table in (copy.LEAD_GAIN, copy.LEAD_LOAD, copy.LEAD_POS, copy.LEAD_NEG)
                     for v in table.values() for i in (2, 3)}
        for _ in range(25):
            b = date(rng.randint(1950, 2005), rng.randint(1, 12), rng.randint(1, 28))
            html = _html(b, time(rng.randint(0, 23), 0), rng.choice(["male", "female"]))
            with self.subTest(birth=b):
                past_n = html.count('data-cycle-state="past"')
                leads = _leads(html)
                self.assertGreaterEqual(len(leads), past_n + 1)
                self.assertFalse(re.search(r"<h5>[^<]*· [^<]*· [^<]*</h5>", html), "지나온 길 제목에 별명이 남았다")
                # 같은 걸림을 앞 구간과 같은 말로 되풀이하지 않는다
                cons = [c for lead in leads for c in cons_bank if lead.startswith(c + ",")]
                self.assertEqual(len(cons), len(set(cons)))

    def test_lead_bank_is_clean(self):
        tables = (copy.LEAD_GAIN, copy.LEAD_LOAD, copy.LEAD_POS, copy.LEAD_NEG,
                  copy.LEAD_YOUNG_GAIN, copy.LEAD_YOUNG_LOAD, copy.LEAD_YOUNG_NEG)
        for table in tables:
            for key, forms in table.items():
                for text in forms:
                    self.assertFalse(find_banned(text), (key, text))
                    self.assertNotIn("수 있", text)
        for table in (copy.LEAD_GAIN, copy.LEAD_LOAD, copy.LEAD_POS, copy.LEAD_NEG):
            for key, forms in table.items():
                self.assertEqual(len(forms), 4, key)
                self.assertTrue(forms[2].endswith("지만") and forms[3].endswith("지만"), key)


if __name__ == "__main__":
    unittest.main()
