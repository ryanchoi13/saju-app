"""Plain Korean rendering of shared overall subjects; no new saju judgments.

달하 마스터 규격으로 다시 쓴 판. 공개 API(render_overall, subjects_html)와 반환 모양은 그대로다.

- 문구 은행(BASE · SPECIAL · LIFETIME)은 따뜻한 에디터 톤(~합니다 / ~해요 / ~해 보세요 / ~인 법이죠)으로 새로 썼다.
- daily_scenarios · daily_scene_context 의 문구는 이 파일에서 고칠 수 없다. 그래서 두 겹의 안전장치를 둔다.
    1) 런타임 가드: 한 주제의 문구 어디에든 HR 금기어·의학 표현이 있으면 그 주제만 깨끗한 BASE 문구로 바꿔 낸다.
    2) audit_sources(): 위 두 모듈 안의 문구를 전수 검사해 걸리는 문자열을 돌려준다. (tests/test_real_engine_smoke.py 가 호출)
- 한 문장만 있는 본문에서 마침표가 겹치던 문제(".." )를 고쳤다.
"""
from html import escape
import logging

from app.engine.semantic.overall import DOMAINS
from app.engine.services.annual_copy import split_sentences
from app.engine.services.daily_copy import find_flagged
from app.engine.services.daily_scenarios import COPY, FAMILIES
from app.engine.services.daily_scene_context import JOIN_CONTEXT, CHANGE_CONTEXT, DAILY_ROLE_CONTEXT

logger = logging.getLogger(__name__)

FAMILY = {"relationships": "social", "money": "money", "work": "pace",
          "learning": "learning", "enjoyment": "expression", "self": "self"}
SHORT_LABEL = {**DOMAINS, "love": "애정·관계", "wellbeing": "생활 리듬", "work": "맡은 일",
               "learning": "배움", "enjoyment": "즐거움", "self": "내 기준", "money": "재물"}
