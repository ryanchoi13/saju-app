"""오늘의 이야기 v2 조립기 — 길흉 등급(daily_score.evaluate)과 근거 카드(daily_rx)를 이어받아 본문을 만든다.

구조(「오늘의 이야기 본문 재구성안」 §3, 「은행 v4·v5 보고」 §3):
  제목       = TITLE[evidence_key][i]  (LEAD 와 같은 i)
  총운       = LEAD.scene(2문장) + SECOND[순접]? + SECOND[역접]? + SECOND[몸]? + (LEAD.advice | ATTITUDE[등급])
  분야 4     = 금전 · 애정·관계 · 일 · 건강.  결(좋음/보통/주의)은 분야 편차 + 등급 보정으로 정한다.
               보통 = DOMAIN 2문장 + GOD_COLOR(십성 색, topic 이 겹칠 때만) / 좋음·주의 = DOMAIN 3문장 (+ EXTRA, 튀는 분야)
               애정·관계 = 첫 문장 뒤에 LOVE[신호] (남 재성 / 여 관성 / 도화 / 일지 육합·충)
  마무리     = CLOSE[등급]. 보통엔 없음.

선택은 결정론이다. 변형 회전은 daily_rx 의 30일 이력(recent)으로 한다 — 안 쓴 변형을 은행 순서대로 먼저, 다 썼으면
가장 오래전에 쓴 것부터. 이력은 daily_rx._history 가 RX_EPOCH 부터 같은 규칙으로 다시 돌려 복원하므로 어느 날 계산해도
지난날이 같게 나온다(저장 없음). 이력 항목은 ("story", 구분, 번호) 꼴로 카드 문장 이력과 같은 목록에 섞여 들어간다.

조립 검사(조합에서 거르고, 마지막에 단언): 인접 문장 말끝 다름 · "오늘" <3(문단) · 명사 반복 없음 · 조각 첫 어절 다름 ·
"~날" 말끝 분야 ≤1·총운 ≤2·본문 ≤6 · "~면 됩니다" ≤3 · 기운 ≤1 · 쪽/결 ≤2 · 법이죠 ≤1 · 금지 어휘 0 ·
좋음 등급에 미지근 관용구 0 · 카드 분야 문장과 명사 2개 이상 겹침 없음 · 총운이 몸을 말한 날엔 건강 보통 '평온' 변형 회피.
"""
from __future__ import annotations

import re
from datetime import date

from app.engine.core.models import MyeongriCoreResult
from app.engine.facts.ten_gods import get_ten_god
from app.engine.facts.twelve_stages import get_twelve_stage
from app.engine.services import daily_score
from app.engine.services import daily_story_bank as B

STORY_VERSION = "dalha-daily-story-v2-bank5"
SECTION_ORDER = (("money", "금전"), ("love", "애정·관계"), ("work", "일"), ("health", "건강"))
USE_ELEMENT = "story"        # recent 목록의 element 자리

GOOD = set(B.GOOD)
TIE_PRIORITY = ["천을귀인", "문창", "삼합", "일간 천간합", "day지 육합", "month지 육합", "year지 육합", "hour지 육합",
                "일간 천간충", "day지 충", "month지 충", "year지 충", "hour지 충", "day지 형", "month지 형"]
ALIAS = {"12운성 birth": "12운성 up", "12운성 official": "12운성 up", "12운성 prosperity": "12운성 up",
         "12운성 death": "12운성 down", "12운성 tomb": "12운성 down", "12운성 extinction": "12운성 down",
         "day지 반합": "반합", "month지 반합": "반합", "year지 반합": "반합", "hour지 반합": "반합"}
NOUNS = ["혼자", "저녁", "결정", "약속", "말", "몸", "급해", "사람", "실수", "고집"]
KEYWORDS = ["세게", "끝까지", "호감", "한 박자", "저녁", "안부", "혼자", "결정", "약속", "밥", "서운", "정해", r"마음이? 편",
            "지갑", "숫자", "어깨", "잠", "화면", "따뜻한", "걷", "비교", "내일", "하루 묵", "저절로", "일찍", "급해", "선배", "어른", "듣", "머리"]
