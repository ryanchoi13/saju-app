// 태어난 시간 입력(시·분 드롭다운) 화면 계약 테스트. 실제 서버·계정 없음.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf('        // 태어난 시간: 시(0~23)');
const end = html.indexOf('        function getSajuStorageKey(');
assert.ok(start > 0 && end > start, 'birth time helpers exist');
const helpers = html.slice(start, end);
const submitStart = html.indexOf('        async function submitSajuRegistration()');
const submitEnd = html.indexOf('        function reopenSajuEditForm()');
const submit = html.slice(submitStart, submitEnd);

assert.ok(!html.includes('id="inputSijin"'), '시진 선택 상자는 없어야 함');
assert.ok(html.includes('id="birthHourSelect"') && html.includes('id="birthMinuteSelect"'));

const dom = new JSDOM(`<input id="inputName" value="테스트">
  <select id="birthYearSelect"><option value="1990" selected>1990</option></select>
  <select id="birthMonthSelect"><option value="5" selected>5</option></select>
  <select id="birthDaySelect"><option value="15" selected>15</option></select>
  <select id="birthHourSelect"></select><select id="birthMinuteSelect"></select>
  <p id="birthTimeLegacyNote" hidden></p>
  <div id="onboardingInputView"></div><div id="bottomNavBar"></div>`, { runScripts: 'outside-only' });
const w = dom.window;
const sent = [], alerts = [];
Object.assign(w, {
  selectedGender: 'male', selectedCalendarType: 'solar', currentUserId: 'user_1', currentCoin: 0,
  alert: msg => alerts.push(msg),
  fetch: async (_url, opts) => { sent.push(JSON.parse(opts.body)); return { ok: true, json: async () => ({ coin_balance: 1, profile: null }) }; },
  saveUserSajuToLocal() {}, updateCoinDisplay() {}, applySajuAnalysisToUI() {}, switchTab() {},
});
w.eval(helpers.replace('const SIJIN_NAMES', 'var SIJIN_NAMES') + submit);
w.initBirthTimeDropdowns();
const $ = id => w.document.getElementById(id);

// 0~23시, 0~59분 + 모름
const hourValues = [...$('birthHourSelect').options].map(o => o.value);
assert.deepEqual(hourValues.slice(0, 2), ['', 'unknown']);
assert.equal(hourValues.length, 26);
assert.equal($('birthMinuteSelect').options.length, 61);

(async () => {
  // 시·분을 고르지 않으면 막음
  await w.submitSajuRegistration();
  assert.equal(sent.length, 0); assert.match(alerts.at(-1), /시와 분/);

  // 시만 고르고 분을 안 고르면 막음
  $('birthHourSelect').value = '23'; $('birthHourSelect').onchange();
  await w.submitSajuRegistration();
  assert.equal(sent.length, 0);

  // 23시 45분 → 그대로 전송
  $('birthMinuteSelect').value = '45';
  await w.submitSajuRegistration();
  assert.equal(sent.at(-1).birth_hour, 23); assert.equal(sent.at(-1).birth_minute, 45);
  assert.equal(sent.at(-1).sijin_index, -1);

  // 모름 → 분 비활성, 시각 없이 전송
  $('birthHourSelect').value = 'unknown'; $('birthHourSelect').onchange();
  assert.equal($('birthMinuteSelect').disabled, true);
  await w.submitSajuRegistration();
  assert.equal(sent.at(-1).birth_hour, null); assert.equal(sent.at(-1).sijin_index, -1);

  // 저장된 정확한 시각 불러오기
  w.setBirthTimeForm({ profile_complete: true, birth_hour: 7, birth_minute: 5, sijin_index: 3 });
  assert.equal($('birthHourSelect').value, '7'); assert.equal($('birthMinuteSelect').value, '5');
  assert.equal($('birthTimeLegacyNote').hidden, true);

  // 예전 시진만 저장된 사용자: 비워 두고 안내
  w.setBirthTimeForm({ profile_complete: true, sijin_index: 6 });
  assert.equal($('birthHourSelect').value, '');
  assert.equal($('birthTimeLegacyNote').hidden, false);
  assert.match($('birthTimeLegacyNote').textContent, /오시/);

  // 생시 미상으로 저장된 사용자
  w.setBirthTimeForm({ profile_complete: true, sijin_index: -1 });
  assert.equal($('birthHourSelect').value, 'unknown');
  // ── 궁합 상대방 입력 ──
  assert.ok(!html.includes('id="partnerSijinSelect"'), '상대방 시진 선택 상자는 없어야 함');
  const gStart = html.indexOf('        function confirmUnlockGunghapOnServer()');
  const gEnd = html.indexOf('        function openThemeSelectModal(');
  const pdom = new JSDOM(`<input id="partnerNameInput" value="상대">
    <select id="partnerRelationSelect"><option value="친구 / 지인" selected>친구</option></select>
    <select id="partnerGenderSelect"><option value="female" selected>여</option></select>
    <select id="partnerBirthYearSelect"><option value="1992" selected>1992</option></select>
    <select id="partnerBirthMonthSelect"><option value="6" selected>6</option></select>
    <select id="partnerBirthDaySelect"><option value="18" selected>18</option></select>
    <select id="partnerCalendarTypeSelect"><option value="solar" selected>양력</option></select>
    <select id="partnerBirthHourSelect"></select><select id="partnerBirthMinuteSelect"></select>
    <select id="birthHourSelect"></select><select id="birthMinuteSelect"></select>`, { runScripts: 'outside-only' });
  const pw = pdom.window, unlocks = [], palerts = [];
  Object.assign(pw, { alert: m => palerts.push(m),
    closeGunghapModal() {},
    handleUnlockReportOnServer: (...args) => unlocks.push(args[5]) });
  pw.eval(helpers.replace('const SIJIN_NAMES', 'var SIJIN_NAMES') + html.slice(gStart, gEnd));
  pw.initBirthTimeDropdowns();
  const p$ = id => pw.document.getElementById(id);
  assert.equal(p$('partnerBirthHourSelect').options.length, 26);
  // 시만 고르고 분 없음 → 막음
  p$('partnerBirthHourSelect').value = '23'; p$('partnerBirthHourSelect').onchange();
  pw.confirmUnlockGunghapOnServer();
  assert.equal(unlocks.length, 0); assert.match(palerts.at(-1), /상대방의 태어난 시와 분/);
  // 23시 45분 → 전송
  p$('partnerBirthMinuteSelect').value = '45';
  pw.confirmUnlockGunghapOnServer();
  assert.equal(unlocks.at(-1).partner_birth_hour, 23); assert.equal(unlocks.at(-1).partner_birth_minute, 45);
  // 모름 → 분 비활성, 시각 없이 전송
  p$('partnerBirthHourSelect').value = 'unknown'; p$('partnerBirthHourSelect').onchange();
  assert.equal(p$('partnerBirthMinuteSelect').disabled, true);
  pw.confirmUnlockGunghapOnServer();
  assert.equal(unlocks.at(-1).partner_birth_hour, null); assert.equal(unlocks.at(-1).partner_sijin_index, -1);

  console.log('birth time picker: ok');
})().catch(err => { console.error(err); process.exit(1); });
