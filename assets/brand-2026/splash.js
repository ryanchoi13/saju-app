/* 앱 시작 화면. 설치형 앱으로 켰을 때(또는 ?splash=1) 한 번만, 최소 1.6초 보여 준다.
   달 모양은 음력 계산 없이 평균 삭망월로 어림한다(홈의 달과 하루쯤 어긋날 수 있음). */
(function () {
  var el = document.getElementById('dalhaSplash');
  if (!el) return;
  var forced = /[?&]splash=1\b/.test(location.search);
  var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  var seen = false;
  try { seen = sessionStorage.getItem('dalhaSplashSeen') === '1'; } catch (e) {}
  if (!(forced || (standalone && !seen))) { el.parentNode.removeChild(el); return; }
  try { sessionStorage.setItem('dalhaSplashSeen', '1'); } catch (e) {}

  var SYN = 29.530588853, REF = Date.UTC(2000, 0, 6, 18, 14);
  var age = (((Date.now() - REF) / 86400000) % SYN + SYN) % SYN;       // 달의 나이(일)
  var angle = age / SYN * 2 * Math.PI, c = Math.cos(angle), r = 44;
  var waxing = age < SYN / 2, lit = waxing ? 1 : 0, inner = c > 0 ? (lit ? 0 : 1) : (lit ? 1 : 0);
  var rx = Math.max(Math.abs(c) * r, 0.01);
  var d = 'M50 ' + (50 - r) + ' A' + r + ' ' + r + ' 0 0 ' + lit + ' 50 ' + (50 + r) +
          ' A' + rx.toFixed(2) + ' ' + r + ' 0 0 ' + inner + ' 50 ' + (50 - r) + 'Z';
  var moon = el.querySelector('.sp-moon');
  moon.innerHTML = '<circle cx="50" cy="50" r="44" fill="#2A2F39"/><path d="' + d + '" fill="#FDFCF9"/>';

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
