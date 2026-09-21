// Server-owned daily recommendations; local selection revisits revealed sets.
(() => {
  const $=id=>document.getElementById(id), labels={breakfast:'아침',lunch:'점심',dinner:'저녁'};
  let state=null,owner=null,busy=false,generation=0,collection=false,selected={},selectionDay=null;
  const today=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  function close(){collection=false;$('menuCollection')?.remove();$('menuHistoryModal')?.classList.add('hidden');}
  const style=document.createElement('style');style.textContent=`
  #menuNext:disabled{cursor:default}
  #menuNext[aria-busy="true"]{cursor:wait}
  #view-today #mealDailyCard{padding:20px 18px;text-align:left}
  #view-today #mealDailyCard #resMenuLabel{font-size:1.2rem!important;font-weight:800!important;color:var(--ui-ink,#172B3A)!important}
  #view-today #dailyLuckCard .grid-cell:last-child{grid-column:auto;border-top:0;border-left:1px solid var(--ui-line,#E2E8F0);margin-top:0;padding:12px 9px}
  #menuModeTabs{margin:12px 0}#menuModeTabs[hidden]{display:none!important}
  #mealDailyCard [hidden]{display:none!important}
  #menuSetNumber{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 10px}
  .meal-set-nav{display:flex;gap:4px;flex-wrap:wrap}
  .meal-set-nav button{min-height:44px;padding:7px 10px;border:0;border-radius:8px;background:transparent;color:var(--ui-muted,#607482);font:inherit;font-size:13px;cursor:pointer}
  .meal-set-nav button[aria-pressed="true"]{background:var(--ui-tint,#EFF5F1);color:var(--ui-accent,#2D6A4F);font-weight:700}
  .meal-set-count{font-size:12px;color:var(--ui-muted,#607482);white-space:nowrap}
  #mealDailyCard #menuNext{background:#2D6A4F;color:#fff;border:1px solid transparent}
  #mealDailyCard #menuNext:enabled{opacity:1;cursor:pointer}
  #mealDailyCard #menuNext:enabled:hover{filter:brightness(.92)}
  #menuAllSets,.meal-back{min-height:46px;border:1px solid var(--ui-line,#DDE5E8);border-radius:11px;background:var(--ui-surface,#fff);color:var(--ui-ink,#203746);font:inherit;font-size:13px;font-weight:600;cursor:pointer}
  #menuAllSets{width:100%;margin-top:9px}
  #menuComplete{margin:0;padding:14px 0;text-align:center;font-size:13px;color:var(--ui-muted,#607482)}
  .meal-footer{display:flex;justify-content:flex-end;padding-top:12px}
  .meal-back{padding:8px 16px}
  #mealDailyCard button:focus-visible{outline:3px solid #C18624;outline-offset:3px}
  #mealDailyCard .meal-reveal .menu-photo-card{animation:meal-reveal .55s ease both}
  #mealDailyCard .meal-reveal .menu-photo-card:nth-child(2){animation-delay:.06s}
  #mealDailyCard .meal-reveal .menu-photo-card:nth-child(3){animation-delay:.12s}
  @keyframes meal-reveal{from{transform:rotateY(80deg);opacity:.25}to{transform:rotateY(0);opacity:1}}
  @media(prefers-reduced-motion:reduce){#mealDailyCard .meal-reveal .menu-photo-card{animation:none}}
  .meal-set-heading{display:flex;align-items:baseline;justify-content:space-between;gap:8px}
  .meal-set-heading h3{margin:0;font-size:16px;color:var(--ui-ink,#233B4D)}
  .meal-set-heading span{font-size:12px;color:#526473;white-space:nowrap}
  .meal-title-kcal{display:block;margin-top:3px;font-size:14px;color:#64748b;font-weight:500}
  .meal-title-name{display:block;overflow-wrap:anywhere}
  .meal-additions{display:block;padding:0 10px 12px;color:#64748b;overflow-wrap:anywhere}
  #menuCollection section{padding-bottom:18px;margin-bottom:18px;border-bottom:1px solid #e4e9e2}
  #menuCollection section:last-of-type{padding-bottom:0;margin-bottom:0;border-bottom:0}
  #menuCollection .menu-photos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:12px 0}
  .food-photo{display:block;width:100%;height:145px;background:#fafbf8}
  @media(max-width:540px){
    #menuCollection .menu-photos{gap:7px;margin:10px 0 0}
    .food-photo{height:130px}
  }
  @media(max-width:540px){
    #view-today #mealDailyCard{padding:16px 14px;border-radius:16px}
    #mealDailyCard #menuModeTabs{width:fit-content;max-width:100%;padding:0;gap:6px;background:transparent;border:0;margin:12px 0}
    #mealDailyCard #menuModeTabs button{flex:0 1 auto;padding:8px 13px;min-height:44px;font-size:12px;font-weight:600;border:1px solid var(--ui-line,#E4E9EB);background:var(--ui-surface,#FFF);box-shadow:none}
    #mealDailyCard #menuModeTabs button[aria-pressed="true"]{color:var(--ui-accent,#2D6A4F);border-color:var(--ui-accent,#2D6A4F);background:var(--ui-tint,#EFF5F1)}
    #mealDailyCard #menuPhotoCards{grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin-top:0}
    :is(#mealDailyCard,#menuCollection) .menu-photo-card{min-width:0;border-radius:11px}
    :is(#mealDailyCard,#menuCollection) .menu-meal-label{padding:7px 8px 0;font-size:11px;font-weight:600}
    :is(#mealDailyCard,#menuCollection) .food-photo,:is(#mealDailyCard,#menuCollection) .menu-photo-placeholder{height:auto;max-height:none;aspect-ratio:1.1;margin-top:4px}
    :is(#mealDailyCard,#menuCollection) .menu-photo-card figcaption{padding:8px 7px 9px;font-size:13px!important;font-weight:600;line-height:1.4;letter-spacing:-.3px}
    :is(#mealDailyCard,#menuCollection) .meal-title-name{min-height:2.8em;word-break:keep-all;overflow-wrap:anywhere}
    :is(#mealDailyCard,#menuCollection) .meal-title-kcal{font-size:11px;letter-spacing:0;white-space:nowrap}
    :is(#mealDailyCard,#menuCollection) .meal-additions{padding:0 7px 9px;font-size:11px;line-height:1.5;word-break:keep-all}
    #mealDailyCard #menuStatus{margin:11px 1px 10px;font-size:12px}
    #mealDailyCard #menuNext{min-height:44px;padding:11px 8px;font-size:13px;font-weight:600;border-radius:9px;border:1px solid transparent}
  }
  @media(max-width:350px){
    #view-today #mealDailyCard{padding:14px 11px}
    #mealDailyCard #menuPhotoCards{gap:5px}
    :is(#mealDailyCard,#menuCollection) .menu-photo-card figcaption{font-size:12px!important}
  }
  `;document.head.append(style);
  function arrangeCards(){
    const label=$('resMenuLabel'),cell=label?.parentElement;
    const luck=cell?.closest('.card');
    if(cell?.classList.contains('grid-cell')&&luck){
      luck.id='dailyLuckCard';cell.className='card';cell.id='mealDailyCard';luck.before(cell);
      const advice=$('resGaewoon')?.closest('.action-card');if(advice)luck.append(advice);
    }
    document.querySelectorAll('#view-today h4').forEach(h=>{if(h.textContent.trim()==='오늘 뭐 입을까?')h.textContent='오늘 뭐 입지?';});
    if(label)label.textContent='🍲 오늘 뭐 먹지?';
  }
  arrangeCards();
  const mealCalories=plan=>Math.round(plan.meals.reduce((sum,m)=>sum+Number(m.kcal||0),0));
  function drawMeals(plan,target){
    renderMenuPhotos(plan.meals.map(x=>x.menu),plan.meals.map(x=>labels[x.period]),target);
    plan.meals.forEach((x,i)=>{const card=target.children[i];if(!card)return;
      const caption=card.querySelector('figcaption'),cal=document.createElement('span');cal.className='meal-title-kcal';cal.textContent=`${Math.round(x.kcal)} kcal`;
      const name=document.createElement('span');name.className='meal-title-name';name.textContent=x.menu;caption.replaceChildren(name,cal);
      if(x.additions?.length){const extra=document.createElement('small');extra.className='meal-additions';extra.textContent=x.additions.map(a=>'+ '+a.menu).join(' · ');card.append(extra);}
    });
  }
  function history(){
    return (state.history?.length?state.history:[state.plan]).map((p,i)=>({...p,recommendation_number:p.recommendation_number??i+1}))
      .sort((a,b)=>a.recommendation_number-b.recommendation_number).slice(0,state.set_limit||3);
  }
  function render(animate=false){
    if(!state)return;
    if(selectionDay!==state.date){selected={};selectionDay=state.date;}
    currentMenuMode=state.mode;
    const plans=history();
    if(!plans.some(p=>p.recommendation_number===selected[state.mode]))selected[state.mode]=plans.at(-1).recommendation_number;
    const plan=plans.find(p=>p.recommendation_number===selected[state.mode]);
    $('resMenuLabel').textContent='🍲 오늘 뭐 먹지?';
    const tabs=$('menuMode-general').parentElement;
    if(tabs.classList.contains('menu-mode-controls')){tabs.id='menuModeTabs';$('resMenuLabel').after(tabs);tabs.hidden=false;}
    $('resMenu').hidden=state.items.length>0||collection;
    $('resMenu').textContent=state.items.length?'':'오늘의 식단을 준비하고 있어요.';
    let number=$('menuSetNumber');
    if(!number){number=document.createElement('div');number.id='menuSetNumber';$('menuPhotoCards').before(number);}
    number.replaceChildren();number.hidden=collection||!state.items.length;
    const nav=document.createElement('div');nav.className='meal-set-nav';nav.setAttribute('role','group');nav.setAttribute('aria-label','확인한 식단 선택');
    plans.forEach(p=>{const btn=document.createElement('button');btn.type='button';btn.textContent=`식단 ${p.recommendation_number}`;btn.dataset.set=p.recommendation_number;btn.disabled=busy;btn.setAttribute('aria-pressed',String(p===plan));btn.onclick=()=>{selected[state.mode]=p.recommendation_number;render();$('menuSetNumber').querySelector(`[data-set="${p.recommendation_number}"]`).focus({preventScroll:true});};nav.append(btn);});
    const count=document.createElement('span');count.className='meal-set-count';count.textContent=`${plans.length} / ${state.set_limit||3}`;count.setAttribute('aria-label',`총 ${state.set_limit||3}개 중 ${plans.length}개 확인`);number.append(nav,count);
    $('menuPhotoCards').hidden=collection;
    $('menuPhotoCards').classList.toggle('meal-reveal',animate);
    drawMeals(plan,$('menuPhotoCards'));
    $('menuSnackCard')?.remove();
    $('menuRecommendationComment').hidden=true;$('menuExplorerControls').hidden=collection;
    $('menuStatus').textContent=`식단 ${plan.recommendation_number} · 하루 합계 ${mealCalories(plan)} kcal`;
    for(const mode of ['general','diet']){const b=$('menuMode-'+mode);b.setAttribute('aria-pressed',String(mode===state.mode));b.disabled=busy;}
    const complete=state.exhausted&&state.date===today();
    $('menuNext').textContent=busy?'새 식단을 준비하고 있어요…':'식단 추천 더 받기';
    $('menuNext').hidden=complete;
    $('menuNext').disabled=busy||!state.items.length;
    $('menuNext').setAttribute('aria-busy',String(busy));
    let done=$('menuComplete');if(!done){done=document.createElement('p');done.id='menuComplete';done.setAttribute('role','status');$('menuNext').after(done);}
    done.textContent='오늘의 추천 식단을 모두 확인했어요';done.hidden=!complete;
    let all=$('menuAllSets');if(!all){all=document.createElement('button');all.id='menuAllSets';all.type='button';all.textContent='추천 식단 모아보기';all.onclick=showAll;$('menuExplorerControls').append(all);}
    all.disabled=busy||!state.items.length;
    $('menuPlanLike').hidden=true;$('menuModeToggle').hidden=true;$('menuLikeStatus').textContent='';
    $('menuCollection')?.remove();
    if(collection)drawCollection(plans);
  }
  function drawCollection(plans){
    const list=document.createElement('div');list.id='menuCollection';$('menuSetNumber').after(list);
    plans.forEach(p=>{
      const section=document.createElement('section'),row=document.createElement('div'),h=document.createElement('h3');
      row.className='meal-set-heading';h.textContent=`식단 ${p.recommendation_number}`;
      const total=document.createElement('span');total.textContent=`하루 합계 ${mealCalories(p)} kcal`;row.append(h,total);section.append(row);
      const meals=document.createElement('div');meals.className='menu-photos';section.append(meals);drawMeals(p,meals);list.append(section);
    });
    const footer=document.createElement('div');footer.className='meal-footer';
    const back=document.createElement('button');back.type='button';back.className='meal-back';back.textContent='돌아가기';back.onclick=()=>{collection=false;render();$('menuAllSets').focus({preventScroll:true});$('mealDailyCard').scrollIntoView({block:'start'});};footer.append(back);list.append(footer);
  }
  function showAll(){if(!valid()||busy)return;collection=true;render();$('menuCollection').querySelector('.meal-back').focus({preventScroll:true});}
  function mount(value){generation++;busy=false;owner=currentUserId;state=value;selected={};selectionDay=null;close();$('menuError').textContent='';render();}
  function reset(){$('menuSetNumber')?.remove();generation++;state=null;owner=null;busy=false;selected={};selectionDay=null;close();$('menuPhotoCards').hidden=false;$('menuExplorerControls').hidden=true;if($('menuModeTabs'))$('menuModeTabs').hidden=true;}
  function valid(){return state&&owner&&owner===currentUserId;}
  async function request(mode,action){
    if(busy||!valid())return;
    const stamp=generation,account=owner,previousDate=state.date,previousCount=state.mode_counts[mode]||0;let revealed=false;busy=true;$('menuError').textContent='';render();
    try{
      const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);let response,body;
      try{response=await fetch('/api/menu/explore',{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,body:JSON.stringify({user_id:account,token:state.token,mode,action,expected_day:state.date,expected_seen:state.mode_counts[mode]||0})});body=await response.json();}finally{clearTimeout(timer);}
      if(!response.ok)throw Error(typeof body.detail==='string'?body.detail:'식단을 불러오지 못했습니다.');
      if(stamp===generation&&account===currentUserId){revealed=action==='next'&&body.date===previousDate&&body.mode_counts[mode]>previousCount;state=body;if(revealed)selected[mode]=body.plan.recommendation_number;}
    }catch(e){if(stamp===generation&&account===currentUserId)$('menuError').textContent=e.name==='AbortError'?'연결이 지연되고 있습니다. 다시 시도해 주세요.':e.message;}
    finally{if(stamp===generation){busy=false;render(revealed);if(revealed){const focus=$('menuNext').hidden?$('menuSetNumber').querySelector('[aria-pressed="true"]'):$('menuNext');focus?.focus({preventScroll:true});}}}
  }
  function changeMode(mode){if(!busy&&state&&['general','diet'].includes(mode)&&(mode!==state.mode||state.date!==today())){collection=false;return request(mode,'open');}}
  function next(){if(!valid())return;if(state.date!==today())return request(state.mode,'open');if(state.exhausted)return;return request(state.mode,'next');}
  function resume(){if(document.visibilityState==='visible'&&valid()&&!busy)return request(state.mode,'open');}
  document.addEventListener('visibilitychange',resume);window.addEventListener('pageshow',e=>{if(e.persisted)resume();});
  setInterval(()=>{if(valid()&&state.date!==today())resume();},60000);
  function startSample(){reset();$('resMenu').hidden=false;$('resMenu').textContent='하루 식단 검토 화면에서 확인해 주세요.';}
  window.DalhaMenu={mount,reset,changeMode,next,close,startSample};
})();
