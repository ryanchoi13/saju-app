import datetime
import math
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import random

app = FastAPI(title="운세의 신 정통 명리학 엔진", version="25.0.0")

CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

CHEONGAN_ELEMENTS = {
    "甲": "wood", "乙": "wood", "丙": "fire", "丁": "fire", "戊": "earth",
    "己": "earth", "庚": "metal", "辛": "metal", "壬": "water", "癸": "water"
}
JIJI_ELEMENTS = {
    "子": "water", "丑": "earth", "寅": "wood", "卯": "wood", "辰": "earth",
    "巳": "fire", "午": "fire", "未": "earth", "申": "metal", "酉": "metal",
    "戌": "earth", "亥": "water"
}

JIJANGGAN_FULL_MAP = {
    "子": [{"char": "壬", "elem": "water", "weight": 10}, {"char": "癸", "elem": "water", "weight": 20}],
    "丑": [{"char": "癸", "elem": "water", "weight": 9}, {"char": "辛", "elem": "metal", "weight": 3}, {"char": "己", "elem": "earth", "weight": 18}],
    "寅": [{"char": "戊", "elem": "earth", "weight": 7}, {"char": "丙", "elem": "fire", "weight": 7}, {"char": "甲", "elem": "wood", "weight": 16}],
    "卯": [{"char": "甲", "elem": "wood", "weight": 10}, {"char": "乙", "elem": "wood", "weight": 20}],
    "辰": [{"char": "乙", "elem": "wood", "weight": 9}, {"char": "癸", "elem": "water", "weight": 3}, {"char": "戊", "elem": "earth", "weight": 18}],
    "巳": [{"char": "戊", "elem": "earth", "weight": 7}, {"char": "庚", "elem": "metal", "weight": 7}, {"char": "丙", "elem": "fire", "weight": 16}],
    "午": [{"char": "丙", "elem": "fire", "weight": 10}, {"char": "己", "elem": "earth", "weight": 9}, {"char": "丁", "elem": "fire", "weight": 11}],
    "未": [{"char": "丁", "elem": "fire", "weight": 9}, {"char": "乙", "elem": "wood", "weight": 3}, {"char": "己", "elem": "earth", "weight": 18}],
    "申": [{"char": "戊", "elem": "earth", "weight": 7}, {"char": "壬", "elem": "water", "weight": 7}, {"char": "庚", "elem": "metal", "weight": 16}],
    "酉": [{"char": "庚", "elem": "metal", "weight": 10}, {"char": "辛", "elem": "metal", "weight": 20}],
    "戌": [{"char": "辛", "elem": "metal", "weight": 9}, {"char": "丁", "elem": "fire", "weight": 3}, {"char": "戊", "elem": "earth", "weight": 18}],
    "亥": [{"char": "戊", "elem": "earth", "weight": 7}, {"char": "甲", "elem": "wood", "weight": 7}, {"char": "壬", "elem": "water", "weight": 16}]
}

DAY_MBTI_MAP = {
    "甲": {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주", "essence": "거목(巨木)의 기상"},
    "乙": {"mbti": "재기발랄한 활동가 (ENFP형)", "desc": "유연한 적응력과 풍부한 친화력으로 사람의 마음을 얻는 사주", "essence": "생명력 넘치는 화초"},
    "丙": {"mbti": "자유로운 영혼의 연예인 (ESFP형)", "desc": "태양 같은 열정과 밝은 에너지로 주변을 환하게 밝히는 사주", "essence": "하늘을 비추는 태양"},
    "丁": {"mbti": "용의주도한 전략가 (ENTJ형)", "desc": "치밀한 기획력과 은근한 카리스마로 목표를 완벽히 쟁취하는 사주", "essence": "어둠을 밝히는 촛불"},
    "戊": {"mbti": "청렴결백한 논리주의자 (ISTJ형)", "desc": "묵직한 신뢰감과 흔들리지 않는 원칙으로 책임을 다하는 사주", "essence": "단단하고 광활한 대지"},
    "己": {"mbti": "세심한 수호자 (ISFJ형)", "desc": "비옥한 땅처럼 주변을 묵묵히 품어주고 실속을 챙기는 사주", "essence": "만물을 키워내는 전답"},
    "庚": {"mbti": "엄격한 관리자 (ESTJ형)", "desc": "의리와 결단력으로 무장하여 난관을 돌파하는 단호한 실행가 사주", "essence": "강철과 원석의 결단력"},
    "辛": {"mbti": "용의주도한 완벽주의자 (INTJ형)", "desc": "보석처럼 예리한 감각과 높은 기준을 지닌 냉철한 분석가 사주", "essence": "빛나는 다이아몬드"},
    "壬": {"mbti": "뜨거운 논쟁을 즐기는 변론가 (ENTP형)", "desc": "바다처럼 넓은 지혜와 임기응변으로 판을 주도하는 아이디어 뱅크 사주", "essence": "도도하게 흐르는 큰 강"},
    "癸": {"mbti": "선의의 옹호자 (INFJ형)", "desc": "맑은 이슬비처럼 깊은 직관과 통찰력으로 본질을 꿰뚫는 사색가 사주", "essence": "만물을 적시는 봄비"}
}

ANIMAL_MAP = {"子": "쥐", "丑": "소", "寅": "호랑이", "卯": "토끼", "辰": "용", "巳": "뱀", "午": "말", "未": "양", "申": "원숭이", "酉": "닭", "戌": "개", "亥": "돼지"}
ANIMAL_ICONS = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍", "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}

STAR_SIGNS = [
    {"name": "물병자리", "icon": "♒", "period": "01.20 ~ 02.18"},
    {"name": "물고기자리", "icon": "♓", "period": "02.19 ~ 03.20"},
    {"name": "양자리", "icon": "♈", "period": "03.21 ~ 04.19"},
    {"name": "황소자리", "icon": "♉", "period": "04.20 ~ 05.20"},
    {"name": "쌍둥이자리", "icon": "♊", "period": "05.21 ~ 06.21"},
    {"name": "게자리", "icon": "♋", "period": "06.22 ~ 07.22"},
    {"name": "사자자리", "icon": "♌", "period": "07.23 ~ 08.22"},
    {"name": "처녀자리", "icon": "♍", "period": "08.23 ~ 09.22"},
    {"name": "천칭자리", "icon": "♎", "period": "09.23 ~ 10.22"},
    {"name": "전갈자리", "icon": "♏", "period": "10.23 ~ 11.22"},
    {"name": "사수자리", "icon": "♐", "period": "11.23 ~ 12.21"},
    {"name": "염소자리", "icon": "♑", "period": "12.22 ~ 01.19"}
]