CROSS = ["짜증", "서두르", "실수", "고집", "윗사람", "선배", "조언", "하는 만큼"]
# 총운 첫 요소가 어느 분야 이야기인지 → 그 분야의 보통 문단은 '평온' 변형을 피한다
KEY_DOMAIN = {"month지 충": "일", "month지 형": "일", "month지 육합": "일",
              "day지 충": "애정·관계", "day지 형": "애정·관계", "일간 천간충": "애정·관계", "일간 천간극": "일",
              "year지 충": "애정·관계", "year지 형": "애정·관계"}
CALM = ["평소대로", "평소와 비슷", "평소와 같은", "특별한 신호", "조용한 하루", "편하게 지내는", "오래 알던", "고르게 가는"]
BODY_WORDS = re.compile("넘치|에너지|힘이 나|가볍|체력")
DAY = re.compile(B.DAY_END_RE)
BAN = re.compile(B.BANNED_RE)
MYEON = re.compile(r"면 됩니다")
MYEON_MAX = 3
GYEOL = re.compile(r"쪽|(?<!해)결(?!정|과|론|제|단|국|핍)")
CARD_STOP = {"오늘", "오늘은", "하루", "사람", "것", "때", "하나"}
_PARTICLE = re.compile(r"(으로|에서|에게|까지|부터|이나|이든|처럼|보다|만큼|은|는|이|가|을|를|의|에|도|과|와|로|만|엔|에는)$")
_VERBISH = re.compile(r"(세요|어요|아요|해요|니다|네요|지만|해서|하면|으면|면|날이에요|날이네요|날입니다)$")
# 도화: 원국 연지·일지의 삼합 국에 대한 목욕지. 오늘 일지가 거기 닿으면 애정 신호 '도화'.
_PEACH = {"申": "酉", "子": "酉", "辰": "酉", "寅": "卯", "午": "卯", "戌": "卯",
          "巳": "午", "酉": "午", "丑": "午", "亥": "子", "卯": "子", "未": "子"}


# ---------------------------------------------------------------------------
# 작은 도구
# ---------------------------------------------------------------------------
def sents(s: str) -> list[str]:
    return [x for x in re.split(r"(?<=[.!?])\s+", s.strip()) if x]


def ending(s: str) -> str:
    last = s.rstrip(". ").split(" ")[-1]
    for e in ("겁니다", "입니다", "습니다", "됩니다", "네요", "니다", "죠", "요"):
        if last.endswith(e):
            return e
    return last[-2:]


def _adjacent_ok(ss: list[str]) -> bool:
    return all(ending(a) != ending(b) or any((a + " " + b) in g for g in B.GOLD) for a, b in zip(ss, ss[1:]))


def n_day(par: str) -> int:
    return sum(1 for x in sents(par) if DAY.search(x))


def _today_ok(par: str) -> bool:
    return par.count("오늘") < 3


def _nouns_of(seg: str) -> set[str]:
    return {n for n in NOUNS if re.search(n + r"(?!끝|끔)", seg)}


def _noun_clash(segs: list[str]) -> str | None:
    seen: dict[str, str] = {}
    for seg in segs:
        for n in _nouns_of(seg):
            if n in seen and seen[n] is not seg:
                return n
            seen[n] = seg
    return None


def _first_word_clash(segs: list[str]) -> bool:
    fw = [s.split(" ")[0] for s in segs]
    return len(fw) != len(set(fw))


def _words(s: str) -> set[str]:
    return set(re.findall(r"[가-힣]{2,}", s))


def _similar(a: str, b: str) -> bool:
    return len(_words(a) & _words(b)) >= 3 or any(re.search(k, a) and re.search(k, b) for k in KEYWORDS)


