// Versioned live revisions. Keep the archived/approved engine paths unchanged.
import {garmentInner, outerGeometry, upperGeometry} from './engine.js';

function pen(fill) {
  if (!/^#[a-f\d]{6}$/i.test(fill)) throw new Error('잘못된 의류 색상');
  const rgb=fill.slice(1).match(/../g).map(x=>parseInt(x,16));
  const dark=(rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722)<90;
  const stroke=dark?'#70777a':'#626b6d';
  return (d,solid=false,width=1.1)=>`<path d="${d}" fill="${solid?fill:'none'}" stroke="${stroke}" stroke-width="${width}" stroke-linejoin="round" stroke-linecap="round"/>`;
}

function hood(fill) {
  const p=pen(fill);
  return `<g data-feature="hood">${p('M79 35 Q65 24 70 10 Q76 -1 100 0 Q124 -1 130 10 Q135 24 121 35 L114 52 Q100 61 86 52 Z',true)}${p('M84 33 Q76 23 81 13 Q100 5 119 13 Q124 23 116 33 L109 46 Q100 51 91 46 Z')}${p('M89 46 L85 76 M111 46 L115 76',false,1.5)}</g>`;
}

function topRevision(name, gender, fill, bodyEase=0) {
  const p=pen(fill), a=upperGeometry(name,gender,bodyEase);
  let result=p(a.outline,true);
  if(name==='후드티') {
    result+=hood(fill)+`<g data-feature="kangaroo-pocket">${p('M77 125 L67 142 L69 160 Q100 164 131 160 L133 142 L123 125 Z')}${p('M77 126 L79 145 M123 126 L121 145')}</g>`;
  } else if(name==='맨투맨') {
    result+=`<g data-feature="crew-rib-neck">${p('M80 33 Q100 61 120 33 L122 38 Q100 70 78 38 Z',true)}${p('M97 60 L100 65 L103 60')}</g>`;
  } else {
    result+=`<g data-feature="polo-collar">${p('M80 32 L100 51 L84 66 L70 42 Z',true)}${p('M120 32 L100 51 L116 66 L130 42 Z',true)}${p('M96 52 L96 84 L104 84 L104 52')}${p('M100 62 L100 63 M100 73 L100 74',false,2)}</g>`;
  }
  if(a.long) result+=`<g data-feature="rib-cuffs">${p('M19 177 L40 180 M181 177 L160 180')}${p('M23 179 L21 189 M29 180 L27 191 M35 181 L33 191 M177 179 L179 189 M171 180 L173 191 M165 181 L167 191',false,.7)}</g>`;
  if(a.knit) result+=`<g data-feature="rib-hem">${p(`M${a.w} 175 Q100 181 ${200-a.w} 175`)}${p(`M${a.w+8} 177 L${a.w+8} 185 M${192-a.w} 177 L${192-a.w} 185`,false,.7)}</g>`;
  return `<g data-garment-revision="${name}">${result}</g>`;
}

export function blousonGeometry(gender='male') {
  const side=gender==='female'?56:50, shoulder=gender==='female'?54:48;
  const left=`M83 32 Q65 36 ${shoulder} 44 Q37 48 31 70 L14 165 Q23 171 38 171 L${side+2} 91 L${side} 156 L${side+3} 176 Q68 181 88 177 L91 170 L90 73 Q88 48 83 32 Z`;
  const aperture='M83 32 Q88 48 90 73 L91 170 L88 177 L112 177 L109 170 L110 73 Q112 48 117 32 Z';
  return {left,aperture,hem:178};
}

function blouson(gender, fill, open, backing=false) {
  const p=pen(fill),a=blousonGeometry(gender);
  let half=p(a.left,true)+p('M83 32 Q76 29 75 36 L82 51 L88 48 Z',true)
    +`<g data-feature="zip-pocket">${p('M63 110 L79 103 M64 113 L80 106')}${p('M88 56 L89 164',false,1.5)}</g>`
    +`<g data-feature="blouson-rib">${p('M53 167 Q68 173 89 169 M16 155 L40 161')}${p('M59 171 L59 178 M64 173 L64 179 M69 173 L69 179 M74 173 L74 179 M79 173 L79 178 M84 172 L84 177 M21 158 L19 167 M27 160 L25 169 M33 161 L31 170',false,.7)}</g>`;
  let art=backing?p('M82 34 Q100 43 118 34 L122 176 L78 176 Z',true):'';
  art+=half+`<g transform="translate(200 0) scale(-1 1)">${half}</g>`;
  if(!open) art+=p(a.aperture,true)+p('M100 37 L100 174',false,1.5);
  return `<g data-garment-revision="블루종">${art}</g>`;
}

export function applyGarmentIdentity(svg,s) {
  // The archive renderer has generated/validated these exact paths already.
  // Replace only supported garments, never guess a shape for an unknown label.
  if(['맨투맨','후드티','반팔 폴로 티셔츠'].includes(s.top)) {
    const bodyEase=s.outer==='패딩'&&s.outerMode==='wear'&&s.tuck==='out'?5:0;
    const old=garmentInner(s.top,{gender:s.gender,fill:s.topColor,bodyEase});
    if(!svg.includes(old)) throw new Error('상의 도안 연결 확인 필요');
    svg=svg.replace(old,topRevision(s.top,s.gender,s.topColor,bodyEase));
  }
  if(s.outer==='블루종') {
    const old=garmentInner(s.outer,{gender:s.gender,fill:s.outerColor,open:s.outerOpen,backing:s.outerMode==='carry'});
    if(!svg.includes(old)) throw new Error('블루종 도안 연결 확인 필요');
    svg=svg.replace(old,blouson(s.gender,s.outerColor,s.outerOpen,s.outerMode==='carry'));
    if(s.outerMode==='wear') {
      const before=outerGeometry(s.outer,s.gender), after=blousonGeometry(s.gender);
      svg=svg.replace(`<path d="${before.aperture}"/>`,`<path d="${after.aperture}"/>`)
        .replace(`<rect x="0" y="${before.hem+1}" width="200" height="400"/>`,
          `<rect x="48" y="${after.hem+1}" width="104" height="20"/><rect x="0" y="199" width="200" height="400"/>`);
    }
  }
  if(s.top==='후드티' && s.outer && s.outerMode==='wear') {
    // A hood lies over the jacket collar, not inside its narrow opening mask.
    const marker='</g><g data-role="shoes"';
    if(!svg.includes(marker)) throw new Error('후드 레이어 연결 확인 필요');
    svg=svg.replace(marker,`<g data-role="hood-over-collar">${hood(s.topColor)}</g>${marker}`);
  }
  return svg;
}
