import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {renderLook} from '../assets/dalha-garments/integration.js';
const require=createRequire(import.meta.url);
const sharp=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'sharp'));
const data=JSON.parse(fs.readFileSync('review-output/svg-integration/automatic-sets.json'));
const looks=Object.fromEntries(data.sets.flatMap(s=>s.looks).map(l=>[l.review_id,l]));
const accepted=JSON.parse(fs.readFileSync('backend/tests/fixtures/svg_accepted_looks.json'));
for(const old of accepted) {
  const svg=renderLook(looks[old.review_id],'accepted-'+old.review_id);
  assert.equal(crypto.createHash('sha256').update(svg).digest('hex'),old.approvedSvgSha256,old.review_id);
}
const neck=renderLook(looks['17-2'],'neck');
const {data:pixels,info}=await sharp(Buffer.from(neck)).ensureAlpha().raw().toBuffer({resolveWithObject:true});
// A neckline gap would show transparent/white where the neck joins the knit.
for(const y of [34,36,37,41,44]) {
  const offset=(y*info.width+160)*4;
  assert.equal(pixels[offset+3],255,'목폴라 연결부가 비었습니다');
  assert(pixels[offset]>pixels[offset+1]+35,'목폴라의 빨간 면 연결 확인');
}
assert.match(neck,/aria-label="[^"]*목폴라 니트/);
const dress=renderLook(looks['18-2'],'formal');
assert.match(dress,/L35 306 Q100 318 165 306/);
assert.match(dress,/aria-label="시계" transform="translate\(0 148\) scale\(\.31\)"/);
assert.match(dress,/fill="#355B48"/);
const skirt={...looks['18-2'],garment_spec:{...looks['18-2'].garment_spec,dress:'',top:'긴팔 정장 셔츠',bottom:'수트 스커트',bottomColor:'#243B59',tuck:'in'}};
assert.match(renderLook(skirt,'skirt'),/149 172 Q100 181 51 172/);
console.log('5 accepted SVG hashes unchanged; turtleneck join, knee variants and watch placement passed.');
