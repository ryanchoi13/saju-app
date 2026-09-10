// Exercise the real HTML and external scripts, with isolated local resources and no network.
const {JSDOM,ResourceLoader,VirtualConsole}=require('jsdom');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
class LocalResources extends ResourceLoader {
  fetch(url) {
    const u=new URL(url);
    if (u.hostname==='dalha.example' && u.pathname.startsWith('/assets/')) {
      const file=path.join(root,u.pathname);
      if (fs.existsSync(file)) return Promise.resolve(fs.readFileSync(file));
    }
    return null;
  }
}
async function boot(url) {
  const errors=[]; let originalStorage,apiCalls=0;
  const logs=new VirtualConsole(); logs.on('jsdomError',e=>errors.push(e));
  const dom=new JSDOM(html,{url,runScripts:'dangerously',resources:new LocalResources(),pretendToBeVisual:true,virtualConsole:logs,beforeParse(w){
    originalStorage=w.localStorage; originalStorage.setItem('wardrobe:real-owner','keep these items');
    w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
    w.fetch=async()=>{apiCalls++;throw Error('No external calls');};w.alert=()=>{};
  }});
  await new Promise(resolve=>dom.window.addEventListener('load',resolve));
  await new Promise(resolve=>setTimeout(resolve,30));
  return {dom,w:dom.window,doc:dom.window.document,errors,originalStorage,get apiCalls(){return apiCalls;}};
}
(async()=>{
  const screens=[];
  for(const design of ['clear','moonlight']) {
    const app=await boot(`https://dalha.example/design/${design}?sample=1`);
    const {doc,w}=app;
    assert.equal(app.errors.length,0,app.errors.map(x=>x.stack).join('\n'));
    assert.equal(doc.documentElement.dataset.design,design);
    assert.equal(w.DALHA_DESIGN_SAMPLE,true);
    assert.equal(doc.getElementById('view-login-gate').classList.contains('hidden'),true);
    assert.equal(doc.getElementById('bottomNavBar').classList.contains('hidden'),false);
    assert.equal(app.apiCalls,0);
    assert.notEqual(w.localStorage,app.originalStorage);
    assert.equal(w.localStorage.getItem('wardrobe:real-owner'),null);
    assert.equal(app.originalStorage.getItem('wardrobe:real-owner'),'keep these items');
    screens.push(doc.getElementById('view-today').textContent.replace(/\s+/g,' ').trim());
    assert.equal(doc.querySelectorAll('.look-card').length,2);
    assert.equal(doc.querySelectorAll('.menu-photo-card').length,2);
    for (const tpo of ['business_casual','business_formal','casual']) {
      const select=doc.getElementById('styleTpoSelect');select.value=tpo;
      select.dispatchEvent(new w.Event('change',{bubbles:true}));
      assert.equal(doc.querySelectorAll('.look-card').length,2,`${design} ${tpo} must keep both looks`);
      assert.ok(!doc.getElementById('resStyle').textContent.includes('불러온'));
    }
    doc.getElementById('tab-saju').click(); doc.getElementById('saju-tab-year').click();
    assert.equal(doc.querySelectorAll('#annualMonthChoices button').length,12);
    doc.querySelectorAll('#annualMonthChoices button')[8].click();
    assert.match(doc.getElementById('annualMonthReading').textContent,/9월/);
    doc.querySelector('#sinnianBox button').click();
    assert.equal(doc.getElementById('archiveDetailModal').classList.contains('hidden'),false);
    doc.getElementById('readingCloseButton').click(); await new Promise(r=>setTimeout(r,20));
    w.openConcern('love');doc.getElementById('btnTheme_love').click();
    await new Promise(r=>setTimeout(r,0));
    assert.equal(doc.querySelectorAll('#modalOptionBox .ui-option').length,4);
    assert.equal(doc.getElementById('themeSelectModal').getAttribute('role'),'dialog');
    w.closeThemeSelectModal();w.openTalismanModal();
    assert.ok(doc.querySelector('#talismanModal .ui-panel'));
    assert.ok(doc.querySelector('#talismanModal .ui-action-primary'));
    w.closeTalismanModal();w.openChargeStore();doc.querySelector('.ui-package').click();
    assert.equal(doc.getElementById('pgPaymentButton').disabled,true);
    doc.getElementById('pgPaymentButton').click();
    assert.equal(app.apiCalls,0);
    await assert.rejects(w.fetch('/api/user/charge',{method:'POST'}));
    assert.equal(app.apiCalls,0);
    assert.equal(app.originalStorage.getItem('wardrobe:real-owner'),'keep these items');
    console.log('PASS',design,'preview content, month navigation, reader, theme options, dialogs, zero requests, untouched account storage');
    w.close();
  }
  assert.equal(screens[0],screens[1]);
  for(const url of ['https://dalha.example/?sample=1','https://dalha.example/design/moonlight']) {
    const app=await boot(url);
    assert.equal(app.w.DALHA_DESIGN_SAMPLE,false);
    assert.equal(app.w.localStorage,app.originalStorage);
    assert.equal(app.doc.getElementById('view-login-gate').classList.contains('hidden'),false);
    assert.equal(app.apiCalls,0);
    assert.equal(app.errors.length,0);
    app.w.close();
  }
  console.log('PASS identical sample content; root and live alternative retain actual login and storage');
})().catch(e=>{console.error(e);process.exitCode=1;});