def card_nouns(text: str | None) -> set[str]:
    """카드 분야 문장의 명사 후보: 2자 이상 한글 어절에서 조사·어미를 떼고 상투어를 뺀 것."""
    out = set()
    for w in re.findall(r"[가-힣]{2,}", text or ""):
        w = _PARTICLE.sub("", w)
        if len(w) >= 2 and w not in CARD_STOP and not _VERBISH.search(w):
            out.add(w)
    return out


def _fit_order(items, key: str, grade: str) -> list[str]:
    items = [x for x in items if B.grade_ok(x, grade)]
    return [x["text"] for x in items if key in x["fits"]] + [x["text"] for x in items if not x["fits"]]


def _order(n: int, recent, kind: str) -> list[int]:
    """0..n-1 을 회전 순서로: 최근 30일에 안 쓴 것(은행 순서) → 가장 오래전에 쓴 것부터."""
    last_pos = {}
    for pos, (e, k, i) in enumerate(recent):
        if e == USE_ELEMENT and k == kind:
            last_pos[i] = pos
    return sorted(range(n), key=lambda i: last_pos.get(i, -1))


# ---------------------------------------------------------------------------
# 입력 유도 — evaluate() 결과 → 조립 입력
# ---------------------------------------------------------------------------
def domain_tiers(deltas: dict, grade: str) -> dict[str, str]:
    """분야 결: 편차 + 등급 보정(좋음·아주 좋음 +3 / 주의·나쁨 −3) → ≥+6 좋음, ≤−6 주의, 그 밖 보통."""
    adj = 3 if grade in GOOD else (-3 if grade in ("주의", "나쁨") else 0)
    out = {}
    for dom, d in (("금전", "금전"), ("애정·관계", "사람"), ("일", "일"), ("건강", "건강")):
        t = deltas.get(d, 0) + adj
        out[dom] = "좋음" if t >= 6 else ("주의" if t <= -6 else "보통")
    return out


def love_signal(items, god: str | None, gender: str | None, natal_branches: tuple[str, ...], day_branch: str) -> str | None:
    """애정·관계 둘째 문장 신호. 일지 육합 > 일지 충 > 일진 십성(남 재성·여 관성) > 도화."""
    names = {ALIAS.get(n, n) for n, _ in items}
    if "day지 육합" in names:
        return "일지 육합"
    if "day지 충" in names:
        return "일지 충"
    if gender == "female" and god in ("direct_officer", "seven_killings"):
        return "관성"
    if gender != "female" and god in ("direct_wealth", "indirect_wealth"):
        return "재성"
    if any(_PEACH.get(b) == day_branch for b in natal_branches):
        return "도화"
    return None


