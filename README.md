# 달하 (dalha.kr)

사주(명리)를 오늘의 운세·코디 색·메뉴 같은 생활 언어로 풀어 주는 웹 서비스입니다.

- 화면: 루트 `index.html` (빌드 도구 없는 바닐라 HTML/CSS/JS) + `assets/`
- 서버: 루트 `main.py` (FastAPI) — Render에 배포, `main` 병합 시 자동 배포
- 명리 엔진: `backend/app/engine/` (`app.engine`으로 import)
- 코디: `fashion_v2/`, 음식: `dalha_food/`
- 만세력: `lunar-python`(절기·간지) + `korean-lunar-calendar`(한국 음력·윤달)

## 로컬 실행

```sh
pip install -r requirements.txt
uvicorn main:app --reload
```

## 테스트

```sh
PYTHONPATH=. python -m pytest -q backend/tests
npm install --ignore-scripts && node scripts/test_session_client.cjs
```

CI에서 도는 테스트 목록은 `.github/workflows/`에 있습니다.
