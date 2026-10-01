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
const oldHtml = execFileSync('git', ['show', '006d8274ca758a4febe65c10953e2dfc55eb2a7c:index.html'], {cwd:root,encoding:'utf8',maxBuffer:2000000});
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
    await test('mobile Kakao login prefers the installed KakaoTalk app', () => {
        let loginOptions = null;
        w.DALHA_DESIGN_SAMPLE = true;
        w.Kakao = {
            isInitialized: () => true,
            Auth: {login: options => { loginOptions = options; }},
        };
        w.loginWithKakaoReal();
        assert.equal(loginOptions?.throughTalk, true);
        assert.equal(loginOptions?.persistAccessToken, true);
    });
    await test('home and every pre-existing DOM target remain available', () => {
        const oldDoc = new JSDOM(oldHtml).window.document;
        const newHome = new JSDOM(homeBeforeBoot).window.document;
        // The full brand refresh intentionally changes presentation. All home actions remain connected.
        const actions = node => [...node.querySelectorAll('[onclick],[onchange]')].map(el=>el.getAttribute('onclick') || el.getAttribute('onchange'));
        assert.deepEqual(actions(newHome.getElementById('view-today')),actions(oldDoc.getElementById('view-today')));
        const ids = [...doc.querySelectorAll('[id]')].map(el => el.id);
        assert.equal(ids.length, new Set(ids).size);
        const removedArchivePromotions = new Set(['recentReportSection','recentReportList']);
        for (const el of oldDoc.querySelectorAll('[id]')) if (!removedArchivePromotions.has(el.id)) assert.ok(doc.getElementById(el.id), el.id);
        for (const id of ['today','saju','theme','mypage']) assert.equal(doc.getElementById(`view-${id}`).parentElement.tagName, 'MAIN');
        assert.equal(doc.getElementById('cg_h_badge').closest('details').id,'sajuEvidence');
    });
    await test('internal tabs and keyboard selection preserve separate panels', () => {
        w.switchTab('saju');
        assert.ok(visible('saju-basic'));
        doc.getElementById('saju-tab-year').click();
        assert.ok(visible('saju-year')); assert.ok(!visible('saju-basic'));
        doc.getElementById('saju-tab-year').dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowLeft',bubbles:true}));
        assert.ok(visible('saju-basic'));
        assert.equal(doc.activeElement.id, 'saju-tab-basic');
        assert.equal(doc.querySelectorAll('.reading-tabs [role=tab]:not([hidden])').length,2);
        assert.equal(doc.getElementById('saju-life').open,false);
        w.selectSajuSection('life');
        assert.ok(visible('saju-basic'));
        assert.equal(doc.getElementById('saju-life').open,true);
        doc.getElementById('saju-life').open=false;
    });
    await test('reading tabs follow the agreed information order', () => {
        const before = (a,b) => Boolean(a.compareDocumentPosition(b) & w.Node.DOCUMENT_POSITION_FOLLOWING);
        const summary = doc.getElementById('sajuSummaryTitle').closest('section');
        const basic = doc.getElementById('saju-basic');
        const life = doc.getElementById('saju-life');
        const year = doc.getElementById('saju-year');
        const evidence = doc.getElementById('sajuEvidence');
        assert.equal(summary.parentElement,basic);
        assert.ok(before(summary,basic.querySelector('.reading-lead')) && before(basic,life) && before(life,year) && before(year,evidence));
        assert.equal(evidence.parentElement.id,'view-saju');

        const choiceTitle = doc.getElementById('concernChoiceTitle');
        const choices = doc.querySelector('.concern-choices');
        const reportTitle = doc.querySelector('.concern-result-title');
        const compatibility = doc.getElementById('concern-gunghap');
        assert.ok(compatibility.classList.contains('hidden'));
        assert.equal(life.parentElement,basic);
        assert.equal(doc.querySelectorAll('#view-saju [onclick^=openConcern]').length,0);
        const allTopics = doc.getElementById('allConcernTopicsLink');
        assert.ok(before(choiceTitle,choices) && before(choices,reportTitle));
        assert.ok(before(reportTitle,compatibility) && before(compatibility,allTopics));
        assert.equal(doc.querySelectorAll('[data-concern-choice]').length,6);
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
    await test('question choices reveal a matching outline, preserve focus and never purchase', () => {
        let requests=0; w.fetch=async()=>{requests++;throw Error('unexpected purchase');};
        for (const key of ['business','love','wealth','study','health']) {
            doc.querySelector(`[data-concern-choice="${key}"]`).click();
            assert.ok(visible(`concern-${key}`));
            assert.equal(doc.querySelectorAll('[data-concern]:not(.hidden)').length,1);
            assert.equal(doc.activeElement.id,`concern-heading-${key}`);
            assert.equal(doc.querySelectorAll(`#concern-${key} .report-preview li`).length,3);
            assert.match(doc.querySelector(`[data-report-price="${key}"]`).textContent,/220/);
        }
        doc.querySelector('[data-concern-choice=gunghap]').click();
        assert.equal(doc.querySelectorAll('[data-concern]:not(.hidden)').length,1);
        assert.match(doc.querySelector('[data-report-price=gunghap]').textContent,/350/);
        w.showCompatibility();
        assert.equal(doc.activeElement.id,'compatibilityTitle');
        assert.equal(requests,0);
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
        // Annual content stays in its dedicated reader; legacy results remain readable.
        assert.equal(doc.querySelectorAll('#annualMonthChoices button').length,0);
        assert.ok(doc.getElementById('annualMonthExplorer').classList.contains('hidden'));
        assert.equal(doc.querySelector('#lifeCycleChoices [aria-pressed="true"]').textContent,'18~27세');
        assert.match(doc.getElementById('lifeCycleReading').textContent,/현재 구간/);
    });
    await test('lifetime preview uses only the saved current section and offers a free explicit upgrade for legacy versions', () => {
        let requests=0; w.fetch=async()=>{requests++;throw Error('unexpected refresh');};
        assert.match(doc.getElementById('lifetimeCurrentReading').textContent,/현재 구간/);
        assert.ok(doc.getElementById('lifetimeRefreshButton'));
        assert.equal(w.readingNeedsRefresh({...life,narrative_version:'reading-conversation-v3'}),true);
        const upgraded={...life,narrative_version:'lifetime-present-v1',report_content:'<div><section data-lifetime-section="current"><section class="reading-chapter"><h3>저장된 현재</h3><p>구매 당시 나의 구체적 이야기</p></section></section><section data-lifetime-section="nature">성향 참고</section><details data-lifetime-section="cycles"><summary>대운</summary>과거 구간</details></div>'};
        evalApp(`serverUnlockedReports=${JSON.stringify([upgraded])}`);w.refreshReportEntrypoints();
        assert.match(doc.getElementById('lifetimeCurrentReading').textContent,/구매 당시 나의 구체적 이야기/);
        assert.doesNotMatch(doc.getElementById('lifetimeCurrentReading').textContent,/과거 구간/);
        assert.equal(doc.getElementById('lifetimeRefreshButton'),null);
        assert.equal(w.readingNeedsRefresh(upgraded),false);
        assert.equal(w.readingNeedsRefresh({...annual,narrative_version:'reading-conversation-v3'}),false);
        assert.equal(requests,0);
        evalApp(`serverUnlockedReports=${JSON.stringify([annual,life])}`);w.refreshReportEntrypoints();
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
        assert.equal(doc.querySelectorAll('#readingReportContents button').length,0);
        assert.ok(!visible('readingReportContents'));
        assert.equal(doc.querySelectorAll('#archiveModalBody h3').length,12);
        w.history.back(); await tick();
        assert.ok(visible('saju-year')); assert.equal(doc.activeElement,button);
        evalApp(`serverUnlockedReports = ${JSON.stringify([report('sinnian','<h3>기존 풀이</h3><p>보존한 본문</p>','2024 예전 리포트')])}`);
        w.refreshReportEntrypoints();
        assert.ok(doc.getElementById('annualMonthExplorer').classList.contains('hidden'));
        w.openServerArchiveDetail(0); assert.match(doc.getElementById('archiveModalBody').textContent,/보존한 본문/);
        w.closeArchiveDetailModal(); await tick();
    });
    await test('all saved readings open directly without a duplicate menu or purchase date and retain their source', async () => {
        let requests=0;
        w.fetch=async()=>{requests++; throw Error('reopening must not request a new report');};
        for(const key of ['daewoon','wealth','business','love','health','study','gunghap']) {
            const saved={...report(key,'<div class="long-reading"><section class="reading-chapter"><h3>첫 번째 이야기</h3><p>구매 당시의 원문</p></section><section class="reading-chapter"><h3>두 번째 이야기</h3><p>그대로 보관할 내용</p></section></div>','가상검증님 정통 명리 평생 직업·사업운'),narrative_version:'reading-conversation-v3'};
            evalApp(`serverUnlockedReports=${JSON.stringify([saved])};`);
            w.renderServerArchive(); w.refreshReportEntrypoints();
            assert.match(doc.getElementById('unlockedArchiveList').textContent,/2025.09.03/);
            const slot=doc.getElementById(key==='daewoon'?'daewoonBox':key==='gunghap'?'gunghapReportBox':`themeReport_${key}`);
            assert.doesNotMatch(slot.textContent,/2025.09.03/);
            w.openServerArchiveDetail(0);
            assert.equal(doc.getElementById('readingReportMeta').hidden,true);
            assert.equal(doc.getElementById('readingReportMeta').textContent,'');
            assert.ok(!visible('readingReportContents'));
            assert.equal(doc.querySelectorAll('#readingReportContents button').length,0);
            assert.equal(doc.getElementById('archiveModalBody').innerHTML,saved.report_content);
            w.closeArchiveDetailModal(); await tick();
            await w.handleUnlockReportOnServer(key,220);
            assert.equal(doc.getElementById('archiveModalBody').innerHTML,saved.report_content);
            assert.equal(evalApp('JSON.stringify(serverUnlockedReports[0])'),JSON.stringify(saved));
            w.closeArchiveDetailModal(); await tick();
        }
        assert.equal(requests,0);
    });
    await test('theme upgrade uses explicit situation choices, preserves cancellation and never purchases again', async () => {
        const old={...report('love','<p>기존 구매 원문</p>','애정운'),narrative_version:'reading-conversation-v3'};
        evalApp(`currentUserId='offline-test'; currentCoin=780; serverUnlockedReports=${JSON.stringify([old])}; readingReportIndex=0;`);
        w.refreshReportEntrypoints();
        let requests=[];
        w.fetch=async(url,opts)=>{
            requests.push({url,body:JSON.parse(opts.body)});
            const updated={...old,narrative_version:'theme-present-v1',report_content:'<section data-theme-section="current"><h2>지금 살펴볼 이야기</h2><p>기혼 상황에 맞춘 새 풀이</p></section>',previous_versions:[old],reading_context:{sub_option:'기혼'}};
            return {ok:true,json:async()=>({new_balance:780,unlocked_reports:[updated]})};
        };
        await w.refreshOwnedReading();
        assert.ok(visible('themeSelectModal'));
        assert.equal(doc.querySelector('input[name="optM"]:checked'),null);
        assert.equal(doc.getElementById('themeSelectConfirm').disabled,true);
        w.closeThemeSelectModal();
        assert.ok(!visible('archiveDetailModal'));
        assert.equal(requests.length,0);
        w.openReadingReport(0);
        await w.refreshOwnedReading();
        assert.ok(!visible('archiveDetailModal'));
        w.closeThemeSelectModal();
        assert.ok(visible('archiveDetailModal'));
        assert.equal(doc.getElementById('archiveModalBody').innerHTML,old.report_content);
        await w.refreshOwnedReading();
        const option=doc.querySelector('input[name="optM"][value="기혼"]');option.checked=true;
        option.dispatchEvent(new w.Event('change',{bubbles:true}));
        assert.equal(doc.getElementById('themeSelectConfirm').disabled,false);
        w.confirm=()=>true; doc.getElementById('themeSelectConfirm').click();await tick();
        assert.deepEqual(requests.map(x=>x.url),['/api/reports/refresh']);
        assert.equal(requests[0].body.sub_option,'기혼');
        assert.equal(evalApp('currentCoin'),780);
        assert.equal(evalApp('JSON.stringify(serverUnlockedReports[0].previous_versions[0])'),JSON.stringify(old));
        assert.equal(w.readingNeedsRefresh(evalApp('serverUnlockedReports[0]')),false);
        assert.match(doc.getElementById('archiveModalBody').textContent,/기혼 상황/);
        assert.ok(doc.getElementById('annualRefreshButton').classList.contains('hidden'));
        assert.equal(doc.querySelectorAll('.theme-refresh').length,0);
        w.closeArchiveDetailModal();await tick();
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
    await test('empty ownership clears prior result surfaces', () => {
        evalApp('serverUnlockedReports=[];'); w.refreshReportEntrypoints();
        for(const id of ['daewoonBox','sinnianBox','gunghapReportBox','themeReport_wealth']) {
            assert.equal(doc.getElementById(id).childElementCount,0);
            assert.ok(doc.getElementById(id).classList.contains('hidden'));
        }
        assert.equal(doc.getElementById('recentReportList'),null);
        assert.equal(doc.getElementById('lifeCycleReading').childElementCount,0);
        assert.equal(doc.getElementById('lifeCycleChoices').childElementCount,0);
        assert.equal(doc.querySelector('[data-report-price="daewoon"]').textContent,'450 복채');
    });
    console.log(`${passed} interface scenarios passed.`);
    dom.window.close();
})().catch(error => {console.error(error); dom.window.close();process.exitCode=1;});
