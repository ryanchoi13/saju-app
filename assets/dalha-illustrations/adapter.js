import {selectIllustration} from './catalog.js';
import {recolor} from './renderer.js';
const BASE='/assets/dalha-illustrations/';
const pending=new Map(),images=new Map();let sequence=0;
const rgb=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
function image(src){if(!images.has(src))images.set(src,new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>{images.delete(src);reject(new Error('Illustration asset unavailable'));};im.src=src;}));return images.get(src);}
function pixels(im){const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;const x=c.getContext('2d',{willReadFrequently:true});x.drawImage(im,0,0);return x.getImageData(0,0,c.width,c.height);}
export function decorateLook(look,prefix,fallback){
 const entry=selectIllustration(look);if(!entry)return fallback;
 const key=String(++sequence);pending.set(key,entry);while(pending.size>12)pending.delete(pending.keys().next().value);
 return `<div data-dalha-illustration="${key}" style="width:100%"><div data-illustration-fallback>${fallback}</div><canvas hidden role="img" aria-label="추천 코디 일러스트" style="max-width:100%;height:auto;max-height:max(220px,calc(94dvh - 370px));margin:auto"></canvas></div>`;
}
export async function hydrateIllustrations(root){
 const nodes=[...root.querySelectorAll('[data-dalha-illustration]')];
 return Promise.allSettled(nodes.map(async node=>{
  const key=node.dataset.dalhaIllustration,entry=pending.get(key);if(!entry)return;
  try{
   const [source,mask]=await Promise.all([image(BASE+entry.id+'.webp?v=1'),image(BASE+entry.id+'-layers.png?v=2')]);
   if(!node.isConnected||node.dataset.dalhaIllustration!==key)return;
   const original=pixels(source),layers=pixels(mask);
   if(original.width!==layers.width||original.height!==layers.height)throw new Error('Illustration layer size mismatch');
   const result=recolor(original.data,layers.data,entry.colours);
   if(entry.stripe){
    const color=rgb(entry.stripe.color),w=original.width,period=Math.max(9,Math.round(w/55));
    for(let p=0;p<result.length;p+=4){if(layers.data[p]!==entry.stripe.region)continue;const pixel=p/4,x=pixel%w,y=Math.floor(pixel/w);if((x+y*.6)%period>period*.17)continue;const line=layers.data[p+1]/255,shadow=(layers.data[p+2]%128)/127;for(let c=0;c<3;c++)result[p+c]=Math.round(color[c]*(1-.13*shadow)*(1-line)+result[p+c]*line);}
   }
   const canvas=node.querySelector('canvas');canvas.width=original.width;canvas.height=original.height;
   canvas.getContext('2d').putImageData(new ImageData(result,original.width,original.height),0,0);
   const label=node.querySelector('svg')?.getAttribute('aria-label');if(label)canvas.setAttribute('aria-label',label);
   canvas.hidden=false;canvas.style.display='block';node.querySelector('[data-illustration-fallback]').hidden=true;
   node.dataset.illustrationAsset=entry.id;
  }catch(error){console.warn('DALHA illustration: retained SVG fallback',error.message);}
  finally{pending.delete(key);}
 }));
}
