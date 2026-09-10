const {JSDOM}=require('jsdom');
const fs=require('node:fs'), assert=require('node:assert/strict'), vm=require('node:vm');
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{url:'https://dalha.example',runScripts:'outside-only'});
const w=dom.window; w.scrollTo=()=>{};
vm.runInContext(fs.readFileSync('assets/food-thumbnails-v1/catalog.js','utf8'),dom.getInternalVMContext());
for(const s of w.document.querySelectorAll('script:not([src])')) vm.runInContext(s.textContent,dom.getInternalVMContext());
const palette={tpo:'casual',gender:'male',style_mood:'casual',top:{name:'Long English Name',name_ko:'네이비',hex:'#123456',standard_color:'네이비'},bottom:{name:'Black',name_ko:'블랙',hex:'#111111',standard_color:'블랙'}};
const formal={...palette,tpo:'business_formal',style_mood:'business_formal',outfit_guidance:'남색 정장 · 블랙 넥타이'};
for(const [word,pair,expected] of [['시계','을/를','시계를'],['가방','을/를','가방을'],['네이비','과/와','네이비와'],['블랙','은/는','블랙은'],['하늘','으로/로','하늘로']]) assert.equal(w.DalhaHangul.josa(word,pair),expected);
assert.match(w.styleWord('시계','을/를'),/시계<\/strong>를/);
assert.ok(!w.styleWord('<img src=x>','을/를').includes('<img'));
const fortune={date:'2026-09-10',lucky_item:'블랙 러버 시계'};
const rubber={id:'1',category:'시계',nickname:'스포츠 시계',materials:['러버/실리콘'],colors:['블랙']};
const leather={id:'2',category:'시계',nickname:'가죽 시계',materials:['가죽/세무'],colors:['블랙']};
assert.equal(w.selectDailyAccessory([rubber],fortune,formal).item,null); // Lucky match cannot cross TPO boundary.
assert.equal(w.selectDailyAccessory([rubber,leather],fortune,formal).item.id,'2');
assert.equal(w.selectDailyAccessory([rubber],fortune,palette).item.id,'1');
const empty=w.selectDailyAccessory([],fortune,palette);
assert.equal(empty.item,null);assert.equal(empty.text,'');assert.ok(!empty.text.includes('러버'));
assert.equal(w.selectDailyAccessory([{...leather,colors:['레드']}],fortune,palette).item,null);
assert.equal(w.selectDailyAccessory([{...leather,materials:[]}],fortune,palette).item,null);
assert.equal(w.selectDailyAccessory([{category:'액세서리',nickname:'포켓 스퀘어',materials:['실크/쉬폰'],colors:['블랙']}],fortune,formal).item,null);
assert.equal(w.selectDailyAccessory([rubber,leather],fortune,palette).item.id,
 w.selectDailyAccessory([leather,rubber],{date:'2026-09-12',lucky_item:'가죽 시계'},palette).item.id);
