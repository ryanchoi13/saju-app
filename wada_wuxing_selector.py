# DALHA: Five-element -> Wada Duo selector
# Uses Wada Duo A+B as an intact historical pair.
# The five-element color correspondence and ranking are DALHA recommendation rules,
# not rules authored by Sanzo Wada.
#
# Selection logic:
# - natal_element + today_element determine the daily relation.
# - For same/pressure days, a supportive generating element is used as the second target.
# - For supported/output/wealth days, natal + today are the target color energies.
# - Candidate Wada duos are ranked by how strongly their two colors fit those two energies.
# - date_key rotates within the candidate pool so the same element relation does not always
#   show the same Wada pair.

from wada_color_rules import WADA_DUOS, WADA_COLORS

GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
GENERATED_BY = {v: k for k, v in GENERATES.items()}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

WUXING_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}

# Ranked candidate pools. These are generated from Wada HEX hue/lightness/saturation
# classifications in wada_color_rules.py. 12 candidates per element-pair keeps variety
# while avoiding unrelated pairings.
CANDIDATES = {'木木': [74, 5, 54, 86, 1, 21, 79, 92, 99, 7, 12, 15], '木火': [1, 21, 79, 92, 7, 17, 58, 63, 84, 20, 25, 105], '木土': [86, 99, 12, 78, 94, 109, 36, 65, 41, 114, 33, 72], '木金': [30, 34, 76, 81, 69, 11, 55, 86, 1, 21, 79, 92], '木水': [5, 38, 44, 15, 54, 119, 75, 49, 6, 28, 46, 52], '火火': [108, 37, 43, 71, 90, 91, 97, 120, 9, 18, 35, 47], '火土': [14, 31, 45, 115, 19, 113, 13, 23, 40, 42, 53, 59], '火金': [30, 34, 55, 47, 56, 76, 81, 69, 11, 6, 28, 1], '火水': [6, 28, 46, 112, 117, 77, 98, 39, 85, 88, 27, 48], '土土': [3, 26, 111, 118, 70, 73, 66, 96, 107, 86, 14, 22], '土金': [76, 81, 11, 30, 34, 69, 55, 3, 86, 14, 22, 31], '土水': [52, 62, 2, 60, 89, 83, 22, 114, 33, 72, 29, 93], '金金': [30, 34, 76, 81, 69, 11, 55, 47, 56, 3, 6, 28], '金水': [69, 6, 28, 30, 34, 46, 52, 62, 76, 81, 112, 117], '水水': [67, 119, 75, 49, 106, 6, 28, 46, 52, 62, 112, 117]}

def relation_of(natal_element, today_element):
    if natal_element == today_element:
        return "same"
    if GENERATES[today_element] == natal_element:
        return "supported"
    if GENERATES[natal_element] == today_element:
        return "output"
    if CONTROLS[natal_element] == today_element:
        return "wealth"
    return "pressure"

def target_elements(natal_element, today_element):
    relation = relation_of(natal_element, today_element)
    if relation in {"same", "pressure"}:
        return natal_element, GENERATED_BY[natal_element]
    return natal_element, today_element

def _candidate_key(e1, e2):
    order = "木火土金水"
    return e1 + e2 if order.index(e1) <= order.index(e2) else e2 + e1

def select_wada_duo(natal_element, today_element, date_key):
    """
    date_key: integer such as YYYYMMDD.
    Returns a deterministic Wada Duo number for that user-energy/day combination.
    """
    e1, e2 = target_elements(natal_element, today_element)
    pool = CANDIDATES[_candidate_key(e1, e2)]

    # Deterministic daily rotation. Natal/today elements also perturb the index so
    # different element profiles do not collapse onto the same daily result.
    order = "木火土金水"
    seed = int(date_key) + order.index(natal_element) * 17 + order.index(today_element) * 31
    duo_no = pool[seed % len(pool)]

    return {
        "duo_no": duo_no,
        "relation": relation_of(natal_element, today_element),
        "target_elements": [e1, e2],
        "duo": WADA_DUOS[duo_no],
    }
