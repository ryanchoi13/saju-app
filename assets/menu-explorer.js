// Daily ranked choices. The server owns quotas and history; likes are deferred.
(() => {
  const $ = id => document.getElementById(id);
  let state=null, owner=null, busy=false, generation=0, sample=null;
  const today=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  function close() { $('menuHistoryModal').classList.add('hidden'); }
  function render() {
    if (!state) return;
    currentMenuMode=state.mode;
    $('resMenuLabel').textContent=state.mode==='diet'?'🥗 오늘의 다이어트 메뉴':'🍲 오늘의 추천 메뉴';
    $('resMenu').hidden=state.items.length>0;
    $('resMenu').textContent=state.items.length?'':'오늘 추천할 메뉴를 준비하고 있어요.';
    renderMenuPhotos(state.items.map(x=>x.menu),state.items.map(x=>`${x.rank}순위`));
    $('menuRecommendationComment').textContent=state.basis_text;
    $('menuRecommendationComment').hidden=false;
    $('menuExplorerControls').hidden=false;
    $('menuStatus').textContent=`오늘 ${state.seen_sets}/${state.set_limit}세트 확인`;
    for (const mode of ['general','diet']) {
      const button=$(`menuMode-${mode}`);
      button.setAttribute('aria-pressed',String(mode===state.mode)); button.disabled=busy;
    }
    const next=$('menuNext');
    next.textContent=busy?'추천 기록을 불러오는 중…':state.exhausted?'오늘 추천받은 메뉴 보기':'다른 메뉴 추천';
    next.disabled=busy || !state.items.length;
    $('menuPlanLike').hidden=true; $('menuModeToggle').hidden=true;
    $('menuLikeStatus').textContent='';
  }
  function mount(value) {
    generation++; busy=false; owner=currentUserId; state=value; sample=null; close();
    $('menuError').textContent=''; render();
  }
  function reset() {
    generation++; state=null; owner=null; busy=false; sample=null; close();
    $('menuExplorerControls').hidden=true;
  }
  function validOwner() { return state && (sample || (owner && owner===currentUserId)); }
  function showHistory() {
    if (!validOwner()) return;
    $('menuHistoryTitle').textContent=state.mode==='diet'?'오늘 추천받은 다이어트 메뉴':'오늘 추천받은 메뉴';
    $('menuHistorySummary').textContent=`${state.date} · ${state.history.length}개 · 추천 순서`;
    renderMenuPhotos(state.history.map(x=>x.menu),state.history.map(x=>`${x.rank}순위`),$('menuHistoryCards'));
    $('menuHistoryModal').classList.remove('hidden');
  }
  function sampleRequest(mode,action) {
    const count=sample.counts[mode],limit=sample.rankings[mode].length/2;
    sample.counts[mode]=count===0?1:Math.min(limit,count+(action==='next'?1:0));
    const seen=sample.counts[mode],display=action==='next'?seen:1;
    const history=sample.rankings[mode].slice(0,seen*2);
    return {date:today(),token:'sample',mode,seen_sets:seen,set_limit:limit,
      mode_counts:{...sample.counts},exhausted:seen>=limit,display_set:display,
      items:history.slice((display-1)*2,display*2),history,
      basis:'sample',basis_text:'디자인 비교를 위한 메뉴 예시입니다.'};
  }
  async function request(mode,action) {
    if (busy || !validOwner()) return;
    const stamp=generation, account=owner;
    busy=true; close(); $('menuError').textContent=''; render();
    try {
      let value;
      if (sample) value=sampleRequest(mode,action);
      else {
        const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);
        try {
          const response=await fetch('/api/menu/explore',{method:'POST',headers:{'Content-Type':'application/json'},
            signal:controller.signal,body:JSON.stringify({user_id:account,token:state.token,mode,action,
              expected_day:state.date,expected_seen:state.mode_counts[mode] || 0})});
          const body=await response.json();
          if (!response.ok) throw Error(typeof body.detail==='string'?body.detail:'추천 기록을 불러오지 못했습니다. 다시 시도해 주세요.');
          value=body;
        } finally { clearTimeout(timer); }
      }
      if (stamp!==generation || account!==currentUserId && !sample) return;
      state=value;
    } catch (error) {
      if (stamp===generation && account===currentUserId)
        $('menuError').textContent=error.name==='AbortError'?'연결이 지연되고 있습니다. 다시 시도해 주세요.':error.message;
    } finally {
      if (stamp===generation) { busy=false; render(); }
    }
  }
  function changeMode(mode) {
    if (!state || !['general','diet'].includes(mode)) return;
    if (mode!==state.mode || state.date!==today()) return request(mode,'open');
  }
  function next() {
    if (!validOwner() || busy) return;
    if (!sample && state.date!==today()) return request(state.mode,'open');
    if (state.exhausted) showHistory(); else return request(state.mode,'next');
  }
  function resume() {
    if (document.visibilityState==='visible' && validOwner() && !busy && !sample)
      return request(state.mode,'open');
  }
  document.addEventListener('visibilitychange',resume);
  window.addEventListener('pageshow',event=>{if(event.persisted) resume();});
  setInterval(()=>{
    if (validOwner() && !sample && state.date!==today()) resume();
  },60000);
  function startSample(rankings) {
    if (!window.DALHA_DESIGN_SAMPLE) return;
    generation++; owner=currentUserId; busy=false;
    sample={rankings:Object.fromEntries(Object.entries(rankings).map(([mode,names])=>
      [mode,names.map((menu,i)=>({menu,rank:i+1}))])),counts:{general:0,diet:0}};
    state=sampleRequest('general','open'); render();
  }
  window.DalhaMenu={mount,reset,changeMode,next,close,startSample};
})();
