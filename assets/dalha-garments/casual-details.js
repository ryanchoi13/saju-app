// Add explicit garment identity without changing the historical approved paths.
// Enabled by the v5 recommendation payload; old review fixtures keep their art.
import {garmentInner, outerGeometry, upperGeometry} from './engine.js';

const safe = value => /^#[a-f\d]{6}$/i.test(value) ? value : '#c5d3df';
function shade(value, ratio=.18) {
  return '#'+safe(value).slice(1).match(/../g).map(v=>Math.round(parseInt(v,16)*(1-ratio)).toString(16).padStart(2,'0')).join('');
}
function pen(value) {
  const fill=safe(value), rgb=fill.slice(1).match(/../g).map(v=>parseInt(v,16));
  const light=rgb.reduce((a,b)=>a+b,0)/3;
  const edge=light<80?'#8b9295':'#606970';
  return {
    path:(d,f=fill,width=1.05)=>`<path d="${d}" fill="${f}" stroke="${edge}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round"/>`,
    line:(d,width=.85)=>`<path d="${d}" fill="none" stroke="${edge}" stroke-width="${width}" stroke-linecap="round"/>`,
    dot:(x,y,r=1.25)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="${edge}"/>`,
  };
}
function hood(fill) {
  const {path,line}=pen(fill);
  return `<g data-detail="visible-hood">${path('M76 48 Q65 34 73 17 Q80 5 100 5 Q120 5 127 17 Q135 34 124 48 L115 59 Q100 66 85 59 Z')}${path('M81 26 Q83 14 100 13 Q117 14 119 26 Q118 43 100 55 Q82 43 81 26 Z',shade(fill,.22))}${path('M76 36 Q80 46 100 55 L87 65 Q76 56 76 36 Z')}${path('M124 36 Q120 46 100 55 L113 65 Q124 56 124 36 Z')}${line('M89 59 L87 88 M111 59 L113 88',1.05)}</g>`;
}
function detailedTop(s, bodyEase) {
  const name=s.top,fill=safe(s.topColor),{path,line,dot}=pen(fill);
  let art=garmentInner(name,{gender:s.gender,fill,bodyEase});
  const a=upperGeometry(name,s.gender,bodyEase);
  if(name==='맨투맨') {
    art=art.replace(/<path[^>]*d="M81 34 Q100 65 119 34"[^>]*\/>/,'');
    art+=`<g data-detail="sweatshirt-rib">${path('M80 32 Q100 46 120 32 L118 39 Q100 56 82 39 Z',shade(fill,.06))}${line('M94 50 L100 57 L106 50')}${path(`M${a.w} 174 Q100 181 ${200-a.w} 174 L${200-a.w} 184 Q100 192 ${a.w} 184 Z`,shade(fill,.06))}${line('M20 179 L38 182 M24 181 L22 189 M29 183 L27 190 M177 179 L161 182 M171 183 L173 190 M166 184 L168 191')}</g>`;
  } else if(name==='후드티') {
    // The visible hood is composited separately when a coat/jacket is worn.
    art+=`<g data-detail="hoodie-pocket">${line('M77 136 L66 161 Q100 170 134 161 L123 136 Z M77 136 L82 144 M123 136 L118 144')}${line(`M${a.w} 176 Q100 184 ${200-a.w} 176`)}</g>`;
    if(!s.outer || s.outerMode==='carry') art+=hood(fill);
  } else if(/폴로/.test(name)) {
    art+=`<g data-detail="polo-collar">${path('M80 33 L100 52 L87 63 L73 45 Z',shade(fill,.06))}${path('M120 33 L100 52 L113 63 L127 45 Z',shade(fill,.06))}${path('M97 53 L103 53 L103 82 L97 82 Z')}${dot(100,64)}${dot(100,75)}</g>`;
  }
  return art;
}
function blouson(s) {
  const fill=safe(s.outerColor),{path,line}=pen(fill),a=outerGeometry('블루종',s.gender);
  let left=path(a.left);
  left+=`<g data-detail="blouson-rib-zip">${path('M79 28 Q72 23 69 30 L72 39 L85 48 L83 37 Z',shade(fill,.08))}${line('M73 29 L78 40 M76 29 L81 40')}${path(`M${a.side-1} 184 Q65 192 86 187 L85 198 Q65 202 ${a.side-2} 195 Z`,shade(fill,.08))}${path('M12 181 L38 185 L36 195 Q22 198 10 191 Z',shade(fill,.08))}${line('M84 68 L85 182 M81 70 L82 181',1)}${line('M57 134 L70 124 M58 139 L71 129',1.2)}${line('M54 190 L54 197 M61 192 L61 199 M69 193 L69 199 M77 192 L77 198')}</g>`;
  let art=left+`<g transform="translate(200 0) scale(-1 1)">${left}</g>`;
  if(!s.outerOpen)art+=path(a.aperture)+line('M100 48 L100 198',1.2);
  return `<g data-detail="blouson">${art}</g>`;
}
function replace(svg, before, after) {
  if(!svg.includes(before)) throw new Error('캐주얼 도안 상세 위치 확인 필요');
  return svg.replace(before,after);
}
export function refineCasualLook(svg, s) {
  const worn=!!s.outer && s.outerMode!=='carry';
  const bodyEase=worn && s.outer==='패딩' && s.tuck==='out' && /니트|후드티|맨투맨/.test(s.top)?5:0;
  if(s.top && /^(맨투맨|후드티)$|폴로/.test(s.top)) {
    const original=garmentInner(s.top,{gender:s.gender,fill:s.topColor,bodyEase});
    svg=replace(svg,original,detailedTop(s,bodyEase));
  }
  if(worn && s.outer==='블루종') {
    svg=replace(svg,garmentInner(s.outer,{gender:s.gender,fill:s.outerColor,open:s.outerOpen}),blouson(s));
  }
  if(worn && s.top==='후드티') {
    // The old neck aperture removed the hood at y<28. Expose only the hood;
    // do not unclip the entire shirt or let its sleeves cross the outer layer.
    svg=svg.replace('</svg>',`<g data-role="hood-over-collar" transform="translate(60 8)">${hood(s.topColor)}</g></svg>`);
  }
  return svg;
}