def derive(core: MyeongriCoreResult, ev: dict, rx: dict, d: date, gender: str | None) -> dict:
    pillars = core.natal_facts.pillars
    dm = pillars["day"].stem
    gj = daily_score.day_ganji(d)
    god = get_ten_god(dm, gj[0]).value
    stage = get_twelve_stage(dm, gj[1]).value
    items = [(ALIAS.get(n, n), w) for n, w in ev["items"]]
    grade = ev["grade"]
    if ev["confidence"] == "약":
        key, top_sign, rest = "잔잔", None, []
    else:
        top = max(items, key=lambda x: (abs(x[1]), x[1] > 0))
        key, top_sign = top[0], ("길" if top[1] > 0 else "흉")
        rest = [x for x in items if x != top]
    if key not in B.LEAD:
        key = "잔잔"

    def pick(sign, min_w):
        c = [x for x in rest if (x[1] > 0) == (sign == "길") and abs(x[1]) >= min_w]
        if not c:
            return None
        c.sort(key=lambda x: (-abs(x[1]), TIE_PRIORITY.index(x[0]) if x[0] in TIE_PRIORITY else 99))
        return c[0]

    same = pick(top_sign, 4) if top_sign else None
    opp = pick("흉" if top_sign == "길" else "길", 6) if top_sign else None
    health = ev["domain"].get("건강", 0)
    body = health <= -4 or (stage in ("tomb", "death", "extinction") and health <= 0)
    tiers = domain_tiers(ev["domain"], grade)
    score = {"금전": ev["domain"].get("금전", 0), "애정·관계": ev["domain"].get("사람", 0),
             "일": ev["domain"].get("일", 0), "건강": health}
    cand = [x for x in tiers if tiers[x] != "보통"]
    standout: tuple = ()
    if cand:
        m = max(abs(score[x]) for x in cand)
        standout = tuple(x for x in cand if abs(score[x]) == m)
    natal_branches = tuple(pillars[p].branch for p in ("year", "day") if pillars.get(p))
    love = love_signal(items, god, gender, natal_branches, gj[1])
    card_ev = rx.get("evidence_text") or ""
    note = rx.get("domain_note") or None
    card = {}
    if note:
        card[note["domain"].replace("사람", "애정·관계")] = card_nouns(note["text"])
    return dict(date=d, grade=grade, evidence=key, top_sign=top_sign, god=god, stage=stage,
                same=same, opp=opp, body_flag=body, domains=tiers, deltas=score, standout=standout, love=love,
                card_first_words=(card_ev.split(" ")[0],) if card_ev else (), card_nouns=card, items=items)


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------
def _build_general(day: dict, recent) -> tuple[str, int, dict, list]:
    grade, key = day["grade"], day["evidence"]
    uses = []
    order = _order(len(B.LEAD[key]), recent, f"lead:{key}")           # 안 쓴 것(은행 순서) → 오래전에 쓴 것
    used = {j for e, k, j in recent if e == USE_ELEMENT and k == f"lead:{key}"}
    lead_all = [(i, B.LEAD[key][i]) for i in order]
    lead_v = [(i, v) for i, v in lead_all if B.grade_ok(v, grade)] or lead_all
    fresh_v = [(i, v) for i, v in lead_v if i not in used] or lead_v
    lead_v = [(i, v) for i, v in fresh_v if B.TITLE[key][i]["text"].split(" ")[0] not in day["card_first_words"]] or fresh_v
    top = day["top_sign"]
    same_list = _fit_order(B.SECOND[("길" if day["same"][1] > 0 else "흉") + "_순접"], day["same"][0], grade) if day["same"] else [None]
    opp_list = _fit_order(B.SECOND[("길" if day["opp"][1] > 0 else "흉") + "_역접"], day["opp"][0], grade) if day["opp"] else [None]
    body_group = ("순접" if top == "흉" else "역접") if day["body_flag"] else None
    body_list = ([x["text"] for x in B.SECOND["몸"][body_group] if B.grade_ok(x, grade)] + [None]) if body_group else [None]
    use_att = (day["date"].year * 1000 + day["date"].timetuple().tm_yday) % 2 == 1
    att_all = B.ATTITUDE[grade]
    att_idx = [i for i in _order(len(att_all), recent, f"att:{grade}")
               if not (top == "흉" and re.search("평소 하던 대로|늘 하던 리듬", att_all[i]))]
    # 느슨하게 하는 단계: 0 그대로 → 1 역접 생략 허용 → 2 순접도 생략 허용 → 3 태도·advice 둘 다 후보
    for relax in range(4):
        opps = opp_list + ([None] if relax >= 1 and opp_list != [None] else [])
        sames = same_list + ([None] if relax >= 2 and same_list != [None] else [])
        for li, lead in lead_v:
            tails = [("ATTITUDE", i, att_all[i]) for i in att_idx] if use_att else [("advice", 0, lead["advice"])]
            if relax >= 3:
                tails = tails + ([("advice", 0, lead["advice"])] if use_att else [("ATTITUDE", i, att_all[i]) for i in att_idx])
            for sec in sames:
                for opp in opps:
                    for body in body_list:
                        for kind, ti, tail in tails:
                            segs = [lead["scene"]] + [x for x in (sec, opp, body) if x] + [tail]
                            par = " ".join(segs)
                            ss = sents(par)
                            if not _adjacent_ok(ss) or not _today_ok(par):
                                continue
                            if _noun_clash(segs) or _first_word_clash(segs[1:]):
                                continue
                            if "기운" in par and key != "day지 충":
                                continue
                            if n_day(par) > 2:           # scene 첫 문장 + 정오님 문장 1개까지
                                continue
                            uses.append((USE_ELEMENT, f"lead:{key}", li))
                            if kind == "ATTITUDE":
                                uses.append((USE_ELEMENT, f"att:{grade}", ti))
                            return par, li, dict(lead=li, same=sec, opp=opp, body=body, tail=kind, tail_i=ti, relax=relax), uses
    raise RuntimeError("총운 조립 실패 " + key)


