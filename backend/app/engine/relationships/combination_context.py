"""Scoped context rules for original roles, separate from force and valence.

These predicates are an explicit implementation interpretation of the cited
examples. They do not establish all transformations or all release mechanisms.
"""
from app.engine.constants import GAN_WUXING
from app.engine.facts.hidden_stems import get_hidden_stems

_ORDER = {"year": 0, "month": 1, "day": 2, "hour": 3}
_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
REN_OFFICER = {
    "work": "滴天髓闡微", "attribution": "任鐵樵 주석",
    "section": "通神論二十一、官殺 — 四曰合官留殺格",
    "url": "https://zh.wikisource.org/zh-hant/滴天髓闡微#二十一、官殺",
}
REN_RELEASE = {
    "work": "滴天髓闡微", "attribution": "任鐵樵 주석",
    "section": "六親論十一、閒神 — 辛巳 丙申 壬寅 庚戌 및 충극 해소 설명",
    "url": "https://zh.wikisource.org/zh-hant/滴天髓闡微#十一、閒神",
}
ZIPING_SHARED = {
    "work": "子平真詮評注", "attribution": "徐樂吾 평주; 원저의 합거 설명과 구별",
    "section": "五、論十干合而不合 — 乙用庚官 및 一丙合兩辛",
    "url": "https://www.ncc.com.tw/fate/paleo/bg/bg_032.htm",
}


def _ordinary_pair(relation, pillars):
    keys = [m.get("pillar") for m in relation.members]
    return (relation.type == "stem_combination" and len(keys) == 2
            and all(pillars.get(k) for k in _ORDER)
            and all(k in _ORDER and k != "day" for k in keys)
            and abs(_ORDER[keys[0]] - _ORDER[keys[1]]) == 1
            and not relation.competing_relationship_ids
            and relation.action_status not in {"inactive", "blocked"})


def shared_officer_context(relation, pillars):
    """Keep the officer's identity; do not claim exclusive use or full force."""
    if not _ordinary_pair(relation, pillars):
        return None
    if relation.transformation and relation.transformation.status.value == "established":
        return None
    day = pillars["day"]
    if day.stem not in "乙丁己辛癸":
        return None
    peers = [k for k in _ORDER if pillars[k].stem == day.stem]
    member_keys = {m["pillar"] for m in relation.members}
    officer = next((t for t in relation.function_targets
                    if t["role_to_day_master"] == "direct_officer"), None)
    if (not officer or len(peers) != 2 or "day" not in peers
            or not (set(peers) - {"day"}) <= member_keys
            or sum(pillars[k].stem == officer["stem"] for k in _ORDER) != 1):
        return None
    return {"rule": "shared-yin-officer-identity-retained-v1", "source": ZIPING_SHARED,
            "target_id": officer["target_id"], "peer_pillars": peers,
            "role_direction": "shared_not_exclusive", "effective_force": "undetermined",
            "scope": "original_role_identity_only", "basis": "adopted_context_rule"}


