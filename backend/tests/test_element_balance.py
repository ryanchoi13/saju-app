"""보완 오행(원국+일진)과 통관 규칙. 2026-10-11 정오님 결정."""
from datetime import date, time

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.element_balance import mediator, tongguan_day, natal_balance, daily_blend


def _core(target=date(2026, 10, 11)):
    return calculate_myeongri_core(BirthInput(name='x', gender='male', birth_date=date(1982, 5, 14),
                                              calendar_type='solar', is_leap_month=False,
                                              birth_time=time(12, 30), time_unknown=False), target_date=target)


def test_mediator_is_the_element_between_controller_and_controlled():
    assert mediator('水', '火') == '木'      # 水克火 → 水生木·木生火
    assert mediator('木', '金') == '水'      # 金克木 → 金生水·水生木
    assert mediator('土', '水') == '金'
    assert mediator('木', '火') is None      # 상생은 통관 대상이 아님
    assert mediator('土', '土') is None


def test_tongguan_only_on_branch_clash_with_different_elements():
    core = _core()
    day_branch = core.natal_facts.pillars['day'].branch          # 酉
    month_branch = core.natal_facts.pillars['month'].branch
    clash = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
             '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
    hit = tongguan_day(core, clash[day_branch])
    assert hit and hit['element'] == mediator(*hit['between'])
    quiet = [b for b in '子丑寅卯辰巳午未申酉戌亥' if b not in {clash[day_branch], clash[month_branch]}]
    assert all(tongguan_day(core, b) is None for b in quiet)
    assert tongguan_day(core, '戌') is None or month_branch == '辰'   # 토-토 충은 이을 오행이 없다


def test_daily_blend_changes_with_the_day_but_keeps_natal_signal():
    balance = natal_balance(_core())
    picks = {daily_blend(balance, e, b)['element'] for e, b in
             (('木', '寅'), ('火', '午'), ('土', '辰'), ('金', '申'), ('水', '子'))}
    assert len(picks) >= 2
