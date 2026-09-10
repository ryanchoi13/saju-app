// Offline DOM regression tests; no real login, payment, or production calls.
// Run with jsdom 26 available through NODE_PATH.
const {JSDOM} = require('jsdom');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const oldHtml = execFileSync('git', ['show', '8dface079c966a67e240bb2013ace414a5055858:index.html'], {cwd:root,encoding:'utf8',maxBuffer:2000000});
const dom = new JSDOM(html, {url:'https://dalha.example/',runScripts:'outside-only',pretendToBeVisual:true});
const w = dom.window, doc = w.document;
const evalApp = code => vm.runInContext(code, dom.getInternalVMContext());
const homeBeforeBoot = doc.getElementById('view-today').outerHTML;
w.scrollTo = () => {};
w.HTMLElement.prototype.scrollIntoView = () => {};
const alerts = [];
w.alert = message => alerts.push(message);
for (const script of doc.querySelectorAll('script:not([src])')) {
    new vm.Script(script.textContent); // Catch syntax failures before executing any tests.
    evalApp(script.textContent);
}
// outside-only intentionally disables HTML handlers; attach the app's own handlers.
for (const el of doc.querySelectorAll('[onclick]')) el.onclick = new w.Function('event', el.getAttribute('onclick'));
let passed = 0;
async function test(name, run) { await run(); passed++; console.log('PASS', name); }
const visible = id => !doc.getElementById(id).closest('.hidden');
const report = (key, body, title=key) => ({report_key:key,report_title:title,report_content:body,created_at:'2025.09.03'});
const tick = () => new Promise(resolve => setTimeout(resolve,30));