def rooted_water_context(relation, pillars, roots, relations):
    """Own water foundation can prevent conversion in two named pair families.

    A remote root or a wood root in a fake earth transformation cannot pass.
    Root-bearing branch combinations/clashes require separate assessment.
    """
    if not _ordinary_pair(relation, pillars):
        return None
    symbols = {m["symbol"] for m in relation.members}
    if symbols not in ({"戊", "癸"}, {"丁", "壬"}):
        return None
    water = next(m for m in relation.members if GAN_WUXING[m["symbol"]] == "水")
    key = water["pillar"]
    own = [r for r in roots.items if r.stem_pillar == key and r.branch_pillar == key
           and r.element == "水"]
    if not own or any(
        (r.type == "branch_clash" or (r.type.startswith("branch_") and "combination" in r.type))
        and any(m["pillar"] == key for m in r.members) for r in relations
    ):
        return None
    branch = pillars[key].branch
    month = pillars["month"].branch
    hidden = get_hidden_stems(branch).stems
    context = None
    rooted_other_water = []
    if symbols == {"戊", "癸"} and branch in {"亥", "子"}:
        context = "water_own_vigorous_root"
    elif symbols == {"丁", "壬"} and branch == "申" and month not in {"寅", "卯"}:
        context = "water_own_growth_root_with_metal_source_outside_wood_season"
    elif symbols == {"戊", "癸"} and branch == "丑" and month in {"巳", "午"}:
        # The 官殺 chapter contrasts 丑 with 巳 while the remote 壬辰 is
        # unchanged. A remote water root alone cannot supply this condition.
        keys = {m["pillar"] for m in relation.members}
        rooted_other_water = [r for r in roots.items if r.stem_pillar not in keys
                              and r.element == "水" and r.branch_pillar != key
                              and not any(q.type == "branch_clash" and any(
                                  m["pillar"] == r.branch_pillar for m in q.members) for q in relations)
                              and not any(q.type == "stem_combination" and any(
                                  m["pillar"] == r.stem_pillar for m in q.members) for q in relations)]
        if rooted_other_water and any(h.element == "金" for h in hidden):
            context = "own_wet_water_reserve_with_metal_and_separate_rooted_water"
    if context is None:
        return None
    return {"rule": "ren-own-water-foundation-prevents-conversion-v1", "source": REN_OFFICER,
            "water_member": water, "own_roots": [r.model_dump(mode="json") for r in own],
            "own_hidden_stems": [h.model_dump(mode="json") for h in hidden],
            "separate_rooted_water": [r.model_dump(mode="json") for r in rooted_other_water],
            "own_branch": branch, "month_branch": month, "context": context,
            "scope": "current_natal_pair_transformation_only", "basis": "adopted_context_rule"}


def metal_fire_release_context(relation, pillars, roots, relations):
    """A bounded metal-season path: day water controls fire, metal moves wood.

    Records release of the metal role from this stem pair only. It neither
    erases all fire roots nor resolves the overlapping branch combination.
    """
    if not _ordinary_pair(relation, pillars):
        return None
    if {m["symbol"] for m in relation.members} != {"丙", "辛"}:
        return None
    day = pillars["day"]
    month = pillars["month"]
    fire = next(m for m in relation.members if m["symbol"] == "丙")
    metal = next(m for m in relation.members if m["symbol"] == "辛")
    if day.stem_element != "水" or month.branch != "申" or day.branch != "寅":
        return None
    if abs(_ORDER[fire["pillar"]] - _ORDER["day"]) != 1:
        return None
    pair_keys = {m["pillar"] for m in relation.members}
    if any(k not in pair_keys | {"day"} and _CONTROLS[p.stem_element] == day.stem_element
           for k, p in pillars.items() if p):
        return None
    controls = [r for r in relations if r.type == "stem_control"
                and {m["pillar"] for m in r.members} == {"day", fire["pillar"]}]
    clashes = [r for r in relations if r.type == "branch_clash"
               and {m["pillar"] for m in r.members} == {"day", "month"}]
    water_roots = [r for r in roots.items if r.stem_pillar == "day" and r.branch_pillar == "month"]
    metal_roots = [r for r in roots.items if r.stem_pillar == metal["pillar"] and r.branch_pillar == "month"]
    moving_fire_roots = [r for r in roots.items if r.stem_pillar == fire["pillar"] and r.branch_pillar == "day"]
    vigorous_fire_roots = [r for r in roots.items if r.stem_pillar == fire["pillar"]
                          and pillars[r.branch_pillar].branch in {"巳", "午"}]
    if not all((controls, clashes, water_roots, metal_roots, moving_fire_roots, vigorous_fire_roots)):
        return None
    return {"rule": "ren-metal-season-control-clash-release-v1", "source": REN_RELEASE,
            "metal_pillar": metal["pillar"], "fire_pillar": fire["pillar"],
            "path_relationship_ids": [r.id for r in controls + clashes],
            "water_roots": [r.model_dump(mode="json") for r in water_roots],
            "metal_roots": [r.model_dump(mode="json") for r in metal_roots],
            "moving_fire_roots": [r.model_dump(mode="json") for r in moving_fire_roots],
            "vigorous_fire_roots": [r.model_dump(mode="json") for r in vigorous_fire_roots],
            "scope": "metal_original_role_released_from_this_stem_pair",
            "effective_force": "undetermined", "root_erased": False,
            "branch_combination_verdict": "unresolved", "basis": "adopted_context_rule"}
