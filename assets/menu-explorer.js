// One current breakfast/lunch/dinner set per mode; server-owned state.
(() => {
  const $=id=>document.getElementById(id), labels={breakfast:'아침',lunch:'점심',dinner:'저녁'};
  let state=null,owner=null,busy=false,generation=0;
  const today=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  function close(){document.getElementById('mealSetsDialog')?.close();$('menuHistoryModal')?.classList.add('hidden');}
  const style=document.createElement('style');style.textContent=`
  #menuNext:disabled{cursor:default}
  #menuNext[aria-busy="true"]{cursor:wait}
  #view-today #mealDailyCard{padding:20px 18px;text-align:left}
  #view-today #mealDailyCard #resMenuLabel{font-size:1.2rem!important;font-weight:800!important;color:var(--ui-ink,#172B3A)!important}
  #view-today #dailyLuckCard .grid-cell:last-child{grid-column:auto;border-top:0;border-left:1px solid var(--ui-line,#E2E8F0);margin-top:0;padding:12px 9px}
  #menuModeTabs{margin:12px 0}#menuModeTabs[hidden]{display:none!important}
  #mealDailyCard #menuSetNumber{margin:0 0 10px;font-size:14px;font-weight:700;line-height:1.5;color:var(--ui-ink,#172B3A);text-align:left}
  html.meal-history-open{overflow:hidden}
  #mealDailyCard #menuNext{background:#2D6A4F;color:#fff;border:1px solid transparent}
  #mealDailyCard #menuNext[data-action="history"]{background:#233B4D;color:#fff}
  #mealDailyCard #menuNext:enabled{opacity:1;cursor:pointer}
  #mealDailyCard #menuNext:enabled:hover{filter:brightness(.92)}
  #mealDailyCard #menuNext:focus-visible,.meal-dialog-heading button:focus-visible{outline:3px solid #C18624;outline-offset:3px}
  #mealSetsDialog{box-sizing:border-box;width:calc(100% - 48px);max-width:800px;max-height:90vh;max-height:90dvh;margin:auto;padding:0;border:1px solid #D5DFE3;border-radius:20px;overflow:hidden;background:#fff;color:#233B4D}
  #mealSetsDialog[open]{display:flex;flex-direction:column}
  #mealSetsDialog::backdrop{background:#10251c80}
  .meal-dialog-heading{flex-shrink:0;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:18px 24px;border-bottom:1px solid #E4E9EB;background:#fff}
  .meal-dialog-heading h2{margin:0;font-size:18px;word-break:keep-all}
  .meal-dialog-heading button{flex-shrink:0;min-height:44px;white-space:nowrap;padding:10px 16px;border:1px solid #b8c7b0;border-radius:10px;background:white;color:#233B4D;font:inherit;font-size:14px;cursor:pointer}
  .meal-dialog-list{min-height:0;overflow:auto;overscroll-behavior:contain;padding:20px 24px}
  .meal-set-heading{display:flex;align-items:baseline;justify-content:space-between;gap:8px}
  .meal-set-heading h3{margin:0;font-size:16px;color:#233B4D}
  .meal-set-heading span{font-size:12px;color:#526473;white-space:nowrap}
  .meal-title-kcal{display:block;margin-top:3px;font-size:14px;color:#64748b;font-weight:500}
  .meal-title-name{display:block;overflow-wrap:anywhere}
  .meal-additions{display:block;padding:0 10px 12px;color:#64748b;overflow-wrap:anywhere}
  #mealSetsDialog section{padding-bottom:18px;margin-bottom:18px;border-bottom:1px solid #e4e9e2}
  #mealSetsDialog section:last-child{padding-bottom:0;margin-bottom:0;border-bottom:0}
  #mealSetsDialog .menu-photos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:12px 0}
  .food-photo{display:block;width:100%;height:145px;background:#fafbf8}
  @media(max-width:540px){
    #mealSetsDialog{width:100%;max-width:none;height:100vh;height:100dvh;max-height:none;margin:0;border:0;border-radius:0}
    .meal-dialog-heading{padding:calc(12px + env(safe-area-inset-top)) max(14px,env(safe-area-inset-right)) 12px max(14px,env(safe-area-inset-left))}
    .meal-dialog-heading h2{font-size:16px}
    .meal-dialog-list{padding:16px max(14px,env(safe-area-inset-right)) calc(20px + env(safe-area-inset-bottom)) max(14px,env(safe-area-inset-left))}
    #mealSetsDialog .menu-photos{gap:7px;margin:10px 0 0}
    .food-photo{height:130px}
  }
  @media(max-width:540px){
    #view-today #mealDailyCard{padding:16px 14px;border-radius:16px}
    #mealDailyCard #menuModeTabs{width:fit-content;max-width:100%;padding:0;gap:6px;background:transparent;border:0;margin:12px 0}
    #mealDailyCard #menuModeTabs button{flex:0 1 auto;padding:8px 13px;min-height:44px;font-size:12px;font-weight:600;border:1px solid var(--ui-line,#E4E9EB);background:var(--ui-surface,#FFF);box-shadow:none}
    #mealDailyCard #menuModeTabs button[aria-pressed="true"]{color:var(--ui-accent,#2D6A4F);border-color:var(--ui-accent,#2D6A4F);background:var(--ui-tint,#EFF5F1)}
    #mealDailyCard #menuPhotoCards{grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin-top:0}
    :is(#mealDailyCard,#mealSetsDialog) .menu-photo-card{min-width:0;border-radius:11px}
    :is(#mealDailyCard,#mealSetsDialog) .menu-meal-label{padding:7px 8px 0;font-size:11px;font-weight:600}
    :is(#mealDailyCard,#mealSetsDialog) .food-photo,:is(#mealDailyCard,#mealSetsDialog) .menu-photo-placeholder{height:auto;max-height:none;aspect-ratio:1.1;margin-top:4px}
    :is(#mealDailyCard,#mealSetsDialog) .menu-photo-card figcaption{padding:8px 7px 9px;font-size:13px!important;font-weight:600;line-height:1.4;letter-spacing:-.3px}
    :is(#mealDailyCard,#mealSetsDialog) .meal-title-name{min-height:2.8em;word-break:keep-all;overflow-wrap:anywhere}
    :is(#mealDailyCard,#mealSetsDialog) .meal-title-kcal{font-size:11px;letter-spacing:0;white-space:nowrap}
    :is(#mealDailyCard,#mealSetsDialog) .meal-additions{padding:0 7px 9px;font-size:11px;line-height:1.5;word-break:keep-all}
    #mealDailyCard #menuStatus{margin:11px 1px 10px;font-size:12px}
    #mealDailyCard #menuNext{min-height:44px;padding:11px 8px;font-size:13px;font-weight:600;border-radius:9px;border:1px solid transparent}
  }
  @media(max-width:350px){
    #view-today #mealDailyCard{padding:14px 11px}
    #mealDailyCard #menuPhotoCards{gap:5px}
    :is(#mealDailyCard,#mealSetsDialog) .menu-photo-card figcaption{font-size:12px!important}
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
  function render(){
    if(!state)return;
    currentMenuMode=state.mode;
    $('resMenuLabel').textContent='🍲 오늘 뭐 먹지?';
    const tabs=$('menuMode-general').parentElement;
    if(tabs.classList.contains('menu-mode-controls')){tabs.id='menuModeTabs';$('resMenuLabel').after(tabs);tabs.hidden=false;}
    $('resMenu').hidden=state.items.length>0;
    $('resMenu').textContent=state.items.length?'':'오늘의 식단을 준비하고 있어요.';
    let number=$('menuSetNumber');
    if(!number){number=document.createElement('p');number.id='menuSetNumber';number.setAttribute('aria-live','polite');$('menuPhotoCards').before(number);}
    number.textContent=`추천 ${state.plan.recommendation_number??state.seen_sets??1}`;
    number.hidden=!state.items.length;
    drawMeals(state.plan,$('menuPhotoCards'));
    $('menuSnackCard')?.remove();
    $('menuRecommendationComment').hidden=true;$('menuExplorerControls').hidden=false;
    const p=state.plan;
    $('menuStatus').textContent=`하루 합계 ${mealCalories(p)} kcal`;
    for(const mode of ['general','diet']){const b=$('menuMode-'+mode);b.setAttribute('aria-pressed',String(mode===state.mode));b.disabled=busy;}
    const viewingHistory=state.exhausted&&state.date===today();
    $('menuNext').textContent=viewingHistory?'전체 추천 식단 다시보기':busy?'새 세트를 준비하고 있어요…':'다른 추천 식단 보기';
    $('menuNext').dataset.action=viewingHistory?'history':'next';
    $('menuNext').disabled=!viewingHistory&&(busy||!state.items.length);
    $('menuNext').setAttribute('aria-busy',String(busy&&!viewingHistory));
    $('menuAllSets')?.remove();
    $('menuPlanLike').hidden=true;$('menuModeToggle').hidden=true;$('menuLikeStatus').textContent='';
  }
  function showAll(){
    if(!valid())return;
    let dialog=$('mealSetsDialog');
    if(!dialog){
      dialog=document.createElement('dialog');dialog.id='mealSetsDialog';
      dialog.addEventListener('close',()=>{if(!dialog.open)document.documentElement.classList.remove('meal-history-open');});
      document.body.append(dialog);
    }
    dialog.replaceChildren();
    const heading=document.createElement('div');heading.className='meal-dialog-heading';
    const title=document.createElement('h2');title.id='mealSetsTitle';title.textContent=(state.mode==='diet'?'다이어트식':'일반식')+' · 오늘 추천 식단';
    const done=document.createElement('button');done.type='button';done.textContent='닫기';done.autofocus=true;done.onclick=()=>dialog.close();heading.append(title,done);dialog.append(heading);dialog.setAttribute('aria-labelledby',title.id);
    const list=document.createElement('div');list.className='meal-dialog-list';dialog.append(list);
    const history=(state.history||[]).map((p,i)=>({...p,recommendation_number:p.recommendation_number??i+1}))
      .sort((a,b)=>a.recommendation_number-b.recommendation_number).slice(0,state.set_limit||3);
    history.forEach(p=>{
      const section=document.createElement('section'),row=document.createElement('div'),h=document.createElement('h3');
      row.className='meal-set-heading';h.textContent=`추천 ${p.recommendation_number}`;
      const total=document.createElement('span');total.textContent=`하루 합계 ${mealCalories(p)} kcal`;row.append(h,total);section.append(row);
      const meals=document.createElement('div');meals.className='menu-photos';section.append(meals);drawMeals(p,meals);list.append(section);
    });
    if(!dialog.open)dialog.showModal();
    document.documentElement.classList.add('meal-history-open');list.scrollTop=0;
  }
  function mount(value){generation++;busy=false;owner=currentUserId;state=value;close();$('menuError').textContent='';render();}
  function reset(){$('menuSetNumber')?.remove();generation++;state=null;owner=null;busy=false;close();$('menuExplorerControls').hidden=true;if($('menuModeTabs'))$('menuModeTabs').hidden=true;}
  function valid(){return state&&owner&&owner===currentUserId;}
  async function request(mode,action){
    if(busy||!valid())return;
    const stamp=generation,account=owner;busy=true;$('menuError').textContent='';render();
    try{
      const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);let response,body;
      try{response=await fetch('/api/menu/explore',{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,body:JSON.stringify({user_id:account,token:state.token,mode,action,expected_day:state.date,expected_seen:state.mode_counts[mode]||0})});body=await response.json();}finally{clearTimeout(timer);}
      if(!response.ok)throw Error(typeof body.detail==='string'?body.detail:'식단을 불러오지 못했습니다.');
      if(stamp===generation&&account===currentUserId)state=body;
    }catch(e){if(stamp===generation&&account===currentUserId)$('menuError').textContent=e.name==='AbortError'?'연결이 지연되고 있습니다. 다시 시도해 주세요.':e.message;}
    finally{if(stamp===generation){busy=false;render();}}
  }
  function changeMode(mode){if(state&&['general','diet'].includes(mode)&&(mode!==state.mode||state.date!==today()))return request(mode,'open');}
  function next(){if(!valid())return;if(state.date!==today())return request(state.mode,'open');if(state.exhausted)return showAll();return request(state.mode,'next');}
  function resume(){if(document.visibilityState==='visible'&&valid()&&!busy)return request(state.mode,'open');}
  document.addEventListener('visibilitychange',resume);window.addEventListener('pageshow',e=>{if(e.persisted)resume();});
  setInterval(()=>{if(valid()&&state.date!==today())resume();},60000);
  function startSample(){reset();$('resMenu').hidden=false;$('resMenu').textContent='하루 식단 검토 화면에서 확인해 주세요.';}
  window.DalhaMenu={mount,reset,changeMode,next,close,startSample};
})();
