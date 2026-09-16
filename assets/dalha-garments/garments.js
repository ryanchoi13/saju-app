import { byName } from './catalog.js';

const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const line = (d, cls='detail') => `<path class="${cls}" d="${d}"/>`;
const shape = (d, cls='fabric') => `<path class="${cls}" d="${d}"/>`;
const rect = (x,y,w,h,rx=0,cls='fabric') => `<rect class="${cls}" x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}"/>`;
const circle = (cx,cy,r,cls='detail-fill') => `<circle class="${cls}" cx="${cx}" cy="${cy}" r="${r}"/>`;

function svg(inner, {fill='#d9e6f1', accent='#f6f1e8', outline='#74777a', detail='#85888b', label='', viewBox='0 0 200 240'}={}) {
  return `<svg class="garment-svg" viewBox="${viewBox}" role="img" aria-label="${esc(label)}" xmlns="http://www.w3.org/2000/svg" style="--fill:${fill};--accent:${accent};--outline:${outline};--detail:${detail}">${inner}</svg>`;
}

function upper(name, gender='male') {
  const female=gender==='female', shoulder=female?47:40, waist=female?62:55;
  const long=/긴팔|니트|맨투맨|후드/.test(name), shirt=/캐주얼 셔츠|정장 셔츠/.test(name), polo=/폴로/.test(name), hood=/후드/.test(name), knit=/니트|맨투맨/.test(name);
  const sleeve=long
    ? `M${shoulder} 48 L18 82 Q14 112 21 158 L42 153 L48 91`
    : `M${shoulder} 48 L17 78 Q29 92 47 98`;
  const sleeveR=long
    ? `M${200-shoulder} 48 L182 82 Q186 112 179 158 L158 153 L152 91`
    : `M${200-shoulder} 48 L183 78 Q171 92 153 98`;
  const hem=shirt?192:(knit?185:188);
  let body=shape(`M${shoulder} 48 Q72 34 84 35 Q100 44 116 35 Q128 34 ${200-shoulder} 48 L152 91 L${145-waist/8} ${hem} Q100 ${hem+7} ${55+waist/8} ${hem} L48 91 Z`);
  body+=shape(sleeve)+shape(sleeveR);
  if (shirt) {
    body+=shape('M82 38 L100 57 L118 38 L126 60 L109 72 L100 60 L91 72 L74 60 Z','accent');
    body+=line(`M100 60 L100 ${hem}`)+line('M74 60 L91 72 M126 60 L109 72');
    if (/캐주얼/.test(name)) body+=line(`M67 ${hem-5} Q100 ${hem+7} 133 ${hem-5}`);
  } else {
    body+=line('M82 39 Q100 61 118 39');
  }
  if (polo) body+=shape('M83 40 L100 58 L117 40 L122 55 L107 66 L100 58 L93 66 L78 55 Z','accent')+line('M100 58 L100 89');
  if (hood) body+=shape('M72 45 Q100 14 128 45 Q124 70 100 77 Q76 70 72 45 Z','accent')+line('M91 61 L88 91 M109 61 L112 91');
  if (knit) body+=line(`M57 ${hem-14} Q100 ${hem-8} 143 ${hem-14} M22 145 L42 141 M178 145 L158 141`);
  return body;
}

function bottom(name, gender='male') {
  const female=gender==='female';
  if (/스커트/.test(name)) {
    const long=/롱/.test(name), suit=/수트/.test(name), y2=long?224:(suit?183:199), spread=long?58:(suit?39:51);
    return shape(`M62 34 Q100 29 138 34 L${100+spread} ${y2-8} Q100 ${y2+8} ${100-spread} ${y2-8} Z`)+rect(61,28,78,17,5)+(!suit?line(`M76 54 L${100-spread+12} ${y2-18} M124 54 L${100+spread-12} ${y2-18}`):line('M100 45 L100 172'));
  }
  const shorts=/반바지/.test(name), y2=shorts?139:224, wide=/데님|면바지/.test(name), outside=wide?47:55, inside=93;
  let s=shape(`M52 30 Q100 24 148 30 L${153-(wide?0:7)} ${y2} Q128 ${y2+4} 108 ${y2} L100 96 L92 ${y2} Q72 ${y2+4} ${outside} ${y2} Z`);
  s+=rect(51,25,98,17,5)+line(`M100 43 L100 96 M67 54 Q76 67 91 67 M133 54 Q124 67 109 67`);
  if (/데님/.test(name)) s+=line('M56 47 L144 47 M61 34 L61 45 M139 34 L139 45');
  if (/슬랙스|수트/.test(name)) s+=line(`M76 43 L72 ${y2-7} M124 43 L128 ${y2-7}`);
  return s;
}

