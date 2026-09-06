"""Versioned Pydantic contracts shared by every Myeongri core stage.

These models define boundaries only. They intentionally contain no calculation
or interpretation rules, so the existing API and fortune output remain
unchanged while the new core is implemented stage by stage.
"""

from __future__ import annotations

from datetime import date, time
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Gender = Literal["male", "female"]
CalendarType = Literal["solar", "lunar"]


class CoreModel(BaseModel):
    """Strict base model used to catch contract typos early."""

    model_config = ConfigDict(extra="forbid")


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNDETERMINED = "undetermined"


class EvidenceLayer(str, Enum):
    FACT = "fact"
    RULE = "rule"
    JUDGMENT = "judgment"
    TIMING = "timing"
    SHENSHA = "shensha"
    TRANSLATION = "translation"


class HiddenStemRole(str, Enum):
    MAIN = "main"
    MIDDLE = "middle"
    RESIDUAL = "residual"


class TenGod(str, Enum):
    DAY_MASTER = "day_master"
    PEER = "peer"
    ROB_WEALTH = "rob_wealth"
    EATING_GOD = "eating_god"
    HURTING_OFFICER = "hurting_officer"
    INDIRECT_WEALTH = "indirect_wealth"
    DIRECT_WEALTH = "direct_wealth"
    SEVEN_KILLINGS = "seven_killings"
    DIRECT_OFFICER = "direct_officer"
    INDIRECT_RESOURCE = "indirect_resource"
    DIRECT_RESOURCE = "direct_resource"


class BirthInput(CoreModel):
    name: str = Field(min_length=1)
    gender: Gender
    birth_date: date
    calendar_type: CalendarType = "solar"
    is_leap_month: bool = False
    birth_time: time | None = None
    time_unknown: bool = False
    timezone: str = "Asia/Seoul"
    birth_place: str | None = None


class PillarFact(CoreModel):
    stem: str
    branch: str
    ganji: str
    stem_element: str
    stem_yin_yang: str
    branch_element: str
    branch_yin_yang: str


class DayMasterFact(CoreModel):
    stem: str
    element: str
    yin_yang: str


class HiddenStemFact(CoreModel):
    stem: str
    element: str
    role: HiddenStemRole


class BranchHiddenStems(CoreModel):
    branch: str
    stems: list[HiddenStemFact]
    rule_version: str = "hidden-stems-v1"


class TenGodFact(CoreModel):
    pillar: str
    position: Literal["visible_stem", "hidden_stem"]
    stem: str
    ten_god: TenGod
    hidden_role: HiddenStemRole | None = None


class TenGodFacts(CoreModel):
    visible: list[TenGodFact] = Field(default_factory=list)
    hidden: list[TenGodFact] = Field(default_factory=list)
    rule_version: str = "ten-gods-v1"


class RootFact(CoreModel):
    stem_pillar: str
    branch_pillar: str
    visible_stem: str
    hidden_stem: str
    element: str
    hidden_role: HiddenStemRole
    exact_stem: bool


class RootFacts(CoreModel):
    items: list[RootFact] = Field(default_factory=list)
    rule_version: str = "rooting-v1"


class ExposedStemFact(CoreModel):
    hidden_pillar: str
    visible_pillar: str
    stem: str
    hidden_role: HiddenStemRole


class ExposedStemFacts(CoreModel):
    items: list[ExposedStemFact] = Field(default_factory=list)
    rule_version: str = "exposed-stems-v1"


class TwelveStage(str, Enum):
    BIRTH = "birth"
    BATH = "bath"
    CROWN_BELT = "crown_belt"
    OFFICIAL = "official"
    PROSPERITY = "prosperity"
    DECLINE = "decline"
    SICKNESS = "sickness"
    DEATH = "death"
    TOMB = "tomb"
    EXTINCTION = "extinction"
    EMBRYO = "embryo"
    NOURISHMENT = "nourishment"


class TwelveStageFact(CoreModel):
    pillar: str
    branch: str
    stage: TwelveStage


class TwelveStageFacts(CoreModel):
    day_master: str
    items: list[TwelveStageFact] = Field(default_factory=list)
    convention: Literal["traditional-yin-reverse"] = "traditional-yin-reverse"
    rule_version: str = "twelve-stages-v1"


