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
  window.renderLuckyItemArt = name => {
    const label = document.getElementById('resItem');
    document.getElementById('luckyItemArt')?.remove();
    if (!label || !name) return;
    // A small diagram of the named object, not a product photograph.
    const color = /베이지/.test(name) ? '#d9c4a1' : /붉|레드/.test(name) ? '#bf685b' : /남색|네이비/.test(name) ? '#465770' : /블랙|검정/.test(name) ? '#45504d' : '#bbc7c3';
    let shape;
    if (/키\s*케이스/.test(name)) shape='<rect x="29" y="25" width="42" height="51" rx="10"/><path d="M42 25v-8a8 8 0 0 1 16 0v8M37 35h26M50 42v20m0-8h8m-8 8h6" fill="none"/><circle cx="50" cy="39" r="4" fill="#fff"/>';
    else if (/지갑|카드\s*케이스/.test(name)) shape='<rect x="16" y="25" width="68" height="48" rx="8"/><path d="M22 34h56M65 43h19v20H65z" fill="none"/><circle cx="73" cy="53" r="2" fill="#fff"/>';
    else if (/시계/.test(name)) shape='<rect x="39" y="5" width="22" height="80" rx="8"/><circle cx="50" cy="45" r="22" fill="#fff"/><path d="M50 30v15l10 6" fill="none"/>';
    else if (/파우치/.test(name)) shape='<path d="M22 29h56l5 43H17z"/><path d="M23 35h53m-5-7v12" fill="none"/>';
    else return; // Unknown objects retain the accurate text label.
    const box = document.createElement('div');box.id='luckyItemArt';
    box.innerHTML = `<svg class="lucky-item-art" viewBox="0 0 100 90" aria-hidden="true"><ellipse cx="50" cy="80" rx="31" ry="4" fill="#edf0ea"/><g fill="${color}" stroke="#59675e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${shape}</g></svg>`;
    label.after(box);
  };
})();
