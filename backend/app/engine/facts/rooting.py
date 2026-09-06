"""Objective rooting (通根) and exposed-stem (透干) connections."""

from __future__ import annotations

from collections.abc import Mapping

from app.engine.constants import GAN_WUXING
from app.engine.core.models import (
    BranchHiddenStems,
    ExposedStemFact,
    ExposedStemFacts,
    PillarFact,
    RootFact,
    RootFacts,
)


ROOTING_RULE_VERSION = "rooting-v1"
EXPOSED_STEM_RULE_VERSION = "exposed-stems-v1"


def calculate_roots(
    pillars: Mapping[str, PillarFact | None],
    hidden_stems: Mapping[str, BranchHiddenStems],
) -> RootFacts:
    """Link each visible stem to same-element hidden stems.

    These are candidate roots only. Strength, usability, and favorable or
    unfavorable meaning belong to later diagnostic stages.
    """

    items: list[RootFact] = []
    for stem_pillar, pillar in pillars.items():
        if pillar is None:
            continue
        try:
            visible_element = GAN_WUXING[pillar.stem]
        except KeyError as exc:
            raise ValueError(f"지원하지 않는 천간입니다: {pillar.stem}") from exc

        for branch_pillar, branch_facts in hidden_stems.items():
            for hidden in branch_facts.stems:
                if hidden.element != visible_element:
                    continue
                items.append(
                    RootFact(
                        stem_pillar=stem_pillar,
                        branch_pillar=branch_pillar,
                        visible_stem=pillar.stem,
                        hidden_stem=hidden.stem,
                        element=visible_element,
                        hidden_role=hidden.role,
                        exact_stem=pillar.stem == hidden.stem,
                    )
                )

    return RootFacts(items=items, rule_version=ROOTING_RULE_VERSION)


def calculate_exposed_stems(
    pillars: Mapping[str, PillarFact | None],
    hidden_stems: Mapping[str, BranchHiddenStems],
) -> ExposedStemFacts:
    """Link hidden stems to identical stems exposed in the heavenly stems."""

    visible = [
        (pillar_name, pillar.stem)
        for pillar_name, pillar in pillars.items()
        if pillar is not None
    ]
    items = [
        ExposedStemFact(
            hidden_pillar=branch_pillar,
            visible_pillar=visible_pillar,
            stem=hidden.stem,
            hidden_role=hidden.role,
        )
        for branch_pillar, branch_facts in hidden_stems.items()
        for hidden in branch_facts.stems
        for visible_pillar, visible_stem in visible
        if hidden.stem == visible_stem
    ]
    return ExposedStemFacts(items=items, rule_version=EXPOSED_STEM_RULE_VERSION)
