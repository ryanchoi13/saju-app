const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
const server=require('child_process').spawn('python3',['-m','http.server','8765','--bind','127.0.0.1'],{stdio:'ignore'});
process.on('exit',()=>server.kill());
(async()=>{
 const root=path.resolve('review-output/svg-integration');
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-webgl','--no-zygote'],...(process.env.DALHA_CHROMIUM_EXECUTABLE?{executablePath:process.env.DALHA_CHROMIUM_EXECUTABLE}: {})});
 const page=await browser.newPage({viewport:{width:390,height:844}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base='http://127.0.0.1:8765';
 for(let n=0;n<30;n++){try{await fetch(base);break;}catch{await new Promise(r=>setTimeout(r,100));}}
 await page.goto(base+'/review-output/svg-integration/'+encodeURIComponent('달하_자동추천_6조건_검토.html'));
 await page.evaluate(()=>document.fonts.ready);
 const dimensions=[];
 for(const width of [360,390,430,1280]){
  await page.setViewportSize({width,height:844});
  const d=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,cards:[...document.querySelectorAll('article')].map(e=>({width:e.clientWidth,scroll:e.scrollWidth})),svgs:document.querySelectorAll('article svg').length}));
  assert(d.document<=width,JSON.stringify(d));assert.equal(d.svgs,12);assert(d.cards.every(c=>c.scroll<=c.width));dimensions.push(d);
 }
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.locator('[data-id="14-1"]').inputValue(),'통과');
 assert.equal(await page.locator('[data-id="18-2"]').inputValue(),'수정 후 재검토');
 await page.selectOption('#review','pending');assert.equal(await page.locator('article:visible').count(),1);
 await page.selectOption('#review','all');
 await page.selectOption('#gender','female');assert.equal(await page.locator('section:visible').count(),3);
 await page.selectOption('#tpo','business_formal');assert.equal(await page.locator('section:visible').count(),1);
 await page.selectOption('#gender','all');await page.selectOption('#tpo','all');
 await page.selectOption('[data-id="13-1"]','수정 필요');
 await page.fill('[data-note="13-1"]','브라우저 검사 메모');await page.locator('h1').click();
 const dl=page.waitForEvent('download');await page.click('#save');const downloaded=await dl;
 assert.equal(downloaded.suggestedFilename(),'달하_자동추천_검토기록.json');
 const file=await downloaded.path();const rows=JSON.parse(fs.readFileSync(file));assert.equal(rows.length,12);assert.equal(rows[0].note,'브라우저 검사 메모');
 await page.reload();assert.equal(await page.locator('[data-note="13-1"]').inputValue(),'브라우저 검사 메모');
 await page.selectOption('[data-id="13-1"]','미검토');await page.fill('[data-note="13-1"]','');await page.locator('h1').click();
 await page.setInputFiles('#file',{name:'review.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(rows))});
 await page.waitForFunction(()=>document.querySelector('[data-note="13-1"]').value==='브라우저 검사 메모');
 await page.evaluate(()=>localStorage.removeItem('dalha-auto-review-13-18-v3'));await page.reload();
 await page.screenshot({path:path.join(root,'모바일_390px_확인.png'),fullPage:false});
 await page.locator('[data-look="13-1"]').screenshot({path:path.join(root,'모바일_착장_390px_확인.png')});
 assert.deepEqual(errors,[]);
 // Load the actual application and render its actual outfit modal from a fixture payload.
 const app=await browser.newPage({viewport:{width:390,height:844}});
 const appErrors=[];app.on('pageerror',e=>appErrors.push(e.message));
 await app.route('**/*',route=>route.request().url().startsWith(base)?route.continue():route.abort());
 await app.goto(base+'/index.html');
 await app.waitForFunction(()=>Boolean(window.DalhaGarments));
 const sets=JSON.parse(fs.readFileSync(path.join(root,'automatic-sets.json'))).sets;
 await app.evaluate(ctx=>{
  currentFortuneData={daily_fortune:{fashion_v2:{[getStyleTpo()]:ctx}}};
  connectFashionV2Summary();
  if(document.getElementById('openOutfitModalButton').hidden)throw new Error('SVG 착장 버튼이 숨겨졌습니다.');
  openFashionV2Modal();
 },sets[2]);
 assert.equal(await app.locator('#fashionV2Slides svg').count(),2);
 assert.equal(await app.locator('#fashionV2DailyTab').innerText(),'추천 1');
 assert.equal(await app.locator('#fashionV2TrendTab').innerText(),'추천 2');
 await app.locator('#fashionV2TrendTab').click();
 assert.equal(await app.locator('#fashionV2TrendTab').getAttribute('aria-selected'),'true');
 await app.locator('#fashionV2DailyTab').click();
 await app.evaluate(()=>document.fonts.ready);
 await app.screenshot({path:path.join(root,'앱_연결_390px_확인.png'),fullPage:false});
 const result={passed:true,widths:dimensions.map(d=>d.viewport),looks:12,filters:true,download:true,localPersistence:true,import:true,actualAppModal:true,feedbackSeeds:true,pendingFilter:true,appErrors,actualPhone:false,liveFortune:false,liveWeather:false};
 fs.writeFileSync(path.join(root,'browser-check.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));await browser.close();server.kill();
})().catch(e=>{console.error(e);process.exit(1)});
