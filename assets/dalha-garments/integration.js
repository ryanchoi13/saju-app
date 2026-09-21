// Approved sources stay immutable. Explicit review variants are opt-in below.
import {renderOutfit, garmentInner, outerGeometry, escapeXml} from './engine.js';
import {byName} from './catalog.js';
import {refineCasualLook} from './casual-details.js';
import {accessoryDrawing,legacyAccessoryDrawing,validateAccessory} from './components.js';

function replaceDrawing(svg, before, after) {
  if (!svg.includes(before)) throw new Error('도안 변형 위치 확인 필요');
  return svg.replace(before, after);
}

function reviewVariants(svg, s, prefix) {
  if(!s.accessoryItems && s.watchCaseColor && s.accessories?.includes('시계')) {
    const original=garmentInner('시계',{gender:s.gender,fill:s.accessoryColor});
    const variant=original.replace(/(<(?:circle|rect) data-layer="fabric" fill=")[^"]*(")/g,`$1${s.watchCaseColor}$2`);
    svg=replaceDrawing(svg,original,variant);
  }
  if(s.knitNeck==='turtleneck' && s.top==='니트') {
    const bodyEase=s.outer==='패딩'&&s.outerMode==='wear'&&s.tuck==='out'?5:0;
    const original=garmentInner('니트',{gender:s.gender,fill:s.topColor,bodyEase});
    let variant=original.replace('Q100 39 80 32 Z','L117 16 Q100 11 83 16 L80 32 Z')
      .replace('M81 34 Q100 65 119 34','M83 29 Q100 33 117 29')
      .replace(/<path[^>]*d="M77 36 Q100 71 123 36"[^>]*\/>/,'');
    svg=replaceDrawing(svg,original,`<g data-variant="turtleneck">${variant}</g>`);
    if(s.outer && s.outerMode==='wear' && s.outerOpen) {
      // Expose the raised neck above the coat opening; sleeves remain clipped.
      const aperture=outerGeometry(s.outer,s.gender).aperture;
      const raised=aperture.replace(/ Z$/,' L118 28 L118 11 L82 11 L82 28 Z');
      svg=svg.replace(`<path d="${aperture}"/>`,`<path d="${raised}"/>`);
    }
  }
  if(s.formalHem==='knee') {
    if(s.dress) {
      const original=garmentInner(s.dress,{gender:s.gender,fill:s.topColor});
      const variant=original.replace('L35 276 Q100 288 165 276','L35 306 Q100 318 165 306')
        .replace('Q62 238 52 270','Q62 253 52 300').replace('Q138 238 148 270','Q138 253 148 300');
      svg=replaceDrawing(svg,original,`<g data-variant="formal-knee">${variant}</g>`);
    } else if(/스커트/.test(s.bottom)) {
      const original=garmentInner(s.bottom,{gender:s.gender,fill:s.bottomColor});
      const suit=s.bottom==='수트 스커트',old=s.bottom==='롱 스커트'?225:suit?164:196;
      const edge=suit?51:27,end=172;
      let variant=original.replace(`${200-edge} ${old} Q100 ${old+9} ${edge} ${old}`,`${200-edge} ${end} Q100 ${end+9} ${edge} ${end}`);
      if(suit)variant=variant.replace('M113 140 L113 160',`M113 ${end-24} L113 ${end-4}`);
      else variant=variant.replaceAll(` ${old-8}`,` ${end-8}`);
      svg=replaceDrawing(svg,original,`<g data-variant="formal-knee">${variant}</g>`);
    }
  }
  return svg;
}

export function renderLook(look, prefix='dalha-look') {
  const s=look?.garment_spec;
  if (!s) throw new Error('착장 도안 정보가 없습니다.');
  for (const k of ['top','bottom','dress','outer','shoe','bag']) {
    if (s[k] && !byName[s[k]]) throw new Error('지원하지 않는 도안');
  }
  for (const k of ['topColor','bottomColor','outerColor','shoeColor','bagColor','accessoryColor','tieAccentColor','watchCaseColor']) {
    if (s[k] && !/^#[a-f\d]{6}$/i.test(s[k])) throw new Error('잘못된 색상');
  }
  if(s.accessoryItems){
    if(!Array.isArray(s.accessoryItems)||s.accessoryItems.length!==(s.accessories||[]).length||s.accessoryItems.length>3)throw new Error('소품 목록이 일치하지 않습니다.');
    s.accessoryItems.forEach((item,i)=>{
      validateAccessory(item);
      if(item.name!==s.accessories[i]||byName[item.name]?.category!=='액세서리')throw new Error('지원하지 않는 소품 도안');
    });
    if(new Set(s.accessories).size!==s.accessories.length)throw new Error('같은 소품은 한 착장에 한 번만 표시합니다.');
  }
  if (!/^[a-z0-9_-]+$/i.test(prefix)) throw new Error('잘못된 도안 식별자');
  // The approved renderer eagerly builds an unused lower path for a dress.
  // Supply its internal default without adding a bottom to the outfit data.
  const base={...s,...(s.dress?{bottom:'슬랙스'}:{}),...(s.accessoryItems?{tieTwoTone:false}:{})};
  let svg=renderOutfit(base,prefix);
  svg=reviewVariants(svg,s,prefix);
  for(const [i,item] of (s.accessoryItems||[]).entries()){
    svg=replaceDrawing(svg,legacyAccessoryDrawing(item.name,s),accessoryDrawing(item,s.gender,`${prefix}-accessory-${i}`));
  }
  // Keep both near the neckline, with separate slots when worn together.
  // Single-accessory positions and the approved garment paths stay unchanged.
  if(s.accessoryItems && s.accessories.includes('귀걸이') && s.accessories.includes('목걸이')){
    svg=svg.replace('aria-label="귀걸이" transform="translate(-43 -38) scale(.72)"','aria-label="귀걸이" transform="translate(-43 -65) scale(.72)"')
      .replace('aria-label="목걸이" transform="translate(0 7) scale(.31)"','aria-label="목걸이" transform="translate(0 27) scale(.31)"');
  }
  if (s.overOuter) {
    const {name,color,open}=s.overOuter;
    if (!byName[name] || !/^#[a-f\d]{6}$/i.test(color) || s.outerMode==='carry') throw new Error('지원하지 않는 겉옷 구성');
    const a=outerGeometry(name,s.gender),id=prefix+'-over';
    const start='<g transform="translate(60 8)">';
    const end='</g><g data-role="shoes"';
    const p=svg.indexOf(start),q=svg.indexOf(end,p);
    if(p<0||q<0) throw new Error('겉옷 합성 위치 확인 필요');
    const clips=`<defs><clipPath id="${id}">${open?`<path d="${a.aperture}"/>`:''}<rect x="0" y="${a.hem-2}" width="200" height="400"/></clipPath></defs>`;
    const inside=svg.slice(p+start.length,q);
    svg=svg.slice(0,p)+start+clips+`<g data-role="inner-outer-clipped" clip-path="url(#${id})">${inside}</g><g data-role="over-outer">${garmentInner(name,{gender:s.gender,fill:color,open})}</g>`+svg.slice(q);
  }
  if (look.renderer==='approved-svg-5') {
    svg=refineCasualLook(svg,s);
    // Keep the entire outfit (including shoes) inside a short mobile modal.
    svg=svg.replace('class="outfit-svg"','class="outfit-svg" style="max-height:max(220px,calc(94dvh - 370px));"');
  }
  return svg.replace('aria-label="코디 도안"',`aria-label="${escapeXml(look.items.map(i=>(i.color_description||i.color_name)+' '+(i.display_label||i.label)).join(', '))}"`);
}

if (typeof window!=='undefined') window.DalhaGarments={renderLook};
