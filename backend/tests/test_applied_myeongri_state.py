from datetime import date

from app.engine.core.models import (
    ActivatedState,
    BirthInput,
    MyeongriCoreResult,
    SemanticState,
    SynthesisResult,
    TimingResult,
)
from app.engine.semantic.applied import build_applied_state
from app.engine.semantic.queries import build_service_query


def _core(*, synthesis=None, timing=None, activated=None):
    return MyeongriCoreResult(
        input=BirthInput(
            name="테스트",
            gender="male",
            birth_date=date(1978, 3, 13),
        ),
        synthesis=synthesis or SynthesisResult(),
        timing=timing or TimingResult(),
        activated_state=activated or ActivatedState(),
        semantic_state=SemanticState(),
    )


def test_pending_operation_is_exposed_as_conditional_not_confirmed():
    core = _core(synthesis=SynthesisResult(
        pending_operations=[{
            "operation": "warm",
            "element": "火",
            "urgency": "medium",
            "source_module": "climate",
            "evidence_origin": "climate",
            "reason": "operation_judgment_unconfirmed",
            "unresolved_requirements": ["personal_climate_need"],
            "evidence_ids": ["evidence:climate:test"],
        }],
    ))

    state = build_applied_state(core, "natal+luck_cycle+annual+monthly+daily")

    assert state["overall_status"] == "conditional"
    assert state["confirmed_elements"] == []
    assert state["conditional_elements"] == ["火"]
    assert state["axes"]["temperature"]["status"] == "conditional"
    assert state["policy"]["conditional_is_not_confirmed"] is True


def test_daily_element_is_observation_only_and_never_promoted():
    core = _core(
        timing=TimingResult(daily={
            "axis": "daily",
            "pillar": {
                "stem": "甲", "branch": "子", "ganji": "甲子",
                "stem_element": "木", "stem_yin_yang": "yang",
                "branch_element": "水", "branch_yin_yang": "yang",
            },
            "ten_god": "peer",
            "date": "2026-09-17",
        }),
    )

    state = build_applied_state(core, "natal+luck_cycle+annual+monthly+daily")

    assert state["confirmed_elements"] == []
    assert state["conditional_elements"] == []
    assert state["overall_status"] == "neutral"
    assert state["timing"]["observations"][0]["stem_element"] == "木"
    assert state["timing"]["observations"][0]["recommendation_status"] == "observation_only"
    assert state["policy"]["timing_observation_is_not_recommendation"] is True


def test_confirmed_direction_remains_confirmed_while_timing_is_separate():
    core = _core(
        synthesis=SynthesisResult(
            favorable_operations=[{
                "operation": "warm",
                "elements": ["火"],
                "urgency": "high",
                "evidence_ids": ["evidence:synthesis:warm"],
            }],
        ),
        timing=TimingResult(daily={
            "axis": "daily",
            "pillar": {
                "stem": "壬", "branch": "子", "ganji": "壬子",
                "stem_element": "水", "stem_yin_yang": "yang",
                "branch_element": "水", "branch_yin_yang": "yang",
            },
            "ten_god": "direct_wealth",
            "date": "2026-09-17",
        }),
    )

    state = build_applied_state(core, "natal+luck_cycle+annual+monthly+daily")

    assert state["overall_status"] == "confirmed"
    assert state["confirmed_elements"] == ["火"]
    assert state["axes"]["temperature"]["confirmed"] == ["warm"]
    assert state["timing"]["observations"][0]["stem_element"] == "水"


def test_direction_timing_summary_preserves_mixed_without_majority_vote():
    synthesis = SynthesisResult(pending_operations=[
        {
            "operation": "mediate",
            "element": "火",
            "urgency": "unspecified",
            "source_module": "mediation",
            "evidence_origin": "mediation",
            "reason": "operation_judgment_unconfirmed",
            "evidence_ids": ["evidence:mediate"],
        },
        {
            "operation": "drain",
            "element": None,
            "urgency": "low",
            "source_module": "strength",
            "evidence_origin": "strength",
            "reason": "source_judgment_unconfirmed",
            "evidence_ids": ["evidence:drain"],
        },
    ])
    conditions = {
        "records": [
            {"relationship_id": "r1", "members": [{"pillar": "timing:daily"}]},
            {"relationship_id": "r2", "members": [{"pillar": "timing:daily"}]},
        ],
    }
    direction = {
        "records": [
            {
                "relationship_id": "r1",
                "comparisons": [
                    {"operation": "mediate", "element": "火", "status": "conditional",
                     "relation": "matches_requested_direction", "evidence_ids": ["evidence:r1:m"]},
                    {"operation": "drain", "element": "土", "status": "conditional",
                     "relation": "matches_requested_direction", "evidence_ids": ["evidence:r1:d"]},
                ],
                "evidence_ids": ["evidence:r1"],
            },
            {
                "relationship_id": "r2",
                "comparisons": [
                    {"operation": "mediate", "element": "火", "status": "conditional",
                     "relation": "opposes_requested_direction", "evidence_ids": ["evidence:r2:m"]},
                ],
                "evidence_ids": ["evidence:r2"],
            },
        ],
    }
    core = _core(
        synthesis=synthesis,
        activated=ActivatedState(
            temporal_conditions=conditions,
            temporal_direction=direction,
        ),
    )

    state = build_applied_state(core, "natal+luck_cycle+annual+monthly+daily")
    by_operation = {item["operation"]: item for item in state["directions"]}

    assert by_operation["mediate"]["timing_assessment"]["relation"] == "mixed"
    assert by_operation["drain"]["timing_assessment"]["relation"] == "supports"
    assert by_operation["drain"]["elements"] == []
    assert by_operation["drain"]["timing_assessment"]["supporting_elements"] == ["土"]
    assert state["policy"]["timing_relation_is_not_vote_count"] is True


def test_service_query_exposes_common_applied_state():
    core = _core(synthesis=SynthesisResult(
        pending_operations=[{
            "operation": "moisten",
            "element": "水",
            "urgency": "low",
            "source_module": "climate",
            "evidence_origin": "climate",
            "reason": "source_judgment_unconfirmed",
            "unresolved_requirements": ["regulator_effectiveness"],
            "evidence_ids": ["evidence:climate:moisten"],
        }],
    ))

    query = build_service_query(core, "daily_overall")

    assert query["applied_state"]["conditional_elements"] == ["水"]
    assert query["constraints"]["timing_observation_standalone_verdict"] is False
