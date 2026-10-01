// Offline day-rollover regression: no real account or production requests.
const {JSDOM} = require('jsdom');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'),
    {url:'https://dalha.example/', runScripts:'outside-only', pretendToBeVisual:true});
const w = dom.window, doc = w.document;
const run = code => vm.runInContext(code, dom.getInternalVMContext());
const requests = [], applied = [];
w.scrollTo = () => {};
w.fetch = (url, options) => new Promise(resolve => requests.push({url, options, resolve}));
for (const script of doc.querySelectorAll('script:not([src])')) run(script.textContent);
const tick = () => new Promise(resolve => setImmediate(resolve));
const payload = (day='2026-10-02', owner='user_test') => ({status:'existing_user', user_id:owner,
    saju_analysis:{daily_fortune:{date:day, title:'오늘 결과'}}});
function answer(request, data=payload()) { request.resolve({ok:true, json:async () => data}); }
function reset(day='2026-10-01') {
    run(`currentUserId='user_test'; currentFortuneData={daily_fortune:{date:${JSON.stringify(day)}}}; dailyRefreshRetryAt=0;`);
}
(async () => {
    await tick(); // Finish the normal boot before the controlled session fixture.
    requests.splice(0);
    w.tarotTodayKey = () => '2026-10-02';
    w.acceptTarotState = () => {};
    w.syncTarotState = () => {};
    w.applySajuAnalysisToUI = data => {applied.push(data); w.__data=data; run('currentFortuneData=window.__data');};
    doc.getElementById('onboardingInputView').classList.add('hidden');
    w.switchTab('saju');
    reset();
    let pending = w.refreshDailyAnalysisIfNeeded();
    assert.equal(requests.length,1);
    assert.equal(requests[0].url,'/api/auth/session');
    assert.equal(requests[0].options.cache,'no-store');
    await w.refreshDailyAnalysisIfNeeded();
    assert.equal(requests.length,1,'concurrent return events share one request');
    answer(requests[0]); await pending;
    assert.equal(applied.length,1);
    assert.equal(run('currentFortuneData.daily_fortune.date'),'2026-10-02');
    assert.ok(!doc.getElementById('view-saju').classList.contains('hidden'),'no forced tab change');
    await w.refreshDailyAnalysisIfNeeded();
    assert.equal(requests.length,1,'same-day data is stable');

    for (const change of ["currentUserId=null", "currentUserId='user_other'", "currentFortuneData={daily_fortune:{date:'2026-10-02'}}"]) {
        reset(); pending=w.refreshDailyAnalysisIfNeeded(); run(change);
        answer(requests.at(-1)); await pending;
        assert.equal(applied.length,1,'late response cannot replace logout/account/profile results');
    }
    reset(); pending=w.refreshDailyAnalysisIfNeeded(); answer(requests.at(-1),payload('2026-10-01')); await pending;
    assert.equal(applied.length,1,'a stale server response stays yesterday');
    reset(); pending=w.refreshDailyAnalysisIfNeeded(); requests.at(-1).resolve({ok:false}); await pending;
    const afterFailure=requests.length;
    await w.refreshDailyAnalysisIfNeeded();
    assert.equal(requests.length,afterFailure,'failed requests back off');
    assert.equal(run('currentFortuneData.daily_fortune.date'),'2026-10-01');

    reset(); w.dispatchEvent(new w.Event('pageshow'));
    answer(requests.at(-1)); await tick();
    assert.equal(applied.length,2,'browser restoration refreshes the day');
    reset(); doc.dispatchEvent(new w.Event('visibilitychange'));
    answer(requests.at(-1)); await tick();
    assert.equal(applied.length,3,'returning to the page refreshes the day');
    reset(); w.switchTab('today'); answer(requests.at(-1)); await tick();
    assert.equal(applied.length,4,'entering today refreshes the day');
    reset(); doc.getElementById('onboardingInputView').classList.remove('hidden');
    const beforeEdit=requests.length; await w.refreshDailyAnalysisIfNeeded();
    assert.equal(requests.length,beforeEdit,'do not refresh during profile editing');
    console.log('PASS: rollover, same-day stability, deduplication, late-response guards, retry, browser return, tab preservation, profile editing');
})().catch(error => {console.error(error);process.exitCode=1;}).finally(() => w.close());
