import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {JSDOM} from 'jsdom';
import {selectIllustration} from '../assets/dalha-illustrations/catalog.js';
import {recolor} from '../assets/dalha-illustrations/renderer.js';
import {decorateLook,hydrateIllustrations} from '../assets/dalha-illustrations/adapter.js';

const looks=JSON.parse(execFileSync('python',['-c',`import json
from fashion_v2.svg_recommendation import build_svg_catalog_contexts,tone
out=[]
for gender in ('female','male'):
 for age in (18,25,35,45,55):
  for c in build_svg_catalog_contexts(gender,'autumn',tone('navy'),tone('pink'),age=age).values(): out.extend(c['looks'])
print(json.dumps(out))`],{encoding:'utf8'}));
assert.equal(looks.length,60);
assert.equal(looks.filter(selectIllustration).length,55);
const base=looks[0];
for(const change of [{shoe:'로퍼'},{overOuter:'코트'},{outerMode:'carry'},{tuck:'in'},{accessories:['목걸이']},{topColor:'invalid'}]){
 assert.equal(selectIllustration({...base,garment_spec:{...base.garment_spec,...change}}),null);
}
assert.equal(selectIllustration({...base,season:'winter'}),null);
const original=new Uint8ClampedArray([17,24,31,255,1,2,3,255,4,5,6,128]);
const layer=new Uint8ClampedArray([0,0,0,255,1,0,0,255,1,255,128,255]);
const painted=recolor(original,layer,['#e3ddcf']);
assert.deepEqual([...painted.slice(0,4)],[17,24,31,255]);
assert.deepEqual([...painted.slice(4,8)],[227,221,207,255]);
assert.deepEqual([...painted.slice(8)],[152,148,139,128]);
assert.throws(()=>recolor(original,layer,[]),/Missing region/);

const dom=new JSDOM('<main></main>');globalThis.document=dom.window.document;
globalThis.ImageData=class{constructor(data,width,height){Object.assign(this,{data,width,height});}};
let fail=false;
globalThis.Image=class{naturalWidth=1;naturalHeight=1;set src(value){this.mask=value.includes('layers');queueMicrotask(()=>fail?this.onerror():this.onload());}};
dom.window.HTMLCanvasElement.prototype.getContext=function(){let im;return {drawImage(x){im=x;},getImageData(){return {width:1,height:1,data:new Uint8ClampedArray(im.mask?[1,0,0,255]:[0,0,0,255])};},putImageData(x){assert.equal(x.data[3],255);}};};
const root=document.querySelector('main'),fallback='<svg aria-label="추천 옷과 색상"></svg>';
root.innerHTML=decorateLook(base,'test',fallback);
assert.equal(root.querySelector('[data-illustration-fallback]').hidden,false);
await hydrateIllustrations(root);
assert.equal(root.querySelector('[data-illustration-fallback]').hidden,true);
assert.equal(root.querySelector('canvas').getAttribute('aria-label'),'추천 옷과 색상');
assert.equal(root.firstChild.dataset.illustrationAsset,'f-casual-a');
fail=true;root.innerHTML=decorateLook(looks[1],'failure',fallback);
await hydrateIllustrations(root);
assert.equal(root.querySelector('[data-illustration-fallback]').hidden,false);
assert.equal(root.querySelector('canvas').hidden,true);
assert.equal(decorateLook({...base,season:'winter'},'unsupported',fallback),fallback);
fail=false;root.innerHTML=decorateLook(looks[2],'stale',fallback);
const pending=hydrateIllustrations(root);root.replaceChildren();await pending;
assert.equal(root.children.length,0);
console.log('PASS: 60 live recommendations; 55 exact matches, 5 safe fallbacks; colour/outline, DOM loading/failure/stale-node checks');