function dress(name) {
  const longSleeve=/긴팔/.test(name), sleeve=longSleeve
    ? `${shape('M56 47 L23 78 Q18 115 27 151 L47 147 L55 92')} ${shape('M144 47 L177 78 Q182 115 173 151 L153 147 L145 92')}`
    : `${shape('M57 47 L24 75 Q34 91 55 98')} ${shape('M143 47 L176 75 Q166 91 145 98')}`;
  return shape('M57 47 Q77 34 86 37 Q100 48 114 37 Q123 34 143 47 L145 99 L165 220 Q100 236 35 220 L55 99 Z')+sleeve+line('M85 38 Q100 56 115 38 M55 99 Q100 109 145 99 M72 107 L54 210 M128 107 L146 210');
}

function outer(name, gender='male', open=true) {
  const female=gender==='female', shoulder=female?50:43, waist=female?62:55, coat=/코트/.test(name), puffer=/패딩/.test(name), blazer=/블레이저|수트 재킷/.test(name), cardigan=/가디건/.test(name), hood=/후드/.test(name), y2=coat?224:190;
  let s=shape(`M${shoulder} 45 Q72 31 84 34 Q100 43 116 34 Q128 31 ${200-shoulder} 45 L181 78 Q183 119 175 ${coat?174:158} L154 ${coat?168:153} L148 91 L${144-waist/10} ${y2} Q121 ${y2+6} 103 ${y2-1} Q82 ${y2+6} ${56+waist/10} ${y2} L52 91 L46 ${coat?168:153} L25 ${coat?174:158} Q17 119 19 78 Z`);
  if (open) {
    s+=shape(`M82 37 Q100 45 118 37 L128 57 L113 79 L104 ${y2} L96 ${y2} L87 79 L72 57 Z`,'opening');
    s+=line(`M82 37 L87 79 L96 ${y2} M118 37 L113 79 L104 ${y2}`);
  } else s+=line(`M100 54 L100 ${y2}`);
  if (blazer) s+=line(open?'M72 57 L91 91 L100 72 M128 57 L109 91 L100 72':'M77 57 L100 88 L123 57');
  if (hood) s+=shape('M72 45 Q100 13 128 45 Q121 70 100 75 Q79 70 72 45 Z','accent');
  if (puffer) for(let y=82;y<174;y+=25)s+=line(`M32 ${y} Q100 ${y+8} 168 ${y}`);
  if (/바람막이|블루종/.test(name)) s+=line(`M54 ${y2-13} Q100 ${y2-5} 146 ${y2-13}`);
  if (cardigan) s+=line(`M78 44 L100 70 L122 44 M100 70 L100 ${y2}`);
  return s;
}

function footwear(name) {
  if (/부츠/.test(name)) {
    const ankle=/앵클/.test(name), top=ankle?91:38;
    return shape(`M53 ${top} L126 ${top+4} L133 151 Q156 157 175 177 Q154 205 42 198 Q30 184 48 169 Z`)+line(`M55 ${top+10} L125 ${top+14} M49 169 Q103 185 171 177`);
  }
  if (/샌들/.test(name)) return shape('M35 133 Q85 102 148 129 Q174 144 166 171 Q106 191 42 174 Q26 158 35 133 Z')+line('M60 132 Q93 160 126 128 M75 119 Q101 144 144 136');
  if (/펌프스/.test(name)) return shape('M31 143 Q69 119 126 132 Q147 137 173 165 L165 179 Q103 193 42 178 Q25 168 31 143 Z')+shape('M153 176 L170 176 L166 205 L155 205 Z','accent')+line('M57 139 Q93 165 130 136');
  if (/플랫슈즈/.test(name)) return shape('M27 148 Q68 117 132 136 Q154 141 175 164 Q171 187 44 181 Q24 176 27 148 Z')+line('M55 143 Q92 169 135 139');
  let s=shape('M27 143 Q57 122 88 113 Q104 105 120 127 Q143 148 174 146 L178 178 Q122 196 40 183 Q21 173 27 143 Z');
  s+=line('M29 151 Q91 176 176 154 M107 124 L129 146');
  if (/운동화/.test(name)) s+=line('M91 126 L122 151 M83 132 L114 157 M45 173 Q105 187 176 169');
  if (/옥스퍼드|더비/.test(name)) s+=line('M77 132 L112 154 M83 125 L118 147 M88 118 L123 140');
  if (/로퍼/.test(name)) s+=line('M79 132 Q101 151 126 140 M84 136 L119 145');
  return s;
}

function bag(name) {
  if (name==='백팩') return shape('M57 72 Q37 73 37 110 L40 181 L53 184 L53 101 Q54 88 66 89 Z')+shape('M143 72 Q163 73 163 110 L160 181 L147 184 L147 101 Q146 88 134 89 Z')+line('M86 52 L86 35 Q100 20 114 35 L114 52')+shape('M50 88 Q49 51 100 49 Q151 51 150 88 L155 183 Q154 199 137 201 L63 201 Q46 199 45 183 Z')+line('M60 97 L60 85 Q62 61 100 61 Q138 61 140 85 L140 97')+shape('M67 130 Q100 126 133 130 L135 177 Q100 187 65 177 Z')+line('M68 140 L132 140 M125 140 L125 148');
  const shoulder=/숄더|핸드백/.test(name), cross=/크로스/.test(name), tote=/토트/.test(name);
  let s=shape(`M42 94 Q100 84 158 94 L167 190 Q100 205 33 190 Z`);
  if (shoulder||tote) s+=line(`M66 96 Q68 ${shoulder?35:55} 100 ${shoulder?35:55} Q132 ${shoulder?35:55} 134 96`);
  if(cross) s+=line('M45 178 Q102 91 158 48');
  return s+line('M42 111 Q100 121 158 111');
}

