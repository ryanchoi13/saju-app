const {JSDOM}=require('jsdom');
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('index.html','utf8'),{url:'https://dalha.example',runScripts:'outside-only'});
const w=dom.window, ctx=dom.getInternalVMContext();
w.scrollTo=()=>{}; w.alert=()=>{};
for(const s of w.document.querySelectorAll('script:not([src])')) vm.runInContext(s.textContent,ctx);
const run=code=>vm.runInContext(code,ctx);
const $=id=>w.document.getElementById(id);
(async()=>{
    run('currentUserId="user_owner"; currentCoin=550; serverUnlockedReports=[{report_key:"daewoon"}];');
    // 마이페이지: 로그아웃은 사주 정보 카드 밖의 '계정' 카드에 있고 탈퇴 버튼과 함께 있다.
    const buttons=[...w.document.querySelectorAll('#view-mypage button')].map(b=>b.textContent.trim());
    assert.ok(buttons.includes('회원 탈퇴') && buttons.includes('로그아웃') && buttons.includes('정보 수정'));
    const profileCard=[...w.document.querySelectorAll('#view-mypage .card')].find(c=>c.textContent.includes('사주 정보 수정'));
    assert.ok(!profileCard.textContent.includes('로그아웃'));

    // 신청 화면: 잔여 복채·감명서 건수 표시, 확인 체크 전에는 신청 불가.
    w.openWithdrawDialog();
    assert.ok(!$('withdrawModal').classList.contains('hidden'));
    assert.match($('withdrawBody').textContent,/남은 복채 550/);
    assert.match($('withdrawBody').textContent,/감명서 1건/);
    assert.equal($('withdrawConfirm').disabled,true);
    let requests=[];
    w.fetch=async(url,opts)=>{requests.push([url,JSON.parse(opts.body)]);return {ok:true,json:async()=>({})};};
    await w.submitWithdrawDialog();
    assert.equal(requests.length,0);
    $('withdrawAgree').checked=true; w.syncWithdrawButton();
    assert.equal($('withdrawConfirm').disabled,false);

    // 서버 실패: 오류 문구만 보이고 계정은 그대로, 버튼은 다시 눌러볼 수 있다.
    w.fetch=async()=>({ok:false,json:async()=>({})});
    await w.submitWithdrawDialog();
    assert.ok(!$('withdrawError').classList.contains('hidden'));
    assert.equal($('withdrawConfirm').disabled,false);
    w.closeWithdrawDialog();
    assert.ok($('withdrawModal').classList.contains('hidden'));

    // 탈퇴 신청 중인 계정으로 로그인하면 삭제일과 취소 버튼이 보이고, 취소는 취소 API를 부른다.
    const deleteAt=Math.floor(Date.parse('2026-11-23T03:00:00Z')/1000);
    w.offerWithdrawalCancel({withdrawal_pending:{requested_at:deleteAt-7*86400,delete_at:deleteAt}});
    assert.match($('withdrawTitle').textContent,/탈퇴를 신청한 계정/);
    assert.match($('withdrawBody').textContent,/11월 23일/);
    assert.ok($('withdrawAgreeRow').classList.contains('hidden'));
    assert.equal($('withdrawConfirm').textContent,'탈퇴 취소');
    requests=[];
    w.fetch=async(url,opts)=>{requests.push([url,JSON.parse(opts.body)]);return {ok:true,json:async()=>({})};};
    await w.submitWithdrawDialog();
    assert.deepEqual(requests,[['/api/user/withdraw/cancel',{user_id:'user_owner',confirm:true}]]);
    assert.ok($('withdrawModal').classList.contains('hidden'));

    // 신청 중이 아니면 아무것도 띄우지 않는다.
    w.offerWithdrawalCancel({withdrawal_pending:null});
    assert.ok($('withdrawModal').classList.contains('hidden'));
    console.log('withdraw dialog ok');process.exit(0);
})().catch(e=>{console.error(e);process.exit(1)});
