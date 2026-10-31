// Offline production-HTML tests. Fake owner; no real login, wallet or requests.
const {JSDOM} = require('jsdom');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const generated = JSON.parse(execFileSync(process.env.PYTHON || 'python', ['-c', `
import main,json
from datetime import date,time
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.annual import build_annual_overall_report
core=calculate_myeongri_core(BirthInput(name='가상검증',gender='female',birth_date=date(1992,5,16),birth_time=time(8)),target_date=date(2026,9,23))
print(json.dumps(build_annual_overall_report(core,'가상검증',2026),ensure_ascii=False))
`], {cwd:root,env:{...process.env,PYTHONUTF8:'1'},encoding:'utf8',maxBuffer:4000000}));

const dom = new JSDOM(source, {url:'https://dalha.test/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window, doc=w.document;
const evaluate = code => vm.runInContext(code,dom.getInternalVMContext());
w.scrollTo=()=>{}; w.HTMLElement.prototype.scrollIntoView=()=>{};
const alerts=[]; w.alert=message=>alerts.push(message); w.confirm=()=>true;
for(const script of doc.querySelectorAll('script:not([src])')) {
    new vm.Script(script.textContent); evaluate(script.textContent);
}
const tick=()=>new Promise(resolve=>setTimeout(resolve,20));
evaluate(fs.readFileSync(path.join(root,'assets/annual-reader.js'),'utf8'));
evaluate(fs.readFileSync(path.join(root,'assets/reading-polish.js'),'utf8'));
const current={report_key:'sinnian',report_title:generated.title,report_content:generated.content,
    narrative_version:generated.narrative_version,report_year:2026,created_at:'2026.02.01'};

(async()=>{
    await tick();
    // 구매한 풀이는 서버가 최신으로 바꿔서 보낸다. 화면에는 새로 받기·이전 원문 선택이 없다.
    for (const id of ['annualRefreshButton','readingVersionControl','readingVersionSelect'])
        assert.equal(doc.getElementById(id),null,id);
    assert.equal(typeof w.refreshOwnedReading,'undefined');
    evaluate(`currentUserId='user_qa';currentCoin=700;serverUnlockedReports=${JSON.stringify([current])};`);
    w.restoreUnlockedUIFromReports();
    assert.equal(doc.querySelector('#sinnianBox .reading-primary').textContent,'2026년 올해운세 확인하기');
    assert.equal(doc.querySelector('[data-report-price="sinnian"]').textContent,'구매한 풀이');
    w.openReadingReport(0);
    assert.equal(doc.querySelectorAll('#archiveModalBody [data-report-domain]').length,5);
    assert.equal(doc.getElementById('annualYearPanel').hidden,false);
    assert.equal(doc.getElementById('annualMonthPanel').hidden,true);
    assert.match(doc.getElementById('annualYearPanel').textContent,/올해 총운/);
    assert.equal(doc.getElementById('archiveModalTitle').firstChild.textContent,'올해·월별 운세');
    assert.equal(doc.querySelector('#archiveModalTitle .reading-report-year').textContent,'2026년');
    assert.equal(doc.getElementById('readingReportMeta').textContent,'');
    const quickMonth=doc.querySelector('#sinnianBox .reading-secondary');
    assert.ok(quickMonth);
    quickMonth.click();
    assert.equal(doc.activeElement.id,'annualReaderTab1');
    assert.equal(doc.getElementById('annualMonthPanel').hidden,false);
    assert.equal(doc.querySelectorAll('.annual-reader-months button').length,12);
    for(const button of doc.querySelectorAll('.annual-reader-months button')) {
        button.click();
        const card=doc.querySelector('#annualMonthPanel [data-report-month]:not([hidden])') || doc.querySelector('#annualMonthPanel [data-report-month]');
        assert.ok(card, button.textContent);
        assert.match(card.textContent,/이달의 초점/);
        assert.match(card.textContent,/근거/);
        assert.match(card.textContent,/처방/);
    }
    const printed = new JSDOM('',{url:'https://dalha.test/'});
    let printCalls=0;
    printed.window.print=()=>printCalls++;
    w.open=()=>printed.window;
    w.printReadingReport(); await tick();
    assert.equal(printCalls,1);
    assert.equal(printed.window.document.querySelectorAll('[data-report-month]').length,12);
    assert.equal(printed.window.document.querySelectorAll('[data-report-domain]').length,5);
    assert.match(printed.window.document.body.textContent,/올해 총운/);
    printed.window.close();
    assert.equal(evaluate('serverUnlockedReports[0].created_at'),'2026.02.01');
    assert.equal(evaluate('currentCoin'),700);
    const ids=[...doc.querySelectorAll('[id]')].map(el=>el.id);
    assert.equal(ids.length,new Set(ids).size);
    assert.match(source,/annual-reading\.css\?v=/);
    console.log('PASS: annual reader, 12 months with grade, 5 domains, print, no refresh UI');
    dom.window.close();
})().catch(error=>{console.error(error);dom.window.close();process.exitCode=1;});
