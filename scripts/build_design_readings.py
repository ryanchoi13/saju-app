"""Refresh fictional design-preview readings using the production generators.

Run from repo root with backend on PYTHONPATH. No account or payment writes.
"""
from datetime import date, time
from pathlib import Path
import json
import re
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import build_lifetime_overall_report, build_annual_overall_report

core = calculate_myeongri_core(BirthInput(name='지우', gender='female', birth_date=date(1992, 5, 16), birth_time=time(8)), target_date=date(2026, 10, 4))
reports = []
for key, generated in [('daewoon', build_lifetime_overall_report(core, '지우')), ('sinnian', build_annual_overall_report(core, '지우', 2026))]:
    item = dict(report_key=key, report_title='[예시] ' + generated['title'], report_content=generated['content'], narrative_version=generated['narrative_version'], created_at='디자인 비교용')
    if key == 'sinnian':
        item['report_year'] = 2026
    reports.append(item)
output = Path('assets/design-sample.js')
source = output.read_text(encoding='utf-8')
replacement = '    serverUnlockedReports=' + json.dumps(reports, ensure_ascii=False, separators=(',', ':')) + ';'
source, count = re.subn(r'^    serverUnlockedReports=.*$', lambda _: replacement, source, flags=re.MULTILINE)
assert count == 1, 'Expected one fictional saved-reading assignment'
output.write_text(source, encoding='utf-8')
print(f'{len(reports)} fictional readings refreshed in {output}')