class ElementOccurrence(CoreModel):
    pillar: str
    position: Literal["visible_stem", "branch", "hidden_stem"]
    symbol: str
    element: str
    hidden_role: HiddenStemRole | None = None


class ElementInventory(CoreModel):
    occurrences: list[ElementOccurrence] = Field(default_factory=list)
    rule_version: str = "element-inventory-v1"


class RelationshipCandidateType(str, Enum):
    STEM_COMBINATION = "stem_combination"
    STEM_CONTROL = "stem_control"
    BRANCH_SIX_COMBINATION = "branch_six_combination"
    BRANCH_CLASH = "branch_clash"
    BRANCH_THREE_COMBINATION = "branch_three_combination"
    BRANCH_HALF_COMBINATION = "branch_half_combination"
    BRANCH_DIRECTIONAL_COMBINATION = "branch_directional_combination"
    BRANCH_PUNISHMENT = "branch_punishment"
    BRANCH_HARM = "branch_harm"
    BRANCH_BREAK = "branch_break"


class RelationshipCandidateMember(CoreModel):
    pillar: str
    position: Literal["visible_stem", "branch"]
    symbol: str


class RelationshipCandidate(CoreModel):
    id: str
    type: RelationshipCandidateType
    members: list[RelationshipCandidateMember]
    target_element: str | None = None
    rule_code: str


class RelationshipCandidates(CoreModel):
    items: list[RelationshipCandidate] = Field(default_factory=list)
    rule_version: str = "relationship-candidates-v1"


class TransformationStatus(str, Enum):
    NOT_ESTABLISHED = "not_established"
    POSSIBLE = "possible"
    CONDITIONAL = "conditional"
    ESTABLISHED = "established"


class StrengthState(str, Enum):
    EXTREMELY_WEAK = "extremely_weak"
    WEAK = "weak"
    BALANCED = "balanced"
    STRONG = "strong"
    EXTREMELY_STRONG = "extremely_strong"


class TransformationResult(CoreModel):
    target_element: str
    status: TransformationStatus
    reasons: list[str] = Field(default_factory=list)


class NatalFacts(CoreModel):
    calendar: dict[str, Any] = Field(default_factory=dict)
    pillars: dict[str, PillarFact | None] = Field(default_factory=dict)
    day_master: DayMasterFact | None = None
    hidden_stems: dict[str, BranchHiddenStems] = Field(default_factory=dict)
    ten_gods: TenGodFacts = Field(default_factory=TenGodFacts)
    roots: RootFacts = Field(default_factory=RootFacts)
    exposed_stems: ExposedStemFacts = Field(default_factory=ExposedStemFacts)
    element_inventory: ElementInventory = Field(default_factory=ElementInventory)
    twelve_stages: TwelveStageFacts | None = None
    relationship_candidates: RelationshipCandidates = Field(default_factory=RelationshipCandidates)
    calculation_meta: dict[str, Any] = Field(default_factory=dict)


class Evidence(CoreModel):
    id: str = Field(min_length=1)
    layer: EvidenceLayer
    source_module: str
    rule_code: str | None = None
    description: str
    source_values: dict[str, Any] = Field(default_factory=dict)
    supports: list[str] = Field(default_factory=list)
    reliability: ConfidenceLevel = ConfidenceLevel.UNDETERMINED


class RelationshipResult(CoreModel):
    id: str = Field(min_length=1)
    type: str
    members: list[dict[str, Any]] = Field(default_factory=list)
    existence: Literal["confirmed", "incomplete"]
    action_status: Literal[
        "inactive", "conditional", "active", "blocked", "competing", "resolved"
    ]
    outcome: str | None = None
    strength: Literal["weak", "moderate", "strong"] | None = None
    transformation: TransformationResult | None = None
    affected_facts: list[dict[str, Any]] = Field(default_factory=list)
    supporting_conditions: list[str] = Field(default_factory=list)
    blocking_conditions: list[str] = Field(default_factory=list)
    competing_relationship_ids: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNDETERMINED


