// 이미 저장된 월별 카드(옛 마크업)가 새 모양(총운 먼저, 라벨 칸+글 칸)으로 바뀌는지 확인한다.
const assert = require('assert'); const fs = require('fs'); const { JSDOM } = require('jsdom');
const OLD = `<article data-report-month="11" class="annual-month"><h4>11월 · 보통</h4><div class="annual-month-period">11월 7일부터 12월 6일까지의 흐름입니다.</div>
<p class="annual-month-grade" data-grade="normal"><strong>근거</strong> 도움이 되는 기운과 부딪히는 기운이 함께 드는 달입니다.<br><strong>처방</strong> 좋은 일과 걸리는 일을 나눠 적으세요.</p>
<p class="annual-month-flow">꾸준함이 보람으로 남는 달입니다.</p><h5>올해와 이어지는 점</h5><p>올해의 흐름입니다.</p>
<p class="annual-month-todo"><strong>할 일</strong> 정한 계획 그대로 지키기<br><strong>피할 일</strong> 새 지출 늘리기</p></article>`;
const dom = new JSDOM(`<body><div id="b">${OLD}</div></body>`, { runScripts: 'outside-only' });
dom.window.eval(fs.readFileSync('assets/annual-reader.js', 'utf8'));
const body = dom.window.document.getElementById('b');
dom.window.formatAnnualReading(body); dom.window.formatAnnualReading(body);          // 두 번 돌려도 같아야 한다
const card = body.querySelector('article'); const kids = [...card.children].map(e => e.className || e.tagName);
assert.ok(kids.indexOf('annual-month-flow') < kids.indexOf('annual-month-grade'), kids.join(','));
const rows = card.querySelectorAll('.annual-month-row'); assert.equal(rows.length, 4);
assert.deepEqual([...rows].map(r => r.firstChild.textContent), ['근거', '처방', '할 일', '피할 일']);
assert.equal(rows[2].lastChild.textContent, '정한 계획 그대로 지키기');
assert.ok(!card.querySelector('br'));
console.log('PASS saved month card upgraded (order, label/text rows, idempotent)');
