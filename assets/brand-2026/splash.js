/* 앱 시작 화면. 설치형 앱으로 켰을 때(또는 ?splash=1) 한 번만, 최소 1.6초 보여 준다.
   (2026-11-18: 달 모양을 오늘의 달 위상에서 앱 아이콘 모양으로 통일) */
(function () {
  var el = document.getElementById('dalhaSplash');
  if (!el) return;
  var forced = /[?&]splash=1\b/.test(location.search);
  var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  var seen = false;
  try { seen = sessionStorage.getItem('dalhaSplashSeen') === '1'; } catch (e) {}
  if (!(forced || (standalone && !seen))) { el.parentNode.removeChild(el); return; }
  try { sessionStorage.setItem('dalhaSplashSeen', '1'); } catch (e) {}

  // 달 모양은 홈 화면 아이콘(app-icon.svg)과 똑같이 그린다: 아이보리 초승달 + 살구 점. 켤 때 아이콘 → 시작 화면 → 앱 안 로고가 한 모양으로 이어진다.
  var moon = el.querySelector('.sp-moon');
  moon.setAttribute('viewBox', '64 74 372 372');
  moon.innerHTML = '<defs><mask id="spCrescent" maskUnits="userSpaceOnUse" x="0" y="0" width="512" height="512">' +
    '<rect width="512" height="512" fill="#000"/><circle cx="252" cy="258" r="168" fill="#fff"/><circle cx="342" cy="292" r="124" fill="#000"/></mask></defs>' +
    '<rect width="512" height="512" fill="#F8F6F1" mask="url(#spCrescent)"/><circle cx="320" cy="322" r="42" fill="#E4B28F"/>';

  // 별: 달·글자와 겹치지 않게 화면 가장자리 위주로 은은하게. [왼쪽%, 위%, 크기px, 깜빡임초, 지연초, 밝기, 십자모양]
  var stars = [[10,9,3,3.4,0,.8,1],[82,7,2,2.8,.6,.7,0],[28,17,2,3.8,1.2,.55,0],[92,21,3,3.2,.3,.75,1],
    [7,34,2,2.6,1.5,.6,0],[88,41,2,3.6,.9,.55,0],[14,62,3,3.0,.4,.7,1],[93,66,2,2.9,1.8,.6,0],
    [24,82,2,3.5,.7,.55,0],[76,86,3,3.3,1.1,.75,1],[56,5,2,2.7,2.0,.5,0],[47,93,2,3.1,.2,.5,0]];
  var sky = document.createElement('div'); sky.className = 'sp-stars';
  stars.forEach(function (a) {
    var s = document.createElement('i');
    s.className = 'sp-star' + (a[6] ? ' plus' : '');
    s.style.cssText = 'left:' + a[0] + '%;top:' + a[1] + '%;width:' + (a[6] ? a[2] * 3 : a[2]) + 'px;height:' + (a[6] ? a[2] * 3 : a[2]) + 'px;--d:' + a[3] + 's;--t:' + a[4] + 's;--o:' + a[5];
    sky.appendChild(s);
  });
  el.insertBefore(sky, el.firstChild);

  var kst = new Date(Date.now() + 9 * 3600000);                         // 한국 날짜
  var w = ['일', '월', '화', '수', '목', '금', '토'];
  el.querySelector('.sp-date').textContent = (kst.getUTCMonth() + 1) + '월 ' + kst.getUTCDate() + '일 ' + w[kst.getUTCDay()] + '요일';

  var meta = document.querySelector('meta[name="theme-color"]'), prev = meta && meta.getAttribute('content');
  if (meta) meta.setAttribute('content', '#1D2129');
  el.classList.add('on');

  var closed = false;
  function close() {
    if (closed) return; closed = true;
    if (meta && prev) meta.setAttribute('content', prev);
    el.classList.add('out');
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 400);
  }
  el.addEventListener('click', close);
  setTimeout(close, 1600);
})();
