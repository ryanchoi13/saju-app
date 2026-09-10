"""Plain Korean rendering of shared overall subjects; no new saju judgments."""
from html import escape

from app.engine.semantic.overall import DOMAINS
from app.engine.services.daily_scenarios import COPY, FAMILIES
from app.engine.services.daily_scene_context import JOIN_CONTEXT, CHANGE_CONTEXT

FAMILY = {"relationships": "social", "money": "money", "work": "pace",
          "learning": "learning", "enjoyment": "expression", "self": "self"}
SHORT_LABEL = {**DOMAINS, "love": "애정·관계", "wellbeing": "생활 리듬", "work": "역할과 책임",
               "learning": "배움", "enjoyment": "즐거움", "self": "내 기준", "money": "재물"}
# Title, opening, preparation, practice, reflection, action.
BASE = {
"love": ("가까운 사람에게 마음을 전하는 방식", "마음에 둔 사람이 있거나 소중한 관계를 이어가고 있다면 서로 원하는 거리와 표현 방식을 살펴보세요. 혼자 짐작하기보다 편안한 질문으로 마음을 확인하는 과정이 중요합니다.", "전하고 싶은 마음을 짧게 정리하세요.", "상대에게 요즘 어떤 시간이 편한지 물어보세요.", "답을 재촉하기보다 서로의 속도를 존중하세요.", "소중한 사람에게 고마웠던 점을 구체적으로 전하세요."),
"relationships": ("가까울수록 필요한 배려", "사람과 함께할 때는 친숙함만큼 서로의 기대를 확인하는 과정도 중요합니다. 부탁을 받거나 의견을 나눌 때 가능한 범위를 분명히 해두세요.", "함께 잡은 약속을 확인하세요.", "의견이 다르면 상대가 원하는 것부터 들으세요.", "고마운 사람에게 짧게 연락해도 좋습니다.", "함께 정할 일이 있다면 상대가 원하는 것도 물어보세요."),
"wellbeing": ("생활 리듬에 여유를 남기세요", "해야 할 일이 많을수록 식사와 쉬는 시간을 함께 챙기는 데 초점을 두세요. 피로가 느껴진다면 계획을 채우는 것보다 감당할 수 있는 양을 조절하는 편이 낫습니다.", "식사와 쉴 시간을 먼저 남겨두세요.", "오래 집중했다면 잠깐 자리를 바꿔 쉬세요.", "늦은 약속보다 편안하게 마무리할 시간을 확보하세요.", "빽빽한 일정 하나를 줄여 편히 쉴 시간을 남기세요."),
"money": ("작은 실속을 챙기는 선택", "돈의 규모보다 관리 방식에 초점을 두세요. 반복되는 소비와 구매·계약의 조건을 살피면 불필요한 부담을 줄이는 데 도움이 됩니다.", "예정된 결제 내역을 챙기세요.", "구매할 때 최종 금액과 필요한 이유를 함께 보세요.", "만족스러웠던 소비와 아쉬웠던 소비를 구분하세요.", "쓰지 않는 정기결제 하나가 있는지 확인하세요."),
"work": ("지킬 수 있는 약속이 신뢰를 만듭니다", "일이나 함께 맡은 역할에서는 책임질 범위를 분명히 하는 것이 중요합니다. 새로운 요청이 들어오면 이미 약속한 시간과 감당할 여력을 먼저 살펴보세요.", "이미 맡은 역할과 약속을 확인하세요.", "추가 요청에는 가능한 범위를 알려주세요.", "마친 일은 알리고 남은 일의 순서를 정하세요.", "부담되는 요청 하나에 가능한 범위나 다른 시간을 제안하세요."),
"learning": ("배운 것을 내 것으로 만드는 시간", "공부나 새로운 방법을 익힐 때는 많이 보는 것보다 이해한 부분을 직접 써보는 데 초점을 두세요. 막힌 부분이 있다면 질문을 구체적으로 좁히는 것이 도움이 됩니다.", "알고 싶은 질문 하나를 적으세요.", "배운 방법을 작은 활동에 적용하세요.", "기억에 남은 내용을 내 말로 정리하세요.", "헷갈리는 개념 하나를 쉬운 예로 설명해 보세요."),
"enjoyment": ("작은 즐거움으로 일상을 채우기", "잘 먹고 취미를 즐기는 시간에도 마음을 두세요. 완성도나 성과를 따지지 않고 좋아하는 활동에 몰입하는 여유가 중요합니다.", "식사를 급하게 넘기지 말고 한 끼를 챙기세요.", "손으로 만들거나 몸을 움직이는 취미를 잠깐 즐기세요.", "편안하게 쉬며 좋았던 순간을 떠올리세요.", "미뤄둔 취미에 짧게라도 시간을 써보세요."),
"self": ("내 기준을 분명히 하는 선택", "남의 기대에 맞추는 것과 내가 원하는 것을 구분하세요. 함께 고르는 자리에서도 편안하게 내 의견을 남기는 태도가 중요합니다.", "꼭 지키고 싶은 것을 하나 정하세요.", "부탁을 받으면 가능한 범위부터 알리세요.", "마음에 걸린 선택은 혼자 정리할 시간을 가지세요.", "원치 않는 부탁에는 짧고 분명하게 의사를 전하세요."),
"change": ("계획을 바꾸기 전에 조건부터 확인", "이동이나 생활 환경을 바꿀 계획이 있다면 편리함과 부담을 함께 살펴보세요. 정해둔 계획도 실제 조건에 맞춰 조정할 수 있습니다.", "이동 시간과 준비할 것을 확인하세요.", "예약이나 약속을 바꾸기 전에 변경 조건을 읽으세요.", "새로 정한 내용을 함께할 사람에게 전하세요.", "변경할 계획 하나의 시간과 비용을 확인하세요."),
"balance": ("내 생활에서 우선할 것을 살피는 시간", "여러 선택이 겹친다면 지금 신경 쓰이는 것부터 차분히 살펴보세요. 중요한 약속과 나를 위한 시간을 함께 남겨두면 좋습니다.", "감당할 수 있는 범위를 정하세요.", "중요한 선택은 필요한 정보를 확인하세요.", "편안하게 쉴 시간을 남겨두세요.", "지금 가장 신경 쓰이는 일 하나에서 필요한 정보를 확인하세요."),
}
SPECIAL = {
("love", "join"): ("마음을 나눌 시간을 마련하세요", "마음에 둔 사람이 있다면 부담 없는 대화나 만남으로 관심을 표현해도 좋습니다. 이미 가까운 사이에서는 익숙한 용건 외에 서로의 기분과 취향을 나누는 시간에 마음을 두세요.", "상대에게 궁금한 것을 하나 떠올리세요.", "대화할 때 내 이야기만큼 상대의 마음도 물어보세요.", "함께 좋았던 순간을 짧게 전해도 좋습니다.", "마음을 전하고 싶은 사람에게 편안한 대화 시간을 제안하세요."),
("love", "change"): ("마음이 다를 때는 추측보다 대화", "소중한 사람과 기대가 다르다면 서둘러 결론 내리기보다 무엇이 다른지 물어보세요. 답장 속도나 한 번의 반응만으로 마음을 단정할 필요는 없습니다.", "마음에 걸린 것이 무엇인지 정리하세요.", "불편했던 상황과 원하는 것을 차분히 말하세요.", "감정이 남아 있다면 대화를 이어갈 시간을 따로 잡으세요.", "가까운 사람에게 혼자 짐작했던 기대 하나를 물어보세요."),
("love", "mixed"): ("가까운 사이에도 서로의 속도가 있습니다", "함께하는 시간과 각자의 시간을 어떻게 나눌지 살펴보세요. 호감이나 애정의 크기를 약속 횟수로 재기보다 서로 편안한 방식을 찾는 것이 중요합니다.", "함께 보내고 싶은 시간을 가늠하세요.", "연락과 만남에서 편한 방식을 이야기하세요.", "답을 서두르지 않아도 되는 여유를 남기세요.", "가까운 사람과 편안한 연락·만남의 방식을 이야기하세요."),
}

