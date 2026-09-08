from datetime import date, time
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app.engine.core.models import BirthInput
from app.engine.services import meal_history


class MealHistoryTests(TestCase):
    def test_reload_persistence_and_mode_separation(self):
        birth = BirthInput(name="검증", gender="male", birth_date=date(1978, 3, 13), birth_time=time(11))
        old = meal_history._DB
        with TemporaryDirectory() as directory, patch.dict("os.environ", {"DALHA_MENU_HISTORY_DB": directory + "/history.sqlite"}):
            meal_history._DB = None
            try:
                def build(general, diet):
                    self.assertEqual(general, ())
                    self.assertEqual(diet, ())
                    return {mode: {"date": "2026-09-08", "meals": [{"menu": mode}]} for mode in ("general", "diet")}
                first = meal_history.stored_plans(birth, date(2026, 9, 8), build)
                meal_history._DB.close()
                meal_history._DB = None
                def forbidden(*args):
                    self.fail("Saved date must not be regenerated")
                self.assertEqual(first, meal_history.stored_plans(birth, date(2026, 9, 8), forbidden))
                def next_day(general, diet):
                    self.assertEqual(general[0]["meals"][0]["menu"], "general")
                    self.assertEqual(diet[0]["meals"][0]["menu"], "diet")
                    return {mode: {"date": "2026-09-09", "meals": []} for mode in ("general", "diet")}
                meal_history.stored_plans(birth, date(2026, 9, 9), next_day)
            finally:
                if meal_history._DB is not None:
                    meal_history._DB.close()
                meal_history._DB = old
