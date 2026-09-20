// One current breakfast/lunch/dinner set per mode; server-owned state.
(() => {
  const $=id=>document.getElementById(id), labels={breakfast:'아침',lunch:'점심',dinner:'저녁'};
  let state=null,owner=null,busy=false,generation=0;
  const today=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  function close(){document.getElementById('mealSetsDialog')?.close();$('menuHistoryModal')?.classList.add('hidden');}
  const style=document.createElement('style');style.textContent=`
  .meal-title-kcal{display:block;margin-top:3px;font-size:14px;color:#64748b;font-weight:500}
  .snack-card{border:1px solid #e4e9e2;border-radius:16px;overflow:hidden;margin:14px 0;background:white}
  .snack-card h3{margin:0;background:#edf3e9;padding:10px 14px;font-size:15px}
  .snack-pictures{display:flex;gap:20px;justify-content:center;padding:18px 12px 8px}
  .snack-component{margin:0;text-align:center;flex:0 1 120px}.snack-component [role=img]{font-size:44px;display:block;line-height:1.4}
  .snack-component figcaption{padding:4px;font-size:13px!important;font-weight:500}
  .snack-total{text-align:center;padding:0 12px 14px;color:#64748b;font-size:14px}
  #mealSetsDialog section{padding-bottom:22px;margin-bottom:22px;border-bottom:1px solid #e4e9e2}
  #mealSetsDialog .menu-photos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:12px 0}
  .food-photo{display:block;width:100%;height:145px;background:#fafbf8}
  @media(max-width:540px){#mealSetsDialog .menu-photos{grid-template-columns:1fr}.food-photo{height:130px}}
  `;document.head.append(style);
  function drawMeals(plan,target){
    renderMenuPhotos(plan.meals.map(x=>x.menu),plan.meals.map(x=>labels[x.period]+' 식사'),target);
    plan.meals.forEach((x,i)=>{const card=target.children[i];if(!card)return;
      const caption=card.querySelector('figcaption'),cal=document.createElement('span');cal.className='meal-title-kcal';cal.textContent=`(${Math.round(x.kcal)} kcal)`;caption.append(cal);
      if(x.additions?.length){const extra=document.createElement('small');extra.style.cssText='display:block;padding:0 10px 12px;color:#64748b';extra.textContent=x.additions.map(a=>'+ '+a.menu).join(' · ');card.append(extra);}
    });
  }
  function drawSnack(snack,target){
    target.replaceChildren();if(!snack||!snack.kcal){target.hidden=true;return;}target.hidden=false;
    const card=document.createElement('div');card.className='snack-card';const h=document.createElement('h3');h.textContent='간식';card.append(h);
    const pictures=document.createElement('div');pictures.className='snack-pictures';
    const icons={'바나나':'🍌','우유':'🥛','호두':'🥣','사과':'🍎','요거트':'🥣'};
    (snack.components||[]).forEach(([name,g])=>{const f=document.createElement('figure');f.className='snack-component';const icon=document.createElement('span');icon.setAttribute('role','img');icon.setAttribute('aria-label',name);icon.textContent=icons[name]||'🍽️';const c=document.createElement('figcaption');c.textContent=`${name} ${g}g`;f.append(icon,c);pictures.append(f);});
    card.append(pictures);const total=document.createElement('div');total.className='snack-total';total.textContent=`(${Math.round(snack.kcal)} kcal)`;card.append(total);target.append(card);
  }
  function render(){
    if(!state)return;
    currentMenuMode=state.mode;
    $('resMenuLabel').textContent=state.mode==='diet'?'🥗 오늘의 다이어트 식단':'🍲 오늘의 일반 식단';
    $('resMenu').hidden=state.items.length>0;
    $('resMenu').textContent=state.items.length?'':'오늘의 식단을 준비하고 있어요.';
    drawMeals(state.plan,$('menuPhotoCards'));
    let snacks=$('menuSnackCard');if(!snacks){snacks=document.createElement('div');snacks.id='menuSnackCard';$('menuPhotoCards').after(snacks);}
    drawSnack(state.plan.snack,snacks);
    $('menuRecommendationComment').hidden=true;$('menuExplorerControls').hidden=false;
    const p=state.plan;
    $('menuStatus').textContent=`하루 합계 ${Math.round(p.total_kcal)} kcal`;
    for(const mode of ['general','diet']){const b=$('menuMode-'+mode);b.setAttribute('aria-pressed',String(mode===state.mode));b.disabled=busy;}
    $('menuNext').textContent=busy?'새 세트를 준비하고 있어요…':'다른 하루 식단 보기';$('menuNext').disabled=busy||!state.items.length||state.exhausted;
    let all=$('menuAllSets');if(!all){all=document.createElement('button');all.id='menuAllSets';all.type='button';all.onclick=showAll;$('menuNext').after(all);}
    all.textContent='오늘 추천 식단 전체 보기';all.disabled=busy;
    $('menuNext').textContent=state.exhausted?'오늘의 5세트를 모두 확인했어요':$('menuNext').textContent;
    $('menuPlanLike').hidden=true;$('menuModeToggle').hidden=true;$('menuLikeStatus').textContent='';
  }
  function showAll(){
    if(!valid())return;
    let dialog=$('mealSetsDialog');if(!dialog){dialog=document.createElement('dialog');dialog.id='mealSetsDialog';dialog.style.cssText='max-width:800px;width:85%;max-height:85vh;border:1px solid #cbd5c5;border-radius:20px;padding:24px';document.body.append(dialog);}
    dialog.replaceChildren();
    const title=document.createElement('h2');title.textContent=(state.mode==='diet'?'다이어트식':'일반식')+' · 오늘 추천 식단';dialog.append(title);
    (state.history||[]).forEach((p,i)=>{const section=document.createElement('section'),h=document.createElement('h3');h.textContent=`${i+1}번째 세트`;section.append(h);
      const meals=document.createElement('div');meals.className='menu-photos';section.append(meals);drawMeals(p,meals);
      const snacks=document.createElement('div');section.append(snacks);drawSnack(p.snack,snacks);
      const total=document.createElement('strong');total.textContent=`하루 합계 ${Math.round(p.total_kcal)} kcal`;section.append(total);dialog.append(section);
    });
    const done=document.createElement('button');done.textContent='닫기';done.onclick=()=>dialog.close();dialog.append(done);dialog.showModal();
  }
  function mount(value){generation++;busy=false;owner=currentUserId;state=value;close();$('menuError').textContent='';render();}
  function reset(){generation++;state=null;owner=null;busy=false;close();$('menuExplorerControls').hidden=true;}
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
  function next(){if(valid()&&!state.exhausted)return request(state.mode,state.date===today()?'next':'open');}
  function resume(){if(document.visibilityState==='visible'&&valid()&&!busy)return request(state.mode,'open');}
  document.addEventListener('visibilitychange',resume);window.addEventListener('pageshow',e=>{if(e.persisted)resume();});
  setInterval(()=>{if(valid()&&state.date!==today())resume();},60000);
  function startSample(){reset();$('resMenu').hidden=false;$('resMenu').textContent='하루 식단 검토 화면에서 확인해 주세요.';}
  window.DalhaMenu={mount,reset,changeMode,next,close,startSample};
})();