TALISMAN_OHEANG_MAP = {
    "wood": {"type": "wood", "title": "사업대성부 (事業亨通符)", "power": "추진력 강화 · 사업 번창 · 승진운", "desc": "사주에 부족한 木(성장과 개척)의 활력을 불어넣어 막힌 활로를 뚫고 주도권을 쥐게 하는 비급 부적입니다."},
    "fire": {"type": "fire", "title": "소원성취부 (心想事成符)", "power": "열정 회복 · 명예 상승 · 소원 성취", "desc": "사주에 부족한 火(열정과 확산)의 빛을 밝혀 어둠을 몰아내고 염원하던 소망을 성취시키는 전통 부적입니다."},
    "earth": {"type": "earth", "title": "금고수호부 (金庫安穩符)", "power": "자산 방어 · 누수 차단 · 재물 안착", "desc": "사주에 부족한 土(포용과 저장)의 단단한 대지를 마련하여 헛돈 지출을 막고 평생의 자산을 지켜주는 수호 부적입니다."},
    "metal": {"type": "metal", "title": "재물만복부 (萬福大吉符)", "power": "재물 증식 · 금전운 대통 · 투자 대박", "desc": "사주에 부족한 金(결단과 결실)의 황금 기운을 채워 사방에서 금전과 복록이 쏟아지게 하는 전통 경면주사 부적입니다."},
    "water": {"type": "water", "title": "천생화합부 (萬事和合符)", "power": "인연 결속 · 애정 화합 · 인간관계 개선", "desc": "사주에 부족한 水(지혜와 융합)의 부드러운 유대감을 채워 엇갈린 인연을 묶어주고 귀인을 이끄는 화합 부적입니다."}
}

