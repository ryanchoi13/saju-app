// URL-scoped alternatives; never persist a theme across comparison addresses.
(() => {
  const match = location.pathname.match(/^\/design\/(clear|moonlight)\/?$/);
  document.documentElement.dataset.design = match?.[1] || 'clear';
  window.DALHA_DESIGN_SAMPLE = Boolean(match && new URLSearchParams(location.search).get('sample') === '1');
  if (match) {
    const robots = document.createElement('meta');
    robots.name = 'robots'; robots.content = 'noindex, nofollow'; document.head.append(robots);
  }
  if (!window.DALHA_DESIGN_SAMPLE) return;
  // A public, fictional preview has its own transient state; it cannot touch a real account.
  const data = new Map();
  Object.defineProperty(window, 'localStorage', {value:{
    getItem:key => data.get(String(key)) ?? null,
    setItem:(key,value) => data.set(String(key),String(value)),
    removeItem:key => data.delete(String(key)), clear:() => data.clear(),
    key:index => [...data.keys()][index] ?? null, get length() { return data.size; }
  }});
  window.fetch = async () => { throw new Error('디자인 예시에서는 서버 요청을 보내지 않습니다.'); };
})();
