/* Presentation only. Never changes report ownership, recommendation data or account state. */
(() => {
  const paths={
    topics:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    people:'<circle cx="8" cy="7" r="3"/><circle cx="18" cy="8" r="2.5"/><path d="M2 21v-3a6 6 0 0 1 12 0v3M16 14a5 5 0 0 1 6 5v2"/>',
    home:'<path d="m3 10 9-7 9 7v10H3Z"/><path d="M9 20v-7h6v7"/>',
    book:'<path d="M12 5c-3-2-7-2-10-1v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Z"/><path d="M12 5v15"/>',
    heart:'<path d="M20.7 4.8a5.3 5.3 0 0 0-7.5 0L12 6l-1.2-1.2a5.3 5.3 0 0 0-7.5 7.5L12 21l8.7-8.7a5.3 5.3 0 0 0 0-7.5Z"/>',
    user:'<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2M7 21h10"/>',
    moon:'<path d="M20.5 14.3A9 9 0 0 1 9.7 3.5a9 9 0 1 0 10.8 10.8Z"/>',
    spark:'<path d="m12 2 2.6 7.4L22 12l-7.4 2.6L12 22l-2.6-7.4L2 12l7.4-2.6Z"/>',
    hanger:'<path d="M9 6a3 3 0 1 1 4 2.8V11l9 6v2H2v-2l10-6"/>',
    palette:'<circle cx="7" cy="7" r="3"/><circle cx="17" cy="7" r="3"/><circle cx="7" cy="17" r="3"/><circle cx="17" cy="17" r="3"/>',
    briefcase:'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M8 7V3h8v4M2 12c6 4 14 4 20 0M10 13v3h4v-3"/>',
    coins:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 4 16 4 16 0V5M4 11v6c0 4 16 4 16 0v-6"/>',
    cards:'<rect x="7" y="2" width="13" height="19" rx="2"/><path d="m7 6-4 1 1 16 9-1M13.5 7l2 4-2 4-2-4Z"/>',
    orbit:'<circle cx="12" cy="12" r="4"/><ellipse cx="12" cy="12" rx="11" ry="6" transform="rotate(-40 12 12)"/><path d="M12 2v1M12 21v1"/>'
  };
  const icon=key=>`<svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${paths[key]||paths.spark}</svg>`;
  function initialize(){
    document.querySelectorAll('[data-brand-icon]').forEach(el=>{el.innerHTML=icon(el.dataset.brandIcon);el.setAttribute('aria-hidden','true');});
    for(const [id,key] of [['today','home'],['saju','book'],['theme','topics'],['mypage','user']]){
      const button=document.getElementById('tab-'+id);button.querySelector('svg')?.remove();button.insertAdjacentHTML('afterbegin',icon(key));
    }
    for(const [id,key] of [['drawerTarot','cards'],['drawerTalisman','spark'],['drawerZodiac','orbit']]){
      const header=document.querySelector('#'+id+' .drawer-header');
      const symbol=header?.querySelector('.drawer-icon-circle');
      if(symbol&&!symbol.querySelector('input')){symbol.innerHTML=icon(key);symbol.classList.add('brand-service-icon');symbol.setAttribute('aria-hidden','true');}
    }
    const date=document.getElementById('journalDate');
    if(date)date.textContent=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',month:'long',day:'numeric',weekday:'short'}).format(new Date());
    // Do not put decorative placeholders above real results while data loads.
    document.querySelectorAll('.ad-slot-box').forEach(el=>{if(/광고 영역/.test(el.textContent)&&!el.querySelector('iframe,ins'))el.hidden=true;});
    // Keep the theme after component-injected rules. Semantic clothing/color swatches are never recolored.
    const stylesheet=document.getElementById('dalhaBrandStyles');if(stylesheet)document.head.append(stylesheet);
  }
  document.addEventListener('DOMContentLoaded',initialize);
})();
