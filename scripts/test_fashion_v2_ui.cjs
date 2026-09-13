const {JSDOM}=require('jsdom');
const fs=require('node:fs'), assert=require('node:assert/strict'), vm=require('node:vm');
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{url:'https://dalha.example',runScripts:'outside-only'});
const w=dom.window;
w.scrollTo=()=>{};
for(const s of w.document.querySelectorAll('script:not([src])')) vm.runInContext(s.textContent,dom.getInternalVMContext());

const item=(category,label,color_name,hex,applied_daily_color)=>({category,label,color_name,hex,applied_daily_color});
const daily={id:'female-autumn-casual-daily',gender:'female',season:'autumn',tpo:'casual',look_role:'daily',items:[
  item('outer','블루종','베이지','#C4B294'),
  item('top','긴팔 티셔츠','아이보리','#E8E0CF','A'),
  item('bottom','스트레이트 청바지','데님 블루','#466889','B'),
  item('shoes','레트로 운동화','그레이','#85888D')
]};
const trend={id:'female-autumn-casual-trend',gender:'female',season:'autumn',tpo:'casual',look_role:'trend',items:[
  item('mid','가디건','더스티 핑크','#B67C87','A'),item('top','긴팔 티셔츠','아이보리','#E8E0CF'),
  item('bottom','플리츠 스커트','네이비','#26354A','B'),item('shoes','앵클부츠','블랙','#252629')
]};
const palette={tpo:'casual',gender:'male',style_mood:'casual',mood_desc:'두 가지 코디를 제안드리니 오늘의 옷차림에 참고해 보세요.',top:{name_ko:'페일 레드',hex:'#f48067',standard_color:'레드'},bottom:{name_ko:'딥 네이비',hex:'#051230',standard_color:'네이비'}};
const ownedShoes={id:'shoe-1',category:'신발',nickname:'호카 운동화',materials:['면/린넨/패브릭'],colors:['네이비']};
vm.runInContext('currentUserId="fashion-stage3";currentFortuneData='+JSON.stringify({daily_fortune:{wada_palette:palette,style_palettes:{casual:palette},fashion_v2:{casual:{status:'ui_connected_stage3',looks:[daily,trend]}}}})+';userWardrobeItems='+JSON.stringify([ownedShoes])+';updateTodayWardrobeMatchPick();',dom.getInternalVMContext());

const open=w.document.getElementById('openOutfitModalButton');
assert.equal(open.hidden,false);
assert.equal(w.document.getElementById('outfitCards').childElementCount,0,'large looks must not render inline');
assert.equal(w.document.getElementById('resStyle').textContent,'블루종 · 긴팔 티셔츠 · 스트레이트 청바지 · 레트로 운동화');
assert.equal(w.document.getElementById('drawerWardrobe').hidden,true,'home wardrobe UI stays preserved but hidden');
assert.equal(w.document.getElementById('wardrobeDailyMatchPick').hidden,true,'wardrobe matching guidance is hidden');
assert.equal(w.document.getElementById('paletteMoodStoryBox').hidden,true,'v2 proposal copy moves into the modal');
assert.equal(w.document.querySelectorAll('#dynamicColorPaletteBox .palette-chip').length,2,'palette appears once on main card');

w.openFashionV2Modal();
const modal=w.document.getElementById('fashionV2Modal');
assert.equal(modal.classList.contains('hidden'),false);
assert.equal(w.document.querySelectorAll('#fashionV2Slides .fashion-v2-slide').length,2);
assert.equal(w.document.querySelectorAll('#fashionV2Modal .palette-chip').length,0,'modal must not repeat palette');
assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-board-photo').length,2,'each look renders as one reviewed complete-board image');
assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-proposal').length,2,'proposal copy appears below each swipeable board');
assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-accessory').length,0,'wardrobe accessories do not override the complete look');
assert.ok(!w.document.getElementById('fashionV2Modal').textContent.includes('호카 운동화'));
assert.equal(w.getComputedStyle(w.document.querySelector('#fashionV2Modal .fashion-v2-board-photo')).width,'85%');
assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-look-visual').length,0,'the old equal-tile garment grid is removed');
assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-hero').length,0,'the retired CSS-composited outfit is not rendered');
assert.equal(vm.runInContext('fashionV2Sprite({gender:"female"},{category:"bottom",label:"플리츠 스커트"})',dom.getInternalVMContext()),12,'skirt labels use the skirt silhouette even when legacy sample data omits form');
assert.equal(w.document.querySelectorAll('#fashionV2Modal button[aria-label*="닫기"]').length,0,'no top-right X close control');
assert.equal(w.document.getElementById('fashionV2CloseButton').textContent,'닫기');
assert.match(w.document.getElementById('fashionV2ModalMeta').textContent,/좌우로 넘겨/);