# Title, opening, preparation(오전), practice(오후), reflection(저녁), action.
BASE = {
"love": ("마음을 전하는 나만의 속도", "소중한 사람과의 거리와 표현 방식을 천천히 살펴보기 좋은 하루입니다. 혼자 짐작하기보다 편안한 질문 하나로 마음을 확인해 보면 훨씬 가벼워져요. 답을 재촉하지 않는 여유가 관계를 오래 이어 주는 법이죠.", "전하고 싶은 마음을 한 줄로 적어 보세요.", "요즘 어떤 시간이 편한지 슬쩍 물어봐요.", "상대의 속도를 존중하며 하루를 마무리해요.", "소중한 사람에게 고마웠던 점을 구체적으로 전해 보세요."),
"relationships": ("가까울수록 필요한 배려", "사람과 함께할 때는 친숙함만큼 서로의 기대를 확인하는 일도 소중합니다. 부탁을 받거나 의견을 나눌 때 가능한 범위를 솔직하게 말해 두면 마음이 한결 편해져요.", "오늘 잡힌 약속을 한 번 더 확인해요.", "의견이 다르면 상대가 원하는 것부터 들어 보세요.", "고마운 사람에게 짧은 안부를 보내 보세요.", "함께 정할 일이 있다면 상대가 원하는 것도 먼저 물어보세요."),
"wellbeing": ("생활 리듬에 여유를 남겨 두세요", "할 일이 많을수록 식사와 쉬는 시간을 먼저 챙기는 편이 좋습니다. 피로가 느껴지는 날에는 계획을 더 채우기보다 감당할 수 있는 양으로 줄여 보세요. 그렇게 남긴 여유가 내일의 힘이 되는 법이죠.", "식사와 쉴 시간을 먼저 일정에 적어 둬요.", "오래 앉아 있었다면 자리를 바꿔 잠깐 쉬어요.", "늦은 약속보다 편안한 마무리를 골라 보세요.", "빽빽한 일정 하나를 줄여 편히 쉴 시간을 남겨 보세요."),
"money": ("작은 실속을 챙기는 선택", "돈의 크기보다 쓰고 모으는 방식에 마음을 두기 좋은 날입니다. 반복되는 지출과 구매 조건을 한 번 살펴보면 불필요한 부담을 덜 수 있어요.", "오늘 나갈 결제 내역을 확인해 봐요.", "살 때는 최종 금액과 필요한 이유를 함께 보세요.", "만족스러웠던 소비와 아쉬웠던 소비를 나눠 봐요.", "쓰지 않는 정기결제가 하나 있는지 확인해 보세요."),
"work": ("지킬 수 있는 약속이 믿음을 만듭니다", "맡은 일에서는 내가 해낼 수 있는 범위를 분명히 해 두는 것이 가장 든든합니다. 새로운 부탁이 오면 이미 약속한 시간과 남은 여력부터 헤아려 보세요. 무리하지 않는 선택이 오래가는 신뢰를 만드는 법이죠.", "이미 맡은 일과 약속을 한 번 훑어봐요.", "새 부탁에는 가능한 범위를 먼저 알려 주세요.", "마친 일은 알리고 남은 일의 순서를 정해요.", "부담스러운 부탁 하나에 가능한 범위나 다른 시간을 제안해 보세요."),
"learning": ("배운 것을 내 것으로 만드는 시간", "공부나 새로운 방법을 익힐 때는 많이 보는 것보다 이해한 만큼 직접 써 보는 일이 도움이 됩니다. 막히는 부분은 질문을 구체적으로 좁혀 보면 의외로 길이 보여요.", "알고 싶은 질문 하나를 적어 두세요.", "배운 방법을 작은 일에 바로 적용해 봐요.", "기억에 남은 내용을 내 말로 정리해 보세요.", "헷갈리는 개념 하나를 쉬운 예로 설명해 보세요."),
"enjoyment": ("작은 즐거움으로 채우는 하루", "잘 먹고 좋아하는 일을 즐기는 시간에도 마음을 두기 좋은 날입니다. 잘하려는 마음은 내려놓고 몰입하는 순간 자체를 누려 보세요. 그런 여유가 일상을 한결 따뜻하게 하는 법이죠.", "식사를 급히 넘기지 말고 한 끼를 챙겨요.", "손으로 만들거나 몸을 움직이는 취미를 잠깐 즐겨요.", "편히 쉬며 오늘 좋았던 순간을 떠올려 보세요.", "미뤄 둔 취미에 짧게라도 시간을 내어 보세요."),
"self": ("내 기준을 또렷하게 세우는 선택", "남의 기대에 맞추는 일과 내가 원하는 일을 구분해 보기 좋은 날입니다. 함께 고르는 자리에서도 편안하게 내 생각을 남겨 보세요. 작은 표현이 쌓여 나다운 기준이 되는 법이죠.", "꼭 지키고 싶은 것을 하나만 정해 봐요.", "부탁을 받으면 가능한 범위부터 알려 주세요.", "마음에 걸린 선택은 혼자 정리할 시간을 가져요.", "원치 않는 부탁에는 짧고 분명하게 마음을 전해 보세요."),
"change": ("바꾸기 전에 조건부터 살펴봐요", "이동이나 생활 환경을 바꿀 계획이 있다면 편리함과 부담을 함께 살펴보기 좋습니다. 정해 둔 계획도 실제 조건에 맞춰 얼마든지 조정할 수 있어요.", "이동 시간과 챙길 것을 확인해요.", "예약을 바꾸기 전에 변경 조건을 읽어 보세요.", "새로 정한 내용을 함께할 사람에게 알려요.", "바꿀 계획 하나의 시간과 비용을 확인해 보세요."),
"balance": ("지금 우선할 것을 살피는 시간", "여러 선택이 겹칠 때는 가장 신경 쓰이는 것부터 차분히 살펴보면 됩니다. 중요한 약속과 나를 위한 시간을 함께 남겨 두면 하루가 훨씬 고르게 흘러가요.", "오늘 감당할 수 있는 범위를 정해요.", "중요한 선택은 필요한 정보를 확인해 보세요.", "편히 쉴 시간을 꼭 남겨 둬요.", "가장 신경 쓰이는 일 하나에서 필요한 정보를 확인해 보세요."),
}
SPECIAL = {
("love", "join"): ("마음을 나눌 시간을 마련해요", "마음에 둔 사람이 있다면 부담 없는 대화나 만남으로 관심을 표현해도 좋습니다. 이미 가까운 사이라면 익숙한 용건 너머로 서로의 기분과 취향을 나눠 보세요.", "상대에게 궁금한 것을 하나 떠올려요.", "내 이야기만큼 상대의 마음도 물어보세요.", "함께 좋았던 순간을 짧게 전해 봐요.", "마음을 전하고 싶은 사람에게 편안한 대화 시간을 제안해 보세요."),
("love", "change"): ("마음이 다를 땐 추측보다 대화", "소중한 사람과 기대가 다르다면 서둘러 결론을 내리기보다 무엇이 다른지 물어보세요. 답장 속도나 한 번의 반응만으로 마음을 단정할 필요는 없어요.", "마음에 걸린 것이 무엇인지 정리해 봐요.", "불편했던 상황과 바라는 점을 차분히 말해 보세요.", "이야기가 남았다면 따로 시간을 잡아요.", "혼자 짐작했던 기대 하나를 가까운 사람에게 물어보세요."),
("love", "mixed"): ("가까운 사이에도 서로의 속도가 있어요", "함께하는 시간과 각자의 시간을 어떻게 나눌지 살펴보세요. 애정의 크기를 약속 횟수로 재기보다 서로 편안한 방식을 찾는 일이 더 중요합니다.", "함께 보내고 싶은 시간을 가늠해 봐요.", "연락과 만남에서 편한 방식을 이야기해 보세요.", "답을 서두르지 않아도 되는 여유를 남겨요.", "편안한 연락과 만남의 방식을 가까운 사람과 이야기해 보세요."),
}

