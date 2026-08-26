import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import random

app = FastAPI(title="운세의 신 API", version="19.0.0")

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
    "甲": {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주"},
    "乙": {"mbti": "재기발랄한 활동가 (ENFP형)", "desc": "유연한 적응력과 풍부한 친화력으로 사람의 마음을 얻는 사주"},
    "丙": {"mbti": "자유로운 영혼의 연예인 (ESFP형)", "desc": "태양 같은 열정과 밝은 에너지로 주변을 환하게 밝히는 사주"},
    "丁": {"mbti": "용의주도한 전략가 (ENTJ형)", "desc": "치밀한 기획력과 은근한 카리스마로 목표를 완벽히 쟁취하는 사주"},
    "戊": {"mbti": "청렴결백한 논리주의자 (ISTJ형)", "desc": "묵직한 신뢰감과 흔들리지 않는 원칙으로 책임을 다하는 사주"},
    "己": {"mbti": "세심한 수호자 (ISFJ형)", "desc": "비옥한 땅처럼 주변을 묵묵히 품어주고 실속을 챙기는 사주"},
    "庚": {"mbti": "엄격한 관리자 (ESTJ형)", "desc": "의리와 결단력으로 무장하여 난관을 돌파하는 단호한 실행가 사주"},
    "辛": {"mbti": "용의주도한 완벽주의자 (INTJ형)", "desc": "보석처럼 예리한 감각과 높은 기준을 지닌 냉철한 분석가 사주"},
    "壬": {"mbti": "뜨거운 논쟁을 즐기는 변론가 (ENTP형)", "desc": "바다처럼 넓은 지혜와 임기응변으로 판을 주도하는 아이디어 뱅크 사주"},
    "癸": {"mbti": "선의의 옹호자 (INFJ형)", "desc": "맑은 이슬비처럼 깊은 직관과 통찰력으로 본질을 꿰뚫는 사색가 사주"}
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
    "wood": {"type": "wood", "title": "사업대성부 (事業亨通符)", "power": "추진력 강화 · 사업 번창 · 승진운", "desc": "사주에 부족한 木(성장과 개척)의 활력을 불어넣어 막힌 활로를 뚫고 사업과 직무에서 강력한 주도권을 쥐게 하는 비급 부적입니다."},
    "fire": {"type": "fire", "title": "소원성취부 (心想事成符)", "power": "열정 회복 · 명예 상승 · 소원 성취", "desc": "사주에 부족한 火(열정과 확산)의 빛을 밝혀 어둠을 몰아내고 오랫동안 염원하던 소망을 일사천리로 성취시키는 전통 부적입니다."},
    "earth": {"type": "earth", "title": "금고수호부 (金庫安穩符)", "power": "자산 방어 · 누수 차단 · 재물 안착", "desc": "사주에 부족한 土(포용과 저장)의 단단한 대지를 마련하여 헛돈 지출을 막고 평생의 자산을 굳건하게 지켜주는 금고 수호 부적입니다."},
    "metal": {"type": "metal", "title": "재물만복부 (萬福大吉符)", "power": "재물 증식 · 금전운 대통 · 투자 대박", "desc": "사주에 부족한 金(결단과 결실)의 황금 기운을 채워 사방에서 금전과 복록이 샘솟듯 쏟아지게 하는 전통 경면주사 수제 부적입니다."},
    "water": {"type": "water", "title": "천생화합부 (萬事和合符)", "power": "인연 결속 · 애정 화합 · 인간관계 개선", "desc": "사주에 부족한 水(지혜와 융합)의 부드러운 유대감을 채워 엇갈린 인연을 묶어주고 귀인의 조력을 이끌어내는 화합 비급 부적입니다."}
}

