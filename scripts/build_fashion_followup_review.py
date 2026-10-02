"""Render the second review's decisions and checked evidence, without new scores."""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'fashion_v2/evidence_data'


def build(output, images):
    feedback = json.loads((DATA/'reviews/outfit-first-20261002-round2.json').read_text())
    evidence = json.loads((DATA/'followups/wardrobe-research-20261002-r2.json').read_text())
    e = html.escape
    names = {'after-1':'새 추천 1', 'after-2':'새 추천 2',
             'private-1':'속옷 안내 사례 1', 'private-2':'속옷 안내 사례 2'}
    verdicts = {'prefer':'긍정 평가', 'hold':'보류', 'revise':'수정 요청'}
    decisions = ''.join(f'''<tr><th>{names[c['case_id']]}</th><td>{verdicts[c['feedback']['verdict']]}</td>
        <td>{e(c['interpretation']['decision'])}<small>{e(c['interpretation']['scope'])}</small></td></tr>'''
        for c in feedback['cases'])
    sources = {s['id']:s for s in evidence['sources']}
    cards = []
    for o in evidence['observations']:
        s = sources[o['source_id']]
        photo = (images/o['image_file']).read_bytes()
        if hashlib.sha256(photo).hexdigest() != o['image_sha256']:
            raise ValueError('Evidence image mismatch: '+o['id'])
        encoded = base64.b64encode(photo).decode()
        limitations = ''.join('<li>'+e(x)+'</li>' for x in s['limitations'])
        cards.append(f'''<article><div class="tag">관련 사례 · 동일 조합 아님</div><h3>{e(o['title'])}</h3>
            <img src="data:image/jpeg;base64,{encoded}" alt="{e(o['title'])}">
            <p>{e(o['supports'])}</p><p class="meta">{e(s['publisher'])} · {e(s['published_at'])}</p>
            <ul>{limitations}</ul><a href="{e(s['url'])}" target="_blank" rel="noopener noreferrer">원문에서 확인하기 ↗</a></article>''')
    audits = ''.join(f'<tr><th>{e(s["publisher"])}</th><td><a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(s["title"])}</a></td><td>{e(" · ".join(s["limitations"]))}</td></tr>' for s in evidence['sources'][2:])
    questions = ''.join('<li><b>'+e(q['question'])+'</b><br>'+e(q['missing'])+'</li>' for q in evidence['questions'])
    page = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>달하 · 검토 의견과 근거 확인</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f5f2eb;color:#273b32;font:16px/1.75 system-ui,sans-serif;word-break:keep-all;overflow-wrap:break-word}
    main{max-width:1060px;margin:auto;padding:34px 24px 60px}h1{font-size:30px;line-height:1.4}h2{font-size:23px;margin-top:38px}h3{font-size:18px;line-height:1.6}a{color:#315f4a}
    .kicker,.meta{color:#677669;font-size:13px}.notice{padding:18px 22px;background:#e2eadd;border-left:4px solid #6b8569;border-radius:5px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}
    article{border:1px solid #d9ddd2;background:#fffdf8;border-radius:14px;padding:22px}article img{width:100%;height:430px;object-fit:contain;background:#f1f0e9;border-radius:8px}.tag{font-size:12px;color:#8b5937;background:#f3e6d6;display:inline-block;padding:4px 9px;border-radius:20px}
    table{width:100%;border-collapse:collapse;background:#fffdf8;font-size:14px}td,th{text-align:left;vertical-align:top;padding:13px;border-bottom:1px solid #d9ddd2}th{min-width:104px}small{display:block;color:#677669;margin-top:7px}li{margin:9px 0}article ul{font-size:14px;padding-left:19px}.table-wrap{overflow-x:auto}.counts{font-size:18px;font-weight:700}.muted{color:#677669}footer{border-top:1px solid #d9ddd2;padding-top:18px;margin-top:32px;font-size:13px}
    @media(max-width:650px){main{padding:23px 16px 42px}.grid{grid-template-columns:1fr}h1{font-size:25px}article{padding:17px}article img{height:390px}.table-wrap table{min-width:590px}}
    </style><main><div class="kicker">DALHA · 2026.10.02 · 2차 검토</div><h1>추측을 줄이고, 확인된 착장을 쌓기</h1>
    <div class="notice"><b>검토 메모 4건을 원문과 해당 코디에 연결했습니다.</b><br>기능 테스트 통과와 코디의 미적 검증은 별개입니다. 이번 조사는 확정된 정답을 만들기보다, 어떤 근거가 있고 무엇이 아직 부족한지 구분하는 데 초점을 맞췄습니다.</div>
    <h2>의견을 이렇게 반영했습니다</h2><div class="table-wrap"><table><thead><tr><th>사례</th><th>상태</th><th>반영 범위</th></tr></thead><tbody>DECISIONS</tbody></table></div>
    <p>코드에서는 검정 겉옷이 미승인이라는 이유로 감점했던 부분을 제거했습니다. 남색·검정 중 어느 쪽이 낫다는 점수는 추가하지 않았습니다. 검토하신 네 코디의 출력은 그대로 보존됩니다.</p>
    <h2>본문과 사진을 함께 확인한 관련 사례</h2><p class="counts">관련 착장 2건 · 게시 플랫폼 1곳 · 요청한 맨투맨 조합과 정확히 일치하는 사례 0건</p><p class="muted">두 자료는 붉은 계열 상의와 베이지 하의를 연결하는 참고입니다. 맨투맨·후드·체크 셔츠의 차이와 전체 착장을 구분해야 합니다.</p><div class="grid">CARDS</div>
    <h2>수집했어도 실착 근거로 쓰지 않은 자료</h2><div class="table-wrap"><table><thead><tr><th>출처</th><th>자료</th><th>확인 결과와 제외 이유</th></tr></thead><tbody>AUDITS</tbody></table></div>
    <p>무신사 기사에서 확인한 이미지 8장에는 모두 ‘AI로 생성’ 표시가 있었습니다. 출처가 명확한 편집 이미지라도 실제 사람이 입은 근거와는 분리했습니다. 확인하지 않은 사진의 생성 여부는 추정하지 않습니다.</p>
    <h2>다음 데이터가 해결해야 할 질문</h2><ol>QUESTIONS</ol>
    <div class="notice">색상명뿐 아니라 <b>데님의 명도·워싱, 소재, 핏, 겉옷·이너·하의·신발 전체 조합</b>을 기록합니다. 조회수나 브랜드 이름을 미적 점수로 바꾸지 않고, 연령은 출처에 명시된 경우에만 사용합니다.</div>
    <footer>이 자료는 검토 기록과 후속 근거 확인 결과입니다. 새 점수 규칙이나 보라→네이비 대체 규칙을 확정하지 않았습니다. 현재 변경 브랜치에 기록했으며 운영 서비스에는 배포하지 않았습니다. 사진의 권리는 각 출처에 있으며, 원본 색은 조명과 후처리에 따라 달라질 수 있습니다.</footer></main></html>'''
    page = page.replace('DECISIONS',decisions).replace('CARDS',''.join(cards)).replace('AUDITS',audits).replace('QUESTIONS',questions)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(page)
    print(json.dumps({'file':str(output),'reviews':len(feedback['cases']),'related_cases':len(cards)},ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--images',type=Path,required=True)
    args=parser.parse_args();build(args.output,args.images)
