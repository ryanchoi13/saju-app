"""Public prose, situation boundaries and folded evidence for all paid themes."""
import re
from datetime import date,time
from html.parser import HTMLParser
from unittest import TestCase
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import (build_lifetime_career_report, build_lifetime_love_report,
    build_lifetime_wealth_report, build_lifetime_health_report, build_lifetime_study_report,
    build_compatibility_report)
from app.engine.services.reading_editorial import THEME_VERSION


class VisibleText(HTMLParser):
    def __init__(self, source):
        super().__init__(); self.folded=0; self.text=[]; self.sections=[]; self.paragraphs=[]; self.headings=[]; self.tag=None; self.buffer=[]; self.open_details=0
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        attr=dict(attrs)
        if tag=='details':
            self.folded+=1
            self.open_details += int('open' in attr)
        if self.folded: return
        if 'data-theme-section' in attr: self.sections.append(attr['data-theme-section'])
        if tag in {'p','h3'}: self.tag=tag; self.buffer=[]
    def handle_endtag(self, tag):
        if tag=='details': self.folded-=1; return
        if self.folded: return
        if tag==self.tag:
            (self.paragraphs if tag=='p' else self.headings).append(''.join(self.buffer)); self.tag=None
    def handle_data(self, data):
        if not self.folded:
            self.text.append(data)
            if self.tag: self.buffer.append(data)


class ThemePresentReaderTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core=calculate_myeongri_core(BirthInput(name='예시',gender='female',birth_date=date(1992,5,16),birth_time=time(8)),target_date=date(2026,10,1))
        cls.partner=calculate_myeongri_core(BirthInput(name='상대',gender='male',birth_date=date(1990,10,4),time_unknown=True),target_date=date(2026,10,1))
        cls.reports={}
        for mode in ['직장인','취업/이직','사업가','창업']:
            cls.reports['business:'+mode]=build_lifetime_career_report(cls.core,'예시',mode)
        for mode in ['솔로','썸/짝사랑','연애중','기혼']:
            cls.reports['love:'+mode]=build_lifetime_love_report(cls.core,'예시',mode)
        for key,builder in [('wealth',build_lifetime_wealth_report),('health',build_lifetime_health_report),('study',build_lifetime_study_report)]:
            cls.reports[key]=builder(cls.core,'예시')
        for relation in ['연인 / 결혼','친구 / 지인','동업 / 비즈니스']:
            cls.reports['gunghap:'+relation]=build_compatibility_report(cls.core,cls.partner,'예시','상대',relation)

    def test_every_situation_has_sustained_plain_reading_before_collapsed_references(self):
        for key,report in self.reports.items():
            with self.subTest(key=key):
                view=VisibleText(report['content']); text=''.join(view.text)
                self.assertEqual(report['narrative_version'],THEME_VERSION)
                self.assertEqual(view.sections,['current','nature','practice'])
                self.assertGreater(len(text),2500)
                self.assertEqual(view.open_details,0)
                self.assertEqual(len(view.paragraphs),len(set(view.paragraphs)))
                self.assertEqual(len(view.headings),len(set(view.headings)))
                self.assertNotRegex(text,r'관계 후보|십성|원국|천간합|천간극|\d+~\d+세|[甲乙丙丁戊己庚辛壬癸]')
                if not key.startswith('gunghap'):
                    self.assertEqual(report['content'].count('data-report-cycle='),9)
                self.assertIn('다시 열어도 저장된 내용은 유지됩니다',text)

    def test_selected_situations_do_not_mix_dating_or_business_contexts(self):
        single=''.join(VisibleText(self.reports['love:솔로']['content']).text)
        married=''.join(VisibleText(self.reports['love:기혼']['content']).text)
        self.assertNotIn('집안일, 가족 일정',single)
        self.assertIn('집안일, 가족 일정',married)
        for mode in ['친구 / 지인','동업 / 비즈니스']:
            text=''.join(VisibleText(self.reports['gunghap:'+mode]['content']).text)
            self.assertNotIn('사랑이 깊어지는 방식',text)
            self.assertNotIn('결혼하면 어떤가',text)
        self.assertIn('일을 맡는 사람과 결정하는 사람',self.reports['gunghap:동업 / 비즈니스']['content'])
        self.assertNotIn('일을 맡는 사람과 결정하는 사람',self.reports['gunghap:친구 / 지인']['content'])

    def test_core_based_text_is_repeatable_and_names_are_never_executable(self):
        a=build_lifetime_love_report(self.core,'<img src=x>','솔로')
        self.assertEqual(a,build_lifetime_love_report(self.core,'<img src=x>','솔로'))
        self.assertNotIn('<img',a['content']); self.assertIn('&lt;img',a['content'])
        other=build_lifetime_love_report(self.partner,'<img src=x>','솔로')
        first=lambda r: VisibleText(r['content']).paragraphs[0]
        self.assertNotEqual(first(a),first(other))
