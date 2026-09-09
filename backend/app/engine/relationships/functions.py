"""Trace which natal functions a relation could change, without a winner claim.

Role identity, effective availability and benefit to this chart are separate.
See 子平真詮評注 IV/V/VII and 滴天髓闡微 衰旺/通關. In particular,
neither every combination removes a role nor every clash is detrimental.
"""
from app.engine.constants import GAN_WUXING
from app.engine.facts.ten_gods import get_ten_god
from app.engine.facts.hidden_stems import get_hidden_stems

VERSION = "relationship-function-targets-v1"
SOURCE = {
    "work": "子平真詮評注", "sections": ["四、論十干配合性情", "五、論十干合而不合", "七、論刑沖會合解法"],
    "attribution": "沈孝瞻 원저와 徐樂吾 평주를 구분해 비교",
    "url": "https://www.ncc.com.tw/fate/paleo/bg/bg_032.htm",
    "scope": "역할 유지·감소와 전체 희기의 구별. 사건 예측 정확도 근거 아님",
}
_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
_SUPPORT = {"day_master", "peer", "rob_wealth", "direct_resource", "indirect_resource"}


def describe_function_targets(kind, members, pillars, roots):
    day = pillars.get("day")
    if day is None or kind not in {"stem_combination", "stem_control", "branch_clash"}:
        return []
    targets = []
    includes_day = any(m.get("pillar") == "day" and m.get("position") == "visible_stem" for m in members)

    def add(member, stem_pillar, stem, root=None, hidden=False):
        if stem_pillar.startswith("timing:"):
            return
        role = "day_master" if stem_pillar == "day" and not hidden else get_ten_god(day.stem, stem).value
        carrier = (f"root:{root.branch_pillar}:{root.hidden_stem}:to:{stem_pillar}"
                   if root else f"hidden:{stem_pillar}:{stem}" if hidden else f"stem:{stem_pillar}:{stem}")
        item = dict(target_id=carrier, stem_pillar=stem_pillar, stem=stem,
            function_kind="root_support" if root else "hidden_role" if hidden else "visible_role",
            carrier_id=(f"hidden:{root.branch_pillar}:{root.hidden_stem}" if root else carrier),
            element=GAN_WUXING[stem], role_to_day_master=role,
            balance_role="supports_day" if role in _SUPPORT else "drains_or_pressures_day",
            source_member=dict(member), root_connection=root.model_dump(mode="json") if root else None,
            effect_status="unresolved", actual_valence="undetermined",
            rule_version=VERSION, source=SOURCE)
        if kind == "stem_combination" and includes_day:
            item.update(original_role_policy="not_removed_by_day_master_combination_alone",
                possible_changes=["retained"],
                separate_review=["transformation", "competition", "effective_role_direction"])
        else:
            item.update(original_role_policy="compare_retention_and_change",
                possible_changes=["retained", "reduced"] + (["activated"] if kind == "branch_clash" else []),
                separate_review=["force", "root_usability", "other_relations"])
        if not any(t["target_id"] == carrier for t in targets):
            targets.append(item)

    if kind == "branch_clash":
        for member in members:
            if member.get("position") != "branch":
                continue
            for hidden in get_hidden_stems(member["symbol"]).stems:
                add(member, member["pillar"], hidden.stem, hidden=True)
            for root in roots.items:
                if root.branch_pillar == member.get("pillar"):
                    add(member, root.stem_pillar, root.visible_stem, root)
    else:
        for member in members:
            if member.get("position") != "visible_stem" or member.get("symbol") not in GAN_WUXING:
                continue
            if kind == "stem_control" and not any(
                other.get("symbol") in GAN_WUXING
                and _CONTROLS[GAN_WUXING[other["symbol"]]] == GAN_WUXING[member["symbol"]]
                for other in members if other is not member
            ):
                continue
            add(member, member["pillar"], member["symbol"])
    return sorted(targets, key=lambda t: t["target_id"])


def compare_balance_function(target, change, operation):
    """Compare a hypothetical change to a requested *balance direction* only.

    This does not equate an officer with harm, a resource with benefit, or
    reduced support with a specific draining remedy.
    """
    if operation not in {"support", "drain"} or change not in {"reduced", "activated"}:
        return None
    role = target.get("balance_role")
    if role not in {"supports_day", "drains_or_pressures_day"}:
        return None
    more_support = (role == "supports_day") == (change == "activated")
    matches = more_support == (operation == "support")
    return "matches_requested_direction" if matches else "opposes_requested_direction"