(async () => {
    await tick(); // Let the original DOMContentLoaded boot sequence run without saved credentials.
    await test('home and every pre-existing DOM target remain available', () => {
        const oldDoc = new JSDOM(oldHtml).window.document;
        assert.equal(homeBeforeBoot, oldDoc.getElementById('view-today').outerHTML);
        const ids = [...doc.querySelectorAll('[id]')].map(el => el.id);
        assert.equal(ids.length, new Set(ids).size);
        for (const el of oldDoc.querySelectorAll('[id]')) assert.ok(doc.getElementById(el.id), el.id);
        for (const id of ['today','saju','theme','mypage']) assert.equal(doc.getElementById(`view-${id}`).parentElement.tagName, 'MAIN');
        assert.equal(doc.getElementById('cg_h_badge').closest('details').id,'sajuEvidence');
    });
    await test('internal tabs and keyboard selection preserve separate panels', () => {
        w.switchTab('saju');
        assert.ok(visible('saju-basic'));
        doc.getElementById('saju-tab-year').click();
        assert.ok(visible('saju-year')); assert.ok(!visible('saju-basic'));
        doc.getElementById('saju-tab-year').dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowLeft',bubbles:true}));
        assert.ok(visible('saju-life'));
        assert.equal(doc.activeElement.id, 'saju-tab-life');
    });
    await test('concern routes use existing products and preserve situation forms', () => {
        w.openConcern('love');
        assert.ok(visible('concern-love')); assert.ok(!visible('concern-business'));
        doc.getElementById('btnTheme_love').click();
        assert.equal(doc.querySelectorAll('input[name="optM"]').length,4);
        assert.ok(doc.getElementById('modalOptionBox').textContent.includes('기혼'));
        w.closeThemeSelectModal();
        w.selectConcern('all');
        for (const key of ['wealth','love','business','health','study','gunghap']) assert.ok(visible(`concern-${key}`));
    });
    await test('unowned reports expose no paid month or cycle content', () => {
        assert.equal(doc.querySelectorAll('#annualMonthChoices button').length,0);
        assert.ok(doc.getElementById('annualMonthExplorer').classList.contains('hidden'));
        assert.ok(doc.getElementById('lifeCycleExplorer').classList.contains('hidden'));
    });
    const months = Array.from({length:12},(_,i)=>`<div data-report-month="${i+1}"><h3>${i+1}월</h3><p>월별 결과 ${i+1}</p></div>`).join('');
    const annual = report('sinnian',`<div data-report-year="2025">${months}</div>`,'2025 검토용 올해운세');
    const life = report('daewoon','<div data-report-cycle="1" data-cycle-ages="8~17세" data-current-cycle="false">이전 구간</div><div data-report-cycle="2" data-cycle-ages="18~27세" data-current-cycle="true">현재 구간</div>','검토용 평생운세');
    await test('owned periods preserve purchased year and select actual content', () => {
        evalApp(`serverUnlockedReports = ${JSON.stringify([annual,life])}`);
        w.refreshReportEntrypoints();
        assert.match(doc.getElementById('annualYearLabel').textContent,/2025/);
        assert.equal(doc.querySelectorAll('#annualMonthChoices button').length,12);
        doc.querySelectorAll('#annualMonthChoices button')[8].click();
        assert.match(doc.getElementById('annualMonthReading').textContent,/월별 결과 9/);
        assert.equal(doc.querySelector('#lifeCycleChoices [aria-pressed="true"]').textContent,'18~27세');
        assert.match(doc.getElementById('lifeCycleReading').textContent,/현재 구간/);
    });
    await test('reading from different entry points never sends a purchase request', async () => {
        let requests = 0;
        w.fetch = async () => {requests++; throw Error('unexpected request');};
        evalApp('currentUserId="offline-test"; currentCoin=0;');
        await w.handleUnlockReportOnServer('daewoon',450);
        assert.equal(requests,0);
        assert.ok(visible('archiveDetailModal'));
        assert.equal(doc.getElementById('archiveModalTitle').textContent,'검토용 평생운세');
        w.closeArchiveDetailModal(); await tick();
        assert.ok(!visible('archiveDetailModal'));
        assert.equal(w.location.hash,'');
        assert.equal(doc.body.style.overflow,'');
    });
    await test('reader back action restores section and focus; legacy archive stays readable', async () => {
        w.switchTab('saju'); w.selectSajuSection('year');
        const button = doc.querySelector('#sinnianBox button'); button.focus(); button.click();
        assert.equal(doc.activeElement.id,'readingCloseButton');
        assert.equal(doc.querySelectorAll('#readingReportContents button').length,12);
        w.history.back(); await tick();
        assert.ok(visible('saju-year')); assert.equal(doc.activeElement,button);
        evalApp(`serverUnlockedReports = ${JSON.stringify([report('sinnian','<h3>기존 풀이</h3><p>보존한 본문</p>','2024 예전 리포트')])}`);
        w.refreshReportEntrypoints();
        assert.ok(doc.getElementById('annualMonthExplorer').classList.contains('hidden'));
        w.openServerArchiveDetail(0); assert.match(doc.getElementById('archiveModalBody').textContent,/보존한 본문/);
        w.closeArchiveDetailModal(); await tick();
    });
    await test('double purchase clicks send one request and failure unlocks the button', async () => {
        evalApp('serverUnlockedReports=[]; currentCoin=1000;'); w.refreshReportEntrypoints();
        let requests = 0, resolve;
        w.fetch = () => {requests++; return new Promise(r => resolve=r);};
        const first = w.handleUnlockReportOnServer('wealth',220);
        const second = w.handleUnlockReportOnServer('wealth',220);
        assert.equal(requests,1); assert.ok(doc.getElementById('btnTheme_wealth').disabled);
        resolve({ok:false,json:async()=>({detail:'생성 실패'})});
        await Promise.all([first,second]);
        assert.ok(!doc.getElementById('btnTheme_wealth').disabled);
        assert.equal(alerts.at(-1),'생성 실패');
    });
    await test('empty ownership clears prior result surfaces and account-only recent links', () => {
        evalApp('serverUnlockedReports=[];'); w.refreshReportEntrypoints();
        for(const id of ['daewoonBox','sinnianBox','gunghapReportBox','themeReport_wealth']) {
            assert.equal(doc.getElementById(id).childElementCount,0);
            assert.ok(doc.getElementById(id).classList.contains('hidden'));
        }
        assert.equal(doc.getElementById('recentReportList').childElementCount,0);
    });
    console.log(`${passed} interface scenarios passed.`);
    dom.window.close();
})().catch(error => {console.error(error); dom.window.close();process.exitCode=1;});