LIFETIME = {
    "love": ("소중한 관계를 오래 이어가는 힘", "가까운 관계에서는 서로 기대하는 표현과 생활 방식을 알아 가는 과정에 마음을 두세요. 호감만큼 대화의 한결같음과 각자의 공간을 존중하는 태도가 오래가는 법이죠."),
    "relationships": ("함께하는 사람들과 믿음을 쌓는 방식", "사람과 함께하는 과정에서는 친밀함과 역할의 경계를 함께 살펴보세요. 상황이 달라질 때 서로의 기대를 다시 확인하는 습관이 관계를 이어 주는 힘이 됩니다."),
    "wellbeing": ("오래 유지할 수 있는 생활 리듬", "활동과 쉼을 번갈아 이어 갈 수 있는 생활 방식을 찾아보세요. 바쁜 시기에도 식사와 휴식의 기본 틀을 남기고, 실제 컨디션에 맞춰 계획을 조절하는 일이 중요합니다."),
    "money": ("생활을 지탱하는 돈 관리의 기준", "돈이 들어올 기회와 감당할 부담을 함께 헤아려 보세요. 구매나 주거처럼 오래 영향을 주는 선택에서는 전체 비용과 유지할 여력을 확인하는 습관이 든든합니다."),
    "work": ("내 역할을 정하고 믿음을 쌓는 과정", "일에서 무엇을 맡고 어떤 방식으로 이어 갈지 나만의 기준을 세워 보세요. 맡는 일이 커질수록 배움과 협력의 여력도 함께 마련해 두는 것이 중요해요."),
    "learning": ("배움을 삶의 힘으로 바꾸는 방식", "공부나 새로운 기술을 익히는 과정에서 내게 맞는 방법을 찾아보세요. 아는 것을 늘리는 데서 한 걸음 더 나아가 직접 써 보고 질문하는 습관이 도움이 됩니다."),
    "enjoyment": ("즐거움과 표현으로 삶을 채우는 방식", "만들고 즐기고 나누는 경험을 생활 속에 남겨 보세요. 취미와 돌봄에서 얻는 만족도 삶의 소중한 한 부분이라는 마음이 도움이 됩니다."),
    "self": ("내 선택의 기준을 만들어 가는 과정", "주변의 기대 속에서도 내가 원하는 삶의 방식을 구분해 보세요. 함께 맞춰 갈 부분과 스스로 지킬 부분을 알아 가는 시간이 중요합니다."),
    "change": ("생활의 변화를 준비하는 방식", "환경을 바꾸는 선택 앞에서는 새로운 가능성과 지켜야 할 기반을 함께 살펴보세요. 이동이나 주거 계획이 있다면 비용과 도움받을 곳까지 확인해 두면 든든해요."),
}


def _object_particle(word):
    last = word[-1:]
    return "을" if last and "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 else "를"


def _first_sentence(text):
    parts = split_sentences(text)
    return parts[0] if parts else text


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _strings(item)


