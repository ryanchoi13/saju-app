# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

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

@app.get("/api/daily-tarot")
async def get_daily_tarot():
    return {
        "name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)",
        "keyword": "전환점, 뜻밖의 행운, 필연적 기회",
        "overview": "정체되었던 흐름이 풀리고 새로운 기운이 상승 궤도에 진입합니다.",
        "action": "변화를 주저하지 말고 찾아온 제안이나 흐름을 긍정적으로 수용하세요.",
        "caution": "과거의 관성에 얽매이지 말고 새 판을 짤 타이밍입니다."
    }

@app.post("/api/analyze")
async def analyze_saju(req: AnalyzeRequest):
    saju_result = calculate_saju_pillars(req.year, req.month, req.day, req.sijin_index)
    
    fortunes = {
        "daily": {
            "title": "금빛 기운이 서서히 솟아나는 도약의 하루",
            "score": 92,
            "advice": "묵혀두었던 계획이나 관계에서 긍정적인 신호가 찾아옵니다.",
            "lucky_color": "포레스트 그린 / 골드",
            "lucky_number": "7, 8",
            "lucky_direction": "동남쪽",
            "fashion_style": "단정하고 깔끔한 세미 캐주얼",
            "lucky_item": "원목 또는 메탈 소품",
            "recommended_menu": "따뜻하고 편안한 한식류",
            "lucky_person": "성실하고 차분한 동료 또는 지인",
            "today_gaewoon": "오전 중 따뜻한 차 한 잔을 마시며 오늘의 목표 3가지를 메모하세요.",
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
