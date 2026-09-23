// View-only partition of the purchased document. PDF always uses its saved source.
window.setupAnnualReader = function(body, navigation) {
    const source = body.querySelector('.annual-reading');
    const cards = source ? [...source.querySelectorAll('[data-report-month]')] : [];
    if (!cards.length) return false; // Older documents remain readable in full.
    const yearPanel = document.createElement('section');
    yearPanel.id = 'annualYearPanel';
    const monthPanel = document.createElement('section');
    monthPanel.id = 'annualMonthPanel';
    const yearCopy = source.cloneNode(true);
    yearCopy.querySelectorAll('[data-report-month]').forEach(el => el.remove());
    const monthHeading = [...yearCopy.querySelectorAll('h3')].find(el => el.textContent.trim() === '12개월 흐름');
    if (monthHeading?.nextElementSibling?.classList.contains('annual-note')) monthHeading.nextElementSibling.remove();
    monthHeading?.remove();
    yearPanel.append(yearCopy);
    const choices = document.createElement('div');
    choices.className = 'annual-reader-months';
    choices.setAttribute('role', 'group');
    choices.setAttribute('aria-label', '월 선택');
    const monthBody = document.createElement('div');
    monthBody.className = 'annual-selected-month';
    monthBody.setAttribute('aria-live', 'polite');
    monthPanel.append(choices, monthBody);
    body.replaceChildren(yearPanel, monthPanel);
    const monthButtons = cards.map(card => {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = `${card.dataset.reportMonth}월`;
        button.onclick = () => {
            [...choices.children].forEach(el => el.setAttribute('aria-pressed', String(el === button)));
            monthBody.replaceChildren(card.cloneNode(true));
        };
        choices.append(button);
        return button;
    });
    const today = new Intl.DateTimeFormat('en-US', {timeZone:'Asia/Seoul', year:'numeric',month:'numeric'}).formatToParts(new Date());
    const year = Number(today.find(p => p.type === 'year').value);
    const month = Number(today.find(p => p.type === 'month').value);
    const selected = Number(source.dataset.reportYear) === year ? cards.findIndex(c => Number(c.dataset.reportMonth) === month) : 0;
    monthButtons[Math.max(0, selected)].click();
    navigation.replaceChildren();
    const panels = [yearPanel, monthPanel];
    const scrollPositions = [0, 0];
    let active = 0;
    ['올해 운세', '월별 운세'].forEach((label, i) => {
        const button = document.createElement('button');
        button.type = 'button'; button.textContent = label;
        button.id = `annualReaderTab${i}`;
        button.setAttribute('role','tab');
        button.setAttribute('aria-controls',panels[i].id);
        panels[i].setAttribute('role','tabpanel');
        panels[i].setAttribute('aria-labelledby',button.id);
        button.onclick = () => {
            scrollPositions[active] = body.scrollTop;
            active = i;
            panels.forEach((panel,j) => panel.hidden = i !== j);
            [...navigation.children].forEach((tab,j) => {
                tab.setAttribute('aria-selected',String(i === j)); tab.tabIndex = i === j ? 0 : -1;
            });
            body.scrollTop = scrollPositions[i];
        };
        button.onkeydown = event => {
            if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
            event.preventDefault();
            const next = event.key === 'Home' ? 0 : event.key === 'End' ? 1 : 1-i;
            navigation.children[next].click(); navigation.children[next].focus();
        };
        navigation.append(button);
    });
    navigation.setAttribute('role','tablist');
    navigation.firstElementChild.click();
    return true;
};

window.ANNUAL_PRINT_STYLE = `
    @page { size:A4; margin:18mm 16mm; }
    body { font-family:sans-serif; font-size:11pt; line-height:1.8; color:#182B3A; }
    h2,h3,h4,h5 { break-after:avoid; page-break-after:avoid; }
    h3 { font-size:15pt; margin-top:24pt; }
    h4 { font-size:13pt; }
    h5 { font-size:11pt; }
    p { orphans:3; widows:3; margin:0 0 10pt; }
    .annual-month { break-before:page; page-break-before:always; border:0!important; }
    .annual-kind { display:none; }
    .annual-note,.annual-evidence { font-size:9pt; color:#526378; }
    button { display:none; }
`;
