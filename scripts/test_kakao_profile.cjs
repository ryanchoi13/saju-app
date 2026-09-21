// Offline SDK/server contract tests. No real accounts or production writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
for (const script of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) new vm.Script(script[1]);
const source = html.slice(html.indexOf('        function buildKakaoAuthPayload('), html.indexOf('        function logoutKakaoUser('));
function setup(account, profile, status = 'new_user') {
    const nodes = new Map(), storage = new Map(), requests = [], logins = [], alerts = [];
    let sdkAccount = account;
    const ctx = {
        console, currentUserId: null, currentCoin: 0, serverUnlockedReports: [],
        document: {getElementById(id) {
            if (!nodes.has(id)) {
                const classes = new Set();
                nodes.set(id, {hidden: false, textContent: '', classList: {
                    add: key => classes.add(key), remove: key => classes.delete(key),
                    contains: key => classes.has(key),
                    toggle: (key, yes) => yes ? classes.add(key) : classes.delete(key),
                }});
            }
            return nodes.get(id);
        }},
        localStorage: {getItem: k => storage.get(k) || null, setItem: (k,v) => storage.set(k,v)},
        getSavedUserSaju: () => null,
        initKakaoSDK() {}, acceptTarotState() {}, updateCoinDisplay() {},
        acceptWardrobeResponse() {}, renderWardrobeUI() {}, renderServerArchive() {},
        restoreUnlockedUIFromReports() {}, switchTab() {}, applySajuAnalysisToUI() {},
        saveUserSajuToLocal() {},
        populateSajuForm: p => {ctx.prefilled = p;},
        alert: s => alerts.push(s),
        Kakao: {isInitialized: () => true, Auth: {login: options => logins.push(options)},
            API: {request: options => options.success({id: '321', kakao_account: sdkAccount})}},
        fetch: async (url, options) => {
            requests.push(JSON.parse(options.body));
            return {ok: true, json: async () => ({status, user_id:'user_321', coin_balance:1000,
                kakao_prefill: profile, profile})};
        },
    };
    ctx.window = ctx;
    vm.createContext(ctx); vm.runInContext(source, ctx);
    const tick = () => new Promise(resolve => setImmediate(resolve));
    return {ctx, nodes, requests, logins, alerts, tick,
        setAccount: value => {sdkAccount = value;},
        async login() {ctx.loginWithKakaoReal(); logins.at(-1).success({access_token:'test-token'}); await tick();},
    };
}
(async () => {
    const partial = {name:'', gender:null, birth_year:null, birth_month:null, birth_day:null, profile_complete:false};
    const flags = {name_needs_agreement:true, gender_needs_agreement:true, birthyear_needs_agreement:true, birthday_needs_agreement:true};
    const t = setup(flags, partial);
    await t.login();
    assert.equal(t.nodes.get('kakaoProfileHelp').hidden, false);
    assert.equal(t.logins.length, 1, 'no blocked or repeated popup from the API callback');
    t.ctx.requestKakaoProfileConsent();
    assert.equal(t.logins.at(-1).scope, 'name,gender,birthyear,birthday');
    assert.equal(t.logins.at(-1).throughTalk, true);
    t.logins.at(-1).fail({error:'access_denied'});
    assert.equal(t.requests.length, 1, 'cancel keeps the current form and login');

    const full = {name:'테스트', gender:'female', birth_year:1992, birth_month:9, birth_day:21, profile_complete:false};
    Object.assign(partial, full);
    t.setAccount({name:'테스트', gender:'female', birthyear:'1992', birthday:'0921'});
    t.ctx.requestKakaoProfileConsent();
    t.logins.at(-1).success({access_token:'new-token'}); await t.tick();
    assert.equal(t.ctx.prefilled.birth_year, 1992);
    assert.equal(t.requests.at(-1).access_token, 'new-token');
    assert.equal(t.requests.at(-1).profile_source, 'kakao');
    assert.equal(t.requests.at(-1).sijin_index, null, 'birth time still requires confirmation');
    assert.equal(t.nodes.get('kakaoProfileHelp').hidden, true);

    const unavailable = setup({profile:{nickname:'별명'}}, {profile_complete:false});
    await unavailable.login();
    assert.equal(unavailable.nodes.get('btnKakaoProfile').classList.contains('hidden'), true);
    assert.equal(unavailable.requests[0].name, null, 'do not substitute nickname for real name');
    assert.match(unavailable.nodes.get('kakaoProfileNotice').textContent, /제공되지 않은/);

    const some = setup(flags, {...full, birth_year:null});
    await some.login(); some.ctx.requestKakaoProfileConsent();
    assert.equal(some.logins.at(-1).scope, 'birthyear', 'only request missing consentable fields');

    const existing = setup(flags, {...full, profile_complete:true}, 'existing_user');
    await existing.login();
    assert.equal(existing.ctx.prefilled.name, '테스트');
    assert.equal(existing.logins.length, 1);
    assert.equal(existing.nodes.has('kakaoProfileHelp'), false, 'confirmed profiles bypass consent UI');

    const resume = setup({}, {profile_complete:false});
    resume.ctx.localStorage.setItem('dalha_kakao_id', '321');
    await resume.ctx.checkAutoLoginSession();
    assert.equal(resume.nodes.get('kakaoProfileHelp').hidden, false);
    resume.ctx.requestKakaoProfileConsent();
    assert.equal(resume.logins.length, 1, 'incomplete returning accounts can reconnect');
    assert.equal(resume.logins[0].scope, undefined, 'do not guess unsupported scopes');
    console.log('PASS: consent recovery, cancellation, verified prefill, unavailable fields, partial consent, existing profile, incomplete resume');
})().catch(error => {console.error(error); process.exitCode = 1;});
