// 2026-10-15 공개 범위(프로젝트 문서 dalha-roadmap): 결제 없이 공개 → 테마운 5개·궁합은 '곧 열려요',
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
        for (const key of ['wealth', 'study', 'gunghap']) {
            const button = doc.getElementById(key === 'gunghap' ? 'btnOpenGunghapModal' : `btnTheme_${key}`);
            assert.ok(button.classList.contains('soon-hidden'), `${key} purchase button hidden`);
            assert.equal(doc.getElementById(`soon_${key}`).textContent, '곧 열려요');
            assert.equal(doc.querySelector(`[data-report-price="${key}"]`).textContent, '곧 열려요');
        }
        for (const key of ['business', 'love', 'health']) {
            assert.ok(!doc.getElementById(`btnTheme_${key}`).classList.contains('soon-hidden'), `${key} free preview stays`);
            assert.equal(doc.querySelector(`[data-report-price="${key}"]`).textContent, '앞부분 무료 · 전체는 곧 열려요');
        }
        w.eval('DALHA_SOON_REPORTS.forEach(applySoonEntrypoint)');
        assert.equal(doc.querySelectorAll('#soon_wealth').length, 1, 'idempotent');

        w.eval(`themePreviewCache.business = {content:'<p>앞부분</p><a data-paywall-cta href="#">결제</a>', price_coins:220}; renderThemePreview('business');`);
        const slot = doc.getElementById('themeReport_business');
        assert.equal(slot.querySelector('.theme-unlock-cta'), null, 'no payment button');
        assert.equal(slot.querySelector('[data-paywall-cta]'), null);
        assert.equal(slot.querySelector('.lock-soon').textContent, '전체 풀이는 곧 열려요');
        assert.match(slot.textContent, /앞부분/);
        console.log('PASS: launch scope — theme 5 + gunghap soon, free previews kept, tarot/zodiac/time tips hidden');
    } finally { w.close(); }
})().catch(e => { console.error(e); process.exit(1); });
