# 실착 기록

사람들이 실제로 입은 코디의 색을 한 줄에 하나씩 적는다. 이미지는 저장하지 않고 링크만 남긴다.
색 이름은 달하 팔레트 id(`fashion_v2/approved_palette.json` + `light_gray`·`mid_gray`·`plum`·`rust`·`pale_pink`)로 적는다.
팔레트에 없는 색은 가장 가까운 id를 적고 `note`에 원래 색을 적는다. 해당 칸이 없으면 `-`.

파일: `<집단>-<계절>-<TPO>.csv` (예: `m40-fw-casual.csv`, `f20-fw-casual.csv`)

| 열 | 뜻 |
| --- | --- |
| source_url | 출처 링크 |
| source_type | lookbook(브랜드 룩북) · magazine(패션지) · snap(스냅·SNS) · report(조사 보고서) |
| grade | 지식서 근거 등급(C·D) |
| seen_on | 기록한 날짜 |
| gender, age_band | 여성/남성, 20s/40s 등(출처에 나온 경우만, 추정이면 note에) |
| season, tpo | fw/ss, casual/business_casual/formal |
| outer, top, bottom, shoes, bag, accessory | 각 자리의 색 id |
| note | 팔레트에 없는 원래 색, 소재, 특이점 |
