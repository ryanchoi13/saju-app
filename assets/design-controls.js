(() => {
  function initDialogs() {
    document.querySelectorAll('.modal-bg').forEach((modal,index) => {
      const heading = modal.querySelector('.modal-content > div:first-child');
      const title = heading?.querySelector('h3');
      heading?.classList.add('ui-modal-heading');
      if (title) {
        title.id ||= `dialog-title-${index}`;
        modal.setAttribute('role','dialog'); modal.setAttribute('aria-modal','true');
        modal.setAttribute('aria-labelledby',title.id);
      }
      modal.querySelectorAll('button[onclick]').forEach(button => {
        const action = button.getAttribute('onclick');
        if (button.textContent.trim() === '×') {
          button.classList.add('ui-close'); button.setAttribute('aria-label','닫기'); return;
        }
        if (action.startsWith('openPgModal')) {
          button.classList.add('ui-package'); button.lastElementChild?.classList.add('ui-price'); return;
        }
        if (button.matches('.fashion-v2-tab,.fashion-v2-close')) return;
        if (button.classList.contains('reading-text-button')) return;
        button.classList.add('ui-action');
        if (action.startsWith('shareZodiacFortune')) return; // Kakao's identifiable share color.
        const secondary = action.startsWith('close') || button.textContent.trim() === '이전';
        button.classList.add(secondary ? 'ui-action-secondary' : 'ui-action-primary');
      });
    });
    document.getElementById('talismanTitle')?.parentElement.classList.add('ui-panel');
    document.getElementById('pgItemName')?.parentElement.classList.add('ui-panel');
    const options = document.getElementById('modalOptionBox');
    const styleOptions = () => options.querySelectorAll('label').forEach(el => el.classList.add('ui-option'));
    new MutationObserver(styleOptions).observe(options,{childList:true});
    // Match the reader's keyboard behavior in the smaller dialogs, using existing close handlers.
    let activeDialog=null, returnFocus=null, previousOverflow='';
    const syncDialogFocus=()=>{
      const visible=[...document.querySelectorAll('.modal-bg:not(.hidden)')];
      const next=visible.at(-1);
      if (next?.id==='archiveDetailModal') return;
      if (next && next!==activeDialog) {
        if (!activeDialog) { returnFocus=document.activeElement; previousOverflow=document.body.style.overflow; }
        activeDialog=next; document.body.style.overflow='hidden';
        (next.querySelector('[data-dialog-close]') || next.querySelector('.ui-close'))?.focus();
      } else if (!next && activeDialog) {
        activeDialog=null; document.body.style.overflow=previousOverflow;
        if (returnFocus?.isConnected) returnFocus.focus();
      }
    };
    const observer=new MutationObserver(syncDialogFocus);
    document.querySelectorAll('.modal-bg').forEach(modal=>observer.observe(modal,{attributes:true,attributeFilter:['class']}));
    document.addEventListener('keydown',event=>{
      if (!activeDialog || activeDialog.classList.contains('hidden')) return;
      if (event.key==='Escape') { event.preventDefault(); (activeDialog.querySelector('[data-dialog-close]') || activeDialog.querySelector('.ui-close'))?.click(); return; }
      if (event.key!=='Tab') return;
      const controls=[...activeDialog.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled),a[href],[tabindex="0"]')].filter(el=>!el.closest('.hidden') && el.getClientRects().length);
      const first=controls[0],last=controls.at(-1);
      if (event.shiftKey && document.activeElement===first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement===last) { event.preventDefault(); first?.focus(); }
    });
  }
  function initComparison() {
    if (!/^\/design\/(clear|moonlight)\/?$/.test(location.pathname)) return;
    const moonlight = document.documentElement.dataset.design === 'moonlight';
    const sample = window.DALHA_DESIGN_SAMPLE;
    const bar = document.createElement('aside');
    bar.className = 'design-comparison'; bar.setAttribute('aria-label','디자인 비교');
    const suffix = sample ? '?sample=1' : '';
    bar.innerHTML = `<p>${sample ? '디자인 미리보기 · 가상 인물과 예시 내용입니다.' : '달하 · 실제 계정으로 보고 있습니다.'}</p><a class="design-sample-link" href="${sample ? '/' : '/design/clear?sample=1'}">${sample ? '내 달하로 가기' : '예시 화면 보기'} →</a>`;
    document.querySelector('.app-container > header').after(bar);
    // Preserve the current page when switching A/B, without changing stored preferences.
    bar.querySelectorAll('a:not(.design-sample-link)').forEach(link => link.addEventListener('click', () => {
      const active = document.querySelector('.tab-view:not(.hidden)');
      const tab = active?.id.replace('view-','');
      const url = new URL(link.href);
      if (['today','saju','theme','mypage'].includes(tab)) url.searchParams.set('tab',tab);
      if (tab === 'saju') url.searchParams.set('section',document.querySelector('.reading-tabs [aria-selected="true"]').id.replace('saju-tab-',''));
      link.href = url.href;
    }));
  }
  document.addEventListener('DOMContentLoaded', () => { initDialogs(); initComparison(); });
})();
