// Synthetic accounts and responses only; no real draw, top-up or user session.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const {JSDOM}=require('jsdom');
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{url:'https://dalha.example',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,doc=w.document,run=code=>vm.runInContext(code,dom.getInternalVMContext());
w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
const alerts=[],confirmations=[];let confirmAnswers=[];
w.alert=m=>alerts.push(m);
w.confirm=m=>{confirmations.push(m);return confirmAnswers.length?confirmAnswers.shift():true;};
for(const script of doc.querySelectorAll('script:not([src])'))run(script.textContent);
const card={name:'0. THE FOOL (바보)',keyword:'새로운 시작',description:'작은 보따리를 메고 여행을 떠나는 인물의 카드입니다.',symbolism:'가능성',reading_male:'한 걸음을 시작해 보세요.',reading_female:'새로운 경험을 즐겨 보세요.',action_guide:'차분하게 시작하세요.'};
const response=(balance=30,cost=0)=>({ok:true,json:async()=>({card:{...card,name:balance===30?card.name:balance===20?'I. THE MAGICIAN (마법사)':'II. THE HIGH PRIESTESS (여사제)'},new_balance:balance,cost,day:w.tarotTodayKey()})});
let calls=[];
function fetcher(fn){w.fetch=async(url,options)=>{calls.push({url,...JSON.parse(options.body)});return fn(url,options);};}
(async()=>{
 await new Promise(resolve=>setTimeout(resolve,10));
 run('currentUserId="reader";currentCoin=30;ensureTarotSession();');
 let release;
 fetcher(()=>new Promise(resolve=>{release=()=>resolve(response());}));
 const drawing=w.handleTarotDraw(1);await w.handleTarotDraw(2);
 assert.equal(calls.length,1);assert.equal(calls[0].is_paid,false);
 assert.ok(doc.getElementById('tarotChoice2').disabled);release();await drawing;
 assert.match(doc.querySelector('.tarot-card-intro').textContent,/보따리/);
 assert.equal(run('currentCoin'),30);
 await w.handleTarotDraw(1);assert.equal(calls.length,1); // Rereading is free.
 confirmAnswers=[false];await w.handleTarotDraw(2);assert.equal(calls.length,1); // Cancel never spends.
 assert.match(confirmations.at(-1),/^C 10을 사용해/);
 assert.equal(run('tarotPendingDraw'),null);
 fetcher(()=>response(20,10));confirmAnswers=[true];await w.handleTarotDraw(2);
 assert.equal(calls.length,2);assert.equal(run('currentCoin'),20);
 assert.equal(calls[1].slot,2);assert.equal(calls[1].is_paid,true);
 // A network failure retains the same confirmed request for retry.
 fetcher(()=>{throw Error('lost reply');});confirmAnswers=[true];await w.handleTarotDraw(3);
 const uncertainId=calls.at(-1).request_id;
 assert.equal(run('currentCoin'),20);assert.equal(run('tarotPendingDraw.submitted'),false);
 fetcher(()=>response(10,10));confirmAnswers=[true];await w.handleTarotDraw(3);assert.equal(calls.at(-1).request_id,uncertainId);
 assert.equal(run('currentCoin'),10);
 // All three remain visible. There is no reshuffle or fourth paid draw.
 const beforeShuffle=calls.length;
 assert.equal(doc.querySelectorAll('.flipped').length,3);
 assert.equal(doc.getElementById('tarotDrawAgain'),null);
 assert.equal(doc.getElementById('tarotCheckout'),null);
 await w.handleTarotDraw(1);assert.equal(calls.length,beforeShuffle);
 w.closeTarotReading();
 run('tarotSessionIdentity=null;ensureTarotSession();');
 assert.equal(doc.querySelectorAll('.flipped').length,3);
 assert.ok(doc.getElementById('tarotReadingModal').classList.contains('hidden'));
 // A different account has its own free draw and insufficient-funds flow.
 run('currentUserId="low-funds";ensureTarotSession();currentCoin=30;');
 fetcher(()=>response());await w.handleTarotDraw(1);
 // Server funds errors keep the old result and use authoritative balance.
 fetcher(()=>({ok:false,status:402,json:async()=>({detail:{code:'insufficient_coins',new_balance:5,message:'복채가 부족합니다.'}})}));
 confirmAnswers=[true];await w.handleTarotDraw(2);assert.equal(run('currentCoin'),5);
 assert.ok(doc.querySelector('.tarot-card-intro'));
 assert.ok(!doc.getElementById('chargeModal').classList.contains('hidden'));
 w.openPgModal(250,1900,'250 복채');assert.ok(!doc.getElementById('pgModal').classList.contains('hidden'));
 const beforeCharge=calls.length;
 fetcher(url=>url.includes('charge-coin')?({ok:true,json:async()=>({new_balance:255})}):response(245,10));
 await w.processPgPaymentOnServer();
 assert.equal(calls.length,beforeCharge+2);assert.equal(calls.at(-2).url,'/api/user/charge-coin');
 assert.equal(calls.at(-1).url,'/api/daily-tarot/draw');
 assert.equal(run('currentCoin'),245);assert.equal(alerts.length,0); // Confirmed card continues after top-up.
 // Restore by account/date. A second account never sees the first account's cards.
 run('tarotSessionIdentity=null;ensureTarotSession();');assert.equal(run('tarotDrawnToday'),true);
 run('currentUserId="another";ensureTarotSession();');assert.equal(run('tarotDrawnToday'),false);
 assert.equal(doc.querySelectorAll('.flipped').length,0);
 assert.ok(doc.getElementById('tarotResultBox').classList.contains('hidden'));
 // A server-observed free draw in another tab opens confirmation, never auto-spends.
 fetcher(()=>({ok:false,status:409,json:async()=>({detail:{code:'payment_required',new_balance:40,message:'10 복채가 필요해요'}})}));
 await w.handleTarotDraw(1);assert.equal(run('tarotDrawnToday'),true);assert.equal(calls.at(-1).is_paid,false);
 assert.equal(run('tarotPendingDraw'),null);
 assert.match(doc.getElementById('tarotDrawStatus').textContent,/C 10/);
 // The actual C icon is consistently placed before its balance number.
 assert.equal(doc.getElementById('coinHeader').previousElementSibling.id,'headerCoinSvg');
 assert.equal(doc.getElementById('coinMypage').previousElementSibling.id,'mypageCoinSvg');
 const tarotCss=fs.readFileSync('assets/tarot-v2.css','utf8');
 assert.match(tarotCss,/#tarotReadingModal \.detail-sheet-body\{flex:1 1 auto/);
 assert.match(tarotCss,/#tarotReadingModal \.detail-close\{position:sticky;bottom:0/);
 // Unique decorative IDs and different element artworks, with portable download SVG.
 const backs=[1,2,3].map(i=>w.getTarotCardBackSvg(i)).join('');
 const artDom=new JSDOM(backs);const ids=[...artDom.window.document.querySelectorAll('[id]')].map(el=>el.id);
 assert.equal(ids.length,new Set(ids).size);
 const types=['wood_growth','fire_vitality','earth_stability','metal_clarity','water_wisdom'];
 const talismans=types.map(t=>w.renderAuthenticCinnabarTalisman(t));assert.equal(new Set(talismans).size,5);
 assert.ok(talismans.every(svg=>!svg.includes('#FFE853')));
 run('currentTalisman={title:"결단정리부",power:"판단과 정리",desc:"차분한 마음",talisman_type:"metal_clarity"};');w.openTalismanModal();
 assert.ok(doc.querySelector('#talismanRealBox #svgTalismanMain'));
 assert.ok(!doc.getElementById('talismanModal').textContent.includes('비급'));
 console.log('PASS free/paid direct draw, cancel, single flight, reread, server balance, retry ID, insufficient funds, automatic top-up return, account restore, cross-tab free conflict, coin icon order, card descriptions, five talismans, unique SVG IDs');
 dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
