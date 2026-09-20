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
  #mealSetsDialog{margin:auto;overflow:auto;background:#fff;color:#233b32}
  #mealSetsDialog::backdrop{background:#10251c80}
  .meal-dialog-heading{position:sticky;top:-24px;background:white;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 0;z-index:1}
  .meal-dialog-heading h2{font-size:18px;word-break:keep-all}.meal-dialog-heading button{flex-shrink:0;white-space:nowrap;padding:10px 16px;border:1px solid #b8c7b0;border-radius:10px;background:white;cursor:pointer}
  .meal-title-kcal{display:block;margin-top:3px;font-size:14px;color:#64748b;font-weight:500}
  #mealSetsDialog section{padding-bottom:22px;margin-bottom:22px;border-bottom:1px solid #e4e9e2}
  #mealSetsDialog .menu-photos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:12px 0}
  .food-photo{display:block;width:100%;height:145px;background:#fafbf8}
  @media(max-width:540px){#mealSetsDialog .menu-photos{grid-template-columns:1fr}.food-photo{height:130px}}
  `;document.head.append(style);
  function arrangeCards(){
    const label=$('resMenuLabel'),cell=label?.parentElement;
    const luck=cell?.closest('.card');
    if(cell?.classList.contains('grid-cell')&&luck){
      luck.id='dailyLuckCard';cell.className='card';cell.id='mealDailyCard';luck.before(cell);
      const advice=$('resGaewoon')?.closest('.action-card');if(advice)luck.append(advice);
    }
    document.querySelectorAll('#view-today h4').forEach(h=>{if(h.textContent.trim()==='오늘 뭐 입을까?')h.textContent='오늘 뭐 입지?';});
    if(label)label.textContent='🍲 오늘 뭐 먹을까?';
  }
  arrangeCards();
  const mealCalories=plan=>Math.round(plan.meals.reduce((sum,m)=>sum+Number(m.kcal||0),0));
  function drawMeals(plan,target){
    renderMenuPhotos(plan.meals.map(x=>x.menu),plan.meals.map(x=>labels[x.period]+' 식사'),target);
    plan.meals.forEach((x,i)=>{const card=target.children[i];if(!card)return;
      const caption=card.querySelector('figcaption'),cal=document.createElement('span');cal.className='meal-title-kcal';cal.textContent=`(${Math.round(x.kcal)} kcal)`;caption.append(cal);
      if(x.additions?.length){const extra=document.createElement('small');extra.style.cssText='display:block;padding:0 10px 12px;color:#64748b';extra.textContent=x.additions.map(a=>'+ '+a.menu).join(' · ');card.append(extra);}
    });
  }
  function render(){
    if(!state)return;
    currentMenuMode=state.mode;
    $('resMenuLabel').textContent='🍲 오늘 뭐 먹을까?';
    const tabs=$('menuMode-general').parentElement;
    if(tabs.classList.contains('menu-mode-controls')){tabs.id='menuModeTabs';$('resMenuLabel').after(tabs);tabs.hidden=false;}
    $('resMenu').hidden=state.items.length>0;
    $('resMenu').textContent=state.items.length?'':'오늘의 식단을 준비하고 있어요.';
    drawMeals(state.plan,$('menuPhotoCards'));
    $('menuSnackCard')?.remove();
    $('menuRecommendationComment').hidden=true;$('menuExplorerControls').hidden=false;
    const p=state.plan;
    $('menuStatus').textContent=`하루 합계 ${mealCalories(p)} kcal`;
    for(const mode of ['general','diet']){const b=$('menuMode-'+mode);b.setAttribute('aria-pressed',String(mode===state.mode));b.disabled=busy;}
    const viewingHistory=state.exhausted&&state.date===today();
    $('menuNext').textContent=viewingHistory?'오늘 추천 식단 전체 보기':busy?'새 세트를 준비하고 있어요…':'다른 하루 식단 보기';
    $('menuNext').disabled=!viewingHistory&&(busy||!state.items.length);
    $('menuNext').setAttribute('aria-busy',String(busy&&!viewingHistory));
    $('menuAllSets')?.remove();
    $('menuPlanLike').hidden=true;$('menuModeToggle').hidden=true;$('menuLikeStatus').textContent='';
  }
  function showAll(){
    if(!valid())return;
    let dialog=$('mealSetsDialog');if(!dialog){dialog=document.createElement('dialog');dialog.id='mealSetsDialog';dialog.style.cssText='max-width:800px;width:85%;max-height:85vh;border:1px solid #cbd5c5;border-radius:20px;padding:24px';document.body.append(dialog);}
    dialog.replaceChildren();
    const heading=document.createElement('div');heading.className='meal-dialog-heading';
    const title=document.createElement('h2');title.id='mealSetsTitle';title.textContent=(state.mode==='diet'?'다이어트식':'일반식')+' · 오늘 추천 식단';
    const done=document.createElement('button');done.type='button';done.textContent='닫기';done.onclick=()=>dialog.close();heading.append(title,done);dialog.append(heading);dialog.setAttribute('aria-labelledby',title.id);
    (state.history||[]).forEach((p,i)=>{const section=document.createElement('section'),h=document.createElement('h3');h.textContent=`${i+1}번째 세트`;section.append(h);
      const meals=document.createElement('div');meals.className='menu-photos';section.append(meals);drawMeals(p,meals);
      const total=document.createElement('strong');total.textContent=`하루 합계 ${mealCalories(p)} kcal`;section.append(total);dialog.append(section);
    });
    if(!dialog.open)dialog.showModal();dialog.scrollTop=0;
  }
  function mount(value){generation++;busy=false;owner=currentUserId;state=value;close();$('menuError').textContent='';render();}
  function reset(){generation++;state=null;owner=null;busy=false;close();$('menuExplorerControls').hidden=true;if($('menuModeTabs'))$('menuModeTabs').hidden=true;}
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

