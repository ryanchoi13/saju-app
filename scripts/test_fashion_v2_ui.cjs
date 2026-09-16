const {JSDOM}=require('jsdom');
const fs=require('node:fs'), assert=require('node:assert/strict'), vm=require('node:vm');
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{url:'https://dalha.example',runScripts:'outside-only'});
const w=dom.window;
w.scrollTo=()=>{};
for(const s of w.document.querySelectorAll('script:not([src])')) vm.runInContext(s.textContent,dom.getInternalVMContext());

const item=(category,label,color_name,hex,applied_daily_color)=>({category,label,color_name,hex,applied_daily_color});
const daily={id:'female-autumn-casual-daily',gender:'female',season:'autumn',tpo:'casual',look_role:'daily',board_image:'/assets/fashion-v2-boards/sample-v5-female-thirties-warm-casual-daily.webp',items:[
  item('outer','블루종','베이지','#C4B294'),
  item('top','긴팔 티셔츠','아이보리','#E8E0CF','A'),
  item('bottom','스트레이트 청바지','데님 블루','#466889','B'),
  item('shoes','레트로 운동화','그레이','#85888D')
]};
const trend={id:'female-autumn-casual-trend',gender:'female',season:'autumn',tpo:'casual',look_role:'trend',board_image:'/assets/fashion-v2-boards/sample-v10-female-thirties-warm-casual-trend.webp',items:[
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
assert.equal(w.document.getElementById('weatherOutfitGuidance').parentElement,w.document.getElementById('resStyle').parentElement,'weather clothing advice belongs to the recommended-look section');

w.openFashionV2Modal();
const modal=w.document.getElementById('fashionV2Modal');
assert.equal(modal.classList.contains('hidden'),false);
assert.equal(w.document.getElementById('fashionV2TrendTab').textContent,'추천 2');
assert.equal(w.document.querySelectorAll('#fashionV2Slides .fashion-v2-slide').length,2);
assert.equal(w.document.querySelectorAll('#fashionV2Modal .palette-chip').length,0,'modal must not repeat palette');
assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-board-photo').length,2,'each look renders as one reviewed complete-board image');
assert.equal(w.document.querySelector('#fashionV2DailySlide .fashion-v2-look-summary').textContent,'베이지 색상의 블루종과 아이보리 색상의 긴팔 티셔츠, 데님 블루 색상의 스트레이트 청바지, 그레이 색상의 레트로 운동화를 매치해 보세요.');
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
assert.equal(w.document.querySelector('#fashionV2TrendSlide h4').textContent,'추천 2');
assert.equal(w.document.getElementById('fashionV2DailyTab').getAttribute('aria-selected'),'false');
w.closeFashionV2Modal();
assert.equal(modal.classList.contains('hidden'),true);

vm.runInContext('currentFortuneData={daily_fortune:{wada_palette:'+JSON.stringify(palette)+',style_palettes:{casual:'+JSON.stringify(palette)+'}}};updateTodayWardrobeMatchPick();',dom.getInternalVMContext());
assert.equal(open.hidden,true,'legacy responses hide the modal entry point');

vm.runInContext('currentFortuneData='+JSON.stringify({daily_fortune:{wada_palette:palette,style_palettes:{casual:palette},fashion_v2:{casual:{looks:[{...daily,id:'unreviewed-daily',board_image:''},trend]}}}})+';updateTodayWardrobeMatchPick();',dom.getInternalVMContext());
assert.equal(open.hidden,true,'unreviewed scopes never reuse a mismatched board image');

const maleDaily={id:'male-autumn-casual-daily',items:[
  item('outer','필드 점퍼','네이비','#26354A'),item('top','맨투맨','라이트 카멜','#ebd3a2','A'),
  item('bottom','스트레이트 청바지','그레이','#a2b0ad','B'),item('shoes','스웨이드 운동화','다크 브라운','#4B352B')
]};
const maleTrend={id:'male-autumn-casual-trend',items:[
  item('outer','워크 재킷','차콜','#44474D'),item('top','후드 티셔츠','라이트 카멜','#ebd3a2','A'),
  item('bottom','블랙 청바지','그레이','#a2b0ad','B'),item('shoes','가죽 운동화','블랙','#252629')
]};
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(maleDaily)+')',dom.getInternalVMContext()),'','legacy right-side item-rail boards are retired');
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(maleTrend)+')',dom.getInternalVMContext()),'','legacy right-side item-rail boards are retired');

