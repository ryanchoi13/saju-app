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
  const ITEM_ICONS = [
    [/키\s*케이스/, '<rect x="6" y="7" width="12" height="14" rx="3"/><path d="M10 7V5a2 2 0 0 1 4 0v2M12 12v5M12 15h2"/>'],
    [/카드\s*케이스|카드지갑|지갑/, '<rect x="3" y="6" width="18" height="13" rx="2.5"/><path d="M3 10h18M15 14h3"/>'],
    [/메모패드/, '<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4M9 11h7M9 14h7M9 17h4"/>'],
    [/펜/, '<path d="M15.5 4.5l4 4L9 19l-5 1 1-5z"/><path d="M13.5 6.5l4 4"/>'],
    [/메모장|스케치\s*노트|노트/, '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M8 2.5v3M12 2.5v3M16 2.5v3M8.5 10h7M8.5 13.5h7"/>'],
    [/파우치/, '<path d="M4 9h16l-1.5 10.5a1.5 1.5 0 0 1-1.5 1.5H7a1.5 1.5 0 0 1-1.5-1.5z"/><path d="M4 9a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2M15 7v4"/>'],
    [/시계/, '<circle cx="12" cy="12" r="6"/><path d="M9 6.5L9.5 2h5l.5 4.5M9 17.5L9.5 22h5l.5-4.5M12 9.5V12l1.8 1.2"/>'],
    [/텀블러/, '<path d="M7 7h10l-1.3 13a1.5 1.5 0 0 1-1.5 1.3H9.8a1.5 1.5 0 0 1-1.5-1.3z"/><path d="M6.5 7V5.5A1.5 1.5 0 0 1 8 4h8a1.5 1.5 0 0 1 1.5 1.5V7M7.6 12h8.8"/>'],
    [/머그/, '<path d="M5 6h11v10a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4z"/><path d="M16 9h1.5a2.5 2.5 0 0 1 0 5H16"/>'],
    [/물병/, '<path d="M10 2.5h4V5h-4z"/><path d="M9 5h6v2.5l1.5 2V20a1.5 1.5 0 0 1-1.5 1.5H9A1.5 1.5 0 0 1 7.5 20V9.5L9 7.5z"/><path d="M7.5 13h9"/>'],
    [/키링/, '<circle cx="8" cy="8" r="4.5"/><path d="M11.2 11.2L19 19M15.5 15.5l2-2M17.5 17.5l1.5-1.5"/>'],
    [/크로스백|가방/, '<path d="M8 10V7a4 4 0 0 1 8 0v3"/><rect x="4.5" y="10" width="15" height="10" rx="2.5"/><path d="M4.5 14h15"/>'],
    [/보조배터리|배터리/, '<rect x="7" y="3" width="10" height="18" rx="2.5"/><path d="M12.8 8l-2.3 4h3l-2.3 4"/>'],
  ];
  const ITEM_TINT = [[/베이지/, '#C9A97A'], [/붉|레드/, '#A9472F'], [/남색|네이비/, '#2C4762'], [/초록|그린|나무/, '#4F6B4C'], [/메탈|스테인리스|실버|보조배터리/, '#8A8F94'], [/도자기/, '#93702F']];
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
})();
