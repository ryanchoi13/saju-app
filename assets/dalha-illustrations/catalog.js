import {illustrations} from './catalog-data.js?v=2';
export {illustrations};
const hex=v=>typeof v==='string'&&/^#[a-f0-9]{6}$/i.test(v);
const basic=['gender','top','bottom','dress','outer','shoe','bag','outerMode','tuck','knitNeck'];
export function geometryMatches(s,shape){
 if(s.overOuter&&typeof s.overOuter!=='object')return false;
 if(basic.some(k=>(s[k]||'')!==(shape[k]||'')))return false;
 if((s.outerOpen!==false)!==(shape.outerOpen!==false))return false;
 if((s.overOuter?.name||'')!==(shape.overOuter?.name||''))return false;
 if(s.overOuter&&(s.overOuter.open!==false)!==(shape.overOuter.open!==false))return false;
 return JSON.stringify(s.accessories||[])===JSON.stringify(shape.accessories||[]);
}
export function selectIllustration(look){
 const s=look?.garment_spec;if(!s||look.renderer!=='approved-svg-5')return null;
 const tie=s.accessoryItems?.find(i=>i.name==='넥타이');
 const watch=s.accessoryItems?.find(i=>i.name==='시계');
 if(tie&&!['solid','stripe'].includes(tie.pattern||'solid'))return null;
 // Do not silently discard newly introduced colour components.
 if((look.items||[]).some(i=>i.color_parts&&!['넥타이','시계'].includes(i.label)))return null;
 for(const entry of illustrations){
  if(!geometryMatches(s,entry.shape))continue;
  if(entry.linkedSuit&&s.bottomColor?.toLowerCase()!==s.outerColor?.toLowerCase())continue;
  const colours=entry.slots.map(k=>k==='tie.body'?(tie?.parts?.body?.hex||tie?.color||s.accessoryColor):k.startsWith('watch.')?watch?.parts?.[k.slice(6)]?.hex:k==='overOuter.color'?s.overOuter?.color:s[k]);
  if(!colours.every(hex))continue;
  let stripe=null;
  if(tie?.pattern==='stripe'){
   if(!hex(tie.parts?.pattern?.hex))continue;
   const region=entry.slots.indexOf('tie.body')+1;if(!region)continue;
   stripe={region,color:tie.parts.pattern.hex};
  }
  // Both approved adult formal variants use the identical packed slot layout.
  const id=entry.id==='06'&&Number(look.age)>=50?'10':entry.id;
  return {...entry,id,colours,stripe};
 }
 return null;
}
