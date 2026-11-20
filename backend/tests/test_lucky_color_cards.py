"""오늘의 행운 색 두 개(2026-10-29 정오님: 코디 지식서가 갖춰질 때까지 코디 대신 이것만 보여 준다)."""
from main import get_saju_pillars_and_analysis


def test_two_lucky_colors_match_the_daily_palette():
    daily = get_saju_pillars_and_analysis('검증', 'male', 1978, 3, 13, 'solar', 5)['daily_fortune']
    cards = daily['lucky_color_cards']
    assert len(cards['colors']) == 2
    assert [c['hex'].upper() for c in cards['colors']] == [daily['daily_palette'][k]['hex'].upper() for k in ('top', 'bottom')]
    assert [c['name'] for c in cards['colors']] == daily['lucky_colors']
    for c in cards['colors']:
        assert c['text'].endswith('기운')
        assert '입' not in c['text']  # 옷차림을 지시하지 않는다
    if daily['outfit'].get('tongguan'):
        assert cards['caption']
    else:
        # 통관 날이 아니면 사유는 비거나, 어제와 같은 칸의 오행이 같을 때 붙는 연결 문구뿐이다(2026-11-20).
        from fashion_v2.daily_colors import CONTINUATION_TEMPLATES
        assert cards['caption'] == '' or any(
            cards['caption'] in (tpl.format(names=n) for n in ('목(木)','화(火)','토(土)','금(金)','수(水)')
                                 + tuple(f'{a}·{b}' for a in ('목(木)','화(火)','토(土)','금(金)','수(水)')
                                         for b in ('목(木)','화(火)','토(土)','금(金)','수(水)') if a != b))
            for tpl in CONTINUATION_TEMPLATES)
