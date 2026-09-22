// Real page, offline resources, fake SDK only. Never accesses a real account.
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
    let loginCount = 0;
    const errors = [], logs = new VirtualConsole();
    logs.on('jsdomError', e => { if (e.type !== 'css parsing') errors.push(e); });
    const dom = new JSDOM(fs.readFileSync(path.join(root, 'index.html'), 'utf8'), {
        url:'https://dalha.example/', runScripts:'dangerously', resources:new Resources(),
        pretendToBeVisual:true, virtualConsole:logs,
        beforeParse(w) {
            w.scrollTo = () => {}; w.HTMLElement.prototype.scrollIntoView = () => {};
            w.fetch = async () => { throw Error('Offline test'); };
            w.alert = () => {};
            w.Kakao = {isInitialized:() => true, Auth:{login:() => loginCount++}};
        }
    });
    const w = dom.window, doc = w.document;
    try {
        await new Promise(resolve => w.addEventListener('load', resolve));
        const gate = doc.getElementById('view-login-gate');
        assert.equal(errors.length, 0, errors.map(e => e.message).join('\n'));
        assert.equal(gate.classList.contains('hidden'), false);
        assert.equal(gate.querySelectorAll('h1').length, 1);
        assert.equal(gate.querySelectorAll('.landing-feature').length, 3);
        assert.deepEqual([...gate.querySelectorAll('.landing-feature h3')].map(n => n.textContent),
            ['오늘 나에게 어울리는 코디', '오늘 나에게 맞는 식단', '오늘의 흐름을 읽어요']);
        assert.match(gate.querySelector('#landing-features-title').textContent, /오늘, 뭐 입을까\? 뭐 먹을까\?/);
        assert.match(gate.querySelectorAll('.landing-feature')[1].textContent, /끼니별 칼로리/);
        assert.match(gate.querySelector('.landing-footer').textContent, /정읍사/);
        assert.match(gate.querySelector('.landing-footer').textContent, /음양오행과 전통 명리학/);
        assert.ok(!gate.querySelector('.landing-footer').textContent.includes('전문적인 판단'));
        assert.match(doc.querySelector('#menuExplorerControls details').textContent, /건강·영양에 관한 전문적인 판단/);
        assert.ok(gate.textContent.includes('소개용 예시'));
        assert.ok(!gate.textContent.includes('3초'));
        assert.ok(!gate.textContent.includes('1,000'));
        for (const link of gate.querySelectorAll('a[href^="#"]')) {
            assert.ok(doc.querySelector(link.getAttribute('href')), 'anchor target exists');
        }
        assert.equal(loginCount, 0, 'no unsolicited login');
        doc.getElementById('btnKakaoLogin').click();
        assert.equal(loginCount, 1, 'CTA invokes the existing Kakao login exactly once');
        const incomplete = {profile_complete:false};
        for (const account of [null, {}, {profile:{nickname:'별명'}}]) {
            w.updateKakaoProfileHelp(incomplete, account);
            assert.ok(doc.getElementById('btnKakaoProfile').classList.contains('hidden'));
            assert.equal(doc.getElementById('kakaoProfileHelp').hidden, false);
            assert.match(doc.getElementById('kakaoProfileNotice').textContent, /처음 한 번만/);
        }
        w.populateSajuForm({name:'테스트',gender:'male',birth_year:1992,birth_month:9,birth_day:21,
            calendar_type:'solar',profile_complete:false});
        assert.equal(doc.getElementById('inputName').value, '테스트');
        assert.equal(doc.getElementById('birthYearSelect').value, '1992');
        assert.equal(doc.getElementById('birthMonthSelect').value, '9');
        assert.equal(doc.getElementById('birthDaySelect').value, '21');
        w.updateKakaoProfileHelp({profile_complete:true});
        assert.equal(doc.getElementById('kakaoProfileHelp').hidden, true);
        console.log('PASS: landing structure, sample disclosure, anchors, login CTA, manual onboarding, real form population');
    } finally { w.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
