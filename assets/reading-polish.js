(() => {
  window.polishReading = body => {
    // Number major sections only, leaving nested periods and monthly labels intact.
    const headings = [...body.querySelectorAll('h3')].filter(h => !h.closest('details'));
    headings.forEach((heading, index) => {
      if (heading.classList.contains('reading-section-heading')) return;
      const original = heading.textContent.trim();
      heading.dataset.tocLabel = heading.dataset.tocLabel || `${String(index + 1).padStart(2, '0')} ${original.split(' · ')[0]}`;
      const number = document.createElement('span');
      number.className = 'reading-section-number';
      number.textContent = String(index + 1).padStart(2, '0');
      const copy = document.createElement('span');
      copy.className = 'reading-heading-copy';
      // Preserve existing semantic spans used by the annual reader.
      if (heading.children.length) copy.append(...heading.childNodes);
      else {
        const match = original.match(/^(직업[·ㆍ\s]*사업운|재물운|애정운|학업[·ㆍ\s]*시험운)\s*[·:—–-]?\s+(.+)$/);
        if (match) {
          const topic = document.createElement('span');
          topic.className = 'reading-heading-topic'; topic.textContent = match[1];
          copy.append(topic, document.createTextNode(match[2]));
        } else copy.textContent = original.replace(/^\d+[.)]\s*/, '');
      }
      heading.classList.add('reading-section-heading');
      heading.replaceChildren(number, copy);
    });
  };
  // 오늘의 행운: 아이템·숫자·방위 세 칸이 같은 무게로 보이도록 아이템은 24px 선 아이콘, 방위는 화살표.
  // 브랜드 기준(24px 선 아이콘)과 같은 굵기·모서리. 그림 파일 없이 코드로 그린다.
  // 2026-11-12: 행운 아이템 40종(backend lucky_items.CATALOG). 더 구체적인 이름을 먼저 둔다(명함지갑 → 지갑, 도시락 가방 → 가방).
  const ITEM_ICONS = [
    [/키\s*케이스/, '<rect x="6" y="7" width="12" height="14" rx="3"/><path d="M10 7V5a2 2 0 0 1 4 0v2M12 12v5M12 15h2"/>'],
    [/명함/, '<rect x="3" y="7" width="18" height="12" rx="2"/><path d="M6 7V5h12v2M7 12h6M7 15h4"/>'],
    [/동전지갑/, '<path d="M5 10h14v8a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2z"/><path d="M5 10a7 7 0 0 1 14 0M10.5 6.5l-1-2M13.5 6.5l1-2"/>'],
    [/머니클립/, '<rect x="4" y="7" width="16" height="10" rx="1.5"/><path d="M14 4v11a2 2 0 0 0 4 0V4"/>'],
    [/카드\s*케이스|카드지갑|지갑/, '<rect x="3" y="6" width="18" height="13" rx="2.5"/><path d="M3 10h18M15 14h3"/>'],
    [/이어폰/, '<path d="M8 4a3 3 0 0 0-3 3v2a3 3 0 0 0 3 3h1V4zM9 12v7"/><path d="M16 4a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3h-1V4zM15 12v7"/>'],
    [/도시락/, '<path d="M5 9h14v11H5z"/><path d="M9 9V6.5a3 3 0 0 1 6 0V9M5 13h14"/>'],
    [/에코백/, '<path d="M5 9h14l-1 12H6z"/><path d="M9 9V5.5a3 3 0 0 1 6 0V9"/>'],
    [/백팩/, '<rect x="5" y="7" width="14" height="14" rx="3"/><path d="M9 7V5.5a3 3 0 0 1 6 0V7M8 14h8v4H8z"/>'],
    [/크로스백|슬링백|가방/, '<path d="M8 10V7a4 4 0 0 1 8 0v3"/><rect x="4.5" y="10" width="15" height="10" rx="2.5"/><path d="M4.5 14h15"/>'],
    [/메모패드/, '<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4M9 11h7M9 14h7M9 17h4"/>'],
    [/다이어리|플래너/, '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 3v18M15 11h4"/>'],
    [/연필|샤프/, '<path d="M16 3l5 5L9 20H4v-5z"/><path d="M14 5l5 5M4 15l5 5"/>'],
    [/펜|만년필/, '<path d="M15.5 4.5l4 4L9 19l-5 1 1-5z"/><path d="M13.5 6.5l4 4"/>'],
    [/메모장|노트/, '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M8 2.5v3M12 2.5v3M16 2.5v3M8.5 10h7M8.5 13.5h7"/>'],
    [/마스킹테이프/, '<circle cx="11" cy="12" r="7"/><circle cx="11" cy="12" r="3"/><path d="M18 12h3.5v4H17"/>'],
    [/립밤/, '<rect x="8" y="10" width="8" height="11" rx="1.5"/><path d="M9.5 10V6.5a2.5 2.5 0 0 1 5 0V10M8 14h8"/>'],
    [/손거울/, '<circle cx="12" cy="9" r="6"/><path d="M12 15v6M10 21h4M9.5 7.5l2-2"/>'],
    [/핸드크림/, '<path d="M8 3h8l-1 13H9z"/><path d="M9.5 16h5v2.5a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1zM10 7h4"/>'],
    [/파우치/, '<path d="M4 9h16l-1.5 10.5a1.5 1.5 0 0 1-1.5 1.5H7a1.5 1.5 0 0 1-1.5-1.5z"/><path d="M4 9a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2M15 7v4"/>'],
    [/시계/, '<circle cx="12" cy="12" r="6"/><path d="M9 6.5L9.5 2h5l.5 4.5M9 17.5L9.5 22h5l.5-4.5M12 9.5V12l1.8 1.2"/>'],
    [/텀블러/, '<path d="M7 7h10l-1.3 13a1.5 1.5 0 0 1-1.5 1.3H9.8a1.5 1.5 0 0 1-1.5-1.3z"/><path d="M6.5 7V5.5A1.5 1.5 0 0 1 8 4h8a1.5 1.5 0 0 1 1.5 1.5V7M7.6 12h8.8"/>'],
    [/머그/, '<path d="M5 6h11v10a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4z"/><path d="M16 9h1.5a2.5 2.5 0 0 1 0 5H16"/>'],
    [/물병/, '<path d="M10 2.5h4V5h-4z"/><path d="M9 5h6v2.5l1.5 2V20a1.5 1.5 0 0 1-1.5 1.5H9A1.5 1.5 0 0 1 7.5 20V9.5L9 7.5z"/><path d="M7.5 13h9"/>'],
    [/키링|열쇠고리/, '<circle cx="8" cy="8" r="4.5"/><path d="M11.2 11.2L19 19M15.5 15.5l2-2M17.5 17.5l1.5-1.5"/>'],
    [/보조배터리|배터리/, '<rect x="7" y="3" width="10" height="18" rx="2.5"/><path d="M12.8 8l-2.3 4h3l-2.3 4"/>'],
    [/양말/, '<path d="M8 3h6v8l3.5 3.5a3 3 0 0 1-4.2 4.2L8 13.4z"/><path d="M8 7h6"/>'],
    [/모자/, '<path d="M3 15a7 7 0 0 1 14 0z"/><path d="M17 15c2 0 4 .3 4.5 1.2.3.5-.2.8-.8.8H3v-2M10 8V6.5"/>'],
    [/헤어/, '<path d="M4 10.5c0-3 3.5-5 8-5s8 2 8 5c0 1.5-1.5 2-3 1.2-1.2-.7-3-1.2-5-1.2s-3.8.5-5 1.2c-1.5.8-3 .3-3-1.2z"/><path d="M7 12.5v5M10 11v7M14 11v7M17 12.5v5"/>'],
    [/반지/, '<circle cx="12" cy="14" r="6"/><path d="M10 8l-1.5-3h7L14 8"/>'],
    [/팔찌/, '<ellipse cx="12" cy="13" rx="8" ry="5"/><circle cx="6" cy="10" r="1.2"/><circle cx="12" cy="8" r="1.2"/><circle cx="18" cy="10" r="1.2"/>'],
    [/손수건/, '<path d="M4 4h16v16H4z"/><path d="M20 4L4 20M7 7h3M7 7v3"/>'],
    [/부채/, '<path d="M12 20L4 9a10 10 0 0 1 16 0z"/><path d="M12 20V7M12 20L8 9.5M12 20l4-10.5"/>'],
    [/선글라스/, '<circle cx="7" cy="13" r="3.5"/><circle cx="17" cy="13" r="3.5"/><path d="M10.5 13h3M3.5 13l-1-4M20.5 13l1-4"/>'],
    [/넥타이/, '<path d="M10 3h4l-1 3h-2z"/><path d="M11 6l-2.5 11L12 21l3.5-4L13 6"/>'],
    [/벨트/, '<path d="M2 10h20v4H2z"/><rect x="8" y="8" width="6" height="8" rx="1"/><path d="M11 12h3"/>'],
    [/안경\s*케이스/, '<rect x="3" y="8" width="18" height="8" rx="4"/><path d="M3.5 12h17M10.5 12v1.5h3V12"/>'],
    [/우산/, '<path d="M3 12a9 9 0 0 1 18 0z"/><path d="M12 3V2M12 12v6.5a2 2 0 0 1-4 0"/>'],
    [/장갑/, '<path d="M8 21v-4.5L6 12V7a3 3 0 0 1 6 0v3l2.2-2a1.6 1.6 0 0 1 2.3 2.2L14 14.5V21z"/><path d="M8 17.5h6"/>'],
    [/책갈피/, '<path d="M7 3h10v18l-5-4-5 4z"/>'],
    [/안대/, '<path d="M3 10c3-3 15-3 18 0v2c-3 4-15 4-18 0z"/><path d="M3 11H1.5M21 11h1.5M8 12c1 1 2 1 3 0M13 12c1 1 2 1 3 0"/>'],
    [/스카프|목도리/, '<path d="M6 5c3 2 9 2 12 0v4c-3 2-9 2-12 0z"/><path d="M8.5 10.5L7.5 20l3-1 .8-8M14 11l1 9-3-1"/>'],
    [/담요/, '<rect x="4" y="5" width="16" height="14" rx="1.5"/><path d="M4 10h16M4 14h16M10 5v14M14 5v14"/>'],
  ];
  // 아이템 이름의 재질·색 말 → 작은 색 점(오행과 같은 계열). 앞에 있는 말이 먼저 잡힌다.
  const ITEM_TINT = [
    [/버건디/, '#7E2E36'], [/코럴/, '#D9765F'], [/로즈골드/, '#C98B79'], [/붉|레드/, '#A9472F'],
    [/남색|네이비|물결/, '#2C4762'], [/블랙/, '#2B2B2E'], [/유리/, '#8FB3C2'],
    [/올리브|초록|그린|나무|우드|원목|대나무|리넨|잎/, '#4F6B4C'],
    [/카멜/, '#B5864F'], [/베이지|한지/, '#C9A97A'], [/브라운|가죽/, '#8A5A3B'], [/크라프트/, '#B08A5E'], [/도자기|세라믹/, '#93702F'],
    [/메탈|스테인리스|실버|은박|그레이/, '#8A8F94'], [/흰|화이트|아이보리/, '#CFC8B8'],
  ];
  const svg = inner => `<svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;
  window.renderLuckyItemArt = name => {
    const slot = document.getElementById('luckyItemIcon');
    if (!slot) return;
    const found = ITEM_ICONS.find(([re]) => re.test(name || ''));
    const shape = found ? found[1] : '<path d="M12 3l2.2 5.6L20 9.3l-4.4 3.8 1.3 5.9L12 16l-4.9 3 1.3-5.9L4 9.3l5.8-.7z"/>';
    const tint = (ITEM_TINT.find(([re]) => re.test(name || '')) || [])[1];
    slot.innerHTML = svg(shape) + (tint ? `<i class="dh-luck-tint" style="background:${tint}"></i>` : '');
  };
  // 방위: 위가 북. '정서쪽 (백호 방위)'·'남동쪽'·'북쪽' 등 앞 단어만 읽는다.
  const DIRECTION_DEG = {'북':0,'북동':45,'동북':45,'동':90,'남동':135,'동남':135,'남':180,'남서':225,'서남':225,'서':270,'북서':315,'서북':315};
  window.renderLuckyDirection = text => {
    const slot = document.getElementById('luckyDirectionIcon');
    if (!slot) return;
    const raw = String(text || '').trim();
    if (/^중앙/.test(raw)) { slot.innerHTML = svg('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.6" fill="currentColor" stroke="none"/>'); return; }
    const key = raw.split(/[\s(·]/)[0].replace(/^정/, '').replace(/쪽$/, '');
    const deg = DIRECTION_DEG[key];
    if (deg === undefined) { slot.innerHTML = ''; return; }
    slot.innerHTML = svg(`<circle cx="12" cy="12" r="9"/><g transform="rotate(${deg} 12 12)"><path d="M12 6.5l2.6 6.5H9.4z" fill="currentColor" stroke="none"/><path d="M12 13v4.5"/></g>`);
  };

  // 지금 절기 카드: 서버가 한국 날짜로 계산한 절기를 받아 그림·한 줄·다음 절기를 채운다. 실패하면 카드는 숨긴 채로 둔다.
  const renderSeason = async () => {
    const card = document.getElementById('seasonCard');
    if (!card) return;
    try {
      const res = await fetch('/api/season');
      if (!res.ok) return;
      const s = await res.json();
      const [, m, d] = s.next_date.split('-').map(Number);
      document.getElementById('seasonArt').src = s.art;
      // 11/13 정오님: 절기를 모르면 '입동'이 무엇인지, '소설'이 책인지 알 수 없다 → 24절기 이름표 + 한자 + "다음 절기"
      const withHanja = (name, hanja) => hanja ? `${name}(${hanja})` : name;
      const kicker = document.getElementById('seasonKicker');
      if (kicker) kicker.textContent = s.order_label ? `24절기 · ${s.order_label}` : '24절기';
      document.getElementById('seasonTitle').textContent = `${s.is_today ? '오늘은' : '지금은'} ${withHanja(s.name, s.hanja)}`;
      document.getElementById('seasonLine').textContent = s.line;
      // 줄이 넘치면 가운뎃점에서 끊기게 두 덩어리로 넣는다("…9일 / 뒤"처럼 한 글자만 떨어지지 않게)
      const next = document.getElementById('seasonNext');
      const part = (text) => { const el = document.createElement('span'); el.style.whiteSpace = 'nowrap'; el.textContent = text; return el; };
      next.replaceChildren(
        part(`다음은 ${withHanja(s.next_name, s.next_hanja)}`), ' · ',
        part(s.days_to_next === 1 ? `내일(${m}월 ${d}일)` : `${m}월 ${d}일, ${s.days_to_next}일 뒤`));
      card.classList.toggle('is-today', !!s.is_today);
      card.hidden = false;
    } catch (_) { /* 절기 카드는 없어도 되는 칸 */ }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderSeason);
  else renderSeason();
})();
