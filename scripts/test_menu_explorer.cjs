// Current three-meal / three-set contract. Offline DOM, fake owner, no real account or network.
const {JSDOM}=require('jsdom');
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{url:'https://dalha.example',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,doc=w.document,context=dom.getInternalVMContext();
w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
for(const s of doc.querySelectorAll('script:not([src])'))vm.runInContext(s.textContent,context);
for(const file of ['assets/food-thumbnails-v1/catalog.js','assets/menu-explorer.js'])vm.runInContext(fs.readFileSync(file,'utf8'),context);
vm.runInContext('currentUserId="user_test";',context);
const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const names=Object.keys(w.DALHA_FOOD_THUMBNAILS.menus).slice(0,12);
const plan=i=>({recommendation_number:i,meals:['breakfast','lunch','dinner'].map((period,j)=>({period,menu:names[(i-1)*3+j],kcal:400+j*100,additions:[]}))});
function snapshot(mode,seen,counts={general:seen,diet:0}){
 const history=Array.from({length:seen},(_,i)=>plan(i+1));
 return {date:day,token:'a'.repeat(64),mode,set_limit:3,mode_counts:counts,exhausted:seen===3,history,plan:history.at(-1),items:history.at(-1).meals};
}
const visibleNames=()=>[...doc.querySelectorAll('#menuPhotoCards .meal-title-name')].map(e=>e.textContent);
let calls=[],respond;
w.fetch=async(url,options)=>{assert.equal(url,'/api/menu/explore');const req=JSON.parse(options.body);calls.push(req);return respond(req);};
(async()=>{
 w.DalhaMenu.mount(snapshot('general',1));
 assert.deepEqual(visibleNames(),names.slice(0,3));
 assert.equal(doc.querySelectorAll('#menuPhotoCards .menu-photo-card').length,3);
 assert.match(doc.getElementById('menuStatus').textContent,/1500 kcal/);
 let release;respond=()=>new Promise(r=>release=r);
 const pending=w.DalhaMenu.next();w.DalhaMenu.next();
 assert.equal(calls.length,1);assert.equal(doc.getElementById('menuNext').disabled,true);
 release({ok:true,json:async()=>snapshot('general',2)});await pending;
 assert.deepEqual(visibleNames(),names.slice(3,6));assert.equal(calls[0].expected_seen,1);
 // Local navigation among previously revealed plans never consumes another set.
 const count=calls.length;doc.querySelector('[data-set="1"]').click();
 assert.deepEqual(visibleNames(),names.slice(0,3));assert.equal(calls.length,count);
 respond=async()=>{throw Error('연결 실패');};await w.DalhaMenu.next();
 assert.deepEqual(visibleNames(),names.slice(0,3));assert.match(doc.getElementById('menuError').textContent,/연결 실패/);
 respond=async()=>({ok:true,json:async()=>snapshot('general',3)});await w.DalhaMenu.next();
 assert.deepEqual(visibleNames(),names.slice(6,9));assert.equal(doc.getElementById('menuNext').hidden,true);
 assert.equal(doc.querySelectorAll('.meal-set-nav button').length,3);
 const exhausted=calls.length;await w.DalhaMenu.next();assert.equal(calls.length,exhausted);
 respond=async()=>({ok:true,json:async()=>snapshot('diet',1,{general:3,diet:1})});await w.DalhaMenu.changeMode('diet');
 assert.equal(calls.at(-1).mode,'diet');assert.equal(doc.getElementById('menuMode-diet').getAttribute('aria-pressed'),'true');
 assert.equal(doc.getElementById('menuNext').hidden,false);
 // Late responses must not render after an account/reset boundary.
 respond=()=>new Promise(r=>release=r);const late=w.DalhaMenu.next();w.DalhaMenu.reset();
 release({ok:true,json:async()=>snapshot('diet',2,{general:3,diet:2})});await late;
 assert.equal(doc.getElementById('menuExplorerControls').hidden,true);
 assert.equal(doc.getElementById('menuSetNumber'),null);
 console.log('PASS: three meals, calories, duplicate prevention, local revisits, failure, three-set limit, mode switch, stale response');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>dom.window.close());
