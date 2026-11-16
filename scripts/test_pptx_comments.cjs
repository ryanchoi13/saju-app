// 11/16 슬라이드 코멘트: 마이페이지 목록·보관함 팝업·약관 칸, 테마운 소개 팝업, 풀이 근거 표시, 평생운세 목차, 용어
const {JSDOM}=require('jsdom');
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8');
const dom=new JSDOM(html,{url:'https://dalha.example',runScripts:'outside-only'});
const w=dom.window, ctx=dom.getInternalVMContext(), doc=w.document;
w.scrollTo=()=>{}; w.alert=()=>{}; w.Element.prototype.scrollIntoView=()=>{};
for(const s of doc.querySelectorAll('script:not([src])')) vm.runInContext(s.textContent,ctx);
const $=id=>doc.getElementById(id);
const hidden=id=>$(id).classList.contains('hidden');
(async()=>{
    // 마이페이지: 제목 + 가는 줄로 나뉜 행, 계정/약관 상자
    const titles=[...doc.querySelectorAll('#view-mypage .my-box-title')].map(e=>e.textContent);
    assert.deepEqual(titles,['내 정보','계정','약관 및 정책']);
    assert.equal(doc.querySelectorAll('#view-mypage .my-box').length,3);
    for(const box of doc.querySelectorAll('#view-mypage .my-box')) assert.ok(box.querySelectorAll('.my-row').length>=2);
    const account=[...doc.querySelectorAll('#myAccountHeading ~ .my-rows .my-row')].map(b=>b.textContent.trim());
    assert.deepEqual(account,['로그아웃','회원 탈퇴']);
    assert.equal(doc.querySelector('#view-mypage details'),null);   // 펼침 방식은 없다

    // 감명서 보관함은 팝업
    assert.ok(hidden('archiveListModal'));
    assert.match($('reportArchiveToggle').getAttribute('onclick'),/openArchiveListModal/); w.openArchiveListModal();
    assert.ok(!hidden('archiveListModal'));
    assert.ok($('archiveListModal').contains($('unlockedArchiveList')));
    w.closeArchiveListModal(); assert.ok(hidden('archiveListModal'));

    // 약관·개인정보처리방침: 준비 중 안내
    for(const name of ['개인정보처리방침','이용약관']){
        const row=[...doc.querySelectorAll('#myLegalHeading ~ .my-rows .my-row')].find(b=>b.textContent.includes(name));
        assert.match(row.textContent,/준비 중/);
        assert.match(row.getAttribute('onclick'),new RegExp(`openLegalNotice\\('${name}'\\)`)); w.openLegalNotice(name);
        assert.ok(!hidden('legalModal'));
        assert.equal($('legalModalTitle').textContent,name);
        assert.match($('legalModal').textContent,/준비 중이에요/);
        w.closeLegalNotice(); assert.ok(hidden('legalModal'));
    }

    // 테마운: 고르면 '이런 이야기를 읽어요' 팝업 → 풀이 보기로 본문 쪽으로
    let previewed=[]; w.fetch=async(url,opts)=>{previewed.push(JSON.parse(opts.body).report_key);throw Error('stop');};
    vm.runInContext('currentUserId="u1"',ctx);
    assert.match(doc.querySelector('[data-concern-choice="wealth"]').getAttribute('onclick'),/openThemeIntro\('wealth'\)/);
    w.openThemeIntro('wealth');
    assert.ok(!hidden('themeIntroModal'));
    assert.match($('themeIntroModal').textContent,/이런 이야기를 읽어요/);
    assert.ok(doc.querySelectorAll('#themeIntroToc li').length>=5);
    assert.equal($('themeIntroTitle').textContent,'평생 재물운');
    assert.ok(doc.querySelector('#concern-wealth').classList.contains('hidden'));
    await w.confirmThemeIntro();
    assert.ok(hidden('themeIntroModal'));
    assert.ok(!doc.querySelector('#concern-wealth').classList.contains('hidden'));
    assert.ok(previewed.includes('wealth'));

    // 이미 산 풀이: 팝업은 하나(풀이 팝업). 목차 → 풀이 보기가 같은 팝업 안에서 이어진다.
    vm.runInContext('serverUnlockedReports=[{report_key:"wealth",report_title:"재물운",report_content:"<h3>본문 시작</h3>"}]',ctx);
    w.openThemeIntro('wealth');
    assert.ok(hidden('themeIntroModal'));
    assert.ok(!hidden('archiveDetailModal'));
    assert.ok(doc.querySelectorAll('#archiveModalBody .theme-intro-inline li').length>=5);
    assert.doesNotMatch($('archiveModalBody').textContent,/본문 시작/);
    assert.equal($('archiveDetailModal').dataset.themeIntro,'true');   // 목차 화면: PDF 저장·닫기 줄 숨김
    assert.match(fs.readFileSync('assets/brand-2026/refine.css','utf8'),/data-theme-intro="true"\] \.reading-modal-actions \{ display:none/);
    $('archiveModalBody').querySelector('button.reading-primary').onclick();
    assert.equal($('archiveDetailModal').dataset.themeIntro,undefined);
    assert.match($('archiveModalBody').textContent,/본문 시작/);
    assert.ok(hidden('themeIntroModal'));
    vm.runInContext('serverUnlockedReports=[]',ctx);

    // 나의 사주: 용어, 풀이 근거 ▼▲, 평생운세 번호 목차, 정보 수정 버튼 상자
    assert.match($('saju-basic').textContent,/나의 원국\(原局\)과 오행/);
    assert.doesNotMatch($('saju-basic').textContent,/여덟 글자/);
    assert.ok(doc.querySelector('#sajuEvidence .pc-basis > summary .fold-caret'));
    assert.ok(doc.querySelector('.reading-profile .reading-edit-btn'));
    const nums=[...doc.querySelectorAll('#daewoonTeaserBox .toc-num')].map(e=>e.textContent);
    assert.deepEqual(nums,['01','02','03','04','05','06']);
    const css=fs.readFileSync('assets/brand-2026/refine.css','utf8');
    assert.match(css,/details\[open\] > summary > \.fold-caret/);
    assert.match(css,/\[data-current-cycle="true"\][\s\S]{0,120}border:0!important/);
    process.exit(0);
})().catch(e=>{console.error(e);process.exit(1)});