LIFETIME = {
    "love": ("소중한 관계를 오래 이어가는 힘", "가까운 관계에서는 서로 기대하는 표현과 생활 방식을 알아가는 과정에 마음을 두세요. 호감만큼 대화의 일관성과 각자의 공간을 존중하는 태도도 중요합니다."),
    "relationships": ("함께하는 사람들과 신뢰를 쌓는 방식", "사람과 함께하는 과정에서는 친밀함과 역할의 경계를 함께 살펴보세요. 상황이 달라질 때 서로의 기대를 다시 확인하는 습관이 관계를 이어가는 데 도움이 됩니다."),
    "wellbeing": ("오래 유지할 수 있는 생활 리듬", "활동과 회복을 번갈아 이어갈 수 있는 생활 방식을 살펴보세요. 바쁜 시기에도 식사와 휴식의 기본 틀을 남기고 실제 컨디션에 맞춰 계획을 조정하는 것이 중요합니다."),
    "money": ("생활을 지탱하는 돈 관리의 기준", "돈을 얻을 기회와 감당할 부담을 함께 살펴보세요. 구매·투자·주거처럼 오래 영향을 주는 선택에서는 전체 비용과 유지할 여력을 확인하는 습관이 중요합니다."),
    "work": ("내 역할을 정하고 신뢰를 쌓는 과정", "진로나 일에서 무엇을 맡고 어떤 방식으로 이어갈지 기준을 세워보세요. 역할이 커지는 만큼 배움과 협력의 여력을 함께 마련하는 것이 중요합니다."),
    "learning": ("배움을 생활의 힘으로 바꾸는 방식", "학업과 새로운 기술을 익히는 과정에서 내게 맞는 방법을 찾아보세요. 아는 것을 늘리는 데서 한 걸음 더 나아가 직접 적용하고 질문하는 습관이 도움이 됩니다."),
    "enjoyment": ("즐거움과 표현으로 삶을 채우는 방식", "만들고 즐기고 나누는 경험을 생활에 남겨보세요. 취미와 돌봄에서 느끼는 만족도 삶의 중요한 부분으로 여기는 태도가 도움이 됩니다."),
    "self": ("내 선택의 기준을 만들어가는 과정", "주변의 기대 속에서도 내가 원하는 삶의 방식을 구분해보세요. 함께 맞춰갈 부분과 스스로 지킬 부분을 알아가는 과정이 중요합니다."),
    "change": ("생활의 변화를 준비하는 방식", "환경을 바꿀 선택에서는 새로운 가능성과 유지할 기반을 함께 살펴보세요. 이동이나 주거 계획이 있다면 비용과 도움받을 자원까지 확인하는 태도가 중요합니다."),
}


def _object_particle(word):
    last = word[-1:]
    return "을" if last and "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 else "를"


def _copy(candidate, selection):
    domain, mode = candidate["domain"], candidate.get("mode", "base")
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
            _period_text(t, scope) for t in _copy(candidate, selection))
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
        paragraphs.append(p["body"] if p["primary"] else p["body"].split(". ")[0] + ".")
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