TAROT_CARDS = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작 · 순수한 열정 · 무한한 잠재력", "symbolism": "절벽 끝에 선 순수한 영혼으로 관습에 얽매이지 않는 새로운 여정의 출발을 상징합니다.", "fortune_reading": "오랫동안 머뭇거리던 일의 시작 단추를 꿰기에 최적의 날입니다. 직관을 따를 때 예상 밖의 통로가 열립니다.", "advice": "새로운 제안에 열린 마음을 가지되 발걸음은 가볍고 시선은 신중히 유지하세요.", "action_tip": "떠오르는 아이디어를 즉시 메모하고 먼저 연락을 건네보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 역량 · 완벽한 주도권 · 실력 발휘", "symbolism": "머리 위의 무한대(∞) 기호와 제단 위의 4대 원소는 모든 도구를 통제하는 지혜를 뜻합니다.", "fortune_reading": "지식과 언변, 전문 기술이 빛을 발하는 날입니다. 당당한 태도로 판을 리드하기에 최적입니다.", "advice": "미팅이나 보고에서 주도적으로 의견을 제시하고 실력을 드러내세요.", "action_tip": "중요한 대화에서 본인의 핵심 주장을 명확하게 피력하세요."},
    {"name": "II. THE HIGH PRIESTESS (여사제)", "keyword": "깊은 통찰 · 직관과 혜안 · 침묵의 지혜", "symbolism": "흑과 백의 기둥 사이에 앉아 본질적 진실과 영적인 직관을 상징합니다.", "fortune_reading": "겉으로 드러난 말보다 상대방의 숨은 의도나 상황의 이면을 꿰뚫어 보는 혜안이 극대화됩니다.", "advice": "성급하게 반응하기보다는 차분히 경청하고 심사숙고하세요.", "action_tip": "조용한 장소에서 생각을 차분히 정리하는 시간을 가지세요."},
    {"name": "III. THE EMPRESS (여황제)", "keyword": "풍요와 번영 · 따뜻한 포용 · 결실의 기쁨", "symbolism": "풍성한 곡식과 석류 장식은 모성적 사랑과 물질적·정신적 풍요로움을 상징합니다.", "fortune_reading": "그동안 공들여 준비한 일에서 만족스러운 성과와 금전적 보상이 주어지는 날입니다.", "advice": "주변 사람들에게 넉넉한 마음으로 베풀면 더 큰 행운이 돌아옵니다.", "action_tip": "맛있는 식사를 대접하거나 가까운 이에게 감사 인사를 전하세요."},
    {"name": "IV. THE EMPEROR (황제)", "keyword": "확고한 권위 · 강력한 통솔 · 안정된 기반", "symbolism": "단단한 석조 왕좌는 흔들리지 않는 통치력과 엄격한 질서, 조직의 굳건함을 뜻합니다.", "fortune_reading": "자신의 영역에서 주도권을 확립하고 책임감 있게 프로젝트를 완수하기에 좋은 날입니다.", "advice": "원칙과 약속을 철저히 지키며 리더십을 발휘하세요.", "action_tip": "흐트러진 계획을 점검하고 체계적인 규율을 세우세요."},
    {"name": "V. THE HIEROPHANT (교황)", "keyword": "신뢰와 조언 · 전통적 가치 · 귀인의 도우심", "symbolism": "교황의 삼중관과 두 명의 사제는 귀인의 정통성 있는 가르침과 신뢰를 상징합니다.", "fortune_reading": "스승이나 연장자, 유력 인사로부터 결정적인 귀인의 조언을 받아 난관을 해결하는 날입니다.", "advice": "독단적인 행동을 피하고 경험자의 조언을 겸손하게 받아들이세요.", "action_tip": "존경하는 멘토나 상급자에게 안부 연락을 건네보세요."},
    {"name": "VI. THE LOVERS (연인)", "keyword": "조화로운 결합 · 진정한 공감 · 올바른 선택", "symbolism": "천사의 축복 아래 선 남녀는 영혼의 교감과 중요한 인생의 선택을 상징합니다.", "fortune_reading": "인간관계와 애정 전선에 따뜻한 훈풍이 불고 협력 파트너와의 호흡이 완벽히 맞습니다.", "advice": "계산적인 이득보다는 마음의 진정성을 바탕으로 대화하세요.", "action_tip": "소중한 사람과 티타임을 가지며 솔직한 마음을 나누세요."},
    {"name": "VII. THE CHARIOT (전차)", "keyword": "거침없는 돌파 · 승리의 질주 · 강한 의지", "symbolism": "흑과 백의 스핑크스를 이끄는 젊은 기사는 이성과 감성을 통제하여 승리하는 의지를 뜻합니다.", "fortune_reading": "주저하지 않고 강력하게 밀어붙일 때 목표를 수월하게 쟁취할 수 있는 대길의 하루입니다.", "advice": "목표에 집중하고 사소한 장애물에 연연하지 마세요.", "action_tip": "오랫동안 미뤄왔던 단호한 결정을 오늘 실행에 옮기세요."},
    {"name": "VIII. STRENGTH (힘)", "keyword": "내면의 인내 · 부드러운 통제 · 카리스마", "symbolism": "사자를 부드럽게 다스리는 여인은 강압적인 힘이 아닌 내면의 온화한 카리스마를 상징합니다.", "fortune_reading": "감정을 자제하고 부드럽지만 단단한 태도로 임할 때 유능한 상대도 내 편으로 만들 수 있습니다.", "advice": "화가 나거나 감정적일 때일수록 미소와 유연함으로 상대하세요.", "action_tip": "깊은 숨을 세 번 쉬며 너그러운 마음을 유지하세요."},
    {"name": "IX. THE HERMIT (은둔자)", "keyword": "깊은 성찰 · 탐구와 지혜 · 내면의 빛", "symbolism": "등불을 들고 눈 덮인 산을 오르는 노인은 깊은 지혜와 진리 탐구를 상징합니다.", "fortune_reading": "외부의 번잡함에서 벗어나 혼자만의 시간에 몰입할 때 중요한 혜안을 얻게 됩니다.", "advice": "남들의 시선에 신경 쓰지 말고 자신의 내면 소리에 집중하세요.", "action_tip": "스마트폰을 잠시 내려놓고 30분간 조용히 독서나 명상을 즐기세요."},
    {"name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)", "keyword": "행운의 반전 · 결정적 기회 · 운명의 전환점", "symbolism": "영원히 회전하는 수레바퀴는 상승과 하강, 기회의 순간을 뜻합니다.", "fortune_reading": "정체되었던 상황이 뜻밖의 계기를 통해 긍정적인 방향으로 급물살을 타게 됩니다.", "advice": "흐름에 맞서지 말고 자연스럽게 변화를 수용하여 기회를 잡으세요.", "action_tip": "오랜 지인에게 온 연락이나 새로운 제안을 긍정적으로 검토하세요."},
    {"name": "XI. JUSTICE (정의)", "keyword": "명확한 판단 · 공정한 균형 · 합리적 계약", "symbolism": "저울과 칼을 든 여신은 감정에 휘둘리지 않는 공정한 판단과 사필귀정을 상징합니다.", "fortune_reading": "공정하고 합리적인 판단이 빛을 발하며 문서 및 계약 건에서 이익이 확보됩니다.", "advice": "사사로운 감정을 배제하고 사실과 데이터에 근거해 결정하세요.", "action_tip": "계약서나 중요한 서류의 조항을 면밀히 재검토하세요."},
    {"name": "XII. THE HANGED MAN (매달린 사람)", "keyword": "발상의 전환 · 인고의 결실 · 새로운 시각", "symbolism": "나무에 거꾸로 매달린 남자의 후광은 희생을 통해 깨달음을 얻는 신성한 시각을 뜻합니다.", "fortune_reading": "잠시 상황이 정체된 것처럼 보이지만 발상을 뒤집을 때 놀라운 해결책이 찾아옵니다.", "advice": "서두르지 말고 현재 상태를 조용히 관조하며 때를 기다리세요.", "action_tip": "기존 방식과 반대되는 새로운 아이디어를 검토해 보세요."},
    {"name": "XIII. DEATH (죽음)", "keyword": "새로운 변혁 · 과거와의 작별 · 불운의 끝", "symbolism": "깃발을 든 기사는 오래된 유통기한이 끝난 상황을 청산하고 새 단계를 시작함을 뜻합니다.", "fortune_reading": "나를 갉아먹던 나쁜 습관이나 원치 않는 상황이 마침내 청산되고 새 출발이 시작됩니다.", "advice": "과거의 미련을 미련 없이 훌훌 털어버리고 새판을 짜세요.", "action_tip": "사용하지 않는 안 쓰는 물건이나 단톡방을 깔끔히 정리하세요."},
    {"name": "XIV. TEMPERANCE (절제)", "keyword": "감정의 조화 · 유연한 중용 · 차분한 융합", "symbolism": "두 컵에 물을 서로 개어 섞는 천사는 이성과 감성, 서로 다른 기운의 완벽한 조화를 뜻합니다.", "fortune_reading": "치우침 없이 조화로운 태도를 유지할 때 원만한 대인관계와 마음의 평화가 유지됩니다.", "advice": "극단적인 선택을 피하고 적절한 타협점을 모색하세요.", "action_tip": "자극적인 음식을 피하고 미온수를 충분히 마시며 속을 달래세요."},
    {"name": "XV. THE DEVIL (악마)", "keyword": "강력한 유혹 · 과감한 집착 · 치명적 매력", "symbolism": "사슬에 묶인 남녀는 유혹과 단기적인 쾌락, 강력한 욕망의 집착을 뜻합니다.", "fortune_reading": "단기적인 이익이나 달콤한 유혹이 다가오나 내실을 따지는 냉철함이 필요합니다.", "advice": "눈앞의 화려함에 혹하지 말고 계약의 조건과 유통기한을 따지세요.", "action_tip": "충동구매나 솔깃한 투자 제안에 쉽게 응하지 마세요."},
    {"name": "XVI. THE TOWER (탑)", "keyword": "낡은 틀의 붕괴 · 전격적 쇄신 · 통쾌한 구체화", "symbolism": "번개를 맞아 부서지는 탑은 거짓된 기반이 깨지고 진실이 드러나는 쇄신을 상징합니다.", "fortune_reading": "갑작스러운 변화나 계획의 수정이 발생하지만 오히려 더 튼튼한 판을 짜게 됩니다.", "advice": "기존의 임시방편을 버리고 근본적인 체질 개선에 나서세요.", "action_tip": "잘못된 오해나 누적된 문제를 오늘 투명하게 드러내어 해결하세요."},
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
        "hour": {
            "cg": h_cg, "cg_elem": CHEONGAN_ELEMENTS.get(h_cg, "none"),
            "jj": h_jj, "jj_elem": JIJI_ELEMENTS.get(h_jj, "none"),
            "jijanggan": JIJANGGAN_FULL_MAP.get(h_jj, [])
        },
        "day": {
            "cg": d_cg, "cg_elem": CHEONGAN_ELEMENTS.get(d_cg, "none"),
            "jj": d_jj, "jj_elem": JIJI_ELEMENTS.get(d_jj, "none"),
            "jijanggan": JIJANGGAN_FULL_MAP.get(d_jj, [])
        },
        "month": {
            "cg": m_cg, "cg_elem": CHEONGAN_ELEMENTS.get(m_cg, "none"),
            "jj": m_jj, "jj_elem": JIJI_ELEMENTS.get(m_jj, "none"),
            "jijanggan": JIJANGGAN_FULL_MAP.get(m_jj, [])
        },
        "year": {
            "cg": y_cg, "cg_elem": CHEONGAN_ELEMENTS.get(y_cg, "none"),
            "jj": y_jj, "jj_elem": JIJI_ELEMENTS.get(y_jj, "none"),
            "jijanggan": JIJANGGAN_FULL_MAP.get(y_jj, [])
        }
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
    elem_percentages = {
        k: round((v / total_score) * 100, 1) for k, v in scores.items()
    }

    day_elem = CHEONGAN_ELEMENTS[d_cg]
    support_score = scores.get(day_elem, 0)
    insoeng_map = {"wood": "water", "fire": "wood", "earth": "fire", "metal": "earth", "water": "metal"}
    support_score += scores.get(insoeng_map.get(day_elem, ""), 0)
    singang_status = "신약(身弱) 사주" if support_score < 45 else ("신강(身强) 사주" if support_score > 65 else "중화(中和) 사주")

    daily_seed = today.toordinal() + diff_days
    
    colors_pool = ["스노우 화이트 / 실버 그레이", "에메랄드 그린 / 포레스트 올리브", "크림슨 레드 / 로즈 골드", "웜 베이지 / 머스터드", "미드나잇 블루 / 네이비", "아이보리 / 스카이 블루"]
    numbers_pool = ["4, 9", "3, 8", "2, 7", "5, 10", "1, 6", "3, 7"]
    directions_pool = ["정서쪽 (백호 방위)", "정동쪽 (청룡 방위)", "정남쪽 (주작 방위)", "중앙 및 동북쪽", "정북쪽 (현무 방위)", "남서쪽 방위"]
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

    advice_templates = {
        "비견(比肩)": (f"오늘({today_iljin_str})은 동료와의 협력이 빛을 발하고 추진력이 곧바로 성과로 연결되는 대길의 하루입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 아이디어를 주변에 공유하고 활발하게 소통하며 기틀을 잡으세요.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 본원({d_cg})의 리더십으로 추진 중인 주요 과제를 당당하게 완성하세요.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 원만한 대화로 하루를 마무리하고 편안한 수면을 취하세요."),
        "겁재(劫財)": (f"오늘({today_iljin_str})은 경쟁력이 크게 상승하나 불필요한 충동 지출을 철저히 방어해야 하는 날입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 불필요한 지출을 차단하고 업무 우선순위를 단단히 정리하세요.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 경쟁 구도에서 기지를 발휘하여 우위를 점하는 승부처입니다.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 마음을 차분히 가라앉히고 미온수로 몸의 열기를 내리세요."),
        "식신(食神)": (f"오늘({today_iljin_str})은 창의적인 아이디어가 샘솟고 새로운 결실의 씨앗을 뿌리는 풍요로운 날입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 구상 중이던 프로젝트나 취미의 첫 단추를 채우기에 최적입니다.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 표현력이 극대화되어 미팅이나 프레젠테이션에서 큰 호응을 얻습니다.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 맛있는 식사와 휴식으로 내면의 에너지를 충전하세요."),
        "상관(傷官)": (f"오늘({today_iljin_str})은 예리한 감각이 돋보이나 언행의 부드러움이 요청되는 날입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 문제의 핵심을 단번에 포착하여 막힌 혈을 시원하게 뚫어냅니다.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 대화 시 직설적 표현보다는 따뜻한 공감 화법을 활용하세요.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 가벼운 스트레칭과 음악 감상으로 과열된 신경을 다스리세요."),
        "편재(偏財)": (f"오늘({today_iljin_str})은 틈새 기회가 포착되고 금전적 결실의 파도가 커지는 대길의 날입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 부동산, 투자, 신규 거래 관련 반가운 소식이 닿습니다.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 과감한 결단력으로 이익을 확정 짓기에 최상의 타이밍입니다.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 자산 포트폴리오를 점검하며 성과를 안정적으로 확정하세요."),
        "정재(正財)": (f"오늘({today_iljin_str})은 쌓아 올린 신뢰가 실속 있는 금전적 보상으로 환원되는 날입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 기존에 추진하던 일에서 실속 있는 인정과 보상이 뒤따릅니다.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 꼼꼼한 문서 검토와 지출 관리로 자산 기틀을 다지세요.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 소중한 사람들과 따뜻한 시간을 보내며 여유를 누리세요."),
        "편관(偏官)": (f"오늘({today_iljin_str})은 책임감이 막중하나 난관을 돌파해 당당히 권위를 세우는 날입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 어려운 과제가 오더라도 담대하게 원칙을 지키며 임하세요.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 강력한 통솔력으로 주변을 이끌고 난제를 완벽히 해결합니다.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 따뜻한 족욕으로 몸의 피로를 풀어주고 숙면을 취하세요."),
        "정관(正官)": (f"오늘({today_iljin_str})은 승진, 인정, 계약 등 명예로운 운의 흐름이 강하게 작용하는 날입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 공공 기관, 상급자, 고객과의 약속이 일사천리로 진행됩니다.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 단정하고 신뢰감 있는 태도로 협상을 리드하여 보람을 얻으세요.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 오늘 일군 성과를 되돌아보며 안정감을 만끽하세요."),
        "편인(偏印)": (f"오늘({today_iljin_str})은 깊은 통찰력과 전문적 지혜로 남다른 기회를 발견하는 날입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 복잡한 기획이나 아이디어 구상에서 족집게 혜안이 떠오릅니다.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 혼자만의 몰입 시간을 통해 독보적인 노하우를 완성하세요.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 독서나 차 한 잔의 여유로 내면의 평온을 얻으세요."),
        "정인(正印)": (f"오늘({today_iljin_str})은 귀인의 따뜻한 조력과 문서운이 크게 결합하는 대길의 하루입니다.",
                     f"☀️ <strong>오전 (06:00~12:00):</strong> 은인의 도움으로 막혀 있던 업무의 혈이 시원하게 풀립니다.<br>"
                     f"🌤️ <strong>오후 (12:00~18:00):</strong> 계약 서명, 자격증, 승인 등 문서와 관련된 대길운을 잡으세요.<br>"
                     f"🌙 <strong>저녁·밤 (18:00~24:00):</strong> 나를 아껴주는 이들에게 따뜻한 고마움을 표현하세요.")
    }

    advice_info = advice_templates.get(today_shipshin, advice_templates["정재(正財)"])
    daily_title = f"[{today_iljin_str}] " + advice_info[0]
    three_stage_advice = advice_info[1]
    daily_score = 82 + (daily_seed * 7) % 17

    min_elem = min(elem_percentages, key=elem_percentages.get)
    user_talisman = TALISMAN_OHEANG_MAP.get(min_elem, TALISMAN_OHEANG_MAP["metal"])

    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주"})
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐶")

    return {
        "user_name": req.name,
        "current_age": current_age,
        "singang_status": singang_status,
        "saju_data": {
            "year_pillar": f"{y_cg}{y_jj}",
            "month_pillar": f"{m_cg}{m_jj}",
            "day_pillar": f"{d_cg}{d_jj}",
            "hour_pillar": h_pillar,
            "pillars_detail": pillars_detail,
            "mbti": user_mbti,
            "animal_symbol": d_animal,
            "animal_icon": user_animal_icon,
            "elements": elem_percentages
        },
        "daily_fortune": {
            "score": daily_score,
            "title": daily_title,
            "advice": three_stage_advice,
            "lucky_color": lucky_color,
            "lucky_number": lucky_number,
            "lucky_direction": lucky_direction,
            "fashion_style": fashion_style,
            "recommended_menu": recommended_menu,
            "mindset": mindset,
            "action": action,
            "talisman": user_talisman
        }
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
            {"year_label": f"{str(adj_years[0])[-2:]}년생 ({today.year - adj_years[0] + 1}세)", "tip": "학업과 진로에서 번뜩이는 영감을 발휘해 주변의 칭찬을 받는 날입니다."},
            {"year_label": f"{str(adj_years[1])[-2:]}년생 ({today.year - adj_years[1] + 1}세)", "tip": "취업·이직 및 새로운 프로젝트에서 중요한 주도권을 쥐게 됩니다."},
            {"year_label": f"{str(adj_years[2])[-2:]}년생 ({today.year - adj_years[2] + 1}세)", "tip": "실속을 차리고 금전적 결실과 성과를 확정 짓는 대길의 타이밍입니다."},
            {"year_label": f"{str(adj_years[3])[-2:]}년생 ({today.year - adj_years[3] + 1}세)", "tip": "귀인의 도움으로 복잡했던 계약이나 사업 협상이 순조롭게 성사됩니다."},
            {"year_label": f"{str(adj_years[4])[-2:]}년생 ({today.year - adj_years[4] + 1}세)", "tip": "무리한 확장보다 내실을 다지며 가족과 평온한 화목을 누리는 날입니다."}
        ]
        
        titles = [
            "주변의 신뢰를 한 몸에 받으며 귀인이 활로를 열어주는 날",
            "오랫동안 정체되었던 문제의 실마리가 시원하게 풀리는 날",
            "재물운과 협상운이 크게 결합하여 실속을 챙기는 대길의 하루",
            "서두르지 않고 원칙을 지킬 때 더 큰 결실이 찾아오는 하루"
        ]
        
        return {
            "name": f"{key}띠",
            "icon": ANIMAL_ICONS.get(key, "🐾"),
            "score": score,
            "title": titles[seed % len(titles)],
            "overview": f"오늘 {key}띠는 자신의 본래 실력과 결단력이 빛을 발하는 날입니다. 사소한 시비에 휘말리지 말고 큰 흐름을 보고 추진하면 오후에 큰 성취가 따릅니다.",
            "year_tips": year_advices,
            "lucky_time": f"오후 {(seed % 6) + 1}시 ~ {(seed % 6) + 3}시",
            "lucky_match": f"호흡이 잘 맞는 띠: {['소띠', '용띠', '원숭이띠', '돼지띠'][seed % 4]}"
        }
    else:
        star_item = next((s for s in STAR_SIGNS if s["name"] == key), STAR_SIGNS[0])
        focus_types = [
            {"badge": "💰 오늘 가장 중요한 재물운", "desc": "뜻밖의 금전적 횡재수가 따르거나 유리한 조건의 거래 계약이 성사될 가능성이 매우 높습니다."},
            {"badge": "💼 오늘 가장 중요한 사업·커리어운", "desc": "직무와 프로젝트에서 탁월한 기획력이 돋보여 상급자나 협력사의 절대적인 신뢰를 얻습니다."},
            {"badge": "💖 오늘 가장 중요한 애정운", "desc": "솔로는 매력적인 귀인과의 깜짝 인연이, 커플은 깊은 대화로 상호 신뢰가 2배로 돈독해집니다."},
            {"badge": "🌿 오늘 가장 중요한 건강·멘탈운", "desc": "두한족열의 수칙을 지키며 가벼운 유산소 운동을 곁들이면 최고의 활력과 집중력을 회복합니다."}
        ]
        chosen_focus = focus_types[seed % len(focus_types)]
        
        return {
            "name": star_item["name"],
            "icon": star_item["icon"],
            "period": star_item["period"],
            "score": score,
            "title": "창의적인 영감과 반가운 기회가 샘솟는 럭키 데이",
            "overview": f"{star_item['name']}에게 오늘은 내면의 직관이 강력하게 작용하는 날입니다. 망설이던 결정이나 프로젝트의 첫 단추를 꿰기에 완벽합니다.",
            "focus_badge": chosen_focus["badge"],
            "focus_content": chosen_focus["desc"],
            "lucky_item": f"{['은색 액세서리', '따뜻한 라떼', '스마트 워치', '향수', '블루 셔츠'][seed % 5]}",
            "lucky_time": f"오전 {(seed % 4) + 9}시 ~ 12시"
        }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    random_idx = random.randint(0, len(TAROT_CARDS) - 1)
    return TAROT_CARDS[random_idx]

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
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A;">
                        🌐 1. {user_name}님의 평생 생애 주기별 대운맥 흐름
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    <div style="border-bottom: 1px solid #F1F5F9; padding-bottom: 8px;">
                        <p style="font-weight: 800; color: #0F172A; margin-bottom: 3px;">🌱 [유년기 (0세 ~ 19세) : 기틀 형성기]</p>
                        <p style="color: #475569;">타고난 영민함과 지적 호기심으로 내면의 가치관과 도덕적 기틀을 확립하던 시기입니다.</p>
                    </div>
                    <div style="border-bottom: 1px solid #F1F5F9; padding-bottom: 8px;">
                        <p style="font-weight: 800; color: #0F172A; margin-bottom: 3px;">🌿 [청년기 (20세 ~ 39세) : 역량 구축기]</p>
                        <p style="color: #475569;">사회에 진출하여 실전 경험과 전문성을 갈고닦으며 진가를 입증해 나간 시기입니다.</p>
                    </div>
                    <div style="border-bottom: 1px solid #F1F5F9; padding-bottom: 8px;">
                        <p style="font-weight: 800; color: #D97706; margin-bottom: 3px;">🔥 [중장년기 (*현재 위치 / 40세 ~ 59세) : 황금 결실기]</p>
                        <p style="color: #92400E;"><strong>{user_name}님 인생 일대에서 가장 강력한 천운의 파도가 솟구치는 최고 하이라이트 구간입니다.</strong> 사회적 주도권을 잡고 자산과 명예의 결실이 폭발적으로 확장됩니다.</p>
                    </div>
                    <div>
                        <p style="font-weight: 800; color: #0F172A; margin-bottom: 3px;">🍎 [말년기 (60세 이후) : 태평성대기]</p>
                        <p style="color: #475569;">평생 축적한 부와 지혜를 토대로 안락하고 평온한 노후를 누리며 가문 번영을 완성합니다.</p>
                    </div>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F;">
                        📈 2. {user_name}님의 현재 10년 대운 감명 ({start_age}세 ~ {end_age}세)
                    </h4>
                </div>
                <p style="color: #78350F; line-height: 1.85; margin-bottom: 8px;">
                    본원에 귀인과 재성의 기운이 결합하는 시기로, 본인이 직접 판을 설계하고 이끌어가는 독보적인 리더십이 발현되는 10년의 절정기입니다.
                </p>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>{start_age}세 ~ {start_age+2}세 (도입기):</strong> 고정 비용 정돈 및 안전 자산 중심 종잣돈 재배치.</p>
                    <p style="color: #B45309; font-weight: 800;">• <strong>{start_age+3}세 ~ {start_age+6}세 (정점기 / ★현재 {age}세 위치):</strong> 귀인의 결정적 조력과 함께 직위·자산 수직 상승 전환점.</p>
                    <p>• <strong>{start_age+7}세 ~ {end_age}세 (결실기):</strong> 성과를 안정적 시스템 수익으로 확정 짓고 차기 대운으로의 연착륙.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #F59E0B; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F;">
                        🔥 3. 이번 10년 대운({start_age}세~{end_age}세) 맞춤 3대 개운(開運) 실천 비책
                    </h4>
                </div>
                
                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 14.5px; line-height: 1.85; color: #451A03;">
                    <p>• <strong>[재물 및 자산 운용]:</strong> 현재 10년 대운은 단기 시세차익보다 실물 부동산, 우량 배당 자산 등 고정 현금 흐름을 창출하는 안전 자산에 집중할 때 부의 크기가 3배 이상 공고해집니다.</p>
                    <p>• <strong>[비즈니스 및 직업 처세]:</strong> 혼자 모든 짐을 짊어지려 하지 말고 주변 전문가와 협력 파트너를 적극적으로 활용하세요. 구두 약속보다는 명확한 계약 문서로 권리를 확보하는 것이 성패를 가릅니다.</p>
                    <p>• <strong>[건강 및 마인드셋]:</strong> 머리는 차갑게 식히고 하체 순환을 돕는 '두한족열' 루틴을 유지하세요. 감정에 휘둘리지 않는 평정심을 유지할 때 인생 최대의 복록을 온전히 담아낼 수 있습니다.</p>
                </div>
            </div>
        </div>
        """
    }

# [신규 추가] 2026 신년운세 & 12개월 토정비결 리포트 생성 API
@app.post("/api/sinnian-report")
def get_sinnian_report(req: dict):
    user_name = req.get("name", "최정오")
    
    monthly_guides = [
        {"m": "1월", "gua": "지천태(地天泰) 괘", "tip": "새해 첫 출발이 매우 상서롭습니다. 오랫동안 구상해온 계획의 첫 단추를 채우기에 최적입니다."},
        {"m": "2월", "gua": "수천수(水天需) 괘", "tip": "조급하게 서두르기보다는 내실을 다지며 주변 상황의 흐름을 관망할 때 이익이 보존됩니다."},
        {"m": "3월", "gua": "천화동인(天火同人) 괘", "tip": "귀인의 조력이 닿아 직무와 인간관계에서 반가운 협력자가 나타나 활로가 열립니다."},
        {"m": "4월", "gua": "풍천소축(風天小畜) 괘", "tip": "작은 성과가 모여 큰 결실을 이루는 달입니다. 지출을 통제하고 종잣돈을 아끼세요."},
        {"m": "5월", "gua": "화천대유(火天大有) 괘", "tip": "재물운이 크게 상승하는 대길의 달입니다. 투자나 계약 문서에서 큰 결실을 맺습니다."},
        {"m": "6월", "gua": "천풍구(天風姤) 괘", "tip": "새로운 인연이나 뜻밖의 제안이 다가오나 계약 조항을 면밀하게 검토하는 신중함이 필요합니다."},
        {"m": "7월", "gua": "천수송(天水訟) 괘", "tip": "사소한 시비나 언쟁을 피하고 원칙을 지키며 부드러운 화법으로 대화할 때 평온이 유지됩니다."},
        {"m": "8월", "gua": "풍지관(風地觀) 괘", "tip": "상반기의 성과를 정리하고 하반기의 새로운 전략을 수립하기에 최적의 전환점입니다."},
        {"m": "9월", "gua": "산지박(山地剝) 괘", "tip": "불필요한 인간관계나 낡은 습관을 정리하고 내면의 체력을 보충해야 하는 힐링의 달입니다."},
        {"m": "10월", "gua": "지뢰복(地雷復) 괘", "tip": "정체되었던 기운이 다시 솟구쳐 오르는 반전의 달로, 승진이나 계약에서 낭보가 전해집니다."},
        {"m": "11월", "gua": "수뢰준(水雷屯) 괘", "tip": "새로운 도전을 위한 기반이 단단해집니다. 경험자의 조언을 경청하면 시행착오를 줄입니다."},
        {"m": "12월", "gua": "지화명이(地火明夷) 괘", "tip": "한 해의 결실을 풍성하게 갈무리하고 가족과 함께 따뜻한 성취를 누리는 대단원의 달입니다."}
    ]

    months_html = "".join([f"""
        <div style="background: #F8FAFC; border-left: 3.5px solid #2D6A4F; border-radius: 6px; padding: 10px 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                <span style="font-weight: 800; color: #0F172A; font-size: 14.5px;">📅 {item['m']} 운세</span>
                <span style="font-size: 11.5px; background: #EBF5EE; color: #2D6A4F; font-weight: 700; padding: 2px 6px; border-radius: 4px;">{item['gua']}</span>
            </div>
            <p style="color: #475569; font-size: 13.5px; line-height: 1.6;">{item['tip']}</p>
        </div>
    """ for item in monthly_guides])

    return {
        "title": "📅 2026 신년운세 & 토정비결",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div>
                <div style="border-left: 4px solid #DC2626; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #DC2626; font-weight: 800;">2026 丙午년(붉은 말의 해)</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #991B1B; margin-top: 2px;">
                        🔥 1. {user_name}님의 2026년 세운(歲運) 총론
                    </h4>
                </div>
                <p style="color: #7F1D1D; line-height: 1.85; margin-bottom: 10px;">
                    2026년은 강렬한 불(火)의 활력이 대지를 비추는 丙午년입니다. {user_name}님의 사주와 만나 정체되었던 문제들이 시원하게 돌파되고, 숨어있던 재능과 결실이 수면 위로 찬란하게 드러나는 역동적인 도약의 한 해가 됩니다.
                </p>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #475569;">
                    <p>• <strong>💰 재물 대박 타이밍:</strong> 양력 5월과 10월에 큰 금전적 횡재수와 유리한 계약이 성사됩니다.</p>
                    <p>• <strong>💼 커리어·직무 발전:</strong> 상반기에 뿌린 씨앗이 하반기(9~11월)에 승진과 명예로운 성과로 환원됩니다.</p>
                    <p>• <strong>🤝 결정적 귀인수:</strong> 서북쪽 방위에서 다가오는 동료 및 전문 파트너가 결정적 난관을 해결해 줍니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 10px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A;">
                        📜 2. 1월~12월 월별 토정비결 & 실전 처세 가이드
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    {months_html}
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F;">
                        ✨ 3. 2026년 운세를 극대화하는 3대 개운(開運) 솔루션
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #92400E; line-height: 1.75;">
                    <p>• <strong>행운의 방위:</strong> 주거지 및 집무실 기준 '정동쪽'과 '서북쪽'이 복록을 부르는 최고의 방위입니다.</p>
                    <p>• <strong>금전 지출 방어:</strong> 양력 7월에는 충동적인 지출이나 무리한 확장을 자제하고 현금 유동성을 확보하세요.</p>
                    <p>• <strong>마인드셋 처세:</strong> 빠른 속도감 속에서도 중요한 계약서는 반드시 문구 하나까지 꼼꼼히 점검할 때 승리합니다.</p>
                </div>
            </div>
        </div>
        """
    }

