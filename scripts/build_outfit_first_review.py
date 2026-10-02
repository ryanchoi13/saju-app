"""Make deterministic before/after cases and an offline visual review file.

First call writes cases.json and a local render page. After capturing production
canvases, pass --illustrations to embed the matching images in the final HTML.
"""
import argparse
from copy import deepcopy
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fashion_v2.svg_recommendation import build_svg_catalog_contexts, PALETTE


def cases():
    yellow = dict(hex='#FBE6A0', name_ko='옅은 노랑')
    pink = PALETTE['pink']
    new = build_svg_catalog_contexts('male', 'autumn', yellow, pink, age=48)['casual']['looks']
    private = build_svg_catalog_contexts('male', 'autumn', PALETTE['red'], PALETTE['purple'], age=48)['casual']['looks']
    original=[]
    for n in range(2):
        look=deepcopy(new[n]);s=look['garment_spec']
        s.update(outerColor=yellow['hex'] if n==0 else pink['hex'],
                 topColor=pink['hex'] if n==0 else yellow['hex'],
                 bottom='데님 바지',bottomColor=PALETTE['denim']['hex'],
                 shoeColor=PALETTE['navy' if n==0 else 'burgundy']['hex'])
        color_name={yellow['hex']:'옅은 노랑',pink['hex']:'연핑크',PALETTE['denim']['hex']:'데님 블루',
                    PALETTE['navy']['hex']:'네이비',PALETTE['burgundy']['hex']:'버건디'}
        for i in look['items']:
            slot={'outer':'outer','top':'top','bottom':'bottom','shoes':'shoe'}[i['category']]
            i.update(label=s[slot],hex=s[slot+'Color'],color_name=color_name[s[slot+'Color']])
            for k in ('applied_daily_color','source_hex','color_parts','color_description'):
                i.pop(k,None)
        look['color_strategy']={'original':{'A':yellow,'B':pink},'private_color_suggestion':None}
        look.pop('coordination',None)
        original.append(look)
    result=[]
    groups=[('before',original,'기존 추천 재현'),('after',new,'새 흐름의 추천'),('private',private,'추천색을 보이지 않는 곳에')]
    for group,looks,label in groups:
        for n,look in enumerate(looks,1):
            result.append(dict(id=f'{group}-{n}',group=group,title=f'{label} {n}',look=look))
    return result


STYLE='''
:root{--ink:#27352e;--muted:#647064;--green:#345747;--line:#deded3;--paper:#f6f3ec}*{box-sizing:border-box}body{word-break:keep-all;overflow-wrap:break-word;margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 system-ui,-apple-system,'Noto Sans KR',sans-serif}.wrap{max-width:1120px;margin:auto;padding:36px 24px 64px}h1{font-size:32px;line-height:1.3;letter-spacing:-.04em;margin:10px 0 18px}h2{font-size:23px;margin:36px 0 12px}h3{font-size:18px;margin:0 0 14px}.kicker{color:var(--green);font-size:12px;letter-spacing:.15em;font-weight:700}.intro{max-width:820px;color:var(--muted)}.notice{background:#e8eee4;border-left:3px solid #789174;padding:17px 20px;margin:22px 0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.card{background:#fffdf8;border:1px solid var(--line);border-radius:15px;padding:22px;min-width:0}.card img{width:100%;height:460px;object-fit:contain;background:#f5eddb;border-radius:10px}.pill{display:inline-block;background:#e8eee4;color:var(--green);font-size:12px;border-radius:20px;padding:4px 11px;margin-bottom:10px}.old{background:#f1e3da;color:#965347}.summary{font-size:15px;color:var(--muted);margin:15px 0}.hint{font-size:14px;line-height:1.8;background:#e8eee4;padding:14px 16px;border-radius:10px}.swatches{display:flex;gap:15px;flex-wrap:wrap;font-size:13px;margin:12px 0}.swatch{display:inline-flex;gap:7px;align-items:center}.dot{width:16px;height:16px;border-radius:50%;border:1px solid #0002}.details{font-size:13px;color:var(--muted);padding-top:12px}.review{border-top:1px solid var(--line);margin-top:15px;padding-top:13px}.review label{font-size:13px;display:block;margin:8px 0 4px}select,textarea,button{font:inherit}select,textarea{width:100%;background:white;color:var(--ink);border:1px solid #cdd1c7;border-radius:7px;padding:9px}textarea{min-height:76px;resize:vertical}button{background:var(--green);color:#fff;border:0;border-radius:8px;padding:12px 18px;cursor:pointer}button:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid #a38b5e;outline-offset:3px}.actions{display:flex;gap:15px;align-items:center;margin:20px 0}.status{font-size:13px;color:var(--muted)}footer{font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:20px;margin-top:38px}li{margin:9px 0}@media(max-width:650px){.wrap{padding:24px 16px 45px}.grid{grid-template-columns:1fr}.card{padding:17px}.card img{height:410px}h1{font-size:27px}.actions{display:block}.status{display:block;margin-top:8px}}'''


