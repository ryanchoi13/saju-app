import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {renderLook} from '../assets/dalha-garments/integration.js';
import {garmentInner} from '../assets/dalha-garments/engine.js';

const payload=JSON.parse(fs.readFileSync('fashion-review-artifacts/teal-camel.json'));
const looks=payload.contexts.casual.looks;
const first=renderLook(looks[0],'regression-first');
const second=renderLook(looks[1],'regression-second');
assert.match(first,/data-garment-revision="블루종"/);
assert.match(first,/data-feature="crew-rib-neck"/);
assert.doesNotMatch(first,/hood-over-collar/);
assert.match(second,/data-feature="kangaroo-pocket"/);
assert.match(second,/data-role="hood-over-collar"/);
assert(second.indexOf('hood-over-collar')>second.indexOf('worn-outer'));
assert.match(first,/<g data-role="shoes"/);
assert.match(second,/<g data-role="shoes"/);
assert(first.includes(looks[0].garment_spec.bottomColor));
assert(second.includes(looks[1].garment_spec.bottomColor));
const polo=structuredClone(looks[0]);polo.garment_spec.top='반팔 폴로 티셔츠';
assert.match(renderLook(polo,'polo'),/data-feature="polo-collar"/);
const carried=structuredClone(looks[1]);carried.garment_spec.outerMode='carry';
assert.doesNotMatch(renderLook(carried,'carry'),/hood-over-collar/);
assert.match(renderLook(carried,'carry'),/data-role="carried-outer"/);
const closed=structuredClone(looks[1]);closed.garment_spec.outerOpen=false;
assert.match(renderLook(closed,'closed'),/hood-over-collar/);
const provenance=JSON.parse(fs.readFileSync('docs/fashion-svg-art-provenance.json'));
for(const [name,hash] of Object.entries(provenance.files))
 assert.equal(crypto.createHash('sha256').update(fs.readFileSync('assets/dalha-garments/'+name)).digest('hex'),hash);
const archived=JSON.parse(fs.readFileSync('backend/tests/fixtures/svg_accepted_looks.json'));
for(const look of archived) {
 const svg=renderLook(look,'accepted-'+look.review_id);
 assert.equal(crypto.createHash('sha256').update(svg).digest('hex'),look.approvedSvgSha256,look.review_id);
}
fs.writeFileSync('fashion-review-artifacts/recommendation-1.svg',first);
fs.writeFileSync('fashion-review-artifacts/recommendation-2.svg',second);
console.log('Garment identity, hood layering, shoes, five archived SVG hashes, immutable source art: passed.');