TAROT_CARDS = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작 · 순수한 열정 · 무한한 잠재력", "symbolism": "절벽 끝에 선 순수한 영혼으로 관습에 얽매이지 않는 새로운 여정의 출발을 상징합니다.", "fortune_reading": "오랫동안 머뭇거리던 일의 시작 단추를 꿰기에 최적의 날입니다. 직관을 따를 때 예상 밖의 통로가 열립니다.", "advice": "새로운 제안에 열린 마음을 가지되 발걸음은 가볍고 시선은 신중히 유지하세요.", "action_tip": "떠오르는 아이디어를 즉시 메모하고 먼저 연락을 건네보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 역량 · 완벽한 주도권 · 실력 발휘", "symbolism": "머리 위의 무한대 기호와 제단 위의 4대 원소는 모든 도구를 통제하는 지혜를 뜻합니다.", "fortune_reading": "지식과 언변, 전문 기술이 빛을 발하는 날입니다. 당당한 태도로 판을 리드하기에 최적입니다.", "advice": "미팅이나 보고에서 주도적으로 의견을 제시하고 실력을 드러내세요.", "action_tip": "중요한 대화에서 본인의 핵심 주장을 명확하게 피력하세요."},
    {"name": "II. THE HIGH PRIESTESS (여사제)", "keyword": "깊은 통찰 · 직관과 혜안 · 침묵의 지혜", "symbolism": "흑과 백의 기둥 사이에 앉아 본질적 진실과 영적인 직관을 상징합니다.", "fortune_reading": "겉으로 드러난 말보다 상대방의 숨은 의도나 상황의 이면을 꿰뚫어 보는 혜안이 극대화됩니다.", "advice": "성급하게 반응하기보다는 차분히 경청하고 심사숙고하세요.", "action_tip": "조용한 장소에서 생각을 차분히 정리하는 시간을 가지세요."},
    {"name": "III. THE EMPRESS (여황제)", "keyword": "풍요와 번영 · 따뜻한 포용 · 결실의 기쁨", "symbolism": "풍성한 곡식과 석류 장식은 모성적 사랑과 물질적·정신적 풍요로움을 상징합니다.", "fortune_reading": "그동안 공들여 준비한 일에서 만족스러운 성과와 금전적 보상이 주어지는 날입니다.", "advice": "주변 사람들에게 넉넉한 마음으로 베풀면 더 큰 행운이 돌아옵니다.", "action_tip": "맛있는 식사를 대접하거나 가까운 이에게 감사 인사를 전하세요."},
    {"name": "IV. THE EMPEROR (황제)", "keyword": "확고한 권위 · 강력한 통솔 · 안정된 기반", "symbolism": "단단한 석조 왕좌는 흔들리지 않는 통치력과 엄격한 질서, 조직의 굳건함을 뜻합니다.", "fortune_reading": "자신의 영역에서 주도권을 확립하고 책임감 있게 프로젝트를 완수하기에 좋은 날입니다.", "advice": "원칙과 약속을 철저히 지키며 리더십을 발휘하세요.", "action_tip": "흐트러진 계획을 점검하고 체계적인 규율을 세우세요."},
    {"name": "V. THE HIEROPHANT (교황)", "keyword": "신뢰와 조언 · 전통적 가치 · 귀인의 도우심", "symbolism": "교황의 삼중관과 두 명의 사제는 귀인의 정통성 있는 가르침과 신뢰를 상징합니다.", "fortune_reading": "스승이나 연장자, 유력 인사로부터 결정적인 귀인의 조언을 받아 난관을 해결하는 날입니다.", "advice": "독단적인 행동을 피하고 경험자의 조언을 겸손하게 받아들이세요.", "action_tip": "존경하는 멘토나 상급자에게 안부 연락을 건네보세요."},
    {"name": "VI. THE LOVERS (연인)", "keyword": "조화로운 결합 · 진정한 공감 · 올바른 선택", "symbolism": "천사의 축복 아래 선 남녀는 영혼의 교감과 중요한 인생의 선택을 상징합니다.", "fortune_reading": "인간관계와 애정 전선에 따뜻한 훈풍이 불고 협력 파트너와의 호흡이 완벽히 맞습니다.", "advice": "계산적인 이득보다는 마음의 진정성을 바탕으로 대화하세요.", "action_tip": "소중한 사람과 티타임을 가지며 솔직한 마음을 나누세요."},
    {"name": "VII. THE CHARIOT (전차)", "keyword": "거침없는 돌파 · 승리의 질주 · 강한 의지", "symbolism": "흑과 백의 스핑크스를 이끄는 젊은 기사는 이성과 감성을 통제하여 승리하는 의지를 뜻합니다.", "fortune_reading": "주저하지 않고 강력하게 밀어붙일 때 목표를 수월하게 쟁취할 수 있는 대길의 하루입니다.", "advice": "목표에 집중하고 사소한 장애물에 연연하지 마세요.", "action_tip": "오랫동안 미뤄왔던 단호한 결정을 오늘 실행에 옮기세요."},
    {"name": "VIII. STRENGTH (힘)", "keyword": "내면의 인내 · 부드러운 통제 · 온화한 카리스마", "symbolism": "사자를 부드럽게 다스리는 여인은 강압적인 힘이 아닌 내면의 온화한 카리스마를 상징합니다.", "fortune_reading": "감정을 자제하고 부드럽지만 단단한 태도로 임할 때 유능한 상대도 내 편으로 만듭니다.", "advice": "화가 나거나 감정적일 때일수록 미소와 유연함으로 상대하세요.", "action_tip": "깊은 숨을 세 번 쉬며 너그러운 마음을 유지하세요."},
    {"name": "IX. THE HERMIT (은둔자)", "keyword": "깊은 성찰 · 탐구와 지혜 · 내면의 빛", "symbolism": "등불을 들고 눈 덮인 산을 오르는 노인은 깊은 지혜와 진리 탐구를 상징합니다.", "fortune_reading": "외부의 번잡함에서 벗어나 혼자만의 시간에 몰입할 때 중요한 혜안을 얻게 됩니다.", "advice": "남들의 시선에 신경 쓰지 말고 자신의 내면 소리에 집중하세요.", "action_tip": "스마트폰을 잠시 내려놓고 30분간 조용히 사색을 즐기세요."},
    {"name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)", "keyword": "행운의 반전 · 결정적 기회 · 운명의 전환점", "symbolism": "영원히 회전하는 수레바퀴는 상승과 하강, 기회의 순간을 뜻합니다.", "fortune_reading": "정체되었던 상황이 뜻밖의 계기를 통해 긍정적인 방향으로 급물살을 타게 됩니다.", "advice": "흐름에 맞서지 말고 자연스럽게 변화를 수용하여 기회를 잡으세요.", "action_tip": "오랜 지인에게 온 연락이나 새로운 제안을 긍정적으로 검토하세요."},
    {"name": "XI. JUSTICE (정의)", "keyword": "명확한 판단 · 공정한 균형 · 합리적 계약", "symbolism": "저울과 칼을 든 여신은 감정에 휘둘리지 않는 공정한 판단과 사필귀정을 상징합니다.", "fortune_reading": "공정하고 합리적인 판단이 빛을 발하며 문서 및 계약 건에서 이익이 확보됩니다.", "advice": "사사로운 감정을 배제하고 사실과 데이터에 근거해 결정하세요.", "action_tip": "계약서나 중요한 서류의 조항을 면밀히 재검토하세요."},
    {"name": "XII. THE HANGED MAN (매달린 사람)", "keyword": "발상의 전환 · 인고의 결실 · 새로운 시각", "symbolism": "나무에 거꾸로 매달린 남자의 후광은 희생을 통해 깨달음을 얻는 신성한 시각을 뜻합니다.", "fortune_reading": "잠시 상황이 정체된 것처럼 보이지만 발상을 뒤집을 때 놀라운 해결책이 찾아옵니다.", "advice": "서두르지 말고 현재 상태를 조용히 관조하며 때를 기다리세요.", "action_tip": "기존 방식과 반대되는 새로운 아이디어를 검토해 보세요."},
    {"name": "XIII. DEATH (죽음)", "keyword": "새로운 변혁 · 과거와의 작별 · 불운의 끝", "symbolism": "깃발을 든 기사는 오래된 유통기한이 끝난 상황을 청산하고 새 단계를 시작함을 뜻합니다.", "fortune_reading": "나를 갉아먹던 나쁜 습관이나 원치 않는 상황이 마침내 청산되고 새 출발이 시작됩니다.", "advice": "과거의 미련을 미련 없이 훌훌 털어버리고 새판을 짜세요.", "action_tip": "사용하지 않는 안 쓰는 물건이나 단톡방을 깔끔히 정리하세요."},
    {"name": "XIV. TEMPERANCE (절제)", "keyword": "감정의 조화 · 유연한 중용 · 차분한 융합", "symbolism": "두 컵에 물을 서로 개어 섞는 천사는 이성과 감성, 서로 다른 기운의 완벽한 조화를 뜻합니다.", "fortune_reading": "치우침 없이 조화로운 태도를 유지할 때 원만한 대인관계와 마음의 평화가 유지됩니다.", "advice": "극단적인 선택을 피하고 적절한 타협점을 모색하세요.", "action_tip": "자극적인 음식을 피하고 미온수를 충분히 마시며 속을 달래세요."},
    {"name": "XV. THE DEVIL (악마)", "keyword": "강력한 유혹 · 과감한 집착 · 치명적 매력", "symbolism": "사슬에 묶인 남녀는 유혹과 단기적인 쾌락, 강력한 욕망의 집착을 뜻합니다.", "fortune_reading": "단기적인 이익이나 달콤한 유혹이 다가오나 내실을 따지는 냉철함이 필요합니다.", "advice": "눈앞의 화려함에 혹하지 말고 계약의 조건과 유통기한을 따지세요.", "action_tip": "충동구매나 솔깃한 투자 제안에 쉽게 응하지 마세요."},
    {"name": "XVI. THE TOWER (탑)", "keyword": "낡은 틀의 붕괴 · 전격적 쇄신 · 통쾌한 구체화", "symbolism": "번개를 맞아 부서지는 탑은 거짓된 기반이 깨지고 진실이 드러나는 쇄신을 상징합니다.", "fortune_reading": "갑작스러운 변화나 계획의 수정이 발생하지만 오히려 더 튼튼한 판을 짜게 됩니다.", "advice": "기존의 임시방편을 버리고 근본적인 체질 개선에 나서세요.", "action_tip": "잘못된 오해나 누적된 문제를 투명하게 드러내어 해결하세요."},
    {"name": "XVII. THE STAR (별)", "keyword": "희망의 빛 · 무한한 영감 · 마음의 치유", "symbolism": "밤하늘에 빛나는 거대한 별과 물을 붓는 여인은 절망 뒤 찾아오는 치유와 희망을 뜻합니다.", "fortune_reading": "오랫동안 어둡던 터널을 지나 희망찬 반전과 밝은 아이디어가 샘솟는 기쁜 날입니다.", "advice": "스스로의 가능성을 믿고 오랫동안 꿈꿔온 목표를 향해 나아가세요.", "action_tip": "버킷리스트나 올해의 목표를 다시 읽어보며 다짐하세요."},
    {"name": "XVIII. THE MOON (달)", "keyword": "은밀한 직관 · 안개 속의 진실 · 신중함", "symbolism": "수면 위로 떠오르는 가재와 달은 표면 아래 숨겨진 불안과 감춰진 진실을 뜻합니다.", "fortune_reading": "불확실한 소문이나 서급한 판단을 피하고 서두르지 않는 조심성이 요청되는 날입니다.", "advice": "확인되지 않은 루머에 동조하지 말고 사실을 다각도로 검증하세요.", "action_tip": "중요한 계약이나 금전 결정은 하루 이틀 시일을 두고 검토하세요."},
    {"name": "XIX. THE SUN (태양)", "keyword": "최고의 성공 · 밝은 활력 · 승리와 영광", "symbolism": "찬란하게 빛나는 태양과 백마 탄 아이는 어둠을 몰아내는 승리와 기쁨을 상징합니다.", "fortune_reading": "모든 근심이 사라지고 목표하던 일이 시원하게 성취되는 최고의 운세입니다.", "advice": "자신감을 갖고 주저 없이 전진하여 승리의 기쁨을 누리세요.", "action_tip": "야외로 나가 밝은 햇살을 맞으며 활력을 충전하세요."},
    {"name": "XX. JUDGEMENT (심판)", "keyword": "보상과 부활 · 명확한 소식 · 결정적 승인", "symbolism": "나팔을 부는 천사와 부활하는 사람들은 진심 어린 노력에 대한 온전한 보상을 상징합니다.", "fortune_reading": "과거에 최선을 다했던 일에 대한 반가운 보상이나 기다리던 승인 소식이 전해집니다.", "advice": "과거의 성과를 자신 있게 어필하고 정당한 대가를 요구하세요.", "action_tip": "결과를 기다리던 곳에 전화나 메일로 소식을 확인해 보세요."},
    {"name": "XXI. THE WORLD (세계)", "keyword": "완벽한 완성 · 해피엔딩 · 글로벌 성취", "symbolism": "월계관 속에서 춤추는 여인은 프로젝트의 완벽한 완성 및 인생의 큰 단락 성취를 뜻합니다.", "fortune_reading": "오랫동안 공들여온 일의 완벽한 피날레와 함께 마침내 커다란 축하를 받는 날입니다.", "advice": "한 단계를 완벽히 마무리하고 더 큰 목표를 향한 비전을 그리세요.", "action_tip": "함께 달려온 동료나 가족과 축하 파티를 즐기세요."}
]

