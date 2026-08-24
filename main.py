# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import random
import hashlib

from saju_engine import calculate_saju_pillars

app = FastAPI(title="운세의 신 API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AnalyzeRequest(BaseModel):
    name: str
    year: int
    month: int
    day: int
    calendar_type: Optional[str] = "solar"
    sijin_index: Optional[int] = None
    is_unknown_time: bool = False

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 모바일 캐시 방지를 위해 버전 타임스탬프 헤더 추가
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/manifest.json")
async def get_manifest():
    return FileResponse(os.path.join(BASE_DIR, "manifest.json"), media_type="application/json")

@app.get("/sw.js")
async def get_sw():
    return FileResponse(os.path.join(BASE_DIR, "sw.js"), media_type="application/javascript")

@app.get("/manifest-talisman.json")
async def get_talisman_manifest():
    return {
        "name": "오늘의 맞춤 부적",
        "short_name": "수호부적",
        "start_url": "/?open=talisman",
        "display": "standalone",
        "background_color": "#18181B",
        "theme_color": "#D97706",
        "icons": [
            {
                "src": "https://cdn-icons-png.flaticon.com/512/3655/3655581.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }

# 12대 전통 비급 부적
TALISMAN_DECK = [
    {
        "id": "talisman_wealth",
        "title": "재물만복부 (財物萬福符)",
        "desc": "금고의 문을 열고 새는 돈을 막아주는 황금 기운",
        "chinese": "勅令 財運大吉 聚財如山",
        "power": "재물통로 개운 · 자산 증식"
    },
    {
        "id": "talisman_safe",
        "title": "금고수호부 (金庫守護符)",
        "desc": "갑작스러운 지출과 손재수를 막고 재산을 단단히 지키는 기운",
        "chinese": "勅令 寶庫固封 漏財永息",
        "power": "손재수 방어 · 자산 보전"
    },
    {
        "id": "talisman_biz",
        "title": "사업대성부 (事業大成符)",
        "desc": "손님이 구름처럼 몰려들고 계약이 성사되는 번창의 기운",
        "chinese": "勅令 商運大吉 千客萬來",
        "power": "매출 폭발 · 계약 성사"
    },
    {
        "id": "talisman_love",
        "title": "인연화합부 (因緣和合符)",
        "desc": "어긋난 관계를 봉합하고 진실된 짝과의 애정을 두텁게 하는 기운",
        "chinese": "勅令 緣分結實 夫婦和合",
        "power": "애정 돈독 · 관계 회복"
    },
    {
        "id": "talisman_dohwa",
        "title": "도화매혹부 (桃花魅惑符)",
        "desc": "나의 숨겨진 매력을 발산하여 대중과 이성의 호감을 끄는 기운",
        "chinese": "勅令 桃花盛開 萬人愛慕",
        "power": "인기 상승 · 이성 호감"
    },
    {
        "id": "talisman_wish",
        "title": "소원성취부 (所願成就符)",
        "desc": "오랫동안 가슴에 품어온 간절한 뜻이 현실로 결실을 맺는 기운",
        "chinese": "勅令 心想事成 萬事如意",
        "power": "소원 성취 · 만사 대길"
    },
    {
        "id": "talisman_noble",
        "title": "귀인상조부 (貴人相助符)",
        "desc": "막힌 곳을 뚫어줄 은인과 귀인이 사방에서 돕는 영험한 기운",
        "chinese": "勅令 貴人助我 萬事亨通",
        "power": "인맥 조력 · 위기 돌파"
    },
    {
        "id": "talisman_honor",
        "title": "관운승진부 (官運昇進符)",
        "desc": "명예를 드높이고 직장 및 사회에서 권한을 확대하는 기운",
        "chinese": "勅令 官運昌盛 出世登科",
        "power": "승진 합격 · 명예 상승"
    },
    {
        "id": "talisman_pass",
        "title": "장원급제부 (壯元及第符)",
        "desc": "머리를 맑게 하여 시험과 면접, 오디션에서 최고 점수를 받는 기운",
        "chinese": "勅令 文星照臨 必得高第",
        "power": "집중력 강화 · 시험 합격"
    },
    {
        "id": "talisman_protect",
        "title": "벽사소재부 (辟邪消災符)",
        "desc": "탁한 액운과 잡귀, 구설수를 칼날처럼 베어내는 수호의 기운",
        "chinese": "勅令 邪氣退散 福德來臨",
        "power": "액막이 소멸 · 악살 방어"
    },
    {
        "id": "talisman_health",
        "title": "칠성무병부 (七星無病符)",
        "desc": "북두칠성의 기운으로 오장육부의 피로를 씻고 활력을 채우는 기운",
        "chinese": "勅令 身心康健 延年益壽",
        "power": "심신 정화 · 면역 증진"
    },
    {
        "id": "talisman_peace",
        "title": "심신안정부 (心神安定符)",
        "desc": "불안과 불면, 잡념을 가라앉히고 평온한 평정심을 선사하는 기운",
        "chinese": "勅令 心神淸明 安祥和平",
        "power": "멘탈 케어 · 불면 해소"
    }
]

DAILY_CURATIONS = [
    {
        "title": "금빛 기운이 서서히 솟아나는 도약의 하루",
        "score_base": 92,
        "advice": "묵혀두었던 계획이나 관계에서 긍정적인 신호가 찾아옵니다. 주도적으로 움직이세요.",
        "lucky_color": "포레스트 그린 / 골드",
        "lucky_number": "7, 8",
        "lucky_direction": "동남쪽",
        "fashion_style": "단정하고 깔끔한 세미 캐주얼",
        "lucky_item": "원목 또는 메탈 소품",
        "recommended_menu": "속이 편안한 영양 한식",
        "lucky_person": "차분하고 책임감 있는 지인",
        "today_gaewoon": "오전 중 따뜻한 차 한 잔을 마시며 핵심 목표 3가지를 메모하세요."
    },
    {
        "title": "귀인의 조력으로 매듭이 풀리는 순풍의 하루",
        "score_base": 95,
        "advice": "뜻밖의 제안이나 기쁜 소식이 전해집니다. 주변 사람과의 대화에 귀를 기울이세요.",
        "lucky_color": "아이보리 / 스카이 블루",
        "lucky_number": "1, 6",
        "lucky_direction": "정북쪽",
        "fashion_style": "밝은 톤의 셔츠 또는 니트",
        "lucky_item": "가죽 지갑 또는 다이어리",
        "recommended_menu": "신선한 샐러드와 담백한 단백질 식단",
        "lucky_person": "오랜만에 연락 온 선배 또는 동료",
        "today_gaewoon": "출근길 또는 외출 시 햇볕을 5분간 쬐며 심호흡을 하세요."
    },
    {
        "title": "내실을 다지고 재물 씨앗을 심는 알찬 하루",
        "score_base": 88,
        "advice": "급하게 서두르기보다 점검과 정리에 집중할 때 더 큰 실익이 발생하는 날입니다.",
        "lucky_color": "네이비 / 딥 브라운",
        "lucky_number": "3, 5",
        "lucky_direction": "남서쪽",
        "fashion_style": "신뢰감을 주는 모노톤 셋업",
        "lucky_item": "손목시계 또는 펜",
        "recommended_menu": "따끈한 국물 요리나 솥밥",
        "lucky_person": "묵묵히 자기 일을 해내는 실무자",
        "today_gaewoon": "책상이나 지갑 속 영수증을 깔끔하게 정리해 금전 통로를 정돈하세요."
    },
    {
        "title": "빛나는 영감과 아이디어가 샘솟는 창조의 하루",
        "score_base": 94,
        "advice": "기존의 틀을 깨는 새로운 시도가 높은 평가를 받습니다. 아이디어를 주저 말고 표현하세요.",
        "lucky_color": "버건디 / 크림 베이지",
        "lucky_number": "2, 9",
        "lucky_direction": "정동쪽",
        "fashion_style": "포인트 컬러가 들어간 스카프나 악세서리",
        "lucky_item": "노트북 파우치 또는 향수",
        "recommended_menu": "풍미가 깊은 이탈리안 파스타 또는 커피",
        "lucky_person": "감각이 뛰어나고 솔직한 후배",
        "today_gaewoon": "새로운 음악을 들으며 평소와 다른 산책로를 걸어보세요."
    }
]

TAROT_DECK = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작, 순수한 열정, 무한한 가능성", "overview": "얽매이지 않는 자유로운 발걸음으로 미지의 새로운 여정을 시작할 최적의 타이밍입니다.", "action": "실패를 두려워하지 말고 호기심과 가벼운 마음으로 첫 발을 내딛으세요.", "caution": "준비 없는 무모한 모험이나 디테일 부족을 경계해야 합니다."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조, 시작, 다재다능, 주도권", "overview": "원하는 것을 현실로 만들어낼 수 있는 능력과 자원이 이미 손안에 있습니다.", "action": "자신감을 가지고 준비해온 기획이나 대화를 먼저 리드하세요.", "caution": "겉모습에만 치중하지 말고 실질적인 내실을 챙겨야 합니다."},
    {"name": "II. THE HIGH PRIESTESS (여사제)", "keyword": "직관, 통찰력, 비밀, 정중동", "overview": "내면의 목소리와 직관이 극대화되는 날입니다. 깊이 있는 사색이 정답을 줍니다.", "action": "서두르지 말고 상황을 관찰하며 내면의 지혜를 믿으세요.", "caution": "차갑거나 배타적인 태도로 주변 사람에게 오해를 사지 않도록 하세요."},
    {"name": "III. THE EMPRESS (여황제)", "keyword": "풍요, 결실, 포용, 창의성", "overview": "물질적·정서적으로 풍요롭고 따뜻한 에너지가 가득 차오르는 결실의 카드입니다.", "action": "주변에 베풀고 스스로에게도 기분 좋은 휴식과 보상을 선물하세요.", "caution": "나태함이나 과도한 소비에 주의하세요."},
    {"name": "IV. THE EMPEROR (황제)", "keyword": "통솔력, 안정, 확고한 원칙, 성취", "overview": "자신의 영역을 확고하게 장악하고 리더십을 발휘하여 목표를 달성합니다.", "action": "원칙과 기준을 명확히 세우고 흔들림 없이 밀고 나가세요.", "caution": "고집이나 독단적인 태도로 파트너와 부딪히지 않도록 조율하세요."},
    {"name": "V. THE HIEROPHANT (교황)", "keyword": "신뢰, 조언, 멘토, 전통", "overview": "신뢰할 수 있는 멘토나 조력자의 가르침을 통해 올바른 방향을 찾습니다.", "action": "혼자 끙끙 앓기보다 경험자의 조언을 구하고 상식을 따르세요.", "caution": "지나친 보수성으로 새로운 기회를 놓치지 않도록 주의하세요."},
    {"name": "VI. THE LOVERS (연인)", "keyword": "조화, 올바른 선택, 유대감", "overview": "사람과의 관계에서 깊은 공감대가 형성되고 중요한 선택의 기로에서 좋은 답을 찾습니다.", "action": "마음이 이끄는 진솔한 결정을 내리고 파트너와 신뢰를 나누세요.", "caution": "우유부단하게 결정을 미루면 기회가 지나갈 수 있습니다."},
    {"name": "VII. THE CHARIOT (전차)", "keyword": "돌파, 승리, 강한 추진력", "overview": "장애물을 뚫고 목표를 향해 거침없이 질주하는 승리의 기운이 감돕니다.", "action": "목표에 집중하고 강한 집중력으로 오늘 안에 끝장을 보세요.", "caution": "과속이나 감정적 폭주로 주변을 다치게 하지 않도록 브레이크를 점검하세요."},
    {"name": "VIII. STRENGTH (힘)", "keyword": "부드러운 통제, 인내, 내면의 용기", "overview": "물리적인 힘이 아닌 따뜻한 포용력과 인내로 거친 상황을 길들입니다.", "action": "화내지 말고 부드러운 미소와 설득으로 상대를 내 편으로 만드세요.", "caution": "지나친 자기 억압으로 스트레스가 쌓이지 않도록 마인드 컨트롤하세요."},
    {"name": "IX. THE HERMIT (은둔자)", "keyword": "탐구, 진리, 고요한 성찰", "overview": "외부의 소음에서 벗어나 나만의 길을 밝히는 등불을 켜는 시간입니다.", "action": "조용히 생각을 정리하고 깊이 있는 연구나 공부에 몰입하세요.", "caution": "세상과의 소통을 완전히 단절하고 외골수로 빠지지 않도록 하세요."},
    {"name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)", "keyword": "전환점, 뜻밖의 행운, 필연적 기회", "overview": "정체되었던 흐름이 풀리고 새로운 기운이 상승 궤도에 진입합니다.", "action": "변화를 주저하지 말고 찾아온 제안이나 흐름을 긍정적으로 수용하세요.", "caution": "과거의 관성에 얽매이지 말고 새 판을 짤 타이밍입니다."},
    {"name": "XI. JUSTICE (정의)", "keyword": "공정함, 균형, 명확한 판단", "overview": "감정을 배제하고 냉철한 이성과 객관적 사실에 근거해 결정을 내립니다.", "action": "계약, 서류, 금전 거래 등에서 꼼꼼하게 시시비비를 가리세요.", "caution": "지나치게 따지다 인간미를 잃지 않도록 배려를 섞어주세요."},
    {"name": "XII. THE HANGED MAN (매달린 사람)", "keyword": "관점의 전환, 희생, 기다림의 지혜", "overview": "남들과 다른 시각으로 세상을 바라볼 때 뜻밖의 돌파구가 열립니다.", "action": "조급하게 움직이지 말고 한 발 물러서서 상황을 넓게 조망하세요.", "caution": "무기력하게 끌려다니지 말고 주체적인 인내를 유지하세요."},
    {"name": "XIII. DEATH (죽음과 재생)", "keyword": "끝과 새로운 시작, 환골탈태", "overview": "쓸모없어진 과거의 패턴을 과감히 잘라내고 완전히 새로운 판을 짭니다.", "action": "미련을 버리고 불필요한 관계나 습관을 정리하세요.", "caution": "과거를 붙잡고 있으면 새로운 복이 들어올 자리가 없습니다."},
    {"name": "XIV. TEMPERANCE (절제)", "keyword": "균형, 융합, 평정심", "overview": "서로 다른 두 기운을 조화롭게 섞어 최적의 황금비율을 찾아냅니다.", "action": "과유불급을 기억하고 중용의 태도로 마음의 평화를 지키세요.", "caution": "극단적인 선택이나 과식, 과음을 피하세요."},
    {"name": "XV. THE DEVIL (악마)", "keyword": "강한 유혹, 집착, 본능적 매력", "overview": "헤어나오기 힘든 강력한 매력이나 유혹, 집착에 얽힐 수 있습니다.", "action": "달콤한 제안의 이면에 숨겨진 계약 조건을 철저히 확인하세요.", "caution": "중독적인 습관이나 집착의 고리를 과감히 끊어내야 합니다."},
    {"name": "XVI. THE TOWER (탑)", "keyword": "예상치 못한 충격, 낡은 틀의 붕괴, 각성", "overview": "불안정한 기반 위에 쌓아올린 탑이 무너지며 진실이 드러납니다.", "action": "위기를 기회로 삼아 바닥부터 새롭고 튼튼하게 다시 시작하세요.", "caution": "당황하지 말고 충격을 차분히 수습하는 침착함이 필요합니다."},
    {"name": "XVII. THE STAR (별)", "keyword": "희망, 영감, 치유, 맑은 비전", "overview": "어둠 속에서 반짝이는 길잡이 별처럼 미래에 대한 밝은 희망과 비전이 생깁니다.", "action": "꿈꾸던 이상을 향해 긍정적인 마음으로 씨앗을 뿌리세요.", "caution": "현실감 없는 막연한 낙관주의에만 머무르지 않도록 실행력을 더하세요."},
    {"name": "XVIII. THE MOON (달)", "keyword": "불안, 안개, 감수성, 비밀", "overview": "상황이 아직 안갯속처럼 명확하지 않아 마음속에 불안이 스밀 수 있습니다.", "action": "중대한 결정은 며칠 뒤로 미루고 감정의 파도를 차분히 가라앉히세요.", "caution": "실체 없는 두려움이나 의심에 휘둘리지 마세요."},
    {"name": "XIX. THE SUN (태양)", "keyword": "성공, 활력, 명확성, 최고의 행운", "overview": "모든 근심이 사라지고 밝은 빛 아래에서 큰 성공과 기쁨을 누립니다.", "action": "자신 있게 나서서 스포트라이트를 받고 열정을 마음껏 발산하세요.", "caution": "자만심으로 주변 사람을 무시하지 않도록 겸손을 챙기세요."},
    {"name": "XX. JUDGEMENT (심판)", "keyword": "부활, 재기, 기쁜 소식, 결단", "overview": "오랫동안 기다려온 결과나 기쁜 보상의 나팔 소리가 울려 퍼집니다.", "action": "망설이지 말고 과거의 오해를 풀고 두 번째 기회를 잡으세요.", "caution": "결정적 신호가 왔을 때 주저하다 타이밍을 놓치지 마세요."},
    {"name": "XXI. THE WORLD (세계)", "keyword": "완성, 완벽한 조화, 글로벌, 대단원", "overview": "한 단계의 완벽한 마무리를 짓고 더 넓은 세계로 도약하는 최고의 결실 카드입니다.", "action": "지금까지의 성취를 자축하고 더 큰 무대를 향해 나아가세요.", "caution": "완성에 안주하지 말고 다음 레벨을 준비하세요."}
]

@app.get("/api/daily-tarot")
async def get_daily_tarot(slot: Optional[int] = 1, rand_seed: Optional[str] = None):
    if rand_seed:
        hash_val = int(hashlib.md5(f"{rand_seed}_{slot}_{random.random()}".encode()).hexdigest(), 16)
    else:
        today_str = datetime.now().strftime("%Y-%m-%d")
        hash_val = int(hashlib.md5(f"{today_str}_slot_{slot}".encode()).hexdigest(), 16)
    
    return TAROT_DECK[hash_val % len(TAROT_DECK)]

@app.post("/api/analyze")
async def analyze_saju(req: AnalyzeRequest):
    saju_result = calculate_saju_pillars(req.year, req.month, req.day, req.sijin_index)
    
    # 생년월일 + 오늘 날짜 기반 1:1 고유 부적 추출 (양력/음력 구분 반영)
    today_str = datetime.now().strftime("%Y-%m-%d")
    cal_flag = req.calendar_type or "solar"
    sijin_flag = req.sijin_index if req.sijin_index is not None else -1
    unique_seed = f"{today_str}_{req.name}_{req.year}_{req.month}_{req.day}_{cal_flag}_{sijin_flag}"
    hash_idx = int(hashlib.md5(unique_seed.encode()).hexdigest(), 16)
    
    # 12종 부적 중 사주별 1:1 매칭
    talisman_idx = (req.year * 3 + req.month * 7 + req.day * 11 + hash_idx) % len(TALISMAN_DECK)
    today_talisman = TALISMAN_DECK[talisman_idx]

    curation = DAILY_CURATIONS[hash_idx % len(DAILY_CURATIONS)]
    score_variance = (hash_idx % 7) - 3
    daily_score = max(82, min(99, curation["score_base"] + score_variance))

    fortunes = {
        "daily": {
            "title": curation["title"],
            "score": daily_score,
            "advice": curation["advice"],
            "lucky_color": curation["lucky_color"],
            "lucky_number": curation["lucky_number"],
            "lucky_direction": curation["lucky_direction"],
            "fashion_style": curation["fashion_style"],
            "lucky_item": curation["lucky_item"],
            "recommended_menu": curation["recommended_menu"],
            "lucky_person": curation["lucky_person"],
            "today_gaewoon": curation["today_gaewoon"],
            "talisman": today_talisman
        }
    }
    
    daewoon_full_report = f"""
    <div class="space-y-4 text-xs text-slate-800 leading-relaxed font-normal">
        <div class="p-3.5 bg-amber-50 rounded-xl border border-amber-300">
            <h5 class="font-bold text-amber-950 text-sm mb-1">👑 【{req.name} 님의 자미두수 & 10년 대운 심층 마스터 리포트】</h5>
            <p class="text-amber-900 text-xs">선천적 사주 원국과 10년 주기 대운의 거대한 계절 흐름을 입체 분석한 평생 지침서입니다.</p>
        </div>

        <div class="space-y-2">
            <h6 class="font-bold text-brand-900 text-xs border-b border-brand-200 pb-1">1. 대운의 계절적 흐름 & 인생의 터닝포인트</h6>
            <p>• {req.name} 님의 사주는 뿌리가 깊은 거목(甲木)의 형상으로, 현재 생애주기 중 가장 에너지가 응축되고 추진력이 폭발하는 <b>40대 중장년 황금기 대운</b>의 중심부를 관통하고 있습니다.</p>
            <p>• 스스로 판을 주도하고 실질적인 자산과 명예를 거머쥐는 결실의 계절로 진입했습니다.</p>
        </div>

        <div class="space-y-2">
            <h6 class="font-bold text-brand-900 text-xs border-b border-brand-200 pb-1">2. 황실 자미두수 4대 핵심 명궁 정밀 해부</h6>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                    <span class="font-bold text-brand-800 block">💰 재백궁(財帛宮) - 평생 재물 그릇</span>
                    <p class="text-slate-600 text-xs">천부성과 무곡성의 길한 기운이 비쳐 금고가 단단하고 부동산, 문서형 자산을 통해 자산이 계단식으로 우상향합니다.</p>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                    <span class="font-bold text-brand-800 block">💼 관록궁(官祿宮) - 직업 & 사회적 성공</span>
                    <p class="text-slate-600 text-xs">독자적 전문 영역이나 책임자 위치에서 최대 역량이 발휘되며 조직 내 영향력이 커집니다.</p>
                </div>
            </div>
        </div>
    </div>
    """

    return {
        "saju_data": saju_result,
        "character_profile": saju_result["character"],
        "jijanggan_data": saju_result["jijanggan"],
        "life_chart": saju_result["life_chart"],
        "fortunes": fortunes,
        "paid_reports": {"daewoon": daewoon_full_report}
    }

@app.post("/api/wealth-fortune")
async def wealth_fortune():
    return {"score": 96, "report": "<div class='p-3 bg-amber-50 rounded-xl text-xs text-amber-950 leading-relaxed font-bold'>💰 평생 재물 그릇: 정재(正財)의 기운으로 부동산 및 시스템 문서 자산이 크게 불어납니다.</div>"}

@app.post("/api/health-fortune")
async def health_fortune():
    return {"score": 93, "report": "<div class='p-3 bg-sky-50 rounded-xl text-xs text-sky-950 leading-relaxed font-bold'>🌿 평생 체질 진단: 하체 근력 운동과 규칙적인 수분 섭취가 사주의 화기를 내려줍니다.</div>"}

@app.post("/api/love-fortune")
async def love_fortune():
    return {"score": 95, "report": "<div class='p-3 bg-rose-50 rounded-xl text-xs text-rose-950 leading-relaxed font-bold'>💖 평생 애정운: 신뢰감 높은 동반자 인연이 자리하여 가운이 번창합니다.</div>"}

@app.post("/api/business-fortune")
async def business_fortune():
    return {"score": 94, "report": "<div class='p-3 bg-amber-50 rounded-xl text-xs text-amber-950 leading-relaxed font-bold'>🏢 사업운: 전문 노하우 및 B2B 시스템 비즈니스에 최적화된 CEO 사주입니다.</div>"}

@app.post("/api/career-jump")
async def career_jump():
    return {"score": 92, "report": "<div class='p-3 bg-sky-50 rounded-xl text-xs text-sky-950 leading-relaxed font-bold'>💼 이직 전략: 2026년 하반기 명예 관성 상승으로 연봉 협상 주도권을 쥡니다.</div>"}

@app.post("/api/gunghap")
async def gunghap():
    return {"score": 88, "report": "<div class='p-3 bg-rose-50 rounded-xl text-xs text-rose-950 leading-relaxed font-bold'>❤️ 정밀 궁합: 상호보완형 상생 궁합으로 최상의 시너지를 냅니다.</div>"}

@app.post("/api/heart")
async def heart():
    return {"score": 84, "report": "<div class='p-3 bg-purple-50 rounded-xl text-xs text-purple-950 leading-relaxed font-bold'>💔 속마음: 상대방도 진지하게 생각하고 있으니 가벼운 안부로 다가가세요.</div>"}
