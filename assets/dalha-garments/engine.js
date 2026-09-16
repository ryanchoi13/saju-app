import {byName} from './catalog.js';
import {renderGarment as legacy} from './garments.js';
import {shoeDrawing} from './shoes.js';

export const escapeXml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const color=s=>/^#[0-9a-f]{6}$/i.test(s)?s:'#c5d3df';
function ink(hex){const a=hex.slice(1).match(/../g).map(x=>parseInt(x,16));const l=(a[0]*.2126+a[1]*.7152+a[2]*.0722)/255;return l<.36?{edge:'#484c51',detail:'#353a40'}:{edge:'#7d7d78',detail:'#999992'};}
const bool=s=>s===true||s==='true';
function painter(fill){fill=color(fill);const c=ink(fill);return {
 p:(d,kind='fabric')=>`<path data-layer="${kind}" d="${d}" fill="${kind==='detail'?'none':fill}" stroke="${kind==='detail'?c.detail:c.edge}" stroke-width="${kind==='detail'?.85:1.25}" stroke-linecap="round" stroke-linejoin="round"/>`,
 line:d=>`<path data-layer="detail" d="${d}" fill="none" stroke="${c.detail}" stroke-width=".85" stroke-linecap="round" stroke-linejoin="round"/>`
};}
export function upperGeometry(name,gender='male',bodyEase=0){
 const f=gender==='female', w=(f?60:52)-bodyEase, shoulder=f?54:48;
 const long=/긴팔|니트|맨투맨|후드/.test(name),knit=/니트|맨투맨|후드/.test(name);
 // One closed perimeter: shoulder -> sleeve -> underarm -> hem. No floating sleeve polygons.
 const left=long?`Q${shoulder-11} 53 ${shoulder-16} 76 L17 188 Q27 193 38 190 L${w} 100 Q${w+1} 132 ${w} 154 L${w} 184`:`Q${shoulder-9} 53 ${shoulder-14} 65 L18 97 Q31 108 46 112 L${w} 96 Q${w+1} 134 ${w} 154 L${w} 184`;
 const right=long?`L${200-w} 154 Q${199-w} 132 ${200-w} 100 L162 190 Q173 193 183 188 L${216-shoulder} 76 Q${211-shoulder} 53 ${200-shoulder} 49`:`L${200-w} 154 Q${199-w} 134 ${200-w} 96 L154 112 Q169 108 182 97 L${214-shoulder} 65 Q${209-shoulder} 53 ${200-shoulder} 49`;
 const outline=`M80 32 Q${shoulder+10} 42 ${shoulder} 49 ${left} Q100 192 ${200-w} 184 ${right} Q${190-shoulder} 42 120 32 Q100 39 80 32 Z`;
 return {outline,w,long,knit};
}
function topDrawing(name,g,fill,bodyEase=0){const {p,line}=painter(fill),a=upperGeometry(name,g,bodyEase);let s=p(a.outline);
 if(/캐주얼 셔츠|정장 셔츠/.test(name)){
  const formal=/정장/.test(name);
  s+=p(formal?'M80 32 L100 53 L88 66 L73 45 Z':'M80 32 L100 58 L83 54 L77 64 L66 57 L73 40 Z');
  s+=p(formal?'M120 32 L100 53 L112 66 L127 45 Z':'M120 32 L100 58 L117 54 L123 64 L134 57 L127 40 Z');
  s+=line('M100 56 L100 187');
 }else if(/폴로/.test(name)){s+=p('M80 33 L100 52 L87 61 L73 45 Z')+p('M120 33 L100 52 L113 61 L127 45 Z')+line('M100 52 L100 82');}
 else if(/후드/.test(name)){s+=p('M79 32 Q68 25 74 15 Q100 3 126 15 Q132 25 121 32 Q116 54 100 62 Q84 54 79 32 Z')+line('M91 49 L88 81 M109 49 L112 81');}
 else{s+=line('M81 34 Q100 65 119 34');if(name==='니트')s+=line('M77 36 Q100 71 123 36');}
 if(a.long)s+=line('M19 177 L40 180 M181 177 L160 180');
 if(a.knit)s+=line(bodyEase?`M${a.w} 180 Q100 187 ${200-a.w} 180`:`M${a.w} 174 Q100 182 ${200-a.w} 174`);
 return s;
}
export function bottomDrawing(name,g,fill,trouserExtraLength=0){const{p,line}=painter(fill),w=g==='female'?60:52,skirt=/스커트/.test(name);let s='';
 if(skirt){const suit=name==='수트 스커트',end=name==='롱 스커트'?225:(suit?164:196),edge=suit?51:27;s=p(`M${w} 26 L${200-w} 26 Q${200-w+7} 52 ${200-edge} ${end} Q100 ${end+9} ${edge} ${end} Q${w-7} 52 ${w} 26 Z`);if(!suit)s+=line(`M${w+10} 56 L${edge+19} ${end-8} M${190-w} 56 L${181-edge} ${end-8}`);else s+=line('M113 140 L113 160');}
 else{const end=name==='반바지'?121:224+Math.min(40,Math.max(0,trouserExtraLength)),wide=/데님|면바지/.test(name),edge=wide?47:51;s=p(`M${w} 26 L${200-w} 26 Q151 61 ${200-edge} ${end} Q128 ${end+5} 109 ${end} L100 91 L91 ${end} Q72 ${end+5} ${edge} ${end} Q49 61 ${w} 26 Z`)+line('M100 39 L100 89');if(/데님/.test(name))s+=line('M59 43 Q66 61 83 61 M141 43 Q134 61 117 61');if(/슬랙스|수트/.test(name))s+=line(`M75 45 L72 ${end-8} M125 45 L128 ${end-8}`);}
 s+=p(`M${w} 25 Q100 30 ${200-w} 25 L${201-w} 38 Q100 43 ${w-1} 38 Z`);return s;
}
function dressDrawing(name,g,fill){
 const {p,line}=painter(fill),long=/긴팔/.test(name);
 // A single fabric perimeter connects the bodice and skirt without a waist seam.
 // Neck, shoulder and sleeve coordinates retain the existing dress proportions.
 const left=long?'Q43 53 38 76 L17 188 Q27 193 38 190 L60 100':'Q45 53 40 65 L18 97 Q31 108 46 112 L60 96';
 const right=long?'L162 190 Q173 193 183 188 L162 76 Q157 53 146 49':'L154 112 Q169 108 182 97 L160 65 Q155 53 146 49';
 const outline=`M80 32 Q64 42 54 49 ${left} Q60 124 62 146 Q62 166 55 198 L35 276 Q100 288 165 276 L145 198 Q138 166 138 146 Q140 124 140 ${long?100:96} ${right} Q136 42 120 32 Q100 39 80 32 Z`;
 return p(outline)+line('M81 34 Q100 65 119 34 M69 200 Q62 238 52 270 M131 200 Q138 238 148 270');
}
export function outerGeometry(name,g='male'){
 const coat=name==='코트',puff=name==='패딩',tailored=/코트|재킷|블레이저/.test(name),f=g==='female';
 const hem=coat?269:(puff?172:198),side=f?55:48,shoulder=puff?42:46;
 // Continuous sleeves with relaxed straight fall, no elbow kink.
 const left=puff?'M79 28 Q58 34 36 48 Q23 55 17 80 L1 157 Q0 177 4 188 Q17 198 31 192 L44 108 Q43 131 40 145 L38 153 Q39 166 52 170 Q69 175 80 170 Q86 168 86 160 ':`M79 28 Q${shoulder+7} 39 ${shoulder} 45 Q${shoulder-10} 52 ${shoulder-14} 77 L10 191 Q22 198 36 195 L${side} 103 Q${side+2} 139 ${side} 167 L${side-2} ${hem-3} Q65 ${hem+4} 85 ${hem} `;
 const inner=tailored?`Q91 ${hem-30} 91 137 Q88 90 79 28 Z`:puff?'Q88 138 86 83 Q84 50 79 28 Z':`Q88 ${hem-30} 86 83 Q84 50 79 28 Z`;
 const neck=tailored?'M79 28 L74 48 L66 61 L80 70 L69 80 Q80 108 91 137':'M79 28 Q68 29 70 47 Q73 61 86 69';
 const aperture=tailored?`M79 28 Q88 90 91 137 Q91 ${hem-30} 85 ${hem} L115 ${hem} Q109 ${hem-30} 109 137 Q112 90 121 28 Z`:puff?'M79 28 Q84 50 86 83 Q88 138 86 160 Q86 168 80 170 L120 170 Q114 168 114 160 Q112 138 114 83 Q116 50 121 28 Z':`M79 28 Q84 50 86 83 Q88 ${hem-30} 85 ${hem} L115 ${hem} Q112 ${hem-30} 114 83 Q116 50 121 28 Z`;
 return {left:left+inner,neck,aperture,hem,side,puff,tailored};
}
function outerDrawing(name,g,fill,open,backing=false){const {p,line}=painter(fill),a=outerGeometry(name,g);let left=p(a.left)+(a.puff?'':line(a.neck));
 if(name==='패딩'){
  const rgb=fill.slice(1).match(/../g).map(v=>parseInt(v,16));
  const seam=rgb.reduce((a,b)=>a+b,0)<300?'#'+rgb.map(v=>Math.round(v*.78+150*.22).toString(16).padStart(2,'0')).join(''):ink(fill).detail;
  left+=line('M20 83 Q50 91 84 85 M12 118 Q25 123 39 122 M44 129 Q64 136 85 130 M5 155 Q18 161 33 158 M6 182 Q18 190 31 185').replace(/stroke="[^"]*"/,`stroke="${seam}"`);
  left+=p('M78 30 Q66 23 70 11 Q78 6 86 11 L91 43 L86 60 Q80 47 78 30 Z')+line('M75 15 Q80 13 85 16');
 }
 if(/블루종|바람막이|후드/.test(name))left+=line(`M49 185 Q65 192 85 187 M12 181 L37 185`);
 if(name==='집업 후드')left+=line('M79 28 Q69 11 54 24 Q52 36 64 48');
 const lining='#'+fill.slice(1).match(/../g).map(v=>Math.round(parseInt(v,16)*.56+244*.44).toString(16).padStart(2,'0')).join('');
 const backCollar=a.puff?`<g data-role="back-collar">${p('M74 13 Q100 0 126 13 L121 35 Q100 29 79 35 Z')}</g>`:'';
 let s=(backing?`<path data-layer="lining" d="M79 29 Q100 36 121 29 L126 ${a.hem-3} Q100 ${a.hem+1} 74 ${a.hem-3} Z" fill="${lining}" stroke="${ink(lining).edge}" stroke-width="1"/>`:'')+backCollar+left+`<g transform="translate(200 0) scale(-1 1)">${left}</g>`;
 if(!open)s+=p(a.aperture)+line(`M100 40 L100 ${a.hem}`);
 return s;
}
export function garmentInner(name,{gender='male',fill='#c5d3df',open=true,backing=false,trouserExtraLength=0,bodyEase=0}={}){
 fill=color(fill);let c=byName[name]?.category;if(!c)throw Error(`알 수 없는 도안: ${name}`);
 if(c==='상의')return topDrawing(name,gender,fill,bodyEase);
 if(c==='하의')return bottomDrawing(name,gender,fill,trouserExtraLength);
 if(c==='원피스')return dressDrawing(name,gender,fill);
 if(c==='아우터')return outerDrawing(name,gender,fill,bool(open),backing);
 if(c==='신발')return shoeDrawing(name,gender,fill);
 const k=ink(fill);return legacy(name,{gender,fill}).replace(/^<svg[^>]*>/,'').replace(/<\/svg>$/,'').replace(/class="(fabric|accent|detail-fill|detail|opening)"/g,(_,kind)=>`data-layer="${kind}" fill="${kind==='detail'?'none':fill}" stroke="${kind==='detail'?k.detail:k.edge}" stroke-width="${kind==='detail'?.85:1.25}" stroke-linecap="round" stroke-linejoin="round"`);
}
export function renderGarment(name,options={}){const h=byName[name]?.category==='원피스'?380:(name==='코트'?290:240);return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 ${h}" role="img" aria-label="${escapeXml(name)}">${garmentInner(name,options)}</svg>`;}
export function normalizeSpec(s={}){const n={gender:'male',top:'긴팔 정장 셔츠',bottom:'수트 바지',dress:'',outer:'수트 재킷',outerMode:'wear',outerOpen:true,shoe:'옥스퍼드',bag:'',topColor:'#cfdfed',bottomColor:'#535a64',outerColor:'#535a64',shoeColor:'#333638',tuck:'in',suitLinked:true,...s};n.outerOpen=bool(n.outerOpen);n.suitLinked=bool(n.suitLinked);if(n.outerMode!=='carry')n.outerMode='wear';if(n.suitLinked&&n.outer==='수트 재킷'&&/수트/.test(n.bottom))n.bottomColor=n.outerColor;return n;}
export function outfitInner(input={},prefix='look'){
 const s=normalizeSpec(input),worn=!!s.outer&&s.outerMode==='wear',carried=!!s.outer&&s.outerMode==='carry',a=worn?outerGeometry(s.outer,s.gender):null;
 const transform=`translate(${carried?30:60} 8)`;
 const bodyEase=a?.puff&&s.tuck==='out'&&/니트|후드티|맨투맨/.test(s.top)?5:0;
 let upper=garmentInner(s.dress||s.top,{gender:s.gender,fill:s.topColor,bodyEase});
 let defs='',under='';
 const lower= `<g data-role="bottom" transform="translate(0 134)">${garmentInner(s.bottom,{gender:s.gender,fill:s.bottomColor,trouserExtraLength:s.trouserExtraLength||0})}</g>`;
 if(!s.dress&&s.tuck==='in'){defs+=`<clipPath id="${prefix}-tuck"><rect x="0" y="0" width="200" height="166"/></clipPath>`;upper=`<g clip-path="url(#${prefix}-tuck)">${upper}</g>`;}
 if(worn){const shortInner=a.puff&&!s.dress,w=shortInner?upperGeometry(s.top,s.gender,bodyEase).w-2:0,y=a.hem-18;
  const clip=shortInner?(s.outerOpen?`<path d="M79 28 Q84 50 86 83 Q88 138 86 ${y} L${w} ${y} L${w} 420 L${200-w} 420 L${200-w} ${y} L114 ${y} Q112 138 114 83 Q116 50 121 28 Z"/>`:`<rect x="${w}" y="${y}" width="${200-2*w}" height="400"/>`):`${s.outerOpen?`<path d="${a.aperture}"/>`:''}<rect x="0" y="${a.hem+1}" width="200" height="400"/>`;
  defs+=`<clipPath id="${prefix}-inner">${clip}</clipPath>`;upper=`<g data-role="inner-clipped" clip-path="url(#${prefix}-inner)">${upper}</g>`;
 }
 if(s.dress)under=upper;else under=s.tuck==='in'?upper+lower:lower+upper;
 const carryLayer=carried?`<g data-role="carried-outer" transform="translate(145 54) scale(.88)">${garmentInner(s.outer,{gender:s.gender,fill:s.outerColor,open:s.outerOpen,backing:true})}</g>`:'';
 let body=`<defs>${defs}</defs>${carryLayer}<g transform="${transform}">${under}${worn?`<g data-role="worn-outer">${garmentInner(s.outer,{gender:s.gender,fill:s.outerColor,open:s.outerOpen})}</g>`:''}</g>`;
 body+=`<g data-role="shoes" transform="translate(${carried?75:99} 332) scale(.58)">${garmentInner(s.shoe,{gender:s.gender,fill:s.shoeColor})}</g>`;
 if(s.bag)body+=`<g data-role="bag" transform="translate(258 334) scale(.62) translate(-100 -120)">${garmentInner(s.bag,{fill:s.bagColor||s.outerColor})}</g>`;
 let tieLayer='';
 for(const [i,name] of (s.accessories||[]).slice(0,3).entries()){
  const placements={'모자':'translate(-2 -22) scale(.52)','시계':'translate(0 148) scale(.31)','머플러':'translate(-10 40) scale(.42)','귀걸이':'translate(-43 -38) scale(.72)','목걸이':'translate(0 7) scale(.31)','넥타이':`translate(${(carried?130:160)-36} 39) scale(.36 .64)`};
  const placement=placements[name]||`translate(0 ${120+i*68}) scale(.31)`;
  let art=garmentInner(name,{gender:s.gender,fill:s.accessoryColor||'#907b56'});
  if(name==='목걸이')art=art.replace(/stroke-width="0.85"/g,'stroke-width="2.3"').replace(/stroke="[^"]*"/g,`stroke="${escapeXml(s.accessoryColor||'#907b56')}"`);
  if(name==='넥타이'&&s.tieTwoTone){const id=`${prefix}-tie-${i}`;art+=`<defs><clipPath id="${id}"><path d="M83 34 L117 34 L111 69 L127 176 L100 211 L73 176 L89 69 Z"/></clipPath></defs><g clip-path="url(#${id})" fill="${escapeXml(s.tieAccentColor||'#b08278')}"><path d="M65 93 L134 61 L139 75 L65 110 Z M65 143 L140 108 L140 124 L65 160 Z M65 193 L140 158 L140 174 L65 210 Z"/></g>`;}
  const layer=`<g data-role="accessory" aria-label="${escapeXml(name)}" transform="${placement}">${art}</g>`;
  if(name==='넥타이')tieLayer+=layer;else body+=layer;
 }
 return body+tieLayer;
}
export function renderOutfit(input={},prefix='look'){return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 470" role="img" aria-label="코디 도안" class="outfit-svg">${outfitInner(input,prefix)}</svg>`;}
export const examples=[
 {title:'01 · 남성 수트',note:'착용 · 셔츠는 재킷 안쪽에',outer:'수트 재킷',top:'긴팔 정장 셔츠',bottom:'수트 바지',shoe:'옥스퍼드',tuck:'in',outerOpen:true},
 {title:'02 · 남성 캐주얼 셔츠',note:'꺼내 입기 · 허리 폭 연결',outer:'',top:'반팔 캐주얼 셔츠',bottom:'면바지',shoe:'로퍼',tuck:'out',topColor:'#c4d7e5',bottomColor:'#e7decd'},
 {title:'03 · 남성 니트와 코트',note:'착용 · 열린 앞부분으로 니트 노출',outer:'코트',top:'니트',bottom:'데님 바지',shoe:'운동화',tuck:'out',topColor:'#b9c0ad',bottomColor:'#58677b',outerColor:'#777b78',shoeColor:'#ece9e1'},
 {title:'04 · 여성 티셔츠와 가디건',note:'착용 · 소매는 겉옷 안으로',gender:'female',outer:'가디건',top:'반팔 티셔츠',bottom:'미디 스커트',shoe:'플랫슈즈',tuck:'in',topColor:'#dfbbb5',bottomColor:'#a4a3a4',outerColor:'#bfc5b3'},
 {title:'05 · 남성 코트',note:'착용 · 열린 코트와 아이보리 니트',outer:'코트',top:'니트',bottom:'슬랙스',shoe:'더비 구두',tuck:'out',topColor:'#efe9dc',bottomColor:'#59677b',outerColor:'#585d61',outerOpen:true},
 {title:'06 · 남성 패딩',note:'착용 · 열린 패딩과 아이보리 니트',outer:'패딩',top:'니트',bottom:'면바지',shoe:'운동화',tuck:'out',topColor:'#efe9dc',bottomColor:'#747372',outerColor:'#adc4d6',outerOpen:true}
];
