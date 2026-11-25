// 2026-10-15 공개 범위(프로젝트 문서 dalha-roadmap): 결제 없이 공개 → 테마운 5개는 '곧 열려요'(궁합은 11/20부터 복채 결제),
// 직업·애정·건강의 앞부분 무료 맛보기는 유지, 타로·별자리·시간대 팁은 숨김. 실제 계정·네트워크 없이 확인한다.
const {JSDOM, ResourceLoader, VirtualConsole} = require('jsdom');
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const root = path.join(__dirname, '..');
class Resources extends ResourceLoader {
    fetch(url) {
        const u = new URL(url);
        if (u.origin === 'https://dalha.example' && u.pathname.startsWith('/assets/')) {
            const file = path.join(root, u.pathname);
            if (fs.existsSync(file)) return Promise.resolve(fs.readFileSync(file));
        }
        return null;
    }
}
(async () => {
    const logs = new VirtualConsole();
    const dom = new JSDOM(fs.readFileSync(path.join(root, 'index.html'), 'utf8'), {
        url:'https://dalha.example/', runScripts:'dangerously', resources:new Resources(),
        pretendToBeVisual:true, virtualConsole:logs,
        beforeParse(w) {
            w.scrollTo = () => {}; w.HTMLElement.prototype.scrollIntoView = () => {};
            w.fetch = async () => { throw Error('Offline test'); };
            w.alert = () => {};
            w.Kakao = {isInitialized:() => true, Auth:{login:() => {}}};
        }
    });
    const w = dom.window, doc = w.document;
    try {
        await new Promise(r => w.addEventListener('load', r));
        for (const sel of ['#drawerTarot', '#drawerZodiac', '.journal-times']) {
            const el = doc.querySelector(sel);
            assert.ok(el && el.hasAttribute('hidden'), `${sel} must be hidden for launch`);
            assert.equal(el.getAttribute('aria-hidden'), 'true');
        }
        assert.ok(!doc.querySelector('#drawerTalisman').hasAttribute('hidden'), 'talisman stays');

        w.eval('DALHA_SOON_REPORTS.forEach(applySoonEntrypoint)');
        // 11/20: 궁합은 복채 결제로 연다 — '곧 열려요' 표시가 없고 가격(250 복채)이 보인다.
        assert.ok(!doc.getElementById('btnOpenGunghapModal').classList.contains('soon-hidden'), 'gunghap purchase button visible');
        assert.equal(doc.getElementById('soon_gunghap'), null, 'gunghap has no soon badge');
        assert.equal(doc.querySelector('[data-report-price="gunghap"]').textContent, '250 복채');
        for (const key of ['business', 'love', 'health', 'wealth', 'study']) {
            assert.ok(!doc.getElementById(`btnTheme_${key}`).classList.contains('soon-hidden'), `${key} free preview stays`);
            // 11/15: 테마운 칸의 가격 안내 줄은 뺐다(열람 버튼·'전체 풀이는 곧 열려요'가 대신 알려 줌).
            assert.equal(doc.querySelector(`[data-report-price="${key}"]`), null);
        }
        w.eval('DALHA_SOON_REPORTS.forEach(applySoonEntrypoint)');
        assert.equal(doc.querySelectorAll('#soon_gunghap').length, 0, 'idempotent');

        w.eval(`themePreviewCache.business = {content:'<p>앞부분</p><a data-paywall-cta href="#">결제</a>', price_coins:220}; renderThemePreview('business');`);
        const slot = doc.getElementById('themeReport_business');
        // 11/25: '곧 열려요'를 없앴다 — 테마운 미리보기 아래에 복채 결제 버튼이 나온다.
        assert.match(slot.querySelector('.theme-unlock-cta').textContent, /220 복채/);
        assert.equal(slot.querySelector('[data-paywall-cta]'), null);
        assert.equal(slot.querySelector('.lock-soon'), null, 'no coming-soon badge');
        assert.equal(doc.querySelectorAll('[id^="soon_"]').length, 0, 'no soon badges anywhere');
        assert.match(slot.textContent, /앞부분/);
        console.log('PASS: launch scope — themes on sale, gunghap on sale, free previews kept, tarot/zodiac/time tips hidden');
    } finally { w.close(); }
})().catch(e => { console.error(e); process.exit(1); });