const publishedBoard={...maleDaily,board_image:'/assets/fashion-v2-boards/sample-v11-male-fifty-cool-business-formal-daily.webp'};
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(publishedBoard)+')',dom.getInternalVMContext()),publishedBoard.board_image,'backend-published reviewed boards take priority');
assert.equal(vm.runInContext('fashionV2BoardImage({...'+JSON.stringify(maleDaily)+',board_image:"https://example.com/untrusted.webp"})',dom.getInternalVMContext()),'','external board paths are rejected');

const todayRecoloredDaily={...maleDaily,board_image:'/assets/fashion-v2-boards/sample-v5-male-thirties-warm-casual-daily.webp',items:[
  item('outer','필드 점퍼','레드','#A33A32'),item('top','맨투맨','오프화이트','#F2EEE6'),
  item('bottom','스트레이트 청바지','진청','#26354A'),item('shoes','스웨이드 운동화','다크 브라운','#4B352B')
]};
const todayRecoloredTrend={...maleTrend,board_image:'/assets/fashion-v2-boards/sample-v9-male-thirties-warm-casual-trend.webp',items:[
  item('outer','워크 재킷','레드','#A33A32'),item('top','후드 티셔츠','오프화이트','#F2EEE6'),
  item('bottom','블랙 청바지','블랙','#252629'),item('shoes','가죽 운동화','블랙','#252629')
]};
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(todayRecoloredDaily)+')',dom.getInternalVMContext()),todayRecoloredDaily.board_image);
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(todayRecoloredTrend)+')',dom.getInternalVMContext()),todayRecoloredTrend.board_image);
vm.runInContext('currentFortuneData='+JSON.stringify({daily_fortune:{wada_palette:palette,style_palettes:{casual:palette},fashion_v2:{casual:{looks:[todayRecoloredDaily,todayRecoloredTrend]}}}})+';updateTodayWardrobeMatchPick();',dom.getInternalVMContext());
assert.equal(open.hidden,false,'today button stays visible when exact-color reviewed boards exist');
w.openFashionV2Modal();
assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-board-photo').length,2);
assert.match(w.document.getElementById('fashionV2ModalMeta').textContent,/좌우로 넘겨/);
w.closeFashionV2Modal();

const todayBusinessCasualDaily={id:'male-autumn-business_casual-daily',board_image:'/assets/fashion-v2-boards/sample-v7-male-forties-mild-business-casual-daily.webp',items:[
  item('outer','블레이저','버건디','#7F2638'),item('top','크루넥 니트','오프화이트','#ffffff'),
  item('bottom','슬랙스','그레이','#85888D'),item('shoes','로퍼','다크 브라운','#4B352B')]};
const todayBusinessCasualTrend={id:'male-autumn-business_casual-trend',board_image:'/assets/fashion-v2-boards/sample-v7-male-forties-mild-business-casual-trend.webp',items:[
  item('outer','필드 재킷','버건디','#7F2638'),item('top','옥스퍼드 셔츠','오프화이트','#ffffff'),
  item('bottom','단정한 면바지','네이비','#26354A'),item('shoes','더비 구두','블랙','#252629')]};
const todayBusinessFormalDaily={id:'male-autumn-business_formal-daily',board_image:'/assets/fashion-v2-boards/sample-v9-male-thirties-cool-business-formal-daily.webp',items:[
  item('outer','수트 재킷','네이비','#26354A'),item('top','드레스 셔츠','오프화이트','#ffffff'),
  item('bottom','수트 바지','네이비','#26354A'),item('tie','레지멘탈 타이','레드','#d46d7a'),item('shoes','옥스퍼드 구두','블랙','#252629')]};
