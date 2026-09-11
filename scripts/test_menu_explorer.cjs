const {JSDOM}=require('jsdom');
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{url:'https://dalha.example',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,doc=w.document,context=dom.getInternalVMContext();
w.scrollTo=()=>{};
for(const s of doc.querySelectorAll('script:not([src])')) vm.runInContext(s.textContent,context);
vm.runInContext(fs.readFileSync('assets/food-thumbnails-v1/catalog.js','utf8'),context);
vm.runInContext(fs.readFileSync('assets/menu-explorer.js','utf8'),context);
vm.runInContext('currentUserId="user_test";',context);
const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const names=Object.keys(w.DALHA_FOOD_THUMBNAILS.menus);
const rankings={general:names.slice(0,20).map((menu,i)=>({menu,rank:i+1})),diet:Array.from({length:10},(_,i)=>({menu:`다이어트 예시 ${i+1}`,rank:i+1}))};
function snapshot(mode,seen,display=seen,counts={general:seen,diet:0}) {
  const history=rankings[mode].slice(0,seen*2);
  return {date:day,token:'a'.repeat(64),mode,seen_sets:seen,set_limit:mode==='general'?10:5,
    mode_counts:counts,exhausted:seen===(mode==='general'?10:5),display_set:display,
    history,items:history.slice((display-1)*2,display*2),basis_text:'오늘의 일진을 참고한 추천'};
}
const captions=()=>[...doc.querySelectorAll('#menuPhotoCards figcaption')].map(el=>el.textContent);
let calls=[],respond;
w.fetch=async(url,options)=>{
  assert.equal(url,'/api/menu/explore'); const request=JSON.parse(options.body);calls.push(request);
  return await respond(request);
};
(async()=>{
  w.DalhaMenu.mount(snapshot('general',1));
  assert.deepEqual(captions(),names.slice(0,2));
  assert.equal(doc.getElementById('menuPlanLike').hidden,true);
  let release;
  respond=()=>new Promise(resolve=>release=resolve);
  const pending=w.DalhaMenu.next();w.DalhaMenu.next();
  assert.equal(calls.length,1);assert.equal(doc.getElementById('menuNext').disabled,true);
  release({ok:true,json:async()=>snapshot('general',2)}); await pending;
  assert.deepEqual(captions(),names.slice(2,4));
  assert.equal(calls[0].expected_seen,1);
  // A network failure does not spend or locally fabricate another set.
  respond=async()=>{throw Error('연결 실패');};await w.DalhaMenu.next();
  assert.deepEqual(captions(),names.slice(2,4));assert.match(doc.getElementById('menuError').textContent,/연결 실패/);
  respond=async req=>({ok:true,json:async()=>snapshot('general',req.expected_seen+1)});
  for(let i=3;i<=10;i++) await w.DalhaMenu.next();
  assert.match(doc.getElementById('menuNext').textContent,/오늘 추천받은 메뉴 보기/);
  const before=calls.length;w.DalhaMenu.next();
  assert.equal(calls.length,before);assert.equal(doc.getElementById('menuHistoryModal').classList.contains('hidden'),false);
  assert.equal(doc.querySelectorAll('#menuHistoryCards .menu-photo-card').length,20);
  assert.deepEqual([...doc.querySelectorAll('#menuHistoryCards figcaption')].map(el=>el.textContent),names.slice(0,20));
  w.DalhaMenu.close();
  // Reopening shows the first set but keeps the exhausted quota and all history.
  w.DalhaMenu.mount(snapshot('general',10,1));
  assert.deepEqual(captions(),names.slice(0,2));assert.match(doc.getElementById('menuNext').textContent,/메뉴 보기/);
  respond=async req=>({ok:true,json:async()=>snapshot('diet',1,1,{general:10,diet:1})});
  await w.DalhaMenu.changeMode('diet');
  assert.equal(calls.at(-1).expected_seen,0);assert.equal(calls.at(-1).action,'open');
  assert.equal(doc.querySelectorAll('#menuPhotoCards .menu-photo-placeholder').length,2);
  assert.equal(doc.querySelectorAll('#menuPhotoCards .food-photo').length,0);
  respond=async req=>({ok:true,json:async()=>snapshot('diet',req.expected_seen+1,req.expected_seen+1,{general:10,diet:req.expected_seen+1})});
  for(let i=2;i<=5;i++) await w.DalhaMenu.next();
  w.DalhaMenu.next();assert.equal(doc.querySelectorAll('#menuHistoryCards .menu-photo-card').length,10);w.DalhaMenu.close();
  assert.equal(doc.getElementById('menuMode-diet').getAttribute('aria-pressed'),'true');
  // A new account cannot receive an old account's pending response.
  w.DalhaMenu.mount(snapshot('general',1));respond=()=>new Promise(resolve=>release=resolve);
  const stale=w.DalhaMenu.next();w.DalhaMenu.reset();vm.runInContext('currentUserId="user_other";',context);
  release({ok:true,json:async()=>snapshot('general',2)});await stale;
  assert.equal(doc.getElementById('menuExplorerControls').hidden,true);
  // Midnight requests open a new day instead of spending a next recommendation.
  vm.runInContext('currentUserId="user_test";',context);
  w.DalhaMenu.mount({...snapshot('general',10,1),date:'2000-01-01'});
  respond=async()=>({ok:true,json:async()=>snapshot('general',1)});
  await w.DalhaMenu.next();assert.equal(calls.at(-1).action,'open');
  assert.deepEqual(captions(),names.slice(0,2));
  assert.ok(!doc.getElementById('menuPhotoCards').textContent.includes('점심'));
  assert.ok(calls.every(c=>!('liked' in c)));
  console.log('PASS ranked pairs, independent limits, popup history, top pair on reopen, failed/duplicate requests, account isolation, midnight and no likes');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>w.close());