def _build_domain(day: dict, dom: str, recent) -> tuple[str, dict, list]:
    g, grade = day["domains"][dom], day["grade"]
    standout = dom in day["standout"]
    love = day["love"] if dom == "애정·관계" else None
    cn = day["card_nouns"].get(dom, set())
    paras_all = B.DOMAIN[dom][g]
    order = _order(len(paras_all), recent, f"para:{dom}:{g}")
    paras = [(pi, paras_all[pi]) for pi in order if B.grade_ok(paras_all[pi], grade)]
    bad_keys = [day["evidence"]] + [x[0] for x in (day["same"], day["opp"]) if x and x[1] < 0]
    for pi, p in paras:
        ss = sents(p["text"])
        if any(k in p["text"] and k in day["_general"] for k in CROSS):
            continue
        if dom == "건강" and g == "보통" and day["_body_mentioned"] and any(c in p["text"] for c in ("비슷", "특별한 신호", "평소와 같은")):
            continue
        if g == "보통" and any(KEY_DOMAIN.get(k) == dom for k in bad_keys) and any(c in p["text"] for c in CALM):
            continue
        love_opts = [x["text"] for x in B.LOVE[love] if B.grade_ok(x, grade)] if love else [None]
        if standout and g != "보통":
            ex_all = B.DOMAIN_EXTRA[dom][g]
            extra_opts = [(i, ex_all[i]["text"]) for i in _order(len(ex_all), recent, f"extra:{dom}:{g}") if B.grade_ok(ex_all[i], grade)]
        else:
            extra_opts = [(None, None)]
        if g == "보통":
            gc = [c for c in B.GOD_COLOR[day["god"]][dom] if B.grade_ok(c, grade)]
            if day["_body_mentioned"]:
                gc = [c for c in gc if not BODY_WORDS.search(c["text"])]
            gc = [c for c in gc if set(c["topic"]) & set(p["topics"])]      # 주제가 겹칠 때만, 아니면 생략
            cols = [c["text"] for c in gc if c["tone"] == "neutral"] or [c["text"] for c in gc if c["tone"] == "warm"] or [None]
            if cols != [None]:
                cols = cols + [None]
        else:
            cols = [None]
        for lv in love_opts:
            for ei, ex in extra_opts:
                for col in cols:
                    seq = [ss[0]] + ([lv] if lv else []) + ss[1:] + ([ex] if ex else []) + ([col] if col else [])
                    par = " ".join(seq)
                    if not _adjacent_ok(seq) or not _today_ok(par):
                        continue
                    if n_day(par) > 1:                                      # 분야 문단 "~날" 말끝 ≤1
                        continue
                    if col and any(_similar(col, s) for s in ss):
                        continue
                    if lv and any(_similar(lv, s) for s in ss):
                        continue
                    if ex and any(_similar(ex, s) for s in ss):
                        continue
                    if any(k in par and k in day["_general"] for k in CROSS):
                        continue
                    if len(cn & card_nouns(par)) >= 2:                      # 카드 분야 문장과 명사 2개+ 겹침 금지
                        continue
                    if day["_myeon"] + len(MYEON.findall(par)) > MYEON_MAX:   # "~면 됩니다" 하루 예산
                        continue
                    day["_myeon"] += len(MYEON.findall(par))
                    uses = [(USE_ELEMENT, f"para:{dom}:{g}", pi)]
                    if ex:
                        uses.append((USE_ELEMENT, f"extra:{dom}:{g}", ei))
                    return par, dict(p=pi, love=lv, extra=ex, color=col), uses
    raise RuntimeError(f"{dom} 조립 실패")


