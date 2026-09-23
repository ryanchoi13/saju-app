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
const legacy={report_key:'sinnian',report_title:'2026 기존 풀이',report_content:'<h3>보존할 원문</h3><p>예전 본문</p>',created_at:'2026.02.01'};
const current={report_key:'sinnian',report_title:generated.title,report_content:generated.content,
    narrative_version:generated.narrative_version,report_year:2026,created_at:'2026.02.01',
    refreshed_at:'2026-09-23T18:00:00+09:00',previous_versions:[legacy]};

(async()=>{
    await tick();
    evaluate(`currentUserId='user_qa';currentCoin=700;serverUnlockedReports=${JSON.stringify([legacy])};`);
    w.restoreUnlockedUIFromReports();
    assert.equal(doc.querySelectorAll('#sinnianBox button').length,1);
    w.openReadingReport(0);
    assert.ok(!doc.getElementById('annualRefreshButton').classList.contains('hidden'));
    assert.ok(doc.getElementById('readingVersionControl').classList.contains('hidden'));
    let requests=0,finish;
    w.fetch=(url,opts)=>{
        requests++; assert.equal(url,'/api/reports/refresh-annual');
        assert.equal(opts.method,'POST');
        assert.deepEqual(JSON.parse(opts.body),{user_id:'user_qa'});
        return new Promise(resolve=>{finish=()=>resolve({ok:true,json:async()=>({new_balance:700,unlocked_reports:[current]})});});
    };
    const pending=w.refreshOwnedAnnualReport();
    assert.equal(doc.getElementById('annualRefreshButton').disabled,true);
    await w.refreshOwnedAnnualReport(); assert.equal(requests,1);
    finish(); await pending;
    assert.equal(evaluate('currentCoin'),700);
    assert.ok(doc.getElementById('annualRefreshButton').classList.contains('hidden'));
    assert.equal(doc.querySelector('#sinnianBox .reading-primary').textContent,'2026년 올해운세 확인하기');
    assert.ok(doc.getElementById('annualMonthExplorer').classList.contains('hidden'));
    assert.equal(doc.querySelectorAll('#annualMonthReading > *').length,0);
    assert.equal(doc.querySelectorAll('#archiveModalBody [data-report-domain]').length,6);
    assert.equal(doc.querySelectorAll('#readingReportContents button').length,2);
    assert.equal(doc.getElementById('annualYearPanel').hidden,false);
    assert.equal(doc.getElementById('annualMonthPanel').hidden,true);
    assert.match(doc.getElementById('annualYearPanel').textContent,/올해 총운/);
    doc.getElementById('annualReaderTab1').click();
    assert.equal(doc.getElementById('annualYearPanel').hidden,true);
    assert.equal(doc.getElementById('annualMonthPanel').hidden,false);
    assert.equal(doc.querySelectorAll('.annual-reader-months button').length,12);
    for(const button of doc.querySelectorAll('.annual-reader-months button')) {
        button.click();
        assert.equal(doc.querySelectorAll('.annual-selected-month [data-month-domain]').length,6);
        assert.match(doc.querySelector('.annual-selected-month').textContent,/이 풀이의 근거/);
        assert.equal(doc.querySelectorAll('#archiveModalBody [data-report-month]').length,1);
    }
    const printed = new JSDOM('',{url:'https://dalha.test/'});
    let printCalls=0;
    printed.window.print=()=>printCalls++;
    w.open=()=>printed.window;
    w.printReadingReport(); await tick();
    assert.equal(printCalls,1);
    assert.equal(printed.window.document.querySelectorAll('[data-report-month]').length,12);
    assert.equal(printed.window.document.querySelectorAll('[data-report-domain]').length,6);
    assert.match(printed.window.document.body.textContent,/올해 총운/);
    assert.match(printed.window.document.head.textContent,/break-before:page/);
    printed.window.close();
    assert.match(doc.getElementById('readingReportMeta').textContent,/새 풀이 반영일/);
    w.openReadingReport(0,'0');
    assert.match(doc.getElementById('archiveModalBody').textContent,/보존할 원문/);
    assert.match(doc.getElementById('readingReportMeta').textContent,/이전 원문 기록/);
    assert.equal(doc.getElementById('archiveDetailModal').dataset.annualPartitioned,'false');
    w.openReadingReport(0);
    assert.equal(doc.getElementById('readingVersionSelect').value,'current');
    assert.match(doc.getElementById('archiveModalBody').textContent,/가상검증님/);
    assert.equal(doc.querySelectorAll('.annual-kind').length,0);
    assert.equal(doc.querySelectorAll('.reading-modal-actions button').length,2);
    evaluate(`serverUnlockedReports=${JSON.stringify([legacy])};`);
    w.fetch=async()=>({ok:false,json:async()=>({detail:'검증용 저장 실패'})});
    await w.refreshOwnedAnnualReport();
    assert.match(alerts.at(-1),/검증용 저장 실패/);
    assert.equal(evaluate('serverUnlockedReports[0].report_content'),legacy.report_content);
    assert.equal(evaluate('currentCoin'),700);
    assert.equal(evaluate('reportRequestPending'),false);
    w.confirm=()=>false;
    w.fetch=async()=>{throw Error('cancel must not send request');};
    await w.refreshOwnedAnnualReport();
    const ids=[...doc.querySelectorAll('[id]')].map(el=>el.id);
    assert.equal(ids.length,new Set(ids).size);
    assert.match(source,/annual-reading\.css\?v=/);
    console.log('PASS: annual reader, 12 month choices, 6 domains, free upgrade, original archive, duplicate prevention, failure and cancel');
    dom.window.close();
})().catch(error=>{console.error(error);dom.window.close();process.exitCode=1;});