def card(c, illustrations):
    look=c['look'];spec=look['garment_spec'];image=illustrations[c['id']]
    if image['spec']!=spec:
        raise ValueError('Illustration does not match case '+c['id'])
    src=image['data_uri']
    if not src.startswith('data:image/webp;base64,'):
        raise ValueError('Expected embedded production canvas')
    e=html.escape;old=c['group']=='before'
    summary=' · '.join(i['color_name']+' '+i['label'] for i in look['items'])
    hint=look['color_strategy'].get('private_color_suggestion')
    message=('<div class="hint"><b>추천색을 즐기는 다른 방법</b><br>'+e(hint['text'])+'</div>') if hint else ''
    colors=look['color_strategy']['original']
    chips=''.join(f'<span class="swatch"><i class="dot" style="background:{e(colors[r]["hex"])}"></i>추천색 {r} · {e(colors[r].get("name_ko",colors[r].get("name","")))}</span>' for r in ('A','B'))
    review='' if old else f'''<div class="review"><label for="verdict-{c['id']}">이 코디에 대한 의견</label><select id="verdict-{c['id']}" data-case="{c['id']}" data-field="verdict"><option value="">아직 선택하지 않음</option><option value="prefer">이 방향이 좋음</option><option value="revise">수정 필요</option><option value="hold">보류</option></select><label for="note-{c['id']}">어울리는 점 / 어색한 점</label><textarea id="note-{c['id']}" data-case="{c['id']}" data-field="note" placeholder="편하게 의견을 적어주세요"></textarea></div>'''
    return f'''<article class="card" data-card="{c['id']}"><span class="pill {'old' if old else ''}">{'수정 요청한 기존안' if old else '새 엔진 결과 · 시각 검토'}</span><h3>{e(c['title'])}</h3><img src="{src}" alt="{e(summary)}"><p class="summary">{e(summary)}</p><div class="swatches">{chips}</div>{message}<div class="details">{'비교를 위해 기존 배색을 현재 화보로 재현했습니다.' if old else '원래 추천색과 화면에 적용한 색은 다를 수 있습니다. 옅은 노랑은 베이지, 레드는 분홍·버건디의 등록된 톤으로 조정할 수 있습니다.'}</div>{review}</article>'''


