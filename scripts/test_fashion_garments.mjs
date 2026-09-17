import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import {renderLook} from '../assets/dalha-garments/integration.js';

const root='review-output/wearable-fix';
const historical=JSON.parse(fs.readFileSync('backend/tests/fixtures/svg_accepted_looks.json'));
for (const look of historical) {
  // Historical sources are unchanged; v5 improvements are explicit and opt-in.
  const svg=renderLook(look,'accepted-'+look.review_id);
  assert.equal(crypto.createHash('sha256').update(svg).digest('hex'),look.approvedSvgSha256);
}
const matrix=JSON.parse(fs.readFileSync(root+'/regression.json'));
for (const [n,look] of matrix.entries()) {
  const svg=renderLook(look,'regression-'+n);
  assert(!/undefined|NaN/.test(svg));
  assert.match(svg,/data-role="shoes"/);
  if(look.garment_spec.top==='후드티' && look.garment_spec.outer && look.garment_spec.outerMode==='wear') {
    assert.match(svg,/data-role="hood-over-collar"/);
  }
}
const looks=JSON.parse(fs.readFileSync(root+'/looks.json')).casual.looks;
const first=renderLook(looks[0],'reported-first'),second=renderLook(looks[1],'reported-second');
assert.match(first,/data-detail="sweatshirt-rib"/);
assert.match(first,/data-detail="blouson-rib-zip"/);
assert.match(second,/data-detail="hoodie-pocket"/);
assert.match(second,/data-detail="visible-hood"/);
assert.match(first,/max-height:max\(220px,calc\(94dvh - 370px\)\)/);
const polo=structuredClone(looks[0]);polo.garment_spec.top='반팔 폴로 티셔츠';
assert.match(renderLook(polo,'polo'),/data-detail="polo-collar"/);
const bad=structuredClone(looks[0]);bad.garment_spec.topColor='" onload="alert(1)';
assert.throws(()=>renderLook(bad,'unsafe'));
for(const [n,look] of looks.entries())fs.writeFileSync(`${root}/look-${n+1}.svg`,renderLook(look,'fixed-'+n));
console.log(JSON.stringify({archivedSvgHashes:historical.length,rendererPayloads:matrix.length,garmentDetails:true,invalidColorRejected:true}));
