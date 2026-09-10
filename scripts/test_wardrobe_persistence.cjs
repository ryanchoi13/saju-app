const {JSDOM}=require('jsdom');
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{url:'https://dalha.example',runScripts:'outside-only'});
const w=dom.window, ctx=dom.getInternalVMContext(), alerts=[];
w.scrollTo=()=>{}; w.alert=x=>alerts.push(x);w.confirm=()=>true;
for(const s of w.document.querySelectorAll('script:not([src])')) vm.runInContext(s.textContent,ctx);
const run=code=>vm.runInContext(code,ctx);
const item={id:17,category:'시계',nickname:'기존 시계',colors:['블랙'],materials:['가죽/세무']};
(async()=>{
    run('currentUserId="user_owner";');
    w.acceptWardrobeResponse({wardrobe_items:[item]});
    assert.equal(w.cachedWardrobe().length,1);
    run('userWardrobeItems=[];');
    w.acceptWardrobeResponse({wardrobe_items:null,wardrobe_error:'불러오기 실패'});
    assert.equal(run('userWardrobeItems.length'),1);
    assert.ok(!w.document.getElementById('wardrobeStorageNotice').hidden);
    run('currentUserId="user_other";');
    w.acceptWardrobeResponse({wardrobe_items:null});
    assert.equal(run('userWardrobeItems.length'),0); // Never show another account's cache.
    run('currentUserId="user_owner";');
    w.acceptWardrobeResponse({wardrobe_items:[item]});
    w.fetch=async()=>({ok:false,json:async()=>({detail:'저장 실패'})});
    await w.deleteWardrobeItem(17);
    assert.equal(run('userWardrobeItems.length'),1);
    assert.equal(w.cachedWardrobe().length,1);
    assert.equal(alerts.at(-1),'저장 실패');
    w.fetch=async()=>({ok:true,json:async()=>({wardrobe_items:[]})});
    await w.deleteWardrobeItem(17);
    assert.equal(w.cachedWardrobe().length,0); // Last-item deletion is authoritative.
    w.acceptWardrobeResponse({wardrobe_items:null});
    assert.equal(run('userWardrobeItems.length'),0); // No resurrection after an outage.
    run('wizardColors=["블랙"];wizardMaterials=["가죽/세무"];wizardCategory="시계";editingWardrobeItemId=null;');
    w.document.getElementById('wardrobeNicknameInput').value='새 시계';
    let resolve, requests=0;
    w.fetch=()=>{requests++;return new Promise(r=>resolve=r);};
    const first=w.saveWardrobeItemToServer(),second=w.saveWardrobeItemToServer();
    assert.equal(requests,1);
    resolve({ok:true,json:async()=>({wardrobe_items:[item]})});
    await Promise.all([first,second]);
    assert.equal(w.cachedWardrobe().length,1);
    assert.equal(run('wardrobeSavePending'),false);
    console.log('PASS account cache, unavailable-vs-empty, failed deletion, final deletion, duplicate save');
    dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
