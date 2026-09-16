// Approved silhouette files remain intact. Explicit accessory variants only.
import {garmentInner, escapeXml as esc} from './engine.js';

const valid=c=>typeof c==='string'&&/^#[0-9a-f]{6}$/i.test(c);
const edge='#797d79';
const partColor=(item,key,fallback)=>item.parts?.[key]?.hex||fallback||item.color;
const circle=(part,x,y,r,fill)=>`<circle data-part="${part}" cx="${x}" cy="${y}" r="${r}" fill="${fill}" stroke="${edge}" stroke-width="1.1"/>`;
const rect=(part,x,y,w,h,rx,fill)=>`<rect data-part="${part}" x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${edge}" stroke-width="1.1"/>`;
const path=(part,d,fill,stroke=edge,width=1.1)=>`<path data-part="${part}" d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round"/>`;

export function validateAccessory(item) {
  if(!item || !valid(item.color) || typeof item.name!=='string')throw Error('잘못된 소품 정보');
  for(const [key,p] of Object.entries(item.parts||{})){
    if(!['body','pattern','strap','case','dial','metal','stone','chain','pendant'].includes(key)||!valid(p?.hex))throw Error('잘못된 소품 부위 색상');
  }
}

export function accessoryDrawing(item,gender,prefix) {
  validateAccessory(item);
  const c=key=>partColor(item,key), name=item.name;
  if(name==='시계'){
    // Product examples inform the ratio; these are legible DALHA variants,
    // not claims about average male/female wrist or watch dimensions.
    const f=gender==='female',r=f?35:42,w=f?30:40,top=f?27:22,round=f?9:6;
    const dial=c('dial'),rgb=dial.slice(1).match(/../g).map(x=>parseInt(x,16));
    const hands=(rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722)<120?'#e7e8e1':'#515952';
    const strap=rect('strap',100-w/2,top,w,120-r-top+6,round,c('strap'))+
      rect('strap',100-w/2,120+r-6,w,218-(120+r-6),round,c('strap'));
    return `<g data-variant="watch-${f?'female':'male'}-basic-v1">${strap}`+
      rect('case',100+r-1,115,5,10,2,c('case'))+
      circle('case',100,120,r,c('case'))+circle('dial',100,120,r-6,dial)+
      path('hands',`M100 120 L100 ${120-r*.58} M100 120 L${100+r*.44} 129`,'none',hands,2.6)+
      `<circle data-part="hands" cx="100" cy="120" r="2" fill="${hands}"/></g>`;
  }
  if(name==='귀걸이'){
    return [84,116].map(x=>circle('metal',x,112,3.5,c('metal'))+
      path('stone',`M${x} 117 Q${x+10} 128 ${x} 134 Q${x-10} 128 ${x} 117 Z`,c('stone'))).join('');
  }
  if(name==='목걸이')return path('chain','M49 45 Q58 166 100 185 Q142 166 151 45','none',c('chain'),2.3)+circle('pendant',100,185,14,c('pendant'));
  let art=garmentInner(name,{gender,fill:c('body')});
  if(name==='넥타이'&&item.pattern==='stripe'&&item.parts?.pattern){
    const id=esc(prefix+'-stripe');
    art+=`<defs><clipPath id="${id}"><path d="M83 34 L117 34 L111 69 L127 176 L100 211 L73 176 L89 69 Z"/></clipPath></defs><g clip-path="url(#${id})" data-part="pattern" fill="${c('pattern')}"><path d="M65 93 L134 61 L139 75 L65 110 Z M65 143 L140 108 L140 124 L65 160 Z M65 193 L140 158 L140 174 L65 210 Z"/></g>`;
  }
  return art;
}

export function legacyAccessoryDrawing(name,s) {
  let art=garmentInner(name,{gender:s.gender,fill:s.accessoryColor||'#907b56'});
  if(name==='목걸이')art=art.replace(/stroke-width="0.85"/g,'stroke-width="2.3"').replace(/stroke="[^"]*"/g,`stroke="${esc(s.accessoryColor||'#907b56')}"`);
  return art;
}
