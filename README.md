# 운세의신 (Fortune God) MVP

캐주얼 UI + 절기 기준 만세력 엔진의 대중 사주 운세 앱입니다.

- 앱: Flutter (iOS / Android)
- API: Python FastAPI
- 만세력: `lunar-python` (절기·원국) + `korean-lunar-calendar` (한국 음력·윤달)
- DB: Supabase `profiles` (선택)

## 기능

1. 입력: 닉네임, 성별, 생년월일(양력/음력/윤달), 시간 또는 시간 모름(삼주)
2. 분기: 애정 상태 4종, 직업·상황 4종
3. 원국 천간/지지, 오행 백분율, 십성, 60갑자 캐릭터
4. 홈 오늘 운세 / 내 사주 / 테마 6종 / 이달·올해 운세

## 백엔드

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- 문서: http://127.0.0.1:8000/docs
- Android 에뮬레이터는 `http://10.0.2.2:8000` 으로 API에 붙습니다.

Supabase를 쓰려면 `.env`에 `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`를 넣고 `supabase/schema.sql`을 SQL Editor에서 실행하세요. 키가 없으면 계산만 하고 저장은 건너뜁니다.

## Flutter

이 PC에 Flutter SDK가 없다면 [설치 가이드](https://docs.flutter.dev/get-started/install/windows) 후:

```powershell
cd mobile
flutter create . --project-name fortune_god --org com.fortunegod --platforms=android,ios
flutter pub get
flutter run
```

`flutter create .` 는 플랫폼 폴더만 채우고 기존 `lib/` 은 유지합니다.

## API

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/profile` | 프로필 저장(선택) + 사주 |
| POST | `/api/saju/analyze` | 원국 + 오늘 운세 |
| POST | `/api/fortune/today` | 오늘의 운세 |
| POST | `/api/fortune/theme` | 테마 운세 (`theme`) |
| POST | `/api/fortune/period` | `month` / `year` |

공통 바디 예:

```json
{
  "nickname": "라이언",
  "gender": "male",
  "calendar_type": "solar",
  "is_leap_month": false,
  "birth_date": "1990-05-15",
  "birth_time": "12:00:00",
  "time_unknown": false,
  "love_status": "solo",
  "career_status": "employee"
}
```

`love_status`: `solo` | `dating` | `married` | `reunion`  
`career_status`: `employee` | `student` | `freelance` | `job_change`  
`theme`: `health` | `wealth` | `love` | `business` | `study` | `career`
