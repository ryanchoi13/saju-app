from datetime import date
from pathlib import Path

import pytest

from fashion_v2.production_schedule import production_plan


def test_monthly_plan_creates_eight_observation_slots_and_35_day_batches():
    plan = production_plan("monthly", date(2026, 9, 1))
    assert plan.cycle_id == "monthly:2026-09"
    assert plan.body.count("근거 기록") == 8
    assert "2026-10-06" in plan.body
    assert plan.standard_scope_count == 144
    assert plan.conditional_scope_count == 12
    assert "자동 생성·자동 공개 금지" in plan.body


@pytest.mark.parametrize("month,season", [(1, "봄"), (4, "여름"), (7, "가을"), (10, "겨울")])
def test_quarterly_plan_prepares_the_named_season(month, season):
    plan = production_plan("seasonal", date(2027, month, 15))
    assert season in plan.title
    assert "정오님 1차 화보 검토" in plan.body
    assert "오른쪽 개별 아이템 레일 없음" in plan.body


def test_seasonal_plan_rejects_unscheduled_month():
    with pytest.raises(ValueError):
        production_plan("seasonal", date(2027, 2, 15))


def test_workflow_runs_at_nine_kst_and_can_be_triggered_manually():
    workflow = Path(".github/workflows/fashion-board-schedule.yml").read_text(encoding="utf-8")
    assert 'cron: "0 0 1 * *"' in workflow
    assert 'cron: "0 0 15 1,4,7,10 *"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "issues: write" in workflow
    assert "github.paginate" in workflow