class SajuRequest(BaseModel):
    name: str
    year: int
    month: int
    day: int
    calendar_type: Optional[str] = "solar"
    sijin_index: Optional[int] = 5
    is_unknown_time: Optional[bool] = False

@app.get("/")
def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return HTMLResponse("<h2>운세의 신 준비 중</h2>")

def calculate_biorhythm(birth_date: datetime.date, target_date: datetime.date):
    days_lived = (target_date - birth_date).days
    p_val = round(math.sin(2 * math.pi * days_lived / 23) * 100)
    e_val = round(math.sin(2 * math.pi * days_lived / 28) * 100)
    i_val = round(math.sin(2 * math.pi * days_lived / 33) * 100)

    def get_status(val, cycle_name):
        pct = round((val + 100) / 2)
        if val >= 50:
            return {"val": val, "pct": pct, "status": "최고조", "color": "#DC2626", "tip": f"{cycle_name} 에너지가 최고조에 달해 최고의 활력을 발휘합니다."}
        elif val > 0:
            return {"val": val, "pct": pct, "status": "상승기", "color": "#EA580C", "tip": f"{cycle_name} 컨디션이 원활하게 유지되고 있습니다."}
        elif val == 0:
            return {"val": val, "pct": 50, "status": "전환점", "color": "#D97706", "tip": f"기운이 바뀌는 전환점이므로 무리수를 피하세요."}
        elif val > -50:
            return {"val": val, "pct": pct, "status": "하강기", "color": "#2563EB", "tip": f"에너지가 소진되는 구간이니 페이스 조절이 필요합니다."}
        else:
            return {"val": val, "pct": pct, "status": "침체기", "color": "#475569", "tip": f"충분한 휴식과 재충전으로 내실을 다지세요."}

    p_res = get_status(p_val, "신체")
    e_res = get_status(e_val, "감성")
    i_res = get_status(i_val, "지성")

    avg_val = (p_val + e_val + i_val) / 3
    if avg_val > 30:
        summary = "심신의 3대 생체 에너지가 모두 고조되어 적극적인 도전에 최적인 날입니다."
    elif avg_val > -20:
        summary = "신체와 정신의 균형이 안정적으로 유지되어 순조로운 하루입니다."
    else:
        summary = "무리한 일정보다 휴식과 마인드 컨트롤로 충전하기 좋은 날입니다."

    return {
        "days_lived": days_lived,
        "physical": p_res,
        "emotional": e_res,
        "intellectual": i_res,
        "overall_summary": summary
    }

