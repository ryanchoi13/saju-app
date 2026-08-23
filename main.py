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
            "theme": "씨앗을 뿌리고 터전을 넓히는 중요한 분기점입니다.",
            "love_advice": "서로의 다름을 존중할 때 관계가 더욱 단단해집니다.",
            "career_advice": "주변과의 원활한 소통이 프로젝트 성공의 열쇠입니다.",
            "health_advice": "규칙적인 수면 패턴으로 면역력을 관리하세요.",
            "study_advice": "장기적인 학습 로드맵을 재점검하기 좋은 시기입니다."
        },
        "yearly": {
            "title": "2026년 대운의 도약과 자산 확장의 해",
            "score": 95,
            "main_trend": "그동안 쌓아온 노력이 결실을 맺으며 인생의 큰 도약을 맞이합니다.",
            "love_advice": "평생을 함께할 든든한 동반자 인연이 두터워집니다.",
            "career_advice": "전문성을 인정받아 직급 상승 및 영향력이 확대됩니다.",
            "health_advice": "규칙적인 운동으로 체력을 길러 큰 기운을 받치세요.",
            "study_advice": "전문 자격 및 지식 확장이 평생의 무기가 됩니다."
        }
    }
    
    paid_reports = {
        "daewoon": f"【{req.name} 님의 자미두수 & 10년 대운 심층 마스터 리포트】\n\n1. 대운의 계절 흐름: 현재 인생의 중장년 황금기에 위치하여 노력 대비 성과가 극대화되는 시기입니다.\n2. 재백궁 & 관록궁: 자산 축적 그릇이 크며, 문서 기반의 안정적 자산 운용이 유리합니다.\n3. 길운 극대화 전략: 명확한 원칙을 지키고 조급함을 내려놓을 때 가장 큰 부가 모입니다."
    }

    return {
        "saju_data": saju_result,
        "character_profile": saju_result["character"],
        "jijanggan_data": saju_result["jijanggan"],
        "life_chart": saju_result["life_chart"],
        "fortunes": fortunes,
        "paid_reports": paid_reports,
        "current_fortune_summary": "현재 정체되었던 기운이 상승 국면으로 전환되며, 귀인의 조력과 재물 통로가 열리는 시점입니다.",
        "asset_checklist": "1. 현금 흐름 및 고정 지출 재점검\n2. 부동산·문서형 자산 포트폴리오 강화\n3. 장기적 관점의 안정적 투자 원칙 준수"
    }

@app.post("/api/health-fortune")
async def health_fortune():
    return {"score": 93, "report": "선천적 장부 밸런스 분석 결과, 규칙적인 식습관과 수분 섭취가 건강운을 극대화합니다."}

@app.post("/api/love-fortune")
async def love_fortune():
    return {"score": 95, "report": "일편단심 순정파 기질로 신뢰 중심의 만남에서 가장 빛을 발하며, 배우자궁이 안정적입니다."}

@app.post("/api/wealth-fortune")
async def wealth_fortune():
    return {"score": 96, "report": "정재(正財)의 안정적인 자산 축적 구조를 지니고 있어 분산 투자와 문서 자산이 유리합니다."}

@app.post("/api/business-fortune")
async def business_fortune():
    return {"score": 94, "report": "식신생재형 CEO 사주로 전문성과 시스템 구축을 통한 사업 확장에 큰 강점이 있습니다."}

@app.post("/api/career-jump")
async def career_jump():
    return {"score": 92, "report": "2026년 하반기 명예 관성운이 상승하여 연봉 협상 및 승진, 이직에 매우 유리한 타이밍입니다."}

@app.post("/api/gunghap")
async def gunghap():
    return {"score": 88, "report": "서로의 부족한 오행을 보완해 주는 상생의 구조로 시간이 지날수록 유대감이 깊어지는 궁합입니다."}

@app.post("/api/heart")
async def heart():
    return {"score": 84, "report": "상대방 역시 진지하고 편안한 마음을 품고 있으며, 먼저 건네는 따뜻한 한마디가 관계의 물꼬를 틉니다."}