vm.runInContext('currentFortuneData.daily_fortune.weather_outfit={available:true,location:"경주",guidance:"낮에는 반팔이 알맞아요. 저녁에는 얇은 바람막이나 긴팔 셔츠를 챙기세요."};updateTodayWardrobeMatchPick();',dom.getInternalVMContext());
assert.equal(w.document.getElementById('weatherOutfitGuidance').hidden,false);
assert.equal(w.document.getElementById('weatherOutfitGuidance').textContent,'낮에는 반팔이 알맞아요. 저녁에는 얇은 바람막이나 긴팔 셔츠를 챙기세요.');
assert.equal(w.document.getElementById('openOutfitModalButton').hidden,false,'weather copy must not hide reviewed boards');

w.showFashionV2Slide(1,false);
assert.equal(w.document.getElementById('fashionV2TrendTab').getAttribute('aria-selected'),'true');
assert.equal(w.document.getElementById('fashionV2DailyTab').getAttribute('aria-selected'),'false');
w.closeFashionV2Modal();
assert.equal(modal.classList.contains('hidden'),true);

vm.runInContext('currentFortuneData={daily_fortune:{wada_palette:'+JSON.stringify(palette)+',style_palettes:{casual:'+JSON.stringify(palette)+'}}};updateTodayWardrobeMatchPick();',dom.getInternalVMContext());
assert.equal(open.hidden,true,'legacy responses hide the modal entry point');

vm.runInContext('currentFortuneData='+JSON.stringify({daily_fortune:{wada_palette:palette,style_palettes:{casual:palette},fashion_v2:{casual:{looks:[{...daily,id:'unreviewed-daily'},trend]}}}})+';updateTodayWardrobeMatchPick();',dom.getInternalVMContext());
assert.equal(open.hidden,true,'unreviewed scopes never reuse a mismatched board image');

const maleDaily={id:'male-autumn-casual-daily',items:[
  item('outer','필드 점퍼','네이비','#26354A'),item('top','맨투맨','라이트 카멜','#ebd3a2','A'),
  item('bottom','스트레이트 청바지','그레이','#a2b0ad','B'),item('shoes','스웨이드 운동화','다크 브라운','#4B352B')
]};
const maleTrend={id:'male-autumn-casual-trend',items:[
  item('outer','워크 재킷','차콜','#44474D'),item('top','후드 티셔츠','라이트 카멜','#ebd3a2','A'),
  item('bottom','블랙 청바지','그레이','#a2b0ad','B'),item('shoes','가죽 운동화','블랙','#252629')
]};
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(maleDaily)+')',dom.getInternalVMContext()),'/assets/fashion-v2-boards/male-autumn-casual-daily-v1.webp');
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(maleTrend)+')',dom.getInternalVMContext()),'/assets/fashion-v2-boards/male-autumn-casual-trend-v1.webp');

const warmDaily={id:'male-warm-transition-casual-daily',gender:'male',season:'weather_transition',tpo:'casual',look_role:'daily',items:[
  {label:'반팔 폴로',color_name:'라이트 카멜',wear_mode:'worn'},
  {label:'경량 스트레이트 팬츠',color_name:'그레이',wear_mode:'worn'},
  {label:'가죽 운동화',color_name:'다크 브라운',wear_mode:'worn'},
  {label:'얇은 바람막이',color_name:'네이비',wear_mode:'carry'}]};
const warmTrend={id:'male-warm-transition-casual-trend',gender:'male',season:'weather_transition',tpo:'casual',look_role:'trend',items:[
  {label:'반팔 니트',color_name:'라이트 카멜',wear_mode:'worn'},
  {label:'세미와이드 경량 팬츠',color_name:'그레이',wear_mode:'worn'},
  {label:'레트로 가죽 운동화',color_name:'블랙',wear_mode:'worn'},
  {label:'얇은 오버셔츠',color_name:'차콜',wear_mode:'carry'}]};
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(warmDaily)+')',dom.getInternalVMContext()),'/assets/fashion-v2-boards/male-warm-transition-casual-daily-v1.webp');
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(warmTrend)+')',dom.getInternalVMContext()),'/assets/fashion-v2-boards/male-warm-transition-casual-trend-v1.webp');
assert.match(vm.runInContext('fashionV2Summary('+JSON.stringify(warmDaily)+')',dom.getInternalVMContext()),/얇은 바람막이 \(챙길 옷\)/);
console.log('PASS fashion v2 stage 3 summary, bottom sheet, swipe tabs, single palette and legacy fallback');
dom.window.close();