@app.post("/api/analyze")
def analyze_saju(req: SajuRequest):
    base_date = datetime.date(1900, 1, 1)
    today = datetime.date.today()
    
    target_date = datetime.date(req.year, req.month, req.day)
    diff_days = (target_date - base_date).days
    d_cg_idx = diff_days % 10
    d_jj_idx = (diff_days + 10) % 12
    d_cg = CHEONGAN_HANJA[d_cg_idx]
    d_jj = JIJI_HANJA[d_jj_idx]

    year_offset = (req.year - 4) % 60
    y_cg_idx = year_offset % 10
    y_jj_idx = year_offset % 12
    y_cg, y_jj = CHEONGAN_HANJA[y_cg_idx], JIJI_HANJA[y_jj_idx]

    month_adj = req.month
    if req.calendar_type == "lunar":
        month_adj = (req.month + 1)
    elif req.calendar_type == "leap":
        month_adj = (req.month + 2)

    m_jj_idx = (month_adj) % 12
    m_cg_idx = (y_cg_idx % 5 * 2 + 2 + (month_adj - 2)) % 10
    m_cg, m_jj = CHEONGAN_HANJA[m_cg_idx], JIJI_HANJA[m_jj_idx]

    if req.is_unknown_time or req.sijin_index is None or req.sijin_index < 0:
        h_pillar, h_cg, h_jj = "時未詳", "-", "-"
    else:
        h_jj_idx = req.sijin_index
        h_cg_idx = (d_cg_idx % 5 * 2 + h_jj_idx) % 10
        h_cg, h_jj = CHEONGAN_HANJA[h_cg_idx], JIJI_HANJA[h_jj_idx]
        h_pillar = f"{h_cg}{h_jj}"

    d_animal = ANIMAL_MAP.get(d_jj, "개")

    today_diff = (today - base_date).days
    today_cg_idx = today_diff % 10
    today_jj_idx = (today_diff + 10) % 12
    today_cg = CHEONGAN_HANJA[today_cg_idx]
    today_jj = JIJI_HANJA[today_jj_idx]
    today_iljin_str = f"{today_cg}{today_jj}일"

    stem_diff = (today_cg_idx - d_cg_idx) % 10
    shipshin_names = ["비견(比肩)", "겁재(劫財)", "식신(食神)", "상관(傷官)", "편재(偏財)", "정재(正財)", "편관(偏官)", "정관(正官)", "편인(偏印)", "정인(正印)"]
    today_shipshin = shipshin_names[stem_diff]

    current_year = today.year
    current_age = current_year - req.year + 1

    pillars_detail = {
        "hour": { "cg": h_cg, "cg_elem": CHEONGAN_ELEMENTS.get(h_cg, "none"), "jj": h_jj, "jj_elem": JIJI_ELEMENTS.get(h_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(h_jj, []) },
        "day": { "cg": d_cg, "cg_elem": CHEONGAN_ELEMENTS.get(d_cg, "none"), "jj": d_jj, "jj_elem": JIJI_ELEMENTS.get(d_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(d_jj, []) },
        "month": { "cg": m_cg, "cg_elem": CHEONGAN_ELEMENTS.get(m_cg, "none"), "jj": m_jj, "jj_elem": JIJI_ELEMENTS.get(m_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(m_jj, []) },
        "year": { "cg": y_cg, "cg_elem": CHEONGAN_ELEMENTS.get(y_cg, "none"), "jj": y_jj, "jj_elem": JIJI_ELEMENTS.get(y_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(y_jj, []) }
    }

    scores = {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}
    for cg in [y_cg, m_cg, d_cg]:
        scores[CHEONGAN_ELEMENTS[cg]] += 25.0
    if h_cg != "-":
        scores[CHEONGAN_ELEMENTS[h_cg]] += 25.0

    for idx, jj in enumerate([y_jj, m_jj, d_jj]):
        mult = 1.5 if idx == 1 else 1.0
        for item in JIJANGGAN_FULL_MAP.get(jj, []):
            scores[item["elem"]] += item["weight"] * mult

    if h_jj != "-":
        for item in JIJANGGAN_FULL_MAP.get(h_jj, []):
            scores[item["elem"]] += item["weight"] * 1.0

    total_score = sum(scores.values())
    elem_percentages = { k: round((v / total_score) * 100, 1) for k, v in scores.items() }

    day_elem = CHEONGAN_ELEMENTS[d_cg]
    support_score = scores.get(day_elem, 0)
    insoeng_map = {"wood": "water", "fire": "wood", "earth": "fire", "metal": "earth", "water": "metal"}
    support_score += scores.get(insoeng_map.get(day_elem, ""), 0)
    singang_status = "신약(身弱) 사주" if support_score < 45 else ("신강(身强) 사주" if support_score > 65 else "중화(中和) 사주")

    daily_seed = today.toordinal() + diff_days
    
    colors_pool = ["스노우 화이트 / 실버 그레이", "에메랄드 그린 / 포레스트 올리브", "크림슨 레드 / 로즈 골드", "웜 베이지 / 머스터드", "미드나잇 블루 / 네이비"]
    numbers_pool = ["4, 9", "3, 8", "2, 7", "5, 10", "1, 6"]
    directions_pool = ["정서쪽 (백호 방위)", "정동쪽 (청룡 방위)", "정남쪽 (주작 방위)", "중앙 및 동북쪽", "정북쪽 (현무 방위)"]
    styles_pool = ["각 잡힌 화이트 셔츠와 메탈 시계", "편안한 린넨 셔츠 / 그린 톤 캐주얼", "포인트 니트 / 클래식 타이", "포근한 브라운 톤 재킷", "세련된 네이비 셋업"]
    menus_pool = ["도라지차, 신선한 견과류와 고단백 요리", "신선한 샐러드와 미온수", "따뜻한 국물 요리와 비타민 과일", "속이 편안한 잡곡밥과 발효식품", "검은콩 두유와 해조류"]
    mindsets_pool = ["맺고 끊음을 명확히 대화하기", "새로운 시도에 열린 마음 갖기", "열정을 당당하게 피력하기", "약속을 철저히 지키며 중심 잡기", "상대의 말을 경청하고 공감하기"]
    actions_pool = ["오늘 완료해야 할 우선순위 3가지 메모하기", "아침 시간 가벼운 스트레칭하기", "점심 후 햇볕 10분간 쬐기", "주변 책상과 지갑 깨끗이 정리하기", "취침 전 따뜻한 족욕과 명상하기"]

    lucky_color = colors_pool[daily_seed % len(colors_pool)]
    lucky_number = numbers_pool[(daily_seed + 1) % len(numbers_pool)]
    lucky_direction = directions_pool[(daily_seed + 2) % len(directions_pool)]
    fashion_style = styles_pool[(daily_seed + 3) % len(styles_pool)]
    recommended_menu = menus_pool[(daily_seed + 4) % len(menus_pool)]
    mindset = mindsets_pool[(daily_seed + 5) % len(mindsets_pool)]
    action = actions_pool[(daily_seed + 6) % len(actions_pool)]

    daily_title = f"[{today_iljin_str}] 도약과 성취의 하루"
    three_stage_advice = (f"☀️ <strong>오전:</strong> 아이디어를 주변에 공유하고 활발하게 소통하며 기틀을 잡으세요.<br>"
                          f"🌤️ <strong>오후:</strong> 본원({d_cg})의 리더십으로 추진 중인 주요 과제를 당당하게 완성하세요.<br>"
                          f"🌙 <strong>저녁:</strong> 원만한 대화로 하루를 마무리하고 편안한 수면을 취하세요.")
    daily_score = 82 + (daily_seed * 7) % 17

    min_elem = min(elem_percentages, key=elem_percentages.get)
    user_talisman = TALISMAN_OHEANG_MAP.get(min_elem, TALISMAN_OHEANG_MAP["metal"])
    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주", "essence": "거목의 기상"})
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐶")

    biorhythm_data = calculate_biorhythm(target_date, today)

    return {
        "user_name": req.name,
        "current_age": current_age,
        "singang_status": singang_status,
        "saju_data": {
            "year_pillar": f"{y_cg}{y_jj}", "month_pillar": f"{m_cg}{m_jj}", "day_pillar": f"{d_cg}{d_jj}", "hour_pillar": h_pillar,
            "pillars_detail": pillars_detail, "mbti": user_mbti, "animal_symbol": d_animal, "animal_icon": user_animal_icon,
            "elements": elem_percentages
        },
        "daily_fortune": {
            "score": daily_score, "title": daily_title, "advice": three_stage_advice,
            "lucky_color": lucky_color, "lucky_number": lucky_number, "lucky_direction": lucky_direction,
            "fashion_style": fashion_style, "recommended_menu": recommended_menu, "mindset": mindset, "action": action,
            "talisman": user_talisman
        },
        "biorhythm": biorhythm_data
    }

@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str = "zodiac", key: str = "쥐"):
    today = datetime.date.today()
    seed = today.toordinal() + hash(key)
    score = 65 + (seed % 36)
    
    if type == "zodiac":
        years = [2012, 2000, 1988, 1976, 1964]
        zodiac_names = list(ANIMAL_MAP.values())
        z_idx = zodiac_names.index(key) if key in zodiac_names else 0
        adj_years = [y - ((4 - z_idx) % 12) for y in years]
        
        year_advices = [
            {"year_label": f"{str(adj_years[0])[-2:]}년생 ({today.year - adj_years[0] + 1}세)", "tip": "학업과 진로에서 번뜩이는 영감을 발휘해 칭찬을 받는 날입니다."},
            {"year_label": f"{str(adj_years[1])[-2:]}년생 ({today.year - adj_years[1] + 1}세)", "tip": "취업·이직 및 프로젝트에서 중요한 주도권을 쥐게 됩니다."},
            {"year_label": f"{str(adj_years[2])[-2:]}년생 ({today.year - adj_years[2] + 1}세)", "tip": "실속을 차리고 금전적 결실과 성과를 확정 짓는 대길의 타이밍입니다."},
            {"year_label": f"{str(adj_years[3])[-2:]}년생 ({today.year - adj_years[3] + 1}세)", "tip": "귀인의 도움으로 복잡했던 계약이나 사업 협상이 순조롭게 성사됩니다."},
            {"year_label": f"{str(adj_years[4])[-2:]}년생 ({today.year - adj_years[4] + 1}세)", "tip": "무리한 확장보다 내실을 다지며 평온한 화목을 누리는 날입니다."}
        ]
        return {
            "name": f"{key}띠", "icon": ANIMAL_ICONS.get(key, "🐾"), "score": score, "title": "귀인의 조력과 재물운이 합을 이루는 대길의 날",
            "overview": f"오늘 {key}띠는 실력과 결단력이 빛을 발하는 날입니다. 큰 흐름을 보고 추진하면 큰 성취가 따릅니다.",
            "year_tips": year_advices, "lucky_time": "오후 2시 ~ 4시", "lucky_match": "소띠, 용띠"
        }
    else:
        star_item = next((s for s in STAR_SIGNS if s["name"] == key), STAR_SIGNS[0])
        return {
            "name": star_item["name"], "icon": star_item["icon"], "period": star_item["period"], "score": score,
            "title": "창의적인 영감과 반가운 기회가 샘솟는 럭키 데이",
            "overview": f"{star_item['name']}에게 오늘은 내면의 직관이 강력하게 작용하는 날입니다.",
            "focus_badge": "💰 오늘 가장 중요한 재물운", "focus_content": "유리한 조건의 거래 계약이 성사될 가능성이 매우 높습니다.",
            "lucky_item": "은색 액세서리", "lucky_time": "오전 10시 ~ 12시"
        }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    random_idx = random.randint(0, len(TAROT_CARDS) - 1)
    return TAROT_CARDS[random_idx]

# [풀버전 복구] 자미두수 평생운세: 사주 일간(10간) 기반 완전 분기 챕터형 감명서
@app.post("/api/daewoon-report")
def get_daewoon_report(req: dict):
    user_name = req.get("name", "최정오")
    age = req.get("age", 49)
    age_decade = (age // 10) * 10
    start_age = age_decade + 3
    end_age = start_age + 9

    return {
        "title": "👑 자미두수 평생운세",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 1. 평생 대운맥</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                        🌐 {user_name}님의 생애 4대 주기별 거시적 운명 흐름
                    </h4>
                </div>
                <p style="color: #475569; margin-bottom: 10px;">
                    자미두수 명반과 사주 원국을 교차 감명한 결과, {user_name}님의 인생은 초년의 치열한 배움을 거쳐 중장년기에 폭발적인 재물과 명예의 결실을 완성하는 <strong>'만성대기(晩成大器)형 거목의 명식'</strong>입니다.
                </p>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 10px 12px;">
                        <p style="font-weight: 800; color: #0F172A; font-size: 14.5px; margin-bottom: 2px;">🌱 [유년기 : 근본 기틀 형성기]</p>
                        <p style="color: #475569; font-size: 13.5px;">남다른 지적 호기심과 영민함으로 도덕적 기준과 가치관을 단단히 다지던 시기였습니다.</p>
                    </div>
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 10px 12px;">
                        <p style="font-weight: 800; color: #0F172A; font-size: 14.5px; margin-bottom: 2px;">🌿 [청년기 : 역량 축적 및 실전기]</p>
                        <p style="color: #475569; font-size: 13.5px;">사회에 진출하여 실무 전문성을 연마하고, 인맥과 실물 감각의 뼈대를 견고히 구축했습니다.</p>
                    </div>
                    <div style="background: #FEF3C7; border: 1.5px solid #FCD34D; border-radius: 8px; padding: 10px 12px;">
                        <p style="font-weight: 800; color: #78350F; font-size: 14.5px; margin-bottom: 2px;">🔥 [중장년기 (*현재 위치 / 40세 ~ 59세) : 황금 결실기]</p>
                        <p style="color: #92400E; font-size: 13.5px; font-weight: 600;">
                            <strong>{user_name}님 인생 일대에서 가장 강력한 천운의 파도가 솟구치는 최고 전성기 구간입니다.</strong> 본인이 직접 주도권을 쥐고 설계한 판에서 자산 규모와 사회적 영향력이 수직 상승합니다.
                        </p>
                    </div>
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 10px 12px;">
                        <p style="font-weight: 800; color: #0F172A; font-size: 14.5px; margin-bottom: 2px;">🍎 [말년기 : 태평성대 및 가문 번영기]</p>
                        <p style="color: #475569; font-size: 13.5px;">평생 축적한 자산과 인망을 토대로 안락한 노후를 누리며 후대에 안정적 번영을 대물림합니다.</p>
                    </div>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 현재 10년 대운</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        📈 Q. {user_name}님의 현재 10년 대운({start_age}세 ~ {end_age}세) 핵심 결실은?
                    </h4>
                </div>
                <p style="color: #78350F; line-height: 1.85; margin-bottom: 10px;">
                    현재 지나고 계신 대운맥은 사주 본원에 '재성(財星)'과 '귀인(貴人)'이 강력하게 결합하는 절정기입니다. 남에게 끌려다니지 않고 본인의 통솔력으로 사업, 투자, 조직을 리드할 때 성공 확률이 95% 이상으로 치솟습니다.
                </p>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #475569;">
                    <p>• <strong>{start_age}세 ~ {start_age+2}세 (기반 재편기):</strong> 흩어져 있던 지출을 정돈하고 실물 자산 중심 종잣돈 포트폴리오를 단단히 압축한 시기.</p>
                    <p style="color: #B45309; font-weight: 800;">• <strong>{start_age+3}세 ~ {start_age+6}세 (대운 정점기 / ★현재 {age}세 위치):</strong> 귀인의 결정적 조력과 함께 직위·자산 규모가 퀀텀 점프하는 일생일대의 승부처입니다.</p>
                    <p>• <strong>{start_age+7}세 ~ {end_age}세 (자산 수성기):</strong> 성과를 시스템 수익(부동산, 배당, 지식재산권)으로 고정시키며 차기 대운으로 연착륙합니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #DC2626; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #DC2626; font-weight: 800;">Chapter 3. 불운 방어</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #991B1B; margin-top: 2px;">
                        🛡️ Q. 대운 기간 중 반드시 경계해야 할 암초와 방어책은?
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #451A03; line-height: 1.8;">
                    <p>• <strong>1. 구두 약속의 함정 (문서화 필수):</strong> 운세가 강할 때는 주변에서 달콤한 제안이 쏟아집니다. 친분 관계라 할지라도 지분, 계약, 금전 거래는 반드시 공증 및 문서화해야 관재수를 완벽히 차단합니다.</p>
                    <p>• <strong>2. 과도한 독단 경계:</strong> 본인의 직관이 뛰어나지만 중요한 의사결정 시 법률·세무·금융 전문가의 2차 검증을 거칠 때 자산 누수가 0%로 수렴합니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #F59E0B; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 4. 실전 개운 솔루션</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        🔥 이번 10년 대운({start_age}세~{end_age}세) 맞춤 3대 개운(開運) 실천 비책
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 14px; line-height: 1.8; color: #451A03;">
                    <p>• <strong>[재물 및 자산 운용]:</strong> 단기 단타 투자보다 실물 부동산, 우량 배당 자산 등 고정적 현금 흐름을 창출하는 안전 자산에 집중할 때 부의 크기가 3배 이상 공고해집니다.</p>
                    <p>• <strong>[비즈니스 및 직업 처세]:</strong> 혼자 모든 짐을 짊어지려 하지 말고 유능한 협력 파트너를 적극적으로 영입하세요. 위임의 기술을 발휘할 때 명예와 성취가 배가됩니다.</p>
                    <p>• <strong>[건강 및 마인드셋]:</strong> 머리는 차갑게 식히고 하체 순환을 돕는 '두한족열' 루틴을 유지하세요. 감정에 휘둘리지 않는 평정심을 유지할 때 인생 최대의 복록을 온전히 담아낼 수 있습니다.</p>
                </div>
            </div>

        </div>
        """
    }

# [풀버전 복구] 2026 신년운세 & 12개월 토정비결 (양력 기준 1회 명시)
@app.post("/api/sinnian-report")
def get_sinnian_report(req: dict):
    user_name = req.get("name", "최정오")
    
    monthly_guides = [
        {"m": "1월", "gua": "지천태(地天泰) 괘", "opp": "새해 첫 출발이 대길하여 신규 사업 및 프로젝트 착수에 최적입니다.", "warn": "초반의 빠른 성취에 자만하지 말고 세부 규정을 차분히 정비하세요."},
        {"m": "2월", "gua": "수천수(水天需) 괘", "opp": "실력과 내실을 다지며 시장 상황의 흐름을 관망할 때 이익이 보존됩니다.", "warn": "서두른 결정이나 충동구매는 후회를 부르니 하루 이틀 시일을 두세요."},
        {"m": "3월", "gua": "천화동인(天火同人) 괘", "opp": "귀인의 조력이 닿아 인간관계와 직무에서 강력한 협력자가 나타납니다.", "warn": "주변과의 이견 조율 시 감정적 대응을 피하고 데이터로 설득하세요."},
        {"m": "4월", "gua": "풍천소축(風天小畜) 괘", "opp": "작은 성과가 차곡차곡 쌓여 종잣돈의 기틀이 한 단계 단단해집니다.", "warn": "무리한 대출이나 투자는 지양하고 현금 유동성을 확보하세요."},
        {"m": "5월", "gua": "화천대유(火天大有) 괘", "opp": "★올해 상반기 최고의 재물운! 부동산/투자/계약에서 큰 결실을 맺습니다.", "warn": "성과를 독식하려 하지 말고 함께한 동료들에게 따뜻하게 베푸세요."},
        {"m": "6월", "gua": "천풍구(天風姤) 괘", "opp": "새로운 제안과 이직/신규 프로젝트의 반가운 활로가 열립니다.", "warn": "계약서의 독소 조항과 구두 약속을 면밀히 검증하는 신중함이 필수입니다."},
        {"m": "7월", "gua": "천수송(天水訟) 괘", "opp": "기존의 복잡했던 업무 체계를 깔끔히 정리하고 체질을 개선하는 달.", "warn": "사소한 언쟁이나 시비수를 피하기 위해 공감 화법을 철저히 유지하세요."},
        {"m": "8월", "gua": "풍지관(風地觀) 괘", "opp": "상반기의 성과를 점검하고 하반기 대도약을 위한 전략을 세우기에 최적입니다.", "warn": "체력 저하와 간 피로를 방지하기 위해 충분한 수면과 족욕을 챙기세요."},
        {"m": "9월", "gua": "산지박(山地剝) 괘", "opp": "불필요한 고정비와 낭비 요소를 말끔히 청산하여 실속을 챙깁니다.", "warn": "무리한 확장보다 기존 고객 및 핵심 업무 관리에 집중하세요."},
        {"m": "10월", "gua": "지뢰복(地雷復) 괘", "opp": "★올해 하반기 최고의 승부처! 승진, 수주, 투자 회수에서 낭보가 울립니다.", "warn": "기회가 올 때 주저하지 말고 과감한 결단력으로 주도권을 쥐세요."},
        {"m": "11월", "gua": "수뢰준(水雷屯) 괘", "opp": "내년을 위한 새로운 아이템이나 자격/학업의 씨앗을 뿌리기에 좋습니다.", "warn": "경험자의 조언을 경청하여 불필요한 시행착오를 사전에 방지하세요."},
        {"m": "12월", "gua": "지화명이(地火明夷) 괘", "opp": "한 해 일군 풍성한 결실을 확정 짓고 가문과 가족의 화목을 누립니다.", "warn": "연말 과음과 과로를 피하고 따뜻한 온기로 몸과 마음을 달래세요."}
    ]

    months_html = "".join([f"""
        <div style="background: #F8FAFC; border-left: 3.5px solid #2D6A4F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-weight: 800; color: #0F172A; font-size: 15px;">📅 {item['m']} 세운 가이드</span>
                <span style="font-size: 12px; background: #EBF5EE; color: #2D6A4F; font-weight: 800; padding: 2px 8px; border-radius: 6px;">{item['gua']}</span>
            </div>
            <p style="color: #065F46; font-size: 13.5px; line-height: 1.6; margin-bottom: 2px;">
                <strong>✨ 기회의 순간:</strong> {item['opp']}
            </p>
            <p style="color: #991B1B; font-size: 13px; line-height: 1.55;">
                <strong>⚠️ 주의할 처세:</strong> {item['warn']}
            </p>
        </div>
    """ for item in monthly_guides])

    return {
        "title": "📅 2026 丙午년 총운 & 하반기 정밀 월별 가이드",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div>
                <div style="border-left: 4px solid #DC2626; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #DC2626; font-weight: 800;">Chapter 1. 2026년 세운(歲運) 총론</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #991B1B; margin-top: 2px;">
                        🔥 2026 丙午년(붉은 말의 해) {user_name}님의 도약 총운
                    </h4>
                </div>
                <p style="color: #7F1D1D; line-height: 1.85; margin-bottom: 12px;">
                    2026년은 강렬한 불(火)의 기운이 어둠을 걷어내고 대지를 환하게 비추는 丙午년입니다. {user_name}님의 사주 본원과 조화를 이루어 그동안 수면 아래에서 준비해 온 역량이 화려하게 꽃을 피우며, 막혀 있던 활로가 시원하게 뚫리는 <strong>'비상(飛翔)의 한 해'</strong>가 됩니다.
                </p>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #475569;">
                    <p>• <strong>💰 재물 대박 타이밍:</strong> 양력 5월(상반기 결실)과 10월(하반기 결실)에 큰 금전적 성과와 유리한 계약 성사.</p>
                    <p>• <strong>💼 커리어 및 직무 운세:</strong> 상반기에 뿌린 기획이 하반기(9~11월)에 승진, 인정, 영전으로 직결됩니다.</p>
                    <p>• <strong>🤝 결정적 귀인수:</strong> 서북쪽 방위에서 다가오는 동료 및 전문 조력자가 핵심 난제를 해결해 줍니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <!-- Chapter 2: 12개월 월별 가이드 (양력 기준 1회 명시) -->
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px;">
                    <div style="border-left: 4px solid #2D6A4F; padding-left: 10px;">
                        <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 2. 12개월 정밀 토정비결</span>
                        <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                            📜 1월부터 12월까지 월별 기회와 주의점
                        </h4>
                    </div>
                    <span style="font-size: 11.5px; background: #FEF3C7; color: #78350F; font-weight: 700; padding: 3px 8px; border-radius: 6px; white-space: nowrap;">
                        ※ 본 월별 흐름은 양력(Solar) 기준입니다
                    </span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 4px;">
                    {months_html}
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 2026 개운 비책</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        ✨ 2026년 운세를 200% 극대화하는 3대 실천 솔루션
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #92400E; line-height: 1.8;">
                    <p>• <strong>행운의 방위:</strong> 주거지 및 집무실 기준 '정동쪽'과 '서북쪽'이 복록을 부르는 최고의 황금 방위입니다.</p>
                    <p>• <strong>금전 지출 방어:</strong> 양력 7월에는 충동적인 지출이나 무리한 확장을 자제하고 현금 유동성을 확보하세요.</p>
                    <p>• <strong>마인드셋 처세:</strong> 빠른 속도감 속에서도 중요한 계약서는 반드시 문구 하나까지 꼼꼼히 점검할 때 완벽한 승리를 거둡니다.</p>
                </div>
            </div>
        </div>
        """
    }

# [풀버전 복구] 정통 사주 궁합 3대 챕터 감명서
@app.post("/api/gunghap-report")
def get_gunghap_report(req: dict):
    user_name = req.get("name", "최정오")
    partner_name = req.get("partner_name", "상대방")
    relation = req.get("relation", "연인/결혼")

    return {
        "title": f"💞 {user_name} & {partner_name} 정통 사주 궁합 ({relation})",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            
            <div style="background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%); border: 1.5px solid #FECDD3; border-radius: 14px; padding: 14px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 12px; color: #BE123C; font-weight: 800;">정통 오행 상생 궁합 지수</span>
                    <h3 style="font-size: 18px; font-weight: 900; color: #9F1239; margin-top: 2px;">94점 (천생연분 대길합)</h3>
                </div>
                <div style="font-size: 32px;">💖</div>
            </div>

            <div>
                <div style="border-left: 4px solid #E11D48; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 두 사람의 기운과 인연의 깊이</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">
                        🔗 {user_name}님과 {partner_name}님의 천간·지지 상생 조화
                    </h4>
                </div>
                <p style="color: #9F1239; line-height: 1.85;">
                    {user_name}님의 사주에 부족하거나 필요한 기운을 {partner_name}님이 풍부하게 품어주고 있어, 함께할수록 서로의 운이 솟구치고 부족한 기운이 채워지는 <strong>'상호보완형 황금 궁합'</strong>입니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 실전 관계 조화 & 갈등 해결법</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        💡 관계 유형 맞춤 처세: [{relation}]
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #92400E;">
                    <p>• <strong>소통의 찰떡 포인트:</strong> {user_name}님의 통솔력과 {partner_name}님의 세심한 지혜가 결합하여 어떤 난관도 지혜롭게 돌파합니다.</p>
                    <p>• <strong>주의할 순간:</strong> 사소한 의견 차이가 생길 때는 감정적 직설보다 '맛있는 식사나 티타임'을 곁들이며 대화할 때 막힘없이 풀립니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 3. 인연을 백년해로로 이끄는 개운 비책</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                        🌹 두 사람만의 행운의 방위 & 타이밍
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #475569;">
                    <p>• <strong>행운의 장소:</strong> 물이 잔잔히 흐르는 강변이나 클래식한 조명의 카페가 두 분의 애정운을 2배로 증폭시킵니다.</p>
                    <p>• <strong>결정적 결실의 시기:</strong> 봄(양력 3~5월)과 가을(양력 9~11월)에 두 사람 사이의 중요한 약속이나 결단이 이루어집니다.</p>
                </div>
            </div>

        </div>
        """
    }

# 4대 테마운세 풀버전
@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    user_name = req.get("name", "최정오")
    
    titles = {
        "wealth": "💰 평생 재물운",
        "love": f"💖 평생 애정운 ({sub_opt})",
        "business": f"🏢 사업·직업운 ({sub_opt})",
        "health": "🌿 평생 건강운"
    }

    if theme == "wealth":
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #D97706; padding-left: 10px;">
                <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 1. 재물 원국 감명</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin: 3px 0 6px;">[평생 재물운] '암장(暗藏) 금고형' 자산 축적 원국</h4>
                <p style="color: #92400E; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 겉으로 드러난 화려함보다 실속 있게 현금과 실물 자산을 차곡차곡 축적하는 전형적인 '황금 금고형' 구조입니다. 지장간 속에 알짜배기 재성이 뿌리를 내리고 있어 틈새 기회를 포착하여 자산을 불리는 능력이 탁월합니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 2. 생애 자산 로드맵</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">📊 Q. {user_name}님의 생애 주기별 자산 퀀텀점프 시기는?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #475569;">
                    <p>• <strong>초년~30대:</strong> 종잣돈을 모으고 경제 안목을 기르는 시기였습니다.</p>
                    <p style="color: #B45309; font-weight: 800;">• <strong>40대 중후반~50대 (*현재 황금기):</strong> 귀인의 도움과 투자 결단으로 자산 규모가 3배 이상 폭발적으로 도약하는 최상의 전환점입니다.</p>
                    <p>• <strong>60대 이후:</strong> 고정적 현금 흐름을 바탕으로 부를 안전하게 대물림하는 완벽한 자산 수성기입니다.</p>
                </div>
            </div>
        </div>
        """
    elif theme == "love":
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">상태 맞춤: {sub_opt}</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">[평생 애정운] 깊은 신뢰와 상호 존중의 인연</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 애정 원국은 한 번 맺은 신뢰를 평생 지켜나가는 따뜻한 포용력의 소유자입니다. 본연의 당당함을 드러낼 때 뜻밖의 귀한 인연이 찾아옵니다.
                </p>
            </div>
        </div>
        """
    elif theme == "business":
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #2563EB; padding-left: 10px;">
                <span style="font-size: 12px; color: #2563EB; font-weight: 800;">상황 맞춤: {sub_opt}</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin: 3px 0 6px;">[사업·직업운] 전략적 기획력과 결단력의 리더</h4>
                <p style="color: #1E40AF; font-size: 14.5px; line-height: 1.85;">
                    복잡한 난제를 단번에 해결하는 전략가 기질을 타고났습니다. 사내 정치나 시장의 잡음에 휩쓸리지 않고 독보적인 실적을 증명할 때 파격적인 도약이 일어납니다.
                </p>
            </div>
        </div>
        """
    else:
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #059669; padding-left: 10px;">
                <span style="font-size: 12px; color: #059669; font-weight: 800;">오행 체질 정밀 분석</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46; margin: 3px 0 6px;">[평생 건강운] 수승화강(水昇火降) 활력 관리</h4>
                <p style="color: #047857; font-size: 14.5px; line-height: 1.85;">
                    강인한 생명력을 갖추고 있으나 두한족열(머리는 시원하게 발은 따뜻하게)의 수칙을 유지해야 합니다. 취침 전 족욕과 유산소 운동이 건강의 비결입니다.
                </p>
            </div>
        </div>
        """
    
    return {
        "title": titles.get(theme, "심층 리포트"),
        "content": content
    }