def _check(title: str, general: str, sections: list[dict], closing: str | None, grade: str) -> None:
    body = " ".join([general] + [s["text"] for s in sections] + ([closing] if closing else []))
    flat = title + " " + body
    assert flat.count("기운") <= 1, "기운 2회+"
    assert len(GYEOL.findall(flat)) <= 2, "쪽/결 3회+"
    assert n_day(body) <= 6, "본문 '~날' 말끝 7회+"
    assert not BAN.search(body), "금지 어휘 " + str(BAN.findall(body))
    assert flat.count("법이죠") <= 1, "법이죠 2회+"
    assert len(MYEON.findall(body)) <= MYEON_MAX, "'~면 됩니다' 4회+"
    if grade in GOOD:
        hit = [w for w in B.LUKEWARM if w in flat]
        assert not hit, f"좋음 등급에 미지근 관용구 {hit}"


def build_story(core: MyeongriCoreResult, evaluation: dict, rx: dict, account_key: str, d: date,
                gender: str | None, recent=()) -> dict:
    """하루치 이야기. rx 는 daily_rx.select_for_day 의 (부분) 결과(evidence_text·domain_note), recent 는 30일 이력.

    돌려주는 것: title · overall · sections[{key,title,text}] · closing(None 가능) · tiers · picks · uses(이력용) · version.
    account_key 는 이력 복원의 열쇠로만 쓰인다(문장 선택은 이력과 날짜로 정해진다).
    """
    recent = list(recent)
    day = derive(core, evaluation, rx, d, gender)
    general, li, ginfo, uses = _build_general(day, recent)
    title = B.TITLE[day["evidence"]][li]["text"]
    scene = B.LEAD[day["evidence"]][li]["scene"]
    day["_body_mentioned"] = bool(ginfo["body"]) or ("몸" in scene) or ("지치" in scene) or ("피곤" in scene)
    day["_general"] = general
    day["_myeon"] = len(MYEON.findall(general))
    sections, picks = [], {"general": dict(title=title, **ginfo)}
    for key, dom in SECTION_ORDER:
        text, info, u = _build_domain(day, dom, recent)
        sections.append({"key": key, "title": dom, "text": text})
        picks[dom] = info
        uses.extend(u)
    closing = None
    if day["grade"] != "보통":
        body_so_far = general + " " + " ".join(s["text"] for s in sections)
        closes = B.CLOSE[day["grade"]]
        for ci in _order(len(closes), recent, f"close:{day['grade']}"):
            c = closes[ci]
            if "법이죠" in c and "법이죠" in body_so_far:
                continue
            if day["_myeon"] + len(MYEON.findall(c)) > MYEON_MAX:
                continue
            closing = c
            uses.append((USE_ELEMENT, f"close:{day['grade']}", ci))
            break
    _check(title, general, sections, closing, day["grade"])
    return {
        "title": title, "overall": general, "sections": sections, "closing": closing,
        "grade": day["grade"], "tiers": day["domains"], "standout": list(day["standout"]), "love": day["love"],
        "evidence_key": day["evidence"], "god": day["god"], "picks": picks, "uses": uses,
        "version": STORY_VERSION,
    }


def story_payload(base: dict | None, story: dict) -> dict:
    """build_story 결과를 화면(index.html renderTodayStory)이 읽는 story 꼴로 합친다. 예전 키(headline·body·sections[].body)는 유지."""
    out = dict(base or {})
    out.update(
        headline=story["title"], title=story["title"],
        body=story["overall"], overall=story["overall"],
        char_count=len(story["overall"]), sentence_count=len(sents(story["overall"])),
        sections=[{"key": s["key"], "title": s["title"], "body": s["text"], "text": s["text"]} for s in story["sections"]],
        closing=story["closing"], tiers=story["tiers"], standout=story["standout"],
        story_version=story["version"], section_version=story["version"],
    )
    return out