vm.runInContext('currentUserId="style-account";currentFortuneData='+JSON.stringify({daily_fortune:{...fortune,wada_palette:palette,style_palettes:{casual:palette,business_formal:formal}}})+';userWardrobeItems=[];updateTodayWardrobeMatchPick();',dom.getInternalVMContext());
assert.equal(w.getStyleTpo(),'casual');
const pick=w.document.getElementById('wardrobeDailyMatchPick');
assert.ok(pick.hidden); assert.equal(pick.textContent,'');
assert.equal(w.document.getElementById('todayStyleMoodBadge'),null);
assert.equal(w.document.querySelectorAll('#styleTpoControls select').length,1);
vm.runInContext('userWardrobeItems='+JSON.stringify([rubber])+';updateTodayWardrobeMatchPick();',dom.getInternalVMContext());
assert.ok(!pick.hidden); assert.match(pick.textContent,/스포츠 시계/);
w.setStyleTpo('business_formal');
assert.equal(w.localStorage.getItem('dalha_style_tpo:style-account'),'business_formal');
assert.ok(pick.hidden);assert.equal(pick.textContent,'');
assert.equal(w.document.getElementById('styleTpoSelect').value,'business_formal');
assert.equal(w.document.getElementById('resStyle').textContent,formal.outfit_guidance);
w.updateTodayWardrobeMatchPick();assert.equal(w.getStyleTpo(),'business_formal');
vm.runInContext('currentUserId="another-account";',dom.getInternalVMContext());
assert.equal(w.getStyleTpo(),'casual'); // No cross-account preference leak.
w.updateTodayWardrobeMatchPick();
const chips=w.document.querySelectorAll('#dynamicColorPaletteBox > .palette-chip');
assert.equal(chips.length,2);assert.match(chips[0].textContent,/네이비/);assert.ok(!chips[0].textContent.includes('Long English'));
w.renderMenuPhotos(['후라이드치킨','김치찌개']);
assert.equal(w.document.querySelectorAll('.food-photo').length,2);
assert.match(w.document.querySelector('.food-photo').getAttribute('aria-label'),/후라이드치킨/);
w.renderMenuPhotos(['생선구이','<img src=x>']);
assert.equal(w.document.querySelectorAll('.food-photo').length,0);
assert.equal(w.document.querySelectorAll('#menuPhotoCards img').length,0);
const foodCatalog=w.DALHA_FOOD_THUMBNAILS;
const foodFiles=new Set();
for(const name of Object.keys(foodCatalog.menus)) {
    w.renderMenuPhotos([name]);
    const photo=w.document.querySelector('#menuPhotoCards .food-photo');
    assert.ok(photo,`Missing food illustration: ${name}`);
    assert.equal(photo.getAttribute('aria-label'),`${name} 예시 일러스트`);
    assert.equal(w.document.querySelector('#menuPhotoCards figcaption').textContent,name);
    const crop=w.foodThumbnail(name);
    const clip=photo.querySelector('svg');
    assert.equal(clip.getAttribute('overflow'),'hidden');
    assert.equal(clip.getAttribute('viewBox'),`0 0 ${crop.width} ${crop.height}`);
    assert.equal(clip.querySelector('image').getAttribute('x'),String(-crop.x));
    foodFiles.add(crop.url);
}
assert.equal(foodFiles.size,foodCatalog.files.length);
delete w.DALHA_FOOD_THUMBNAILS;
w.renderMenuPhotos(['김치찌개']);
assert.equal(w.document.querySelectorAll('#menuPhotoCards .food-photo').length,0);
assert.equal(w.document.querySelector('#menuPhotoCards figcaption').textContent,'김치찌개');
w.DALHA_FOOD_THUMBNAILS=foodCatalog;
console.log(`PASS ${Object.keys(foodCatalog.menus).length} exact food illustrations and missing-catalog fallback`);
w.renderOutfitCards({looks:[{title:'페일 레드 포인트',items:[{label:'셔츠',color_name:'화이트',hex:'#FFFFFF',sprite:2}]}]});
assert.equal(w.document.querySelectorAll('.look-card').length,1);
assert.equal(w.document.querySelector('.garment rect').getAttribute('fill'),'#FFFFFF');
assert.match(w.document.querySelector('.look-piece').textContent,/화이트셔츠/);
// All sprites clip both the mask and detail source, including two shoe components.
w.renderOutfitCards({looks:[0,1].map(n=>({title:'검증',items:Array.from({length:16},(_,sprite)=>({label:'옷',color_name:'네이비',hex:'#26354A',sprite}))}))});
const garments=[...w.document.querySelectorAll('.garment')];
assert.equal(garments.length,32);
assert.equal(new Set(garments.map(el=>el.querySelector('mask').id)).size,32);
for(const garment of garments) {
    const clip=garment.querySelector('svg');
    assert.equal(clip.getAttribute('overflow'),'hidden');
    assert.equal(clip.querySelector('mask').style.maskType,'alpha');
    assert.equal(clip.querySelectorAll('image').length,2);
    const sources=[...clip.querySelectorAll('image')];
    assert.equal(sources[0].outerHTML,sources[1].outerHTML);
}
const orderedFortune={recommended_menus:['후라이드치킨','김치찌개'],recommended_meals:[
    {period:'dinner',menu:'후라이드치킨'},{period:'lunch',menu:'김치찌개'}],
    recommended_menu_reason:'오늘 점심에는 칼칼한 김치찌개를, 저녁에는 바삭한 후라이드치킨을 즐겨 보세요.'};
vm.runInContext('currentFortuneData='+JSON.stringify({daily_fortune:orderedFortune})+';renderRecommendedMenu();',dom.getInternalVMContext());
assert.deepEqual([...w.document.querySelectorAll('#menuPhotoCards figcaption')].map(el=>el.textContent),['김치찌개','후라이드치킨']);
assert.deepEqual([...w.document.querySelectorAll('.menu-meal-label')].map(el=>el.textContent),['점심','저녁']);
assert.equal(w.document.getElementById('menuRecommendationComment').textContent,orderedFortune.recommended_menu_reason);
assert.equal(w.document.getElementById('menuRecommendationComment').hidden,false);
vm.runInContext('currentFortuneData={daily_fortune:{recommended_menus:["김치찌개","후라이드치킨"]}};renderRecommendedMenu();',dom.getInternalVMContext());
assert.equal(w.document.querySelectorAll('.menu-meal-label').length,0);
assert.equal(w.document.getElementById('menuRecommendationComment').hidden,true);
assert.equal(w.document.getElementById('bioInterpretationNote'),null);
w.renderOutfitCards(null);
assert.equal(w.document.getElementById('outfitCards').childElementCount,0);
console.log('PASS images match menu names, unknown dishes abstain, outfit colors and item captions, empty state');
console.log('PASS particles, escaping, TPO hard gate, empty/unknown abstention, independent lucky item, stable matching, account-scoped preference, palette');
dom.window.close();
