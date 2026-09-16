import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {renderLook} from '../assets/dalha-garments/integration.js';
import {escapeXml as esc} from '../assets/dalha-garments/engine.js';
const require=createRequire(import.meta.url);
const sharp=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'sharp'):'sharp');
const out=path.resolve('review-output/svg-integration');
const data=JSON.parse(fs.readFileSync(path.join(out,'automatic-sets.json')));
const fontPath=process.argv[2]||path.resolve('assets/dalha-garments/NanumGothic-Regular.ttf');
fs.copyFileSync(fontPath,path.join(out,'NanumGothic-Regular.ttf'));
fs.writeFileSync(path.join(out,'fonts.conf'),`<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>${out}</dir><cachedir>/tmp/dalha-svg-font-cache</cachedir></fontconfig>`);
process.env.FONTCONFIG_FILE=path.join(out,'fonts.conf');
const season={spring:'봄',summer:'여름',autumn:'가을',winter:'겨울'};
const tpos={casual:'캐주얼',business_casual:'비즈니스 캐주얼',business_formal:'비즈니스 포멀'};
const heading=s=>`${s.id} · ${season[s.season]} · ${s.age}대 ${s.gender==='male'?'남성':'여성'} · ${tpos[s.tpo]}`;
const text=(v,x,y,size=18)=>`<text x="${x}" y="${y}" font-family="NanumGothic" font-size="${size}" fill="#404940">${esc(v)}</text>`;
const swatch=(v,h,x,y)=>`<rect x="${x}" y="${y-15}" width="17" height="17" rx="4" fill="${h}" stroke="#aeb3ac"/>${text(v,x+25,y,15)}`;
const itemLabel=i=>`${i.applied_daily_color||'기본'}${i.color_relation==='similar'?' 톤':''} · ${i.color_name} · ${i.display_label||i.label}${i.wear_mode==='carry'?' (챙기기)':''}`;
const paletteOnly=l=>l.color_strategy.unresolved.map(x=>`${x.role} ${x.name}`).join(', ');
const card=l=>`<article data-look="${l.review_id}"><p class="review-state">${esc(l.review.verdict)}</p><p class="change-note">${esc(l.review.change_note)}</p><h3>${l.review_id} · 추천 ${l.recommendation_number}</h3>${renderLook(l,'review-'+l.review_id)}<ul class="items">${l.items.map(i=>`<li><i style="background:${i.hex}"></i>${esc(itemLabel(i))}</li>`).join('')}</ul>${l.color_strategy.unresolved.length?`<p class="palette-note">팔레트 안내: ${esc(paletteOnly(l))}</p>`:''}<p class="muted">${l.color_strategy.color_count}색${l.color_strategy.review_required?' · 배색 검토':''}</p><details><summary>추천색 적용 기록</summary>${l.items.filter(i=>i.applied_daily_color).map(i=>`<p>${esc(i.display_label||i.label)}: ${esc(i.source_color_name)} ${i.source_hex} → ${esc(i.color_name)} ${i.hex}${i.tone_reason?`<br>${esc(i.tone_reason)}`:''}</p>`).join('')}</details><details><summary>이전 검토 의견</summary><p>${esc(l.review.previous_note||"통과")}</p></details><label>판정 <select data-id="${l.review_id}">${["미검토","통과","수정 필요","수정 후 재검토"].map(v=>`<option${v===l.review.verdict?" selected":""}>${v}</option>`).join("")}</select></label><textarea data-note="${l.review_id}" placeholder="어색한 부분을 적어주세요" aria-label="${l.review_id} 메모"></textarea></article>`;
let overview=text('달하 · 자동 추천 연결 검토 12벌',28,40,26)+text('11벌 통과 유지 · 시계 배색 수정 · 가상 기온·시험 A/B 입력',28,68,14);
const sections=[];
for(const [index,s] of data.sets.entries()){
  const raw=`A ${s.raw.A.name} · B ${s.raw.B.name}`;
  const weather=`시험 체감온도 · 낮 ${s.weather.daytime_apparent_high}도 / 아침저녁 ${s.weather.evening_apparent_low}도`;
  let body=text(heading(s),25,40,24)+swatch('A · '+s.raw.A.name,s.raw.A.hex,27,77)+swatch('B · '+s.raw.B.name,s.raw.B.hex,430,77)+text(weather,27,108,14)+text(s.focus,27,134,14);
  for(const [j,l] of s.looks.entries()){
    const x=20+j*455;
    body+=`<rect x="${x}" y="157" width="440" height="800" rx="18" fill="white"/>`+text(`${l.review_id} · ${l.review.verdict}`,x+22,195,21);
    body+=renderLook(l,'sheet-'+l.review_id).replace('<svg ',`<svg x="${x+35}" y="205" width="360" height="528.75" `);
    l.items.forEach((i,k)=>body+=swatch(itemLabel(i),i.hex,x+22,755+k*25));
    if(l.color_strategy.unresolved.length)body+=text('팔레트 안내: '+paletteOnly(l),x+22,920,13);
    body+=text(`${l.color_strategy.color_count}색${l.color_strategy.review_required?' · 배색 검토':''}`,x+22,943,12);
  }
  body+=text('착장·색 위치 자동 선택 / 실제 개인 운세·현재 날씨 결과 아님 / 통과 유지 또는 수정 후 재검토',27,990,14);
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="940" height="1020"><rect width="940" height="1020" fill="#f6f5f0"/>${body}</svg>`;
  fs.writeFileSync(path.join(out,`자동추천_${s.id}.svg`),svg);
  await sharp(Buffer.from(svg)).png().toFile(path.join(out,`자동추천_${s.id}.png`));
  const ox=20+(index%2)*590,oy=92+Math.floor(index/2)*560;
  overview+=`<rect x="${ox}" y="${oy}" width="570" height="545" rx="16" fill="white"/>`+text(heading(s),ox+18,oy+32,19)+text(raw,ox+18,oy+60,16);
  s.looks.forEach((l,j)=>{overview+=renderLook(l,'overview-'+l.review_id).replace('<svg ',`<svg x="${ox+12+j*285}" y="${oy+82}" width="260" height="382" `)+text(`${l.review_id} · ${l.review.verdict}`,ox+84+j*285,oy+499,15);});
  sections.push(`<section data-season="${s.season}" data-gender="${s.gender}" data-tpo="${s.tpo}"><h2>${heading(s)}</h2><p class="raw"><span><i style="background:${s.raw.A.hex}"></i>A ${s.raw.A.name}</span><span><i style="background:${s.raw.B.hex}"></i>B ${s.raw.B.name}</span></p><p>${s.focus}<br><span class="muted">${weather}</span></p><div class="pair">${s.looks.map(card).join('')}</div></section>`);
}
const ov=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1785"><rect width="1200" height="1785" fill="#f6f5f0"/>${overview}</svg>`;
await sharp(Buffer.from(ov)).png().toFile(path.join(out,'달하_자동추천_12벌_모아보기.png'));
const font=fs.readFileSync(fontPath).toString('base64');
const html=`<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>달하 자동 추천 · 6조건 12벌</title><style>@font-face{font-family:D;src:url(data:font/ttf;base64,${font})}*{box-sizing:border-box}body{margin:0;background:#f6f5f0;color:#3a443d;font:15px D,sans-serif}main{max-width:1050px;margin:auto;padding:22px}h1{font-size:26px}h2{font-size:20px;line-height:1.6}h3{font-size:19px}p{line-height:1.65}section{margin:36px 0}.filters,.raw{display:flex;gap:12px;flex-wrap:wrap}.raw span{display:flex;align-items:center;gap:7px}i{display:inline-block;width:18px;height:18px;flex:0 0 18px;border-radius:4px;border:1px solid #b2b8ad}.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}article{background:white;border-radius:18px;padding:20px;min-width:0}article svg{display:block;width:100%;height:auto;max-height:560px}.items{list-style:none;padding:0;line-height:1.8}.items li{display:flex;gap:8px;align-items:center;margin:5px 0;font-size:13px}.review-state{font-size:13px;font-weight:bold}.change-note{font-size:13px;background:#edf2ed;padding:10px;border-radius:8px}article[hidden],section[hidden]{display:none}.muted{font-size:12px;color:#677467}.palette-note{font-size:13px;padding:8px 12px;border-radius:8px;background:#f3f1e9}select,button,textarea{font:inherit;color:inherit;background:white;border:1px solid #b6c0b2;border-radius:8px;padding:10px;max-width:100%}button{cursor:pointer}textarea{display:block;margin-top:10px;width:100%;min-height:70px}details{font-size:12px;margin:14px 0}details p{overflow-wrap:anywhere}summary{cursor:pointer}label{line-height:2.5}header p{max-width:800px}#status{font-size:13px}@media(max-width:640px){main{padding:14px}h1{font-size:22px}.pair{grid-template-columns:1fr}article{padding:16px}.filters label{flex:1 1 100%}.filters select{width:100%}article svg{max-height:485px}}</style></head><body><main><header><h1>자동 추천 검토 · 6조건 12벌</h1><p>검토 의견을 반영했습니다. 목폴라와 50대 여성 포멀 무릎 기장은 요청하신 변형을 적용했습니다. 계절·기온·추천 A/B는 시험 입력이며, 실제 오늘의 개인 운세 결과는 아닙니다.</p><p class="muted">11벌은 통과했습니다. 18-2의 시계 배색만 다시 확인하면 됩니다. 앞서 통과한 24벌의 기록도 별도로 유지됩니다.</p></header><div class="filters"><label>계절 <select id="season"><option value="all">전체</option>${Object.entries(season).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><label>성별 <select id="gender"><option value="all">전체</option><option value="male">남성</option><option value="female">여성</option></select></label><label>TPO <select id="tpo"><option value="all">전체</option>${Object.entries(tpos).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><label>검토 대상 <select id="review"><option value="all">전체 12벌</option><option value="pending">다시 볼 착장만</option></select></label><button id="save">검토 기록 저장</button><button id="load">기록 불러오기</button><input id="file" type="file" accept="application/json" hidden></div><p id="count">6세트 표시</p><p id="status">메모는 이 브라우저에 보관됩니다. 다른 기기로 옮기려면 기록을 저장해 불러오세요.</p>${sections.join('')}</main><script>
const storageKey='dalha-auto-review-13-18-v3';
const reviewMeta=${JSON.stringify(Object.fromEntries(data.sets.flatMap(s=>s.looks).map(l=>[l.review_id,l.review])))};
const verdicts=['미검토','통과','수정 필요','수정 후 재검토'];
function records(){return [...document.querySelectorAll('[data-id]')].map(e=>({id:e.dataset.id,revision:3,previous_verdict:reviewMeta[e.dataset.id].previous_verdict,previous_note:reviewMeta[e.dataset.id].previous_note,change_note:reviewMeta[e.dataset.id].change_note,verdict:e.value,note:document.querySelector('[data-note="'+e.dataset.id+'"]').value}));}
function apply(rows){if(!Array.isArray(rows)||rows.some(r=>r.revision!==3))throw new Error('수정본 기록 파일 확인 필요');for(const r of rows){if(!/^1[3-8]-[12]$/.test(r.id)||!verdicts.includes(r.verdict))continue;document.querySelector('[data-id="'+r.id+'"]').value=r.verdict;document.querySelector('[data-note="'+r.id+'"]').value=typeof r.note==='string'?r.note:'';}}
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(records()));document.getElementById('status').textContent='이 브라우저에 기록했습니다. 다른 기기에서는 파일을 불러오세요.';}catch{document.getElementById('status').textContent='이 환경에서는 자동 보관이 안 됩니다. 검토 기록 저장을 눌러주세요.';}}
try{const saved=localStorage.getItem(storageKey);if(saved)apply(JSON.parse(saved));}catch{}
document.querySelectorAll('[data-id],[data-note]').forEach(e=>e.addEventListener('change',()=>{persist();filter();}));
const keys=['season','gender','tpo'];function filter(){let n=0,m=0;document.querySelectorAll('section').forEach(s=>{const matches=keys.every(k=>document.getElementById(k).value==='all'||s.dataset[k]===document.getElementById(k).value);let visible=0;s.querySelectorAll('article').forEach(a=>{const verdict=a.querySelector('[data-id]').value;a.querySelector('.review-state').textContent=verdict;a.hidden=document.getElementById('review').value==='pending'&&verdict==='통과';if(!a.hidden)visible++;});s.hidden=!matches||!visible;if(!s.hidden){n++;m+=visible;}});document.getElementById('count').textContent=n+'세트 · '+m+'벌 표시';}keys.concat('review').forEach(k=>document.getElementById(k).onchange=filter);filter();
document.getElementById('save').onclick=()=>{persist();const u=URL.createObjectURL(new Blob([JSON.stringify(records(),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='달하_자동추천_검토기록.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};
document.getElementById('load').onclick=()=>document.getElementById('file').click();document.getElementById('file').onchange=async e=>{try{apply(JSON.parse(await e.target.files[0].text()));persist();filter();}catch{document.getElementById('status').textContent='이 수정본에서 저장한 검토 기록 JSON 파일을 불러와 주세요.';}};
</script></body></html>`;
fs.writeFileSync(path.join(out,'달하_자동추천_6조건_검토.html'),html);
console.log('Rendered 12 automatic outfits, 6 sheets, overview and standalone review.');
