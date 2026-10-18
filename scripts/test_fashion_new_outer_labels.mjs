// #188: the fallback SVG renderer must accept the new outer labels (플리스, 퀼팅 재킷) worn
// and carried, draw them with the approved blouson shape, never mutate the input, keep the
// protected kit files untouched, and still reject unknown labels. Self-contained.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {renderLook, FALLBACK_OUTER_SHAPE} from '../assets/dalha-garments/integration.js';

const fixtures = JSON.parse(fs.readFileSync('backend/tests/fixtures/svg_accepted_looks.json'));
const base = fixtures.find(look => look.garment_spec.outer === '패딩' && look.garment_spec.outerMode === 'wear');
assert(base, 'fixture with a worn outer is required');

let rendered = 0;
for (const name of ['플리스', '퀼팅 재킷']) {
  assert.equal(FALLBACK_OUTER_SHAPE[name], '블루종');
  for (const mode of ['wear', 'carry']) {
    const look = structuredClone(base);
    look.garment_spec = {...look.garment_spec, outer: name, outerMode: mode};
    const before = JSON.stringify(look);
    const blouson = structuredClone(look);
    blouson.garment_spec.outer = '블루종';
    const svg = renderLook(look, `new-outer-${rendered}`);
    assert.equal(JSON.stringify(look), before, 'input must not be mutated');
    assert.equal(svg, renderLook(blouson, `new-outer-${rendered}`), `${name}/${mode}: must reuse the blouson drawing`);
    assert(!/undefined|NaN/.test(svg));
    rendered += 1;
  }
}
// Layered outer (overOuter): inner outer stays an approved label, the outer layer is new.
const layeredBase = fixtures.find(look => look.garment_spec.outer === '수트 재킷' && look.garment_spec.outerMode === 'wear');
assert(layeredBase, 'fixture with a worn suit jacket is required');
let layered = 0;
for (const name of ['플리스', '퀼팅 재킷']) {
  for (const open of [true, false]) {
    const look = structuredClone(layeredBase);
    look.garment_spec = {...look.garment_spec, overOuter: {name, color: '#5B6770', open}};
    const before = JSON.stringify(look);
    const blouson = structuredClone(look);
    blouson.garment_spec.overOuter.name = '블루종';
    const svg = renderLook(look, `new-over-${layered}`);
    assert.equal(JSON.stringify(look), before, 'layered input must not be mutated');
    assert.match(svg, /data-role="over-outer"/);
    assert.equal(svg, renderLook(blouson, `new-over-${layered}`), `${name}/open=${open}: must reuse the blouson over-layer`);
    assert(!/undefined|NaN/.test(svg));
    layered += 1;
  }
}
const unknownOver = structuredClone(layeredBase);
unknownOver.garment_spec = {...unknownOver.garment_spec, overOuter: {name: '없는 겉옷', color: '#5B6770', open: true}};
assert.throws(() => renderLook(unknownOver, 'unknown-over'), /지원하지 않는 겉옷 구성/);

const unknown = structuredClone(base);
unknown.garment_spec = {...unknown.garment_spec, outer: '없는 겉옷'};
assert.throws(() => renderLook(unknown, 'unknown-outer'), /지원하지 않는 도안/);
console.log(JSON.stringify({newOuterLabelsRendered: rendered, newOverOuterLabelsRendered: layered, unknownRejected: true}));