const todayBusinessFormalTrend={id:'male-autumn-business_formal-trend',board_image:'/assets/fashion-v2-boards/male-autumn-business-formal-trend-single-v2.webp',items:[
  item('outer','수트 재킷','차콜','#44474D'),item('top','드레스 셔츠','오프화이트','#ffffff'),
  item('bottom','수트 바지','차콜','#44474D'),item('tie','솔리드 타이','레드','#d46d7a'),item('shoes','더비 구두','다크 브라운','#4B352B')]};
for (const look of [todayBusinessCasualDaily,todayBusinessCasualTrend,todayBusinessFormalDaily,todayBusinessFormalTrend]) {
  assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(look)+')',dom.getInternalVMContext()),look.board_image);
  assert.ok(fs.statSync('.'+look.board_image).size>20000,look.board_image+' must be a real reviewed board image');
}

const warmDaily={id:'male-warm-transition-casual-daily',gender:'male',season:'weather_transition',tpo:'casual',look_role:'daily',board_image:'/assets/fashion-v2-boards/sample-v5-male-thirties-warm-casual-daily.webp',items:[
  {label:'반팔 폴로',color_name:'라이트 카멜',wear_mode:'worn'},
  {label:'경량 스트레이트 팬츠',color_name:'그레이',wear_mode:'worn'},
  {label:'가죽 운동화',color_name:'다크 브라운',wear_mode:'worn'},
  {label:'얇은 바람막이',color_name:'네이비',wear_mode:'carry'}]};
const warmTrend={id:'male-warm-transition-casual-trend',gender:'male',season:'weather_transition',tpo:'casual',look_role:'trend',board_image:'/assets/fashion-v2-boards/sample-v9-male-thirties-warm-casual-trend.webp',items:[
  {label:'반팔 니트',color_name:'라이트 카멜',wear_mode:'worn'},
  {label:'세미와이드 경량 팬츠',color_name:'그레이',wear_mode:'worn'},
  {label:'레트로 가죽 운동화',color_name:'블랙',wear_mode:'worn'},
  {label:'얇은 오버셔츠',color_name:'차콜',wear_mode:'carry'}]};
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(warmDaily)+')',dom.getInternalVMContext()),warmDaily.board_image);
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(warmTrend)+')',dom.getInternalVMContext()),warmTrend.board_image);
assert.match(vm.runInContext('fashionV2Summary('+JSON.stringify(warmDaily)+')',dom.getInternalVMContext()),/얇은 바람막이 \(챙길 옷\)/);
assert.equal(vm.runInContext('fashionV2Narrative('+JSON.stringify(warmDaily)+')',dom.getInternalVMContext()),'라이트 카멜 색상의 반팔 폴로와 그레이 색상의 경량 스트레이트 팬츠, 다크 브라운 색상의 가죽 운동화를 매치해 보세요. 아침저녁에는 쌀쌀할 수 있으니 네이비 색상의 얇은 바람막이를 챙기면 좋습니다.');

const businessCasualDaily={id:'male-warm-transition-business_casual-daily',board_image:'/assets/fashion-v2-boards/sample-v7-male-forties-mild-business-casual-daily.webp',items:[
  item('top','반팔 클래식 셔츠','라이트 카멜','#ebd3a2'),item('bottom','서머 슬랙스','그레이','#a2b0ad'),
  item('shoes','로퍼','다크 브라운','#4B352B'),{category:'carry_outer',label:'경량 해링턴 재킷',color_name:'베이지',hex:'#C4B294',wear_mode:'carry'}]};
const businessCasualTrend={id:'male-warm-transition-business_casual-trend',board_image:'/assets/fashion-v2-boards/sample-v7-male-forties-mild-business-casual-trend.webp',items:[
  item('top','니트 폴로','라이트 카멜','#ebd3a2'),item('bottom','원턱 서머 슬랙스','그레이','#a2b0ad'),
  item('shoes','미니멀 가죽 운동화','블랙','#252629'),{category:'carry_outer',label:'얇은 언스트럭처드 재킷',color_name:'네이비',hex:'#26354A',wear_mode:'carry'}]};
