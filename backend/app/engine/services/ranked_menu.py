"""Rank food ideas from the shared Applied Myeongri State contract.

The existing menu pool, familiarity/popularity/accessibility ordering, diet
family spreading, seasonal tie break, and output sizes remain unchanged.
Applied-state status only supplies the element ordering band. A standalone
daily element is never promoted into a recommendation direction.
"""

import hashlib
from collections import Counter

from .daily_menu import MENU_POOL, DIET_MENU_POOL, season_for
from .diet_catalog_revision import diet_family
from .menu_applied import project_menu_direction

VERSION = "ranked-menu-v3-applied-state"
LIMITS = {"general": 10, "diet": 5}


def _diet_order(candidates, key, limit):
    """Spread culinary families inside equal element priorities deterministically."""

    remaining = [(item, key(item), diet_family(item.name)) for item in candidates]
    chosen, families, cuisines = [], Counter(), Counter()
    previous = None
    while remaining and len(chosen) < limit:
        def diverse_key(entry):
            item, priority, family = entry
            return (
                priority[0],
                families[family],
                int(family == previous),
                cuisines[item.cuisine],
                *priority[1:],
            )

        entry = min(remaining, key=diverse_key)
        remaining.remove(entry)
        item, _, family = entry
        chosen.append(item)
        families[family] += 1
        cuisines[item.cuisine] += 1
        previous = family
    return chosen


def build_rankings(birth, day, applied_state):
    direction = project_menu_direction(applied_state)
    scores = direction["element_weights"]
    states = direction["element_states"]

    identity = birth.model_dump_json(exclude={"name"})
    # Preserve the approved deterministic per-day tie breaker.
    seed = f"ranked-menu-v1|{identity}|{day}"
    season = season_for(day.month)
    rankings = {}

    for mode, pool in (("general", MENU_POOL), ("diet", DIET_MENU_POOL)):
        # Preserve the existing caution behavior for this connection step.
        # Whether this creates permanent exclusions is measured in the 30-day
        # simulation before any diversity/exclusion policy is changed.
        candidates = [item for item in pool if scores[item.element] >= 0]

        def key(item):
            everyday = (
                item.popularity,
                item.familiarity,
                item.accessibility,
                int(season in item.seasons),
            )
            tie = hashlib.sha256(
                f"{seed}|{mode}|{item.name}".encode()
            ).hexdigest()
            return (
                -scores[item.element],
                *(-value for value in everyday),
                tie,
                item.name,
            )

        ordered = (
            _diet_order(candidates, key, LIMITS[mode] * 2)
            if mode == "diet"
            else sorted(candidates, key=key)[: LIMITS[mode] * 2]
        )
        ordered = ordered[: len(ordered) // 2 * 2]
        rankings[mode] = [
            dict(
                menu=item.name,
                rank=i + 1,
                element=item.element,
                element_score=scores[item.element],
                element_state=states[item.element],
            )
            for i, item in enumerate(ordered)
        ]

    return dict(
        version=VERSION,
        date=str(day),
        rankings=rankings,
        basis=direction["basis"],
        basis_text=direction["basis_text"],
        confidence=direction["confidence"],
        element_scores=scores,
        element_states=states,
        applied_policy=direction["policy"],
        pool_sizes={"general": len(MENU_POOL), "diet": len(DIET_MENU_POOL)},
    )
