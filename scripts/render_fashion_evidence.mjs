import fs from 'node:fs';
import {renderOutfit} from '../assets/dalha-garments/engine.js';
import {refineCasualLook} from '../assets/dalha-garments/casual-details.js';

const root=new URL('../fashion_v2/evidence_data/v1/',import.meta.url);
const load=name=>JSON.parse(fs.readFileSync(new URL(name+'.json',root),'utf8'));
const garments=Object.fromEntries(load('garments').map(x=>[x.id,x]));
const colors=Object.fromEntries(load('colors').map(x=>[x.id,x]));
const output={};
for(const b of load('benchmarks')){
  const spec={gender:b.context.gender,outer:'',top:'',bottom:'',shoe:'',bag:'',dress:'',accessories:[],outerMode:'wear',outerOpen:true,tuck:'out'};
  for(const i of b.items){
    const garment=garments[i.garment_id],color=colors[i.color_id];
    const slot={'상의':'top','하의':'bottom','아우터':'outer','신발':'shoe'}[garment.category];
    if(!slot)throw Error('unhandled benchmark garment');
    spec[slot]=garment.name;spec[slot+'Color']=color.hex;
  }
  if(b.id==='B06')spec.tuck='in';
  let svg=refineCasualLook(renderOutfit(spec,'evidence-'+b.id),spec);
  if(/undefined|NaN/.test(svg))throw Error('invalid rendered outfit');
  output[b.id]=svg;
}
fs.writeFileSync(process.argv[2],JSON.stringify(output));
