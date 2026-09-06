"""Element occurrences without shortage, excess, or usefulness judgments."""

from __future__ import annotations

from collections.abc import Mapping

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import BranchHiddenStems, ElementInventory, ElementOccurrence, PillarFact


ELEMENT_INVENTORY_RULE_VERSION = "element-inventory-v1"


def calculate_element_inventory(
    pillars: Mapping[str, PillarFact | None],
    hidden_stems: Mapping[str, BranchHiddenStems],
) -> ElementInventory:
    """Record where each element occurs; do not convert presence into scores."""

    occurrences: list[ElementOccurrence] = []
    for pillar_name, pillar in pillars.items():
        if pillar is None:
            continue
        try:
            stem_element = GAN_WUXING[pillar.stem]
            branch_element = ZHI_WUXING[pillar.branch]
        except KeyError as exc:
            raise ValueError(f"지원하지 않는 간지입니다: {exc.args[0]}") from exc
        occurrences.extend(
            [
                ElementOccurrence(
                    pillar=pillar_name,
                    position="visible_stem",
                    symbol=pillar.stem,
                    element=stem_element,
                ),
                ElementOccurrence(
                    pillar=pillar_name,
                    position="branch",
                    symbol=pillar.branch,
                    element=branch_element,
                ),
            ]
        )
        branch_facts = hidden_stems.get(pillar_name)
        if branch_facts is not None:
            occurrences.extend(
                ElementOccurrence(
                    pillar=pillar_name,
                    position="hidden_stem",
                    symbol=item.stem,
                    element=item.element,
                    hidden_role=item.role,
                )
                for item in branch_facts.stems
            )
    return ElementInventory(
        occurrences=occurrences,
        rule_version=ELEMENT_INVENTORY_RULE_VERSION,
    )