const businessFormalDaily={id:'male-summer-business_formal-daily',board_image:'/assets/fashion-v2-boards/sample-v9-male-thirties-cool-business-formal-daily.webp',items:[
  item('outer','수트 재킷','그레이','#85888D'),item('top','드레스 셔츠','화이트','#F5F4EF'),
  item('bottom','수트 바지','그레이','#85888D'),item('tie','솔리드 타이','라이트 카멜','#ebd3a2'),item('shoes','옥스퍼드 구두','블랙','#252629')]};
const businessFormalTrend={id:'male-summer-business_formal-trend',board_image:'/assets/fashion-v2-boards/male-autumn-business-formal-trend-single-v2.webp',items:[
  item('outer','수트 재킷','그레이','#85888D'),item('top','드레스 셔츠','라이트 블루','#A9C5D8'),
  item('bottom','수트 바지','그레이','#85888D'),item('tie','레지멘탈 타이','라이트 카멜','#ebd3a2'),item('shoes','더비 구두','블랙','#252629')]};
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(businessCasualDaily)+')',dom.getInternalVMContext()),businessCasualDaily.board_image);
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(businessCasualTrend)+')',dom.getInternalVMContext()),businessCasualTrend.board_image);
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(businessFormalDaily)+')',dom.getInternalVMContext()),businessFormalDaily.board_image);
assert.equal(vm.runInContext('fashionV2BoardImage('+JSON.stringify(businessFormalTrend)+')',dom.getInternalVMContext()),businessFormalTrend.board_image);
for(const board of [businessCasualDaily,businessCasualTrend,businessFormalDaily,businessFormalTrend]) {
  const src=vm.runInContext('fashionV2BoardImage('+JSON.stringify(board)+')',dom.getInternalVMContext());
  assert.ok(fs.existsSync('.'+src),`reviewed board asset must exist: ${src}`);
  assert.ok(fs.statSync('.'+src).size>20000,`reviewed board asset must not be an empty placeholder: ${src}`);
}

const businessCasualPalette={...palette,tpo:'business_casual'};
const businessFormalPalette={...palette,tpo:'business_formal'};
vm.runInContext('currentFortuneData='+JSON.stringify({daily_fortune:{wada_palette:palette,style_palettes:{casual:palette,business_casual:businessCasualPalette,business_formal:businessFormalPalette},fashion_v2:{business_casual:{looks:[businessCasualDaily,businessCasualTrend]},business_formal:{looks:[businessFormalDaily,businessFormalTrend]}}}})+';',dom.getInternalVMContext());
w.setStyleTpo('business_casual');
assert.equal(open.hidden,false,'business casual shows the outfit button when both reviewed boards exist');
w.openFashionV2Modal();
assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-board-photo').length,2);
w.closeFashionV2Modal();
w.setStyleTpo('business_formal');
assert.equal(open.hidden,false,'business formal shows the outfit button when both reviewed boards exist');
w.openFashionV2Modal();
assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-board-photo').length,2);
w.closeFashionV2Modal();

const femaleCasualDaily={id:'female-warm-transition-casual-daily',gender:'female',board_image:'/assets/fashion-v2-boards/sample-v10-female-fifty-warm-casual-daily.webp',items:[
  item('top','반팔 티셔츠','라이트 카멜','#ebd3a2'),item('bottom','경량 스트레이트 팬츠','그레이','#a2b0ad'),
  item('shoes','가죽 운동화','그레이','#a2b0ad'),{category:'carry_outer',label:'얇은 바람막이',color_name:'베이지',wear_mode:'carry'}]};
