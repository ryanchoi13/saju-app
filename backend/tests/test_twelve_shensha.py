"""12신살 표 — 기준 지지의 삼합 생지를 지살로 두고 12지지를 차례로 배정한다."""
import unittest

from app.engine.shensha import TWELVE_SHENSHA, TWELVE_SHENSHA_HANJA, twelve_shensha
from app.engine.shensha.engine import _TRIAD_RULES

BRANCHES = "子丑寅卯辰巳午未申酉戌亥"


class TwelveShenshaTests(unittest.TestCase):
    def test_every_base_maps_twelve_branches_to_twelve_names(self):
        for base in BRANCHES:
            names = [twelve_shensha(base, b) for b in BRANCHES]
            self.assertEqual(sorted(names), sorted(TWELVE_SHENSHA), base)

    def test_matches_the_existing_triad_rules(self):
        for star, name in (("travel_horse", "역마"), ("peach_blossom", "년살"), ("flower_canopy", "화개")):
            for base, target in _TRIAD_RULES[star].items():
                self.assertEqual(twelve_shensha(base, target), name, (star, base, target))

    def test_in_o_sul_table(self):
        # 寅午戌: 지살 寅 · 년살 卯 · 월살 辰 · 망신 巳 · 장성 午 · 반안 未 · 역마 申 · 육해 酉 · 화개 戌 · 겁살 亥 · 재살 子 · 천살 丑
        expect = dict(zip("寅卯辰巳午未申酉戌亥子丑", TWELVE_SHENSHA))
        for base in "寅午戌":
            for target, name in expect.items():
                self.assertEqual(twelve_shensha(base, target), name, (base, target))

    def test_same_triad_gives_same_answer_and_hanja_is_complete(self):
        for group in ("申子辰", "寅午戌", "巳酉丑", "亥卯未"):
            for b in BRANCHES:
                self.assertEqual(len({twelve_shensha(base, b) for base in group}), 1)
        self.assertEqual(set(TWELVE_SHENSHA_HANJA), set(TWELVE_SHENSHA))


if __name__ == "__main__":
    unittest.main()
