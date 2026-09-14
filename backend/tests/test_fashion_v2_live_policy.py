import os
import unittest

from fashion_v2.color_application import build_colored_catalog_contexts
from fashion_v2.published_boards import PUBLISHED_PAIRS, published_looks_for


A = {"name": "Grenadine Pink", "name_ko": "페일 레드", "hex": "#f48067"}
B = {"name": "Deep Indigo", "name_ko": "딥 네이비", "hex": "#051230"}


class FashionV2LivePolicyTests(unittest.TestCase):
    def test_women_thirty_plus_always_receive_a_tpo_appropriate_bag(self):
        contexts = build_colored_catalog_contexts("female", "autumn", A, B, age=38)
        for tpo, context in contexts.items():
            for look in context["looks"]:
                bags = [item for item in look["items"] if item["category"] == "bag"]
                self.assertEqual(len(bags), 1, (tpo, look["look_role"]))
                self.assertTrue(bags[0]["age_required"])

    def test_women_under_thirty_do_not_have_a_forced_bag(self):
        contexts = build_colored_catalog_contexts("female", "autumn", A, B, age=29)
        self.assertFalse(any(
            item["category"] == "bag"
            for context in contexts.values()
            for look in context["looks"]
            for item in look["items"]
        ))

    def test_every_fifty_plus_shoe_passes_the_comfort_gate(self):
        for gender in ("male", "female"):
            contexts = build_colored_catalog_contexts(gender, "autumn", A, B, age=55)
            for context in contexts.values():
                for look in context["looks"]:
                    shoe = next(item for item in look["items"] if item["category"] == "shoes")
                    self.assertTrue(shoe["comfort_gate_passed"])
                    self.assertIn("comfort_profile", shoe)

    def test_final_mature_formal_board_is_selected_for_cool_weather(self):
        weather = {"daytime_apparent_high": 15}
        pair = published_looks_for("male", 55, "business_formal", weather, "autumn")
        self.assertEqual(len(pair), 2)
        self.assertTrue(pair[0]["board_image"].endswith("sample-v11-male-fifty-cool-business-formal-daily.webp"))
        self.assertIn("재킷 아래로 연결된", next(
            item["label"] for item in pair[0]["items"] if item["category"] == "bottom"))

    def test_forties_casual_uses_the_approved_adult_single_outfit_pair(self):
        pair = published_looks_for(
            "male", 48, "casual", {"daytime_apparent_high": 24}, "autumn")
        self.assertEqual(len(pair), 2)
        self.assertTrue(all("sample-v" in look["board_image"] for look in pair))
        self.assertTrue(all("thirties-warm-casual" in look["board_image"] for look in pair))

    def test_every_published_scope_is_a_complete_pair_with_real_assets(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        for scope, pair in PUBLISHED_PAIRS.items():
            self.assertEqual([look["look_role"] for look in pair], ["daily", "trend"], scope)
            for look in pair:
                path = os.path.join(root, look["board_image"].lstrip("/"))
                self.assertTrue(os.path.exists(path), path)
                self.assertGreater(os.path.getsize(path), 20_000, path)


if __name__ == "__main__":
    unittest.main()