const femaleCasualTrend={id:'female-warm-transition-casual-trend',gender:'female',board_image:'/assets/fashion-v2-boards/sample-v10-female-fifty-warm-casual-trend.webp',items:[
  item('top','반팔 파인 니트','라이트 카멜','#ebd3a2'),item('bottom','라이트 플리츠 스커트','그레이','#a2b0ad'),
  item('shoes','메리제인 플랫','블랙','#252629'),{category:'carry_outer',label:'얇은 크롭 셔츠',color_name:'아이보리',wear_mode:'carry'}]};
const femaleBusinessCasualDaily={id:'female-warm-transition-business_casual-daily',gender:'female',board_image:'/assets/fashion-v2-boards/sample-v7-male-forties-mild-business-casual-daily.webp',items:[
  item('top','반팔 니트','라이트 카멜','#ebd3a2'),item('bottom','서머 슬랙스','그레이','#a2b0ad'),
  item('shoes','로퍼','다크 브라운','#4B352B'),{category:'carry_outer',label:'얇은 칼라리스 재킷',color_name:'베이지',wear_mode:'carry'}]};
const femaleBusinessCasualTrend={id:'female-warm-transition-business_casual-trend',gender:'female',board_image:'/assets/fashion-v2-boards/sample-v10-female-fifty-warm-business-casual-trend.webp',items:[
  item('top','반팔 블라우스','라이트 카멜','#ebd3a2'),item('bottom','라이트 미디 스커트','그레이','#a2b0ad'),
  item('shoes','슬링백 플랫','블랙','#252629'),{category:'carry_outer',label:'얇은 셔츠 재킷',color_name:'더스티 블루',wear_mode:'carry'}]};
const femaleFormalDaily={id:'female-summer-business_formal-daily',gender:'female',board_image:'/assets/fashion-v2-boards/sample-v10-female-fifty-cool-business-formal-trend.webp',items:[
  item('outer','수트 재킷','그레이','#a2b0ad'),item('top','블라우스','라이트 카멜','#ebd3a2'),
  item('bottom','수트 바지','그레이','#a2b0ad'),item('shoes','펌프스','블랙','#252629')]};
const femaleFormalTrend={id:'female-summer-business_formal-trend',gender:'female',board_image:'/assets/fashion-v2-boards/sample-v10-female-fifty-cool-business-formal-trend.webp',items:[
  item('outer','경량 재킷','머스터드','#C89B3C'),item('dress','반팔 정장 원피스','그레이','#a2b0ad'),item('shoes','플랫','블랙','#252629')]};

const femaleContexts={
  casual:{looks:[femaleCasualDaily,femaleCasualTrend]},
  business_casual:{looks:[femaleBusinessCasualDaily,femaleBusinessCasualTrend]},
  business_formal:{looks:[femaleFormalDaily,femaleFormalTrend]}
};
for(const context of Object.values(femaleContexts)) for(const board of context.looks) {
  const src=vm.runInContext('fashionV2BoardImage('+JSON.stringify(board)+')',dom.getInternalVMContext());
  assert.ok(src.startsWith('/assets/fashion-v2-boards/'),`reviewed board path is required: ${board.id}`);
  assert.ok(fs.existsSync('.'+src),`female reviewed board asset must exist: ${src}`);
  assert.ok(fs.statSync('.'+src).size>20000,`female reviewed board asset must not be an empty placeholder: ${src}`);
}
vm.runInContext('currentFortuneData='+JSON.stringify({daily_fortune:{wada_palette:palette,style_palettes:{casual:palette,business_casual:businessCasualPalette,business_formal:businessFormalPalette},fashion_v2:femaleContexts}})+';',dom.getInternalVMContext());
for(const tpo of ['casual','business_casual','business_formal']) {
  w.setStyleTpo(tpo);
  assert.equal(open.hidden,false,`female ${tpo} shows the outfit button when both reviewed boards exist`);
  w.openFashionV2Modal();
  assert.equal(w.document.querySelectorAll('#fashionV2Modal .fashion-v2-board-photo').length,2);
  w.closeFashionV2Modal();
}

console.log('PASS fashion v2 stage 3 summary, published single-outfit boards, bottom sheet, swipe tabs and single palette');
dom.window.close();
