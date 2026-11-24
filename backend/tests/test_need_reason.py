"""'필요한 기운' 뒤 한 줄 이유 (2026-11-16). 필요한 기운 ≠ 모자란 기운: 정오님 사주(목·토 넘침, 금·수 모자람)에서
금·화가 필요하고 수는 모자라도 우선하지 않는 이유를 한 줄로 설명한다."""
import datetime as dt

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.element_balance import element_tiers, natal_balance
from app.engine.services.need_reason import need_reason


def _core(birth, gender="male", hour=11):
    return calculate_myeongri_core(BirthInput(
        name="검사", gender=gender, birth_date=birth, calendar_type="solar", is_leap_month=False,
        birth_time=dt.time(hour, 0), time_unknown=False), target_date=dt.date(2026, 11, 16))


def _good(core):
    tiers, ranking = element_tiers(core)["tiers"], natal_balance(core)["ranking"]
    return [e for e in ranking if tiers[e] == "good"][:2]


def test_reference_person():
    core = _core(dt.date(1978, 3, 13))
    assert _good(core) == ["金", "火"]
    text = need_reason(core, ["金", "火"])
    assert text == ("목(木) 기운이 단단한 편이라 금(金)은 눌러 주고 화(火)는 풀어 줘서 균형이 맞아요. "
                    "수(水)는 모자라지만 목(木)을 더 키우는 쪽이라 우선하지 않아요.")


def test_empty_and_undetermined_give_nothing():
    core = _core(dt.date(1978, 3, 13))
    assert need_reason(core, []) == ""
    for d in range(0, 4000, 97):          # 강약 보류인 사람은 문장을 붙이지 않는다(깨지지도 않는다)
        c = _core(dt.date(1950, 1, 1) + dt.timedelta(days=d), "female", d % 24)
        text = need_reason(c, _good(c))
        if str(c.synthesis.strength_state) not in {"strong", "extremely_strong", "weak", "extremely_weak"}:
            assert text == ""
        else:
            assert text.endswith("요.")
