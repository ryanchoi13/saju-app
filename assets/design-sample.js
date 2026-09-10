// Public fictional content for comparing the two designs. No login, API, billing or persistent writes.
(() => {
  if (!window.DALHA_DESIGN_SAMPLE) return;
  const $ = id => document.getElementById(id);
  const text = (id,value) => { if ($(id)) $(id).textContent = value; };
  const intro = '<div style="background:#ECFDF5;border-left:4px solid #10B981;padding:16px;border-radius:14px;margin-bottom:16px;"><h4 style="color:#065F46;font-size:16px;">내 속도를 지키며, 선택의 기준을 세우는 시간</h4><p style="color:#047857;font-size:13px;">여러 가지를 한꺼번에 바꾸기보다 지금 가장 중요한 일 하나를 정해 보세요. 작은 선택을 이어가는 과정에서 나에게 맞는 방향이 더 선명해질 수 있습니다.</p></div>';
  const paragraph = '<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:13px;padding:16px;margin:16px 0;"><h5 style="font-size:14px;color:#334155;">일과 생활에서 살펴볼 점</h5><p style="font-size:13px;color:#475569;">일정을 정리할 때는 꼭 해야 할 일과 조정할 수 있는 일을 나누어 보세요. 타인의 기대에 맞추기 전에 나에게 필요한 시간과 여유도 함께 생각해 보는 것이 좋겠습니다.</p><p style="font-size:12px;color:#64748B;">오늘의 작은 실천 · 미루던 일 하나를 정하고, 시작할 시간을 달력에 적어 보세요.</p></div>';
  const report = (key,title,body) => ({report_key:key,report_title:`[예시] ${title}`,report_content:body,created_at:'디자인 비교용'});
  function showExample(title) {
    serverUnlockedReports.push(report('design-example',title,intro+paragraph+paragraph));
    document.querySelectorAll('.modal-bg:not(#archiveDetailModal)').forEach(el => el.classList.add('hidden'));
    openReadingReport(serverUnlockedReports.length-1);
  }
  let noticeTimer;
  function notice() {
    let box = $('designSampleNotice');
    if (!box) { box=document.createElement('div'); box.id='designSampleNotice'; box.className='design-notice'; box.setAttribute('role','status'); document.body.append(box); }
    box.textContent='예시 화면입니다. 실제 저장과 결제는 ‘내 정보로 보기’에서 이용해 주세요.';
    box.hidden=false; clearTimeout(noticeTimer); noticeTimer=setTimeout(()=>box.hidden=true,4000);
  }
  // Stop only state-changing actions; navigation, forms, tabs and dialog opening use the real UI.
  document.addEventListener('click',event => {
    const target=event.target.closest('[onclick]');
    if (!target) return;
    const action=target.getAttribute('onclick');
    if (/^(confirmUnlockThemeOnServer|confirmUnlockGunghapOnServer)/.test(action)) {
      event.preventDefault(); event.stopImmediatePropagation();
      showExample(action.includes('Gunghap')?'두 사람의 궁합':$('modalThemeTitle').textContent); return;
    }
    if (/^handleUnlockReportOnServer/.test(action)) {
      const key=action.match(/'([^']+)'/)?.[1];
      if (latestOwnedReportIndex(key)>=0) return;
      event.preventDefault(); event.stopImmediatePropagation(); showExample('주제별 풀이'); return;
    }
    if (/^openZodiacModal/.test(action)) {
      event.preventDefault(); event.stopImmediatePropagation();
      text('zodiacModalName','오늘의 운세 · 예시'); text('zodiacModalScore','82점');
      text('zodiacModalTitle','작은 여유가 시야를 넓혀 주는 날');
      text('zodiacModalOverview','바쁜 일정 사이 잠시 숨을 고르고 주변의 이야기를 들어 보세요. 익숙한 일에서도 새로운 관점을 발견할 수 있습니다.');
      $('zodiacYearTipsBox').innerHTML=paragraph; text('zodiacExtraInfo','추천 색상 · 네이비');
      $('zodiacModal').classList.remove('hidden'); return;
    }
    if (/^(processPgPaymentOnServer|submitSajuRegistration|saveWardrobeItemToServer|deleteWardrobe|logoutKakao|loginWithKakao|shareZodiac|printReading|reopenSajuEditForm)/.test(action)) {
      event.preventDefault(); event.stopImmediatePropagation(); notice(); return;
    }
    if (/^(handleTarotDraw|drawTarot|selectTarot|confirmTarot|chooseAnotherTarot)/.test(action)) {
      event.preventDefault(); event.stopImmediatePropagation();
      renderTarotReading({cost:0,card:{name:'마법사 · 예시',description:'탁자 위의 도구와 하늘을 향한 손은 가능성을 행동으로 옮기는 힘을 상징합니다.',symbolism:'시작 · 집중 · 실행',reading_male:'준비해 둔 생각을 작은 행동으로 옮겨 보세요.',reading_female:'준비해 둔 생각을 작은 행동으로 옮겨 보세요.',action_guide:'오늘 끝낼 수 있는 한 가지부터 시작해 보세요.'}});
      return;
    }
  },true);
  window.startDalhaDesignSample = () => {
    currentUserId=null; currentUserName='지우'; currentCoin=550; selectedGender='female';
    const color=(name,hex)=>({name,name_ko:name,standard_color:name,hex});
    const item=(label,color_name,hex,sprite)=>({label,color_name,hex,sprite});
    const palette={tpo:'casual',gender:'female',style_mood:'casual',mood_tag:'캐주얼',top:color('아이보리','#F2EBDC'),bottom:color('네이비','#263C55'),mood_desc:'지우님을 위해 두 가지 코디를 제안드리니, 오늘의 코디에 참고해 보세요.',looks:[
      {title:'차분한 데님 코디',items:[item('티셔츠','아이보리','#F2EBDC',11),item('데님 팬츠','블루','#466989',9),item('로퍼','브라운','#745442',15)]},
      {title:'편안한 셔츠 코디',items:[item('블라우스','스카이블루','#B9CDDC',10),item('치노 팬츠','베이지','#C8B696',9),item('로퍼','브라운','#745442',15)]}
    ]};
    const business={...palette,tpo:'business_casual',style_mood:'business_casual',mood_tag:'비즈니스 캐주얼',looks:[{title:'단정한 재킷과 슬랙스',items:[item('재킷','네이비','#263C55',8),item('블라우스','화이트','#F5F4EE',10),item('슬랙스','네이비','#263C55',9),item('로퍼','브라운','#745442',15)]},{title:'차분한 재킷과 팬츠',items:[item('재킷','차콜','#454B50',8),item('블라우스','아이보리','#F2EBDC',10),item('슬랙스','차콜','#454B50',9),item('로퍼','블랙','#272C31',15)]}]};
    currentTalisman={title:'결단정리부',power:'판단과 정리의 힘',desc:'차분히 판단하고 필요한 것을 정리하는 마음을 담았습니다.',talisman_type:'metal_clarity'};
    const pillar={cg:'甲',cg_elem:'wood',jj:'子',jj_elem:'water',jijanggan:[]};
    const channel={status:'안정',val:64};
    applySajuAnalysisToUI({user_name:'지우',current_age:34,birth_summary:'디자인 비교용 예시 프로필',saju_profile_detail:'같은 내용으로 글자와 화면 구성을 비교해 보세요.',biorhythm:{days_lived:12000,physical:channel,emotional:channel,intellectual:channel,overall_summary:'무리한 계획보다 익숙한 일에 집중해 보세요. 잠깐의 휴식이 생각을 정리하는 데 도움이 될 수 있습니다.'},
      saju_data:{singang_label:'예시',pillars_detail:{year:pillar,month:pillar,day:pillar,hour:pillar},elements:{wood:25,fire:15,earth:20,metal:15,water:25},elements_note:'디자인을 확인하기 위한 예시 수치입니다.',daeyun_phase:{name:'청년기',cycle:'대운 3~4',age_range:'예시'}},
      daily_fortune:{date:'2026-09-10',title:'나의 속도로, 한 걸음 더',advice:'익숙한 하루에도 작은 변화는 시작됩니다. 오늘은 가장 마음이 가는 일 하나에 집중해 보세요.',score:82,mode_badge:'차분한 흐름',time_flow:{morning:'중요한 일 하나를 정하며 시작해 보세요.',afternoon:'함께하는 사람의 이야기에 귀 기울여 보세요.',evening:'오늘 잘한 일을 돌아보고 편안하게 마무리하세요.'},lucky_item:'실버 시계',lucky_number:'3, 8',lucky_direction:'동쪽',unified_advice:'오늘의 작은 선택이 내일의 방향을 만듭니다. 해야 할 일 하나를 정하고, 나머지는 여유 있게 바라보세요.',talisman:currentTalisman,wada_palette:palette,style_palettes:{casual:palette,business_casual:business,business_formal:{...business,tpo:'business_formal',mood_tag:'비즈니스 포멀'}},recommended_meals:[{period:'lunch',menu:'김치찌개'},{period:'dinner',menu:'후라이드치킨'}],recommended_menu_reason:'점심에는 칼칼한 김치찌개를, 저녁에는 바삭한 후라이드치킨을 즐겨 보세요.'}
    });
    const cycles=[['18~27세',false],['28~37세',true],['38~47세',false]].map(([ages,active],i)=>`<section data-report-cycle="${i+1}" data-cycle-ages="${ages}" data-current-cycle="${active}"><h4>${ages} · ${active?'현재의 흐름':'삶의 흐름'}</h4>${paragraph}</section>`).join('');
    const months=Array.from({length:12},(_,i)=>`<section data-report-month="${i+1}"><h4>${i+1}월 · 나의 균형을 살펴보기</h4>${paragraph}</section>`).join('');
    serverUnlockedReports=[report('daewoon','나의 기질과 인생 흐름',intro+paragraph+cycles),report('sinnian','2026년 올해와 월별',`<div data-report-year="2026">${intro}${months}</div>`)];
    userWardrobeItems=[{id:'example-shirt',category:'상의',nickname:'아이보리 니트 · 예시',colors:['아이보리/크림'],materials:['니트/울']},{id:'example-pants',category:'하의',nickname:'네이비 팬츠 · 예시',colors:['네이비'],materials:['면/린넨/패브릭']}];
    updateCoinDisplay(); renderWardrobeUI(); renderServerArchive(); refreshReportEntrypoints();
    $('view-login-gate').classList.add('hidden'); $('onboardingInputView').classList.add('hidden'); $('bottomNavBar').classList.remove('hidden');
    const params=new URLSearchParams(location.search), tab=params.get('tab'), section=params.get('section');
    switchTab(['today','saju','theme','mypage'].includes(tab)?tab:'today');
    if (['basic','life','year'].includes(section)) selectSajuSection(section);
    // Keep prices visible for layout review, but make the final payment action visibly unavailable.
    $('pgPaymentButton').disabled=true; text('pgPaymentButton','예시 화면 · 결제되지 않습니다');
  };
})();
