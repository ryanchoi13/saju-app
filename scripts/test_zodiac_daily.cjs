// Offline DOM checks; NODE_PATH must include jsdom 26.
const {JSDOM} = require('jsdom');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const dom = new JSDOM(html, {url:'https://dalha.example/', runScripts:'outside-only'});
const w = dom.window, doc = w.document;
w.scrollTo = () => {};
w.HTMLElement.prototype.scrollIntoView = () => {};
const alerts = [], requests = [];
w.alert = value => alerts.push(value);
w.fetch = (url, options) => new Promise(resolve => requests.push({url, options, resolve}));
for (const script of doc.querySelectorAll('script:not([src])')) {
    new vm.Script(script.textContent);
    w.eval(script.textContent);
}
const data = (name, date) => ({name, date, score:85, title:'날짜별 제목', overview:`${date} 안내`,
    star_element:'물 (Water)', star_planet:'해왕성 (Neptune)', focus_content:'오늘의 실천',
    lucky_color:'네이비', lucky_time:'오전 9시 ~ 11시', lucky_match:'오늘의 관계 포인트: 듣기',
    year_tips:[{year_label:'1978년생 (무오)', tip:'오늘의 연도별 안내'}],
    guide_note:'날짜별 일일 가이드', score_note:'점수는 참고 지표'});
function answer(request, payload) { request.resolve({ok:true,json:async () => payload}); }
(async () => {
    await new Promise(resolve => setImmediate(resolve));
    let opening = w.openZodiacModal('star', '물고기자리');
    assert.equal(requests.at(-1).options.cache, 'no-store');
    answer(requests.at(-1), data('물고기자리', '2026-09-21')); await opening;
    assert.equal(doc.getElementById('zodiacModalSub').innerText, '2026-09-21 · 한국 날짜 기준');
    assert.match(doc.getElementById('zodiacYearTipsBox').textContent, /오늘의 실천/);
    assert.match(doc.getElementById('zodiacGuideNote').textContent, /참고 지표/);
    w.closeZodiacModal();
    opening = w.openZodiacModal('zodiac', '말');
    answer(requests.at(-1), data('말띠', '2026-09-22')); await opening;
    assert.equal(doc.getElementById('zodiacModalSub').innerText, '2026-09-22 · 한국 날짜 기준');
    assert.match(doc.getElementById('zodiacYearTipsBox').textContent, /1978년생/);
    const slow = w.openZodiacModal('star', '양자리'), old = requests.at(-1);
    const fast = w.openZodiacModal('star', '황소자리');
    answer(requests.at(-1), data('황소자리','2026-09-22')); await fast;
    answer(old, data('양자리','2026-09-22')); await slow;
    assert.equal(doc.getElementById('zodiacModalName').innerText, '황소자리 오늘의 운세');
    opening = w.openZodiacModal('star','양자리'); w.closeZodiacModal();
    answer(requests.at(-1),data('양자리','2026-09-22')); await opening;
    assert.equal(doc.getElementById('zodiacModal').classList.contains('hidden'),true);
    opening = w.openZodiacModal('star','양자리');
    requests.at(-1).resolve({ok:false}); await opening;
    assert.equal(alerts.length,1);
    assert.equal(doc.getElementById('zodiacModal').classList.contains('hidden'),true);
    console.log('PASS: date label, both guide types, cache bypass, next-day reopen, response race, close, API failure');
})().catch(error => {console.error(error); process.exitCode=1;}).finally(() => w.close());
