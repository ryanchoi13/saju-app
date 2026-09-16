import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {renderLook} from '../assets/dalha-garments/integration.js';
import {accessoryDrawing} from '../assets/dalha-garments/components.js';

const root='review-output/realwear-v3';
const samples=JSON.parse(fs.readFileSync(root+'/samples.json'));
const regression=JSON.parse(fs.readFileSync(root+'/regression.json'));
const accepted=JSON.parse(fs.readFileSync('backend/tests/fixtures/svg_accepted_looks.json'));
for(const old of accepted){
  const look=regression.find(l=>l.review_id===old.review_id);
  // Compare the original base render separately from the newly authorised
  // part colours/patterns. Keep the historical hash and fixture immutable.
  const base=structuredClone(look);
  delete base.garment_spec.accessoryItems;
  for(const item of base.items)delete item.color_description;
  const svg=renderLook(base,'accepted-'+old.review_id);
  assert.equal(crypto.createHash('sha256').update(svg).digest('hex'),old.approvedSvgSha256,old.review_id+' base');
  const updated=renderLook(look,'accepted-'+old.review_id);
  if(look.garment_spec.accessoryItems.some(i=>i.pattern==='stripe'))assert.match(updated,/data-part="pattern"/);
  else if(!look.garment_spec.accessories.length)assert.equal(updated,svg,old.review_id+' full');
}
for(const [n,s] of samples.entries()){
  const svg=renderLook(s.look,'sample-'+n);
  assert(!svg.includes('undefined')&&!svg.includes('NaN'));
  fs.writeFileSync(root+`/sample-${n+1}.svg`,svg);
}
const demo=samples.at(-1).look;
const svg=renderLook(demo,'parts');
assert.match(svg,/data-part="dial"[^>]*fill="#355B48"/);
assert.match(svg,/data-part="stone"[^>]*fill="#243B59"/);
assert.match(svg,/data-part="pendant"[^>]*fill="#355B48"/);
assert.match(svg,/aria-label="귀걸이" transform="translate\(-43 -65\)/);
assert.match(svg,/aria-label="목걸이" transform="translate\(0 27\)/);
const watch=demo.garment_spec.accessoryItems[0];
const male=accessoryDrawing(watch,'male','m'), female=accessoryDrawing(watch,'female','f');
assert.notEqual(male,female);
assert.match(male,/data-part="strap"[^>]*width="40"/);
assert.match(female,/data-part="strap"[^>]*width="30"/);
assert.match(renderLook(samples[2].look,'tie'),/data-part="pattern"/);
const invalid=structuredClone(demo);invalid.garment_spec.accessoryItems[0].parts.dial.hex='" onload="alert(1)';
assert.throws(()=>renderLook(invalid,'bad'));
for(const gender of ['male','female']){
 fs.writeFileSync(root+`/watch-${gender}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 240">${accessoryDrawing(watch,gender,'watch-'+gender)}</svg>`);
}
fs.writeFileSync(root+'/svg-check.json',JSON.stringify({approved_base_svg_hashes:5,generated_outfits:6,independent_parts:true,gender_watch_variants:true,two_tone_tie:true,invalid_part_colour_rejected:true,actual_mobile_browser:false},null,2));
console.log('5 approved base SVG hashes unchanged; authorised tie pattern checked separately. 6 outfits, independent parts, gender watches and invalid-colour boundary passed.');