def build(output, illustrations_path):
    output.mkdir(parents=True,exist_ok=True);rows=cases()
    (output/'cases.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    data=json.dumps(rows,ensure_ascii=False).replace('<','\\u003c')
    render='''<!doctype html><meta charset="utf-8"><div id="drawings"></div><script type="module">import {renderLook} from '/assets/dalha-garments/integration.js'; import {decorateLook,hydrateIllustrations} from '/assets/dalha-illustrations/adapter.js?v=20261001-2'; const rows=DATA; const root=document.getElementById('drawings'); root.innerHTML=rows.map(c=>`<div id="${c.id}">${decorateLook(c.look,c.id,renderLook(c.look,c.id))}</div>`).join(''); await hydrateIllustrations(root); window.reviewRows=rows; window.reviewReady=true;</script>'''.replace('DATA',data)
    (output/'render.html').write_text(render)
    if not illustrations_path:
        return
    illustrations=json.loads(illustrations_path.read_text())
    sections=[]
    for group,title,desc in [('before','먼저, 기존 두 코디','오늘 말씀하신 문제를 비교 기준으로 남겼습니다.'),('after','같은 노랑·핑크에서 다시 출발','기본 배색을 우선하고, 추천색은 자연스러운 위치와 톤으로 활용했습니다.'),('private','겉으로 쓰기 어려운 추천색이 남으면','레드·보라를 입력한 예입니다. 보라는 선택형 속옷 안내로 남기고, 실제 코디는 현재 배색을 유지합니다.')]:
        sections.append(f'<section><h2>{title}</h2><p class="intro">{desc}</p><div class="grid">'+''.join(card(c,illustrations) for c in rows if c['group']==group)+'</div></section>')
    script='''const version='outfit-first-20261002',key='dalha-'+version+'-reviews';let reviews={};try{reviews=JSON.parse(localStorage.getItem(key)||'{}')}catch{}document.querySelectorAll('[data-case]').forEach(el=>{el.value=reviews[el.dataset.case]?.[el.dataset.field]||'';el.addEventListener('input',()=>{const id=el.dataset.case;reviews[id]={...reviews[id],[el.dataset.field]:el.value,updated_at:new Date().toISOString()};try{localStorage.setItem(key,JSON.stringify(reviews));document.getElementById('status').textContent='이 브라우저에 의견을 보관했습니다.'}catch{document.getElementById('status').textContent='검토 기록을 파일로 내보내 주세요.'}})});document.getElementById('export').addEventListener('click',()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify({review_version:version,exported_at:new Date().toISOString(),reviews},null,2)],{type:'application/json'}));a.download='dalha-outfit-first-review-notes.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);document.getElementById('status').textContent='검토 기록을 내보냈습니다.'});'''
    page='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>달하 · 코디 우선 변경안</title><style>STYLE</style></head><body><main class="wrap"><div class="kicker">DALHA · OUTFIT FIRST</div><h1>코디를 먼저, 추천색은 자연스럽게</h1><p class="intro">2026.10.02 검토 의견을 반영한 변경안입니다. 실제 코디와 선택형 안내 문구를 함께 보실 수 있습니다.</p><div class="notice"><b>기본 코디 → 추천색 적용 후보 → 전체 착장 재평가</b><br>와다 조합이 없어도 추천이 동작합니다. 추천색을 모두 넣는 것보다 현실성과 전체 조화를 먼저 비교합니다.</div><p class="intro">남성 48세·가을·캐주얼의 고정 비교 사례입니다. 오늘의 실제 기온을 적용한 결과는 아닙니다. 서비스에서 쓰는 화보와 색상 변환 방식으로 그렸습니다.</p><div class="actions"><button id="export">내 검토 기록 내보내기</button><span class="status" id="status" aria-live="polite"></span></div>SECTIONS<section><h2>이번에 반영한 기준</h2><ul><li>추천색 A/B는 기존 실용 색상 목록에서 독립적으로 선택합니다. 와다는 후순위 참고 자료입니다.</li><li>오늘 사례의 남성 운동화는 흰색·검정부터 비교합니다.</li><li>핑크 이너·베이지 바지에 검정 겉옷을 추가하는 안은 전체 승인을 받은 것으로 처리하지 않습니다.</li><li>속옷 활용은 선택 사항입니다. 그림이나 코디 색상 수에 추가하지 않습니다.</li></ul></section><footer>이 파일은 변경 결과를 검토하기 위한 자료입니다. 새 코디의 미적 완성도를 승인한 기록은 아니며, 조건별 현실성 평가는 초기 편집 기준입니다. 기존 원본 화보의 형태와 겹침은 유지했습니다.</footer></main><script>SCRIPT</script></body></html>'''.replace('STYLE',STYLE).replace('SECTIONS',''.join(sections)).replace('SCRIPT',script)
    (output/'dalha-outfit-first-review.html').write_text(page)
    print(json.dumps(dict(cases=len(rows),file=str(output/'dalha-outfit-first-review.html')),ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--illustrations',type=Path)
    args=p.parse_args();build(args.output,args.illustrations)