class DiagnosticResult(CoreModel):
    module: Literal[
        "structure", "strength", "climate", "pathology", "mediation", "special_structure"
    ]
    status: Literal["completed", "conditional", "insufficient", "failed"]
    conclusion: str | None = None
    summary: str | None = None
    signals: list[dict[str, Any]] = Field(default_factory=list)
    recommended_operations: list[dict[str, Any]] = Field(default_factory=list)
    counter_evidence: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNDETERMINED
    evidence_ids: list[str] = Field(default_factory=list)


class SynthesisResult(CoreModel):
    overall_structure: dict[str, Any] = Field(default_factory=dict)
    strength_state: str | None = None
    climate_state: dict[str, Any] = Field(default_factory=dict)
    favorable_operations: list[dict[str, Any]] = Field(default_factory=list)
    caution_operations: list[dict[str, Any]] = Field(default_factory=list)
    diagnostic_conflicts: list[dict[str, Any]] = Field(default_factory=list)
    summary: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNDETERMINED


class TimingResult(CoreModel):
    luck_cycle: dict[str, Any] = Field(default_factory=dict)
    annual: dict[str, Any] = Field(default_factory=dict)
    monthly: dict[str, Any] = Field(default_factory=dict)
    daily: dict[str, Any] = Field(default_factory=dict)
    relationship_changes: list[dict[str, Any]] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class ActivatedState(CoreModel):
    activated_ten_gods: list[str] = Field(default_factory=list)
    strength_shift: str | None = None
    relationship_changes: list[dict[str, Any]] = Field(default_factory=list)
    climate_shift: dict[str, Any] = Field(default_factory=dict)
    structure_changes: list[dict[str, Any]] = Field(default_factory=list)
    favorable_operations: list[dict[str, Any]] = Field(default_factory=list)
    caution_operations: list[dict[str, Any]] = Field(default_factory=list)
    opportunity_signals: list[str] = Field(default_factory=list)
    pressure_signals: list[str] = Field(default_factory=list)


class ShenshaResult(CoreModel):
    name: Literal["travel_horse", "peach_blossom", "solitary_star", "literary_star", "heavenly_noble"]
    source: str
    basis: str
    activation: Literal["observed", "active", "strongly_active"]
    core_cross_checks: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNDETERMINED


class SemanticState(CoreModel):
    overall_flow: str | None = None
    energy_direction: str | None = None
    favorable_elements: list[str] = Field(default_factory=list)
    caution_elements: list[str] = Field(default_factory=list)
    activated_ten_gods: list[str] = Field(default_factory=list)
    strongest_interactions: list[str] = Field(default_factory=list)
    opportunity_topics: list[str] = Field(default_factory=list)
    caution_topics: list[str] = Field(default_factory=list)
    action_tendencies: list[str] = Field(default_factory=list)
    emotional_tendencies: list[str] = Field(default_factory=list)
    indicators: dict[str, str] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNDETERMINED


class UncertaintyResult(CoreModel):
    time_unknown: bool = False
    scenario_count: int = Field(default=0, ge=0, le=12)
    stable_conclusions: list[dict[str, Any]] = Field(default_factory=list)
    conditional_conclusions: list[dict[str, Any]] = Field(default_factory=list)
    sensitive_topics: list[str] = Field(default_factory=list)


class MyeongriCoreResult(CoreModel):
    schema_version: Literal["myeongri-core-v1"] = "myeongri-core-v1"
    input: BirthInput
    natal_facts: NatalFacts = Field(default_factory=NatalFacts)
    relationships: list[RelationshipResult] = Field(default_factory=list)
    diagnostics: dict[str, DiagnosticResult] = Field(default_factory=dict)
    synthesis: SynthesisResult = Field(default_factory=SynthesisResult)
    timing: TimingResult = Field(default_factory=TimingResult)
    activated_state: ActivatedState = Field(default_factory=ActivatedState)
    shensha: list[ShenshaResult] = Field(default_factory=list)
    semantic_state: SemanticState = Field(default_factory=SemanticState)
    uncertainty: UncertaintyResult = Field(default_factory=UncertaintyResult)
    evidence: list[Evidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