function accessory(name) {
  const map={
    '시계':()=>circle(100,120,43,'fabric')+circle(100,120,30,'accent')+rect(86,22,28,58,8)+rect(86,160,28,58,8)+line('M100 120 L100 96 M100 120 L119 130'),
    '모자':()=>shape('M51 126 Q57 73 105 70 Q151 69 162 121 L158 138 Q105 151 51 136 Z')+shape('M52 124 Q34 126 16 142 Q12 147 23 150 Q60 160 109 139 Q78 138 52 124 Z')+line('M105 72 Q82 91 83 131 M52 124 Q106 142 159 126')+shape('M98 71 Q98 65 105 65 Q112 65 112 71 Z'),
    '머플러':()=>shape('M69 27 Q122 17 133 52 L116 132 L138 212 L106 219 L91 144 L78 215 L47 206 L65 126 L53 59 Z')+line('M65 126 Q92 142 116 132'),
    '장갑':()=>shape('M45 114 L40 57 Q41 43 52 47 L62 91 L58 38 Q60 25 71 31 L79 87 L80 28 Q84 16 94 25 L96 87 L103 37 Q109 27 118 36 L113 102 Q139 80 148 94 Q124 125 109 180 Q75 197 51 176 Z'),
    '벨트':()=>rect(22,103,156,34,7)+rect(82,96,42,48,6,'accent')+rect(92,106,22,28,3,'fabric'),
    '귀걸이':()=>circle(84,112,3.5,'fabric')+shape('M84 117 Q94 128 84 134 Q74 128 84 117 Z')+circle(116,112,3.5,'fabric')+shape('M116 117 Q126 128 116 134 Q106 128 116 117 Z'),
    '목걸이':()=>line('M49 45 Q58 166 100 185 Q142 166 151 45')+circle(100,185,14,'fabric'),
    '넥타이':()=>shape('M83 34 L117 34 L111 69 L127 176 L100 211 L73 176 L89 69 Z')+line('M89 69 L111 69')
  };
  return map[name]();
}

export function renderGarment(name,{gender='male',fill='#d9e6f1',accent='#f6f1e8',outline='#74777a',detail='#85888b',open=true}={}) {
  const category=byName[name]?.category;
  let inner='';
  if(category==='상의') inner=upper(name,gender);
  else if(category==='하의') inner=bottom(name,gender);
  else if(category==='원피스') inner=dress(name);
  else if(category==='아우터') inner=outer(name,gender,open);
  else if(category==='신발') inner=footwear(name);
  else if(category==='가방') inner=bag(name);
  else if(category==='액세서리') inner=accessory(name);
  else throw new Error(`Unknown garment: ${name}`);
  return svg(inner,{fill,accent,outline,detail,label:name});
}

const dataSvg = markup => `data:image/svg+xml;charset=utf-8,${encodeURIComponent(markup)}`;

export function renderOutfit({gender='male',top='긴팔 정장 셔츠',bottom='슬랙스',outer='',dress='',shoe='옥스퍼드',bag='',topColor='#d9e6f1',bottomColor='#66686b',outerColor='#3f4246',shoeColor='#262729',tuck='in',outerOpen=true,suitLinked=false}={}) {
  const isOpen=outerOpen===true||outerOpen==='true';
  if(suitLinked && /수트 재킷/.test(outer) && /수트/.test(bottom)) bottomColor=outerColor;
  const parts=[];
  const item=(name,opts,cls,style='')=>`<div class="look-part ${cls}" style="${style}">${renderGarment(name,{gender,...opts})}</div>`;
  if(dress) parts.push(item(dress,{fill:topColor},'dress-layer'));
  else {
    parts.push(item(bottom,{fill:bottomColor},'bottom-layer'));
    parts.push(item(top,{fill:topColor},`top-layer tuck-${tuck}`));
  }
  if(outer) parts.push(item(outer,{fill:outerColor,open:isOpen},`outer-layer outer-${isOpen?'open':'closed'}`));
  parts.push(item(shoe,{fill:shoeColor},'shoe-layer'));
  if(bag) parts.push(item(bag,{fill:outerColor},'bag-layer'));
  return `<div class="outfit-canvas" data-tuck="${tuck}" data-outer="${isOpen?'open':'closed'}">${parts.join('')}</div>`;
}

export function downloadSvg(name, options={}) {
  const markup=renderGarment(name,options);
  const a=document.createElement('a'); a.href=dataSvg(markup); a.download=`dalha-${name}.svg`; a.click();
}