def audit_sources() -> list[tuple[str, list[str], str]]:
    """daily_scenarios · daily_scene_context 의 문구 중 금기어·의학 표현이 든 것을 전부 돌려준다.

    반환: [(출처 이름, 걸린 낱말들, 문자열 앞부분)]. 비어 있어야 정상이다.
    """
    found = []
    for name, table in (("COPY", COPY), ("JOIN_CONTEXT", JOIN_CONTEXT),
                        ("CHANGE_CONTEXT", CHANGE_CONTEXT), ("DAILY_ROLE_CONTEXT", DAILY_ROLE_CONTEXT)):
        for text in _strings(table):
            hits = find_flagged(text)
            if hits:
                found.append((name, hits, text[:40]))
    return found


def _copy(candidate, selection):
    domain, mode = candidate["domain"], candidate.get("mode", "base")
    if selection["scope"] == "daily":
        role_key = (domain, mode, selection.get("focal_god"))
        if role_key in DAILY_ROLE_CONTEXT:
            return DAILY_ROLE_CONTEXT[role_key]
    if (domain, mode) in SPECIAL:
        return SPECIAL[domain, mode]
    family = FAMILY.get(domain)
    context = JOIN_CONTEXT if mode == "join" else CHANGE_CONTEXT if mode == "change" else {}
    key = (family, FAMILIES.get(selection.get("focal_god")))
    if key in context:
        return context[key]
    if (family, mode) in COPY:
        return COPY[family, mode]
    return BASE.get(domain, BASE["balance"])


def _safe_copy(candidate, selection):
    """_copy 결과에 금기어·의학 표현이 있으면 그 주제만 깨끗한 BASE 문구로 바꾼다."""
    chosen = _copy(candidate, selection)
    hits = [h for text in chosen for h in find_flagged(text)]
    if not hits:
        return chosen
    logger.warning("overall_narrative 금기 문구 대체 domain=%s mode=%s terms=%s",
                   candidate["domain"], candidate.get("mode", "base"), sorted(set(hits)))
    return BASE.get(candidate["domain"], BASE["balance"])


def _period_text(text, scope):
    if scope == "daily":
        return text
    label = {"annual": "올해", "monthly": "이번 달", "luck_cycle": "이 시기", "natal": "일상"}[scope]
    return text.replace("오늘", label).replace("내일을 위해", "다음 일정을 위해")


def render_overall(selection):
    scope = selection["scope"]
    selected = selection["selected"]
    pieces = []
    for candidate in selected:
        title, body, morning, afternoon, evening, action = (
            _period_text(t, scope) for t in _safe_copy(candidate, selection))
        if scope == "natal" and candidate["domain"] in LIFETIME:
            title, body = LIFETIME[candidate["domain"]]
        pieces.append(dict(domain=candidate["domain"], label=candidate["label"],
            title=title, body=body, action=action,
            time_flow=dict(morning=morning, afternoon=afternoon, evening=evening),
            primary=candidate["domain"] in selection["primary_domains"]))
    if not pieces:
        title, body, morning, afternoon, evening, action = BASE["balance"]
        return dict(title=title, advice=body, unified_advice=action,
            time_flow=dict(morning=morning, afternoon=afternoon, evening=evening), subjects=[])
    primary = [p for p in pieces if p["primary"]]
    title = primary[0]["title"]
    if len(primary) > 1:
        labels = [SHORT_LABEL[p["domain"]] for p in primary]
        label_text = " · ".join(labels)
        title = label_text + _object_particle(label_text) + " 함께 살피는 시간"
    paragraphs = []
    for i, p in enumerate(pieces):
        # Main reading gets its full explanation. Other independent subjects get
        # a concise practical point; important ties are never silently omitted.
        paragraphs.append(p["body"] if p["primary"] else _first_sentence(p["body"]))
    time_flow = dict(pieces[0]["time_flow"])
    if len(pieces) > 1:
        time_flow["afternoon"] = pieces[1]["time_flow"]["afternoon"]
    if len(pieces) > 2:
        time_flow["evening"] = pieces[2]["time_flow"]["evening"]
    return dict(title=title, advice=" ".join(paragraphs),
        unified_advice=" ".join(p["action"] for p in primary),
        time_flow=time_flow, subjects=pieces)


def subjects_html(narrative):
    return "".join(
        '<div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;">'
        f'<h5 style="font-size:14px;color:#334155;margin:0 0 5px;">{escape(p["label"])}'
        f'{" · 먼저 살필 내용" if p["primary"] else ""}</h5>'
        f'<p style="font-size:13px;color:#475569;margin:0;line-height:1.75;">{escape(p["body"])} {escape(p["action"])}</p></div>'
        for p in narrative["subjects"])
