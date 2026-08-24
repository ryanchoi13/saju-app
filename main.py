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
    sijin_index: Optional[int] = None
    is_unknown_time: bool = False

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

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
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    seed_str = f"{today_str}_{req.year}_{req.month}_{req.day}_{saju_result.get('day_stem', '갑')}"
    hash_idx = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    
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
            "love_advice": "마음을 솔직하게 표현할수록 신뢰가 깊어집니다.",
            "career_advice": "기초를 탄탄히 다지면 곧 큰 결실로 이어집니다.",
            "health_advice": "스트레칭으로 목과 어깨의 긴장을 풀어주세요.",
            "study_advice": "핵심 요점을 정리하고 집중 시간을 확보하세요.",
            "talisman": {
                "title": "재물만복부 (財物萬福符)",
                "desc": "금고의 문을 열고 새는 돈을 막아주는 황금 기운",
                "chinese": "財運大吉\n聚財如山",
                "power": "재물통로 개운 · 자산 증식"
            }
        },
        "monthly": {
            "title": "안정적인 기반 위에 새로운 기회가 열리는 달",
            "score": 89,
            "theme": "씨앗을 뿌리고 터전을 넓히는 중요한 분기점입니다. 주변 조력자와의 협업이 결실을 앞당깁니다.",
            "love_advice": "서로의 다름을 존중할 때 관계가 더욱 단단해집니다.",
            "career_advice": "주변과의 원활한 소통이 프로젝트 성공의 열쇠입니다.",
            "health_advice": "규칙적인 수면 패턴으로 면역력을 관리하세요.",
            "study_advice": "장기적인 학습 로드맵을 재점검하기 좋은 시기입니다."
        },
        "yearly": {
            "title": "2026년 대운의 도약과 자산 확장의 해",
            "score": 95,
            "main_trend": "그동안 쌓아온 노력과 인내가 마침내 시장에서 큰 가치로 환산되는 시기입니다. 명예운과 문서 자산운이 함께 상승합니다.",
            "love_advice": "평생을 함께할 든든한 동반자 인연이 두터워집니다.",
            "career_advice": "전문성을 인정받아 직급 상승 및 영향력이 확대됩니다.",
            "health_advice": "규칙적인 운동으로 체력을 길러 큰 기운을 받치세요.",
            "study_advice": "전문 자격 및 지식 확장이 평생의 무기가 됩니다."
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
            <p>• 20대와 30대가 토대를 닦고 경험을 축적하는 담금질의 시기였다면, 현재 대운은 <b>스스로 판을 주도하고 실질적인 자산과 명예를 거머쥐는 결실의 계절</b>입니다. 사주 내 화(火)와 토(土)의 기운이 식신생재(食神生財)를 이루어 아이디어와 전문성이 직접적인 자산 증식으로 직결됩니다.</p>
        </div>

        <div class="space-y-2">
            <h6 class="font-bold text-brand-900 text-xs border-b border-brand-200 pb-1">2. 황실 자미두수(紫微斗數) 4대 핵심 명궁 정밀 해부</h6>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                    <span class="font-bold text-brand-800 block">💰 재백궁(財帛宮) - 평생 재물 그릇</span>
                    <p class="text-slate-600 text-xs">천부성(天府星)과 무곡성(武曲星)의 길한 기운이 비쳐 금고가 단단하고 새는 돈을 지키는 힘이 매우 강합니다. 일확천금보다는 <b>부동산, 시스템 구축, 문서형 자산</b>을 통해 자산이 계단식으로 우상향합니다.</p>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                    <span class="font-bold text-brand-800 block">💼 관록궁(官祿宮) - 직업 & 사회적 성공</span>
                    <p class="text-slate-600 text-xs">남 밑에서 단순 수동적 업무를 하기보다는 <b>자신의 독자적 전문 영역이나 책임자 위치</b>에서 최대 역량이 발휘됩니다. 후반기로 갈수록 조직 내 영향력과 명예가 크게 상승합니다.</p>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                    <span class="font-bold text-rose-800 block">💖 부처궁(夫妻宮) - 배우자 인연 & 가정</span>
                    <p class="text-slate-600 text-xs">배우자 자리에 듬직하고 신뢰감 높은 인연이 자리하여, 인생의 중대한 결정 때마다 현명한 조력자 역할을 해줍니다. 서로의 독립성을 존중할수록 가운(家運)이 번창합니다.</p>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                    <span class="font-bold text-sky-800 block">🌿 질악궁(疾厄宮) - 건강 관리 골든룰</span>
                    <p class="text-slate-600 text-xs">화(火)와 토(土)의 기운이 왕성하여 위장계통과 혈액순환, 간 해독 관리가 핵심입니다. 규칙적인 수분 섭취와 하체 근력 운동이 대운의 복을 받치는 기둥이 됩니다.</p>
                </div>
            </div>
        </div>

        <div class="space-y-2">
            <h6 class="font-bold text-brand-900 text-xs border-b border-brand-200 pb-1">3. 향후 5개년 대운 로드맵 & 실전 액션 플랜</h6>
            <p>• <b>2026~2027년 (도약기):</b> 새로운 프로젝트 론칭, 전문 자산 확장, 권한 확대 등 외연 확장의 최적기입니다. 망설이지 말고 적극적으로 기회를 선점하세요.</p>
            <p>• <b>2028~2030년 (안정기):</b> 축적된 자산을 바탕으로 부동산 매입 및 장기 안전자산으로 포트폴리오를 전환하여 평생의 부를 공고히 다지는 시기입니다.</p>
        </div>

        <div class="p-3 bg-brand-50 rounded-xl border border-brand-200 space-y-1">
            <span class="font-bold text-brand-900 block text-xs">✨ {req.name} 님만을 위한 평생 맞춤 개운(開運) 처방</span>
            <p class="text-slate-700 text-xs">• <b>행운의 색상:</b> 청록색, 포레스트 그린, 블랙 계열 (부족한 수/목 보완)</p>
            <p class="text-slate-700 text-xs">• <b>공간 인테리어:</b> 집무실이나 침실 동남쪽에 수생식물(수경재배)이나 작은 분수대를 배치하면 재물길이 활짝 열립니다.</p>
        </div>
    </div>
    """

    paid_reports = {
        "daewoon": daewoon_full_report
    }

    return {
        "saju_data": saju_result,
        "character_profile": saju_result["character"],
        "jijanggan_data": saju_result["jijanggan"],
        "life_chart": saju_result["life_chart"],
        "fortunes": fortunes,
        "paid_reports": paid_reports,
        "current_fortune_summary": "현재 정체되었던 기운이 본격적인 상승 궤도에 진입하고 있으며, 귀인의 조력과 재물 통로가 열리는 인생의 중대한 분기점입니다.",
        "asset_checklist": "1. 고정 지출 효율화 및 현금 흐름 극대화\n2. 안정적 부동산 및 문서 기반 포트폴리오 강화\n3. 조급한 단기 투자 지양 및 장기 원칙 투자 고수"
    }

@app.post("/api/wealth-fortune")
async def wealth_fortune():
    report = """
    <div class="space-y-3.5 text-xs text-slate-800 leading-relaxed font-normal">
        <div class="p-3 bg-amber-50 rounded-xl border border-amber-300">
            <h5 class="font-bold text-amber-950 text-xs">💰 【평생 재물 그릇 & 부동산/투자운 심층 마스터 리포트】</h5>
            <p class="text-amber-900 text-xs">선천적 재물 그릇의 크기와 형태, 평생 자산 증식 로드맵 분석</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-brand-900 text-xs block">1. 선천적 재물 그릇 (정재형 자산 축적가)</span>
            <p>• 타고난 사주 구조상 일확천금을 노리는 투기성 자산보다는, <b>정당한 시스템과 전문성, 문서 자산을 통해 차곡차곡 쌓여 거대한 산을 이루는 정재(正財)의 그릇</b>을 가지고 있습니다.</p>
            <p>• 금고의 문이 굳게 닫혀 있어 남들에게 쉽게 돈을 뜯기거나 낭비하지 않는 탁월한 자산 방어력을 지니고 있습니다.</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-brand-900 text-xs block">2. 부동산 & 문서 자산 취득 골든타임</span>
            <p>• 사주 내 토(土) 기운이 튼튼하게 받쳐주고 있어 <b>토지, 상가, 아파트 등 실물 부동산과 궁합이 매우 우수</b>합니다.</p>
            <p>• <b>최적의 매수 방위:</b> 거주지 기준 동남쪽 또는 서남쪽 방면의 부동산이 가치를 크게 불려줍니다.</p>
            <p>• <b>골든타임:</b> 2026년 하반기부터 2028년 상반기 사이에 생애 가장 가치 있는 핵심 문서(계약)를 쥐게 됩니다.</p>
        </div>
        <div class="p-3 bg-[#F8FAF7] rounded-xl border border-brand-200 space-y-1">
            <span class="font-bold text-brand-900 block text-xs">💡 실전 부자 포트폴리오 전략</span>
            <p>1. 현금성 자산 30%, 실물 부동산/문서 자산 50%, 안정형 배당/채권 20% 황금 비율 유지</p>
            <p>2. 지인의 구두 제안이나 감에 의존한 투자는 철저히 배제하고 법적 계약서 중심 운용</p>
        </div>
    </div>
    """
    return {"score": 96, "report": report}

@app.post("/api/health-fortune")
async def health_fortune():
    report = """
    <div class="space-y-3.5 text-xs text-slate-800 leading-relaxed font-normal">
        <div class="p-3 bg-sky-50 rounded-xl border border-sky-300">
            <h5 class="font-bold text-sky-950 text-xs">🌿 【평생 체질 진단 & 오행 건강 개운 솔루션】</h5>
            <p class="text-sky-900 text-xs">오행 불균형 진단을 통한 선천적 장부 밸런스 및 평생 웰니스 가이드</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-sky-900 text-xs block">1. 선천적 오행 밸런스 및 장부 분석</span>
            <p>• 목(木)과 토(土)의 기운이 왕성하고 수(水)와 금(金)이 상대적으로 부족한 체질입니다.</p>
            <p>• <b>강한 장부:</b> 간장, 근육계통 (지구력과 회복 탄력성이 뛰어남)</p>
            <p>• <b>집중 관리 장부:</b> 신장·방광, 혈액순환계 및 위장 점막 보호가 필수적입니다.</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-sky-900 text-xs block">2. 연령대별 건강 리스크 예방책</span>
            <p>• 40대 중후반부터는 혈압 및 대사증후군 예방을 위해 나트륨 섭취를 줄이고 하루 1.5L 이상의 미온수를 꾸준히 섭취해야 합니다.</p>
            <p>• 과도한 유산소보다는 <b>하체 근력 운동(스쿼트, 계단 오르기)</b>이 사주의 화기를 아래로 내려주는 최고의 명약입니다.</p>
        </div>
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
            <span class="font-bold text-slate-900 block text-xs">🧘 사주 맞춤 데일리 힐링 리추얼</span>
            <p>• 기상 직후 따뜻한 물 한 잔으로 수(水) 기운 보충하기</p>
            <p>• 취침 전 10분간 종아리 및 어깨 스트레칭으로 림프 순환 극대화</p>
        </div>
    </div>
    """
    return {"score": 93, "report": report}

@app.post("/api/love-fortune")
async def love_fortune():
    report = """
    <div class="space-y-3.5 text-xs text-slate-800 leading-relaxed font-normal">
        <div class="p-3 bg-rose-50 rounded-xl border border-rose-300">
            <h5 class="font-bold text-rose-950 text-xs">💖 【평생 애정/결혼운 & 배우자복 심층 리포트】</h5>
            <p class="text-rose-900 text-xs">일편단심 순정파 기질과 배우자궁 분석, 평생 화목한 가정 비법</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-rose-900 text-xs block">1. 나의 선천적 연애 스타일 & 매력 포인트</span>
            <p>• 첫인상은 듬직하고 진중하며, 가벼운 만남보다는 <b>신의와 신뢰를 바탕으로 한 깊은 유대감</b>을 중요하게 생각합니다.</p>
            <p>• 겉으로 화려한 감정 표현을 자주 하지 않더라도, 결정적인 순간에 든든한 버팀목이 되어주는 묵직한 사랑을 주는 타입입니다.</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-rose-900 text-xs block">2. 배우자궁(配偶者宮) 정밀 분석</span>
            <p>• 일지에 듬직한 조력자 기운이 자리하여, 나를 현실적으로 챙겨주고 자산 관리를 함께 도맡아 줄 수 있는 <b>지혜롭고 포용력 있는 배우자</b>와 평생의 연을 맺습니다.</p>
            <p>• 서로의 일과 프라이버시를 존중해 줄 때 부부 금슬이 두터워지며 집안에 재물이 크게 모입니다.</p>
        </div>
        <div class="p-3 bg-rose-50/50 rounded-xl border border-rose-200 space-y-1">
            <span class="font-bold text-rose-950 block text-xs">💑 애정운을 200% 상승시키는 실전 팁</span>
            <p>• 고마운 마음을 마음속에만 담아두지 말고 말이나 작은 쪽지, 선물로 표현할 것</p>
            <p>• 주말 중 하루는 함께 자연(산책, 근교 힐링)을 찾으며 공감 대화를 나누세요.</p>
        </div>
    </div>
    """
    return {"score": 95, "report": report}

@app.post("/api/business-fortune")
async def business_fortune():
    report = """
    <div class="space-y-3.5 text-xs text-slate-800 leading-relaxed font-normal">
        <div class="p-3 bg-amber-50 rounded-xl border border-amber-300">
            <h5 class="font-bold text-amber-950 text-xs">🏢 【평생 사업운 & 대박 아이템/동업 심층 리포트】</h5>
            <p class="text-amber-900 text-xs">식신생재형 CEO 사주 구조와 성공 창업 로드맵</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-amber-950 text-xs block">1. 사업가적 자질 & 핵심 성공 역량</span>
            <p>• 기획력과 결단력을 두루 갖춘 <b>식신생재(食神生財)형 CEO 사주</b>로, 본인의 전문 기술이나 독창적인 시스템을 사업화하는 데 최적화되어 있습니다.</p>
            <p>• 한 번 방향을 정하면 흔들리지 않는 뚝심이 있어 위기 극복 능력이 매우 뛰어납니다.</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-amber-950 text-xs block">2. 사주 맞춤 대박 사업 아이템 TOP 3</span>
            <p>• <b>1위 - 전문 지식/컨설팅/교육 서비스:</b> 독점적 노하우를 바탕으로 한 지식 기반 사업</p>
            <p>• <b>2위 - 플랫폼/시스템 기반 B2B 비즈니스:</b> 정기적인 캐시카우가 발생하는 구독·중개 모델</p>
            <p>• <b>3위 - 공간/부동산 연계 임대·공간 비즈니스:</b> 안정적 자산 가치 상승을 동반하는 사업</p>
        </div>
        <div class="p-3 bg-amber-100/60 rounded-xl border border-amber-300 space-y-1">
            <span class="font-bold text-amber-950 block text-xs">⚠️ 동업 및 투자 시 주의사항</span>
            <p>• 감정적인 동업은 피하고, 지분 구조와 역할 분담을 계약서로 명확히 공증할 것</p>
            <p>• 초기 고정비를 최소화하는 린(Lean) 스타트업 방식으로 시장성을 검증 후 확장하세요.</p>
        </div>
    </div>
    """
    return {"score": 94, "report": report}

@app.post("/api/career-jump")
async def career_jump():
    report = """
    <div class="space-y-3.5 text-xs text-slate-800 leading-relaxed font-normal">
        <div class="p-3 bg-sky-50 rounded-xl border border-sky-300">
            <h5 class="font-bold text-sky-950 text-xs">💼 【2026 이직 합격 & 연봉 상승 극대화 전략】</h5>
            <p class="text-sky-900 text-xs">명예 관성(官星) 상승기 활용 및 연봉 15~25% 점프 비결</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-sky-900 text-xs block">1. 2026년 하반기 이직/승진 운세 총평</span>
            <p>• 관성(官星)과 인성(印星)이 쌍으로 길하게 작용하여, 그동안의 성과를 외부에서 높이 평가받는 <b>이직의 최적 타이밍</b>입니다.</p>
            <p>• 지원하거나 제안받는 곳마다 협상 주도권을 쥐게 되며 권한이 대폭 확대됩니다.</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-sky-900 text-xs block">2. 연봉 협상 실전 가이드</span>
            <p>• 첫 면접 단계부터 정량적 수치(매출 기여도, 프로세스 개선율)를 담은 포트폴리오를 제시하세요.</p>
            <p>• 이전 연봉 대비 최소 15~20% 상향을 기본 목표로 잡고 당당하게 가치를 어필할 때 상대방이 수용합니다.</p>
        </div>
    </div>
    """
    return {"score": 92, "report": report}

@app.post("/api/gunghap")
async def gunghap():
    report = """
    <div class="space-y-3.5 text-xs text-slate-800 leading-relaxed font-normal">
        <div class="p-3 bg-rose-50 rounded-xl border border-rose-300">
            <h5 class="font-bold text-rose-950 text-xs">❤️ 【상대방과의 1:1 정밀 궁합 & 인연 분석】</h5>
            <p class="text-rose-900 text-xs">오행 상생 밸런스, 성격 조화도 및 평생 시너지 진단</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-rose-900 text-xs block">1. 오행 상생 밸런스 (88점 - 대길)</span>
            <p>• 서로의 원국에서 부족한 오행을 자연스럽게 채워주는 <b>상호보완형 상생 궁합</b>입니다.</p>
            <p>• 한 사람이 추진하면 다른 한 사람이 현실적인 위험을 걸러주는 이상적인 파트너십을 형성합니다.</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-rose-900 text-xs block">2. 갈등 예방 및 시너지 극대화 처방</span>
            <p>• 둘 다 자존감이 강할 수 있으므로, 의견이 다를 때는 승패를 가리지 말고 '각자의 역할 영역'을 분리해 존중해 주는 것이 관계를 평생 탄탄하게 유지하는 비결입니다.</p>
        </div>
    </div>
    """
    return {"score": 88, "report": report}

@app.post("/api/heart")
async def heart():
    report = """
    <div class="space-y-3.5 text-xs text-slate-800 leading-relaxed font-normal">
        <div class="p-3 bg-purple-50 rounded-xl border border-purple-300">
            <h5 class="font-bold text-purple-950 text-xs">💔 【그 사람의 속마음 & 연락 타이밍 심층 분석】</h5>
            <p class="text-purple-900 text-xs">상대방의 현재 심리 상태와 최적의 접촉 골든타임</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-purple-900 text-xs block">1. 상대방의 현재 속마음 & 심리 기류</span>
            <p>• 겉으로는 차분하고 무심한 척하고 있지만, 마음속 깊은 곳에서는 당신과의 인연과 대화를 진지하게 되새기고 있습니다.</p>
            <p>• 먼저 다가가기에는 체면이나 조심스러움이 앞서는 상태이므로, 부담 없는 가벼운 안부 인사가 결정적인 물꼬를 틉니다.</p>
        </div>
        <div class="space-y-1.5">
            <span class="font-bold text-purple-900 text-xs block">2. 최고의 연락 타이밍 & 추천 멘트</span>
            <p>• <b>골든 타이밍:</b> 주말 늦은 오후 또는 평일 퇴근 후 편안해진 저녁 시간대</p>
            <p>• <b>추천 멘트:</b> 부담을 주지 않는 일상적인 질문("오늘 날씨가 맑아서 문득 생각나서 연락해봐요, 잘 지내시죠?")으로 가볍게 시작하세요.</p>
        </div>
    </div>
    """
    return {"score": 84, "report": report}