def generate_love_report_content(user_name: str, sub_opt: str) -> str:
    if sub_opt == "기혼":
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">상태 맞춤: 기혼 (부부 해로)</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">[부부 해로 및 가정 화목운] 신뢰와 상호 존중의 평생 동반자</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주 원국은 부부 간의 신뢰와 가정의 안정을 최우선으로 삼는 묵직한 포용력을 지니고 있습니다. 기혼 생활에서 일방적인 헌신이나 잔소리보다는 서로의 독립적인 영역을 인정하고 격려해 줄 때 부부 금실과 가정의 재물운이 함께 상승합니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #BE123C; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337;">🏡 1. {user_name}님 가정의 화목 및 배우자 합(合) 분석</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569; line-height: 1.85;">
                    <p>• <strong>배우자와의 성향 조화:</strong> 겉으로는 무던해 보여도 속정이 깊은 배우자궁을 타고났으며, 서로의 장단점을 보완해 주는 상생의 구조입니다.</p>
                    <p>• <strong>가정 내 갈등 관리:</strong> 자녀 교육이나 재정 계획에 이견이 생길 때는 감정적 직설보다 차 한 잔을 나누며 대화할 때 막힘없이 풀립니다.</p>
                    <p>• <strong>가정 번영 오행 기운:</strong> {user_name}님과 배우자 사이에 온화한 기운을 북돋워 주는 방위는 '남서쪽'이며, 거실에 따뜻한 조명을 두면 부부 화합이 배가됩니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F;">🌹 2. 평생 백년해로를 완성하는 실전 부부 처세법</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E; line-height: 1.85;">
                    <p>• <strong>감사 표현의 생활화:</strong> 당연하게 여기기 쉬운 일상적인 배려에 대해 "고마워요"라는 말을 하루 한 번 전하는 것이 최고의 부부 개운법입니다.</p>
                    <p>• <strong>행운의 데이트 추천:</strong> 주말 가벼운 근교 숲길 산책이나 조용한 힐링 여행이 부부의 권태감을 씻어내고 새로운 활력을 줍니다.</p>
                </div>
            </div>
        </div>
        """
    elif sub_opt == "연애중":
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">상태 맞춤: 연애중 (결속과 발전)</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">[연애 발전 및 결실운] 깊은 교감과 미래를 약속하는 인연</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님은 연인과의 관계에서 진실된 소통과 배려를 중시하는 따뜻한 사랑의 소유자입니다. 현재 연애는 단순한 설렘을 넘어 미래의 진지한 동반자로 발전하기에 매우 좋은 기운이 흐르고 있습니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #BE123C; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337;">💍 1. {user_name}님의 결혼 및 장기적 인연 발전 가이드</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569; line-height: 1.85;">
                    <p>• <strong>관계의 성숙 포인트:</strong> 상대방에게 바라는 점을 솔직하면서도 부드럽게 표현할 때 신뢰의 뿌리가 깊어집니다.</p>
                    <p>• <strong>결혼 및 결실의 타이밍:</strong> 가을(9~11월)과 봄(3~5월)에 두 사람 사이의 중요한 약속이나 결혼 논의가 급물살을 타게 됩니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F;">🌹 2. 둘만의 사랑을 공고히 하는 실전 연애 처세법</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E; line-height: 1.85;">
                    <p>• <strong>밀당 없는 진정성:</strong> 계산적인 밀고 당기기보다 솔직하고 일관된 태도를 보여줄 때 상대방의 마음을 완전히 사로잡습니다.</p>
                    <p>• <strong>추천 데이트 장소:</strong> 야경이 내려다보이는 레스토랑이나 클래식한 전시회가 로맨틱한 기운을 증폭시킵니다.</p>
                </div>
            </div>
        </div>
        """
    elif sub_opt == "썸/짝사랑":
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">상태 맞춤: 썸/짝사랑 (관계 진전)</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">[호감 발전 및 연인 전환운] 매력 어필과 결정적 고백의 타이밍</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님은 은근한 매력과 진중함으로 상대방에게 호감을 심어주는 기운을 지니고 있습니다. 망설이기보다는 적절한 순간에 확실한 시그널을 보낼 때 연인 관계로의 전환이 빠르게 이루어집니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #BE123C; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337;">💘 1. 상대방의 마음을 여는 핵심 전략</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569; line-height: 1.85;">
                    <p>• <strong>공감대 형성:</strong> 상대방의 취향이나 관심사를 미리 파악하여 자연스러운 대화 주제로 이끌어내세요.</p>
                    <p>• <strong>결정적 타이밍:</strong> 비가 오는 날이나 저녁 티타임에 은근한 칭찬과 함께 호감을 표현할 때 성공 확률이 2배로 높아집니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F;">🌹 2. 썸을 연애로 만드는 실전 액션 팁</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E; line-height: 1.85;">
                    <p>• <strong>과도한 조급함 금물:</strong> 상대방의 반응 속도에 일희일비하지 말고 여유 있고 당당한 태도를 유지하세요.</p>
                    <p>• <strong>행운의 아이템:</strong> 은은한 우디/플로럴 계열 향수와 단정한 셔츠 차림이 매력도를 극대화합니다.</p>
                </div>
            </div>
        </div>
        """
    else:
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">상태 맞춤: 솔로 (새로운 인연)</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">[평생 애정운] 깊은 신뢰와 상호 존중의 천생연분</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 애정 원국은 가벼운 감정의 불꽃보다는 한 번 맺은 신뢰를 평생 지켜나가는 따뜻한 포용력의 소유자입니다. 주변 사람들에게 굳이 맞추려 하지 않고 본인 본연의 당당함을 드러낼 때 뜻밖의 귀한 인연이 찾아옵니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #BE123C; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337;">💞 1. {user_name}님과 운명적으로 통하는 상대방의 특징</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569; line-height: 1.85;">
                    <p>• <strong>성향과 인품:</strong> 감정 기복이 적고 원칙이 뚜렷하며, 대화 시 상대방의 이야기를 깊이 경청해 주는 차분한 스타일.</p>
                    <p>• <strong>외모 및 이미지:</strong> 부드럽고 온화한 인상에 단정하고 세련된 옷차림을 선호하며 지적인 분위기를 풍기는 사람.</p>
                    <p>• <strong>오행 궁합 조화:</strong> {user_name}님 사주에 꼭 필요한 차분한 기운을 채워줄 수 있는 띠(쥐띠, 닭띠, 원숭이띠)와 대길연을 이룹니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F;">🌹 2. 평생 인연을 완성하는 실전 관계 처세법</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E; line-height: 1.85;">
                    <p>• <strong>만남의 장소:</strong> 물이 잔잔하게 흐르는 호수 주변, 조용한 미술관이나 테라스가 있는 카페가 인연의 기운을 조화롭게 묶어줍니다.</p>
                    <p>• <strong>인연 대길 시기:</strong> 가을(양력 9~11월)과 초봄(양력 2~3월)에 귀인의 소개로 다가오는 만남을 주목하세요.</p>
                </div>
            </div>
        </div>
        """

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

    if theme == "love":
        content_html = generate_love_report_content(user_name, sub_opt)
    elif theme == "wealth":
        content_html = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #D97706; padding-left: 10px;">
                <span style="font-size: 12px; color: #D97706; font-weight: 800;">원국 정밀 감명</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin: 3px 0 6px;">[평생 재물운] '암장(暗藏) 금고형' 자산 축적 원국</h4>
                <p style="color: #92400E; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 겉으로 드러난 화려함보다 실속 있게 현금과 실물 자산을 차곡차곡 축적하는 전형적인 '황금 금고형' 구조입니다. 지장간 속에 알짜배기 재성이 은밀하게 뿌리를 내리고 있어 틈새 기회를 포착하여 자산을 불리는 능력이 탁월합니다. 단기 시세 차익보다는 실물 부동산과 우량 배당 자산 중심 포트폴리오가 운명을 견인합니다.
                </p>
            </div>
            
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A;">📊 1. {user_name}님의 생애 자산 증식 3단계 로드맵</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569; line-height: 1.85;">
                    <p>• <strong>초년~30대 (씨앗 축적기):</strong> 종잣돈을 모으고 금융/실물 경제의 안목을 기르는 시기였습니다.</p>
                    <p style="color: #B45309; font-weight: 800;">• <strong>40대 중후반~50대 (*현재 황금기):</strong> 귀인의 도움과 부동산/사업 결단으로 자산 규모가 3배 이상 폭발적으로 퀀텀점프하는 최상의 전환점입니다.</p>
                    <p>• <strong>60대 이후 (임대/배당 태평기):</strong> 고정적 현금 흐름을 바탕으로 부를 안전하게 대물림하는 완벽한 자산 수성기입니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #059669; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46;">💡 2. 재물운을 극대화하는 실전 개운(開運) 솔루션</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #047857; line-height: 1.85;">
                    <p>• <strong>행운의 방위:</strong> 주거지나 사무실 기준 '정북쪽'과 '동북쪽'이 재물이 샘솟는 황금 방위입니다.</p>
                    <p>• <strong>금전 누수 방어법:</strong> 지갑 안에 현금을 항상 짝수 매수로 정돈하여 넣고, 노란색 소품을 휴대하면 헛돈 지출이 차단됩니다.</p>
                    <p>• <strong>문서 계약 대길 타이밍:</strong> 음력 4월, 8월, 12월에 체결하는 부동산/투자 계약이 평생의 복록을 부릅니다.</p>
                </div>
            </div>
        </div>
        """
    elif theme == "business":
        content_html = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #2563EB; padding-left: 10px;">
                <span style="font-size: 12px; color: #2563EB; font-weight: 800;">직업군 맞춤: {sub_opt}</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin: 3px 0 6px;">[사업·직업운] 치밀한 기획력과 결단력의 수장</h4>
                <p style="color: #1E40AF; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 복잡한 문제의 핵심을 단번에 꿰뚫고 시스템을 정돈하는 전략가 기질을 타고났습니다. 현재 직업군({sub_opt})에서 남들이 기피하는 난제를 해결하며 대체 불가능한 리더로서 두각을 나타내게 됩니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #1E40AF; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A;">🚀 1. {user_name}님의 대박 직무 분야 및 사업 아이템</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569; line-height: 1.85;">
                    <p>• <strong>추천 핵심 직무:</strong> 전략 기획, 경영 컨설팅, IT/기술 매니지먼트, 금융 분석 등 시스템을 설계하는 분야.</p>
                    <p>• <strong>창업 및 사업 방향:</strong> 지식 기반 플랫폼, 전문 라이선스 비즈니스 등 무형의 노하우를 자산화하는 모델에 최적입니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F;">💼 2. 승진·이직·사업 대성을 위한 실전 처세 가이드</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E; line-height: 1.85;">
                    <p>• <strong>이직/창업 대길 시기:</strong> 가을(양력 9~11월)과 초봄(양력 2~3월)에 들어오는 스카우트 제의나 신규 사업 론칭이 큰 명예를 안겨줍니다.</p>
                    <p>• <strong>사무 공간 개운법:</strong> 책상을 출입문이 대각선으로 보이는 자리에 앉고, 메탈 소품을 두면 집중력이 극대화됩니다.</p>
                </div>
            </div>
        </div>
        """
    else:
        content_html = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #059669; padding-left: 10px;">
                <span style="font-size: 12px; color: #059669; font-weight: 800;">오행 체질 정밀 분석</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46; margin: 3px 0 6px;">[평생 건강운] 수승화강(水昇火降) 활력 관리</h4>
                <p style="color: #047857; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 오행 체질은 강인한 생명력을 갖추고 있으나 두한족열(머리는 시원하게 발은 따뜻하게)의 수칙을 유지해야 합니다. 스트레스 누적 시 간 피로와 소화기계로 신호가 올 수 있으므로 규칙적인 유산소 운동이 건강의 비결입니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #047857; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A;">🏥 1. {user_name}님이 각별히 챙겨야 할 3대 취약 장기</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569; line-height: 1.85;">
                    <p>• <strong>간장 & 담낭:</strong> 만성 피로와 눈의 침침함을 방지하기 위해 과도한 음주를 피하고 간 보호 성분을 섭취하세요.</p>
                    <p>• <strong>신장 & 방광:</strong> 노폐물 배출을 위해 하루 1.5L 이상의 미온수를 나누어 마시는 습관이 필수적입니다.</p>
                    <p>• <strong>위장 & 비장:</strong> 야식을 지양하고 담백한 식단을 유지해야 소화 흡수력이 강화됩니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #1E40AF; padding-left: 10px; margin-bottom: 8px;">
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A;">🌿 2. 평생 활력을 완성하는 일상 개운 섭생 루틴</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #1E40AF; line-height: 1.85;">
                    <p>• <strong>취침 전 힐링 루틴:</strong> 매일 밤 15분간 따뜻한 족욕을 통해 하체 순환을 돕고 숙면을 취하세요.</p>
                    <p>• <strong>추천 운동 요법:</strong> 주 3회 30분 이상의 빠른 걷기나 수영 등 유산소 운동이 오행 밸런스를 맞춰줍니다.</p>
                </div>
            </div>
        </div>
        """
    
    return {
        "title": titles.get(theme, "심층 리포트"),
        "content": content_html
    }
