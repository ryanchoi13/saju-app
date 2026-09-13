"""Use existing Wada placement rules within the user's selected clothing context.

Color allowance scores are editorial clothing rules, not fortune scores.
The original daily A/B selection is preserved across all three contexts.
"""
from wada_color_rules import evaluate_duo, score_color_for_item, WADA_COLORS
from wada_color_ko import get_wada_color_ko

TPO_LABELS = {'casual': '캐주얼', 'business_casual': '비즈니스 캐주얼', 'business_formal': '비즈니스 포멀'}
ITEM_LABELS = {'top':'상의', 'bottom':'바지', 'outer':'겉옷', 'shoes':'신발', 'bag':'가방',
               'shirt_knit_polo':'셔츠·니트·폴로', 'jacket':'재킷', 'belt':'벨트', 'watch':'시계',
               'suit':'상하의가 같은 색인 정장', 'shirt':'셔츠', 'tie':'넥타이',
               'bottom_skirt':'바지·스커트', 'dress':'원피스', 'blouse_knit':'블라우스·니트',
               'suit_jacket':'정장 재킷', 'blouse':'블라우스', 'scarf':'스카프', 'jewelry':'주얼리'}


# Supporting neutrals translate the existing daily element into a restrained
# styling choice. They are not extra lucky colors or new fortune scores.
BASES = {'water': ('네이비', '#26354A'), 'wood': ('네이비', '#26354A'),
         'fire': ('차콜', '#44474D'), 'earth': ('차콜', '#44474D'),
         'metal': ('라이트 그레이', '#B6BAC1')}


# Restrained everyday trouser colors, reviewed against Korean retail ranges.
# These are supporting styling colors, not additional lucky colors or a claim
# about population percentages. See docs/practical-daily-recommendations.md.
PANTS_COLORS = {
    'denim': ('데님 블루', '#466889'), 'black': ('블랙', '#252629'),
    'navy': ('네이비', '#26354A'), 'gray': ('그레이', '#85888D'),
    'beige': ('베이지', '#C4B294'), 'brown': ('브라운', '#705443'),
    'ivory': ('아이보리', '#E8E0CF'), 'off_white': ('오프화이트', '#F0EDE5'),
    'olive': ('차분한 올리브', '#787E62'),
}
PANTS_PAIRS = {'wood': ('denim', 'beige'), 'fire': ('black', 'gray'),
               'earth': ('beige', 'brown'), 'metal': ('gray', 'navy'),
               'water': ('navy', 'denim')}

# Shoes finish the outfit; these are practical coordination choices, not
# additional lucky colors. Each pair is for a light top, then a dark top.
SHOE_COLORS = {key: PANTS_COLORS[key] for key in ('black', 'navy', 'gray', 'beige', 'brown')}
SHOE_COLORS['white'] = ('화이트', '#F5F4EF')
CASUAL_SHOE_PAIRS = {
    'denim': ('gray', 'white'), 'black': ('black', 'gray'),
    'navy': ('gray', 'white'), 'gray': ('navy', 'black'),
    'beige': ('brown', 'white'), 'brown': ('beige', 'white'),
    'ivory': ('brown', 'black'), 'off_white': ('brown', 'black'),
    'olive': ('brown', 'beige'),
}

# Age changes template priority and silhouette wording, never eligibility.
# A user may still wear any template outside the preferred decade.
AGE_STYLE = {
    '10s': {
        'male': ('캐주얼 코치 재킷', '후드 티셔츠', '여유 있는 청바지', '코트 스니커즈'),
        'female': ('캐주얼 코치 재킷', '맨투맨', '여유 있는 캐주얼 팬츠', '코트 스니커즈'),
        'business_bottom': '단정한 스트레이트 슬랙스', 'formal_bottom': '기본 정장 바지'},
    '20s': {
        'male': ('워크 재킷', '후드 티셔츠', '여유 있는 청바지', '레트로 스니커즈'),
        'female': ('크롭 캐주얼 재킷', '후드 티셔츠', '와이드 캐주얼 팬츠', '레트로 스니커즈'),
        'business_bottom': '세미와이드 슬랙스', 'formal_bottom': '모던 스트레이트 정장 바지'},
    '30s': {
        'male': ('봄버 재킷', '맨투맨', '스트레이트 청바지', '미니멀 스니커즈'),
        'female': ('봄버 재킷', '맨투맨', '스트레이트 캐주얼 팬츠', '미니멀 스니커즈'),
        'business_bottom': '스트레이트 슬랙스', 'formal_bottom': '스트레이트 정장 바지'},
    '40s': {
        'male': ('캐주얼 필드 점퍼', '맨투맨', '진청 스트레이트 청바지', '스웨이드 스니커즈'),
        'female': ('캐주얼 점퍼', '니트 맨투맨', '스트레이트 캐주얼 팬츠', '스웨이드 스니커즈'),
        'business_bottom': '단정한 스트레이트 슬랙스', 'formal_bottom': '클래식 정장 바지'},
    '50s': {
        'male': ('캐주얼 블루종', '부드러운 맨투맨', '편안한 스트레이트 청바지', '쿠션 스니커즈'),
        'female': ('캐주얼 블루종', '부드러운 니트', '편안한 스트레이트 팬츠', '쿠션 스니커즈'),
        'business_bottom': '편안한 스트레이트 슬랙스', 'formal_bottom': '클래식 정장 바지'},
    '60plus': {
        'male': ('가벼운 캐주얼 점퍼', '부드러운 니트', '편안한 스트레이트 팬츠', '쿠션 스니커즈'),
        'female': ('가벼운 캐주얼 점퍼', '부드러운 니트', '편안한 스트레이트 팬츠', '쿠션 스니커즈'),
        'business_bottom': '편안한 정장 팬츠', 'formal_bottom': '편안한 클래식 정장 바지'},
}


def age_band(age):
    """Return a preferred editorial band; it is not an exclusion rule."""
    if age is None:
        return '30s'
    age = max(0, int(age))
    if age < 20:
        return '10s'
    if age < 30:
        return '20s'
    if age < 40:
        return '30s'
    if age < 50:
        return '40s'
    if age < 60:
        return '50s'
    return '60plus'


def _casual_bottom_label(band, pants_key):
    fit = {'10s': '여유 있는', '20s': '여유 있는', '30s': '스트레이트', '40s': '단정한 스트레이트',
           '50s': '편안한 스트레이트', '60plus': '편안한 스트레이트'}[band]
    kind = ('청바지' if pants_key in {'denim', 'navy'} else
            '면바지' if pants_key in {'beige', 'brown', 'olive', 'ivory', 'off_white'} else
            '캐주얼 팬츠')
    return f'{fit} {kind}'


def _shoe_color(pieces, tpo, pants):
    if tpo == 'business_formal':
        return SHOE_COLORS['black']
    pants_key, _ = pants
    if tpo == 'business_casual':
        return SHOE_COLORS['brown' if pants_key in {'navy', 'beige', 'brown', 'ivory', 'off_white'} else 'black']
    top = next(piece for piece in pieces if piece['item_type'] == 'top')
    rgb = [int(top['hex'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)]
    brightness = sum(channel * weight for channel, weight in zip(rgb, (0.2126, 0.7152, 0.0722)))
    key = CASUAL_SHOE_PAIRS[pants_key][0 if brightness >= 150 else 1]
    return SHOE_COLORS[key]


def _pants_base(gender, tpo, element, variant):
    keys = list(PANTS_PAIRS.get(element, PANTS_PAIRS['water']))
    if gender == 'female':
        keys[1] = {'wood': 'ivory', 'fire': 'off_white', 'earth': 'olive'}.get(element, keys[1])
    if tpo == 'business_casual':
        keys = ['navy' if k == 'denim' else ('brown' if k == 'olive' else k) for k in keys]
        if keys[0] == keys[1]:
            keys[1] = 'gray'
    return keys[variant], PANTS_COLORS[keys[variant]]


def _piece(label, color, sprite, slot):
    return {'label': label, 'color_name': color[0], 'hex': color[1],
            'sprite': sprite, 'item_type': slot}


def _look(color, other, gender, tpo, base, pants, profile, band, season, variant):
    female = gender == 'female'
    white = ('화이트', '#F5F4EF')
    accent = (color['name_ko'], color['hex'])
    scores = dict(color['ranked_items'])
    other_scores = dict(other['ranked_items'])
    top_slot = ('blouse' if female else 'shirt') if tpo == 'business_formal' else (
        ('blouse_knit' if female else 'shirt_knit_polo') if tpo == 'business_casual' else 'top')
    bottom_slot = 'bottom_skirt' if female else 'bottom'
    pieces = []
    if tpo == 'business_formal':
        pieces = [_piece('정장 재킷', base, 8 if female else 0, 'suit_jacket' if female else 'suit'),
                  _piece(profile['formal_bottom'], base, 9 if female else 1, bottom_slot),
                  _piece('블라우스' if female else '셔츠', white, 10 if female else 2, top_slot)]
        slot = 'scarf' if female else 'tie'
        if scores.get(slot, 0) >= 60:
            pieces.append(_piece('스카프' if female else '넥타이', accent, 14 if female else 5, slot))
        else:
            slot = next((s for s in (top_slot, 'suit_jacket' if female else 'suit') if scores.get(s, 0) >= 60), None)
            if slot == top_slot:
                pieces[2].update(color_name=accent[0], hex=accent[1])
            elif slot:
                pieces[0].update(color_name=accent[0], hex=accent[1])
                if not female:
                    pieces[1].update(color_name=accent[0], hex=accent[1])
        # Only use the other color on a shirt when it clears the stricter
        # shirt gate. Otherwise the second card is an alternative accent.
        if slot != top_slot and other_scores.get(top_slot, 0) >= 80:
            pieces[2].update(color_name=other['name_ko'], hex=other['hex'])
    else:
        slot = top_slot if scores.get(top_slot, 0) >= 60 else None
        pants_key, pants_color = pants
        casual_outer, casual_top, casual_bottom, casual_shoes = profile[gender]
        pants_label = (profile['business_bottom'] if tpo == 'business_casual'
                       else _casual_bottom_label(band, pants_key))
        top_label = ('블라우스' if female else '셔츠') if tpo == 'business_casual' else casual_top
        pieces = [_piece(top_label,
                         accent if slot else white, (11 if female else 3) if tpo == 'casual' else (10 if female else 2), top_slot),
                  _piece(pants_label, pants_color, 9 if female else 4, bottom_slot)]
        if tpo == 'casual' and season in {'spring', 'autumn', 'winter'}:
            outer_label = casual_outer if variant == 0 else ('텍스처 ' + casual_outer)
            pieces.insert(0, _piece(outer_label, base, 8 if female else 0, 'outer'))
        if tpo == 'business_casual':
            pieces.insert(0, _piece('재킷', base, 8 if female else 0, 'jacket'))
            # A tie is optional in business casual; a pale shirt can carry A
            # while the tie carries B. Reuse the formal tie allowance gate.
            meta = WADA_COLORS[color['hex'].lower()]
            if not female and meta['lightness'] >= 72 and meta['saturation'] <= 55 and score_color_for_item(other['hex'], 'male', 'business_formal', 'tie') >= 60:
                pieces.append(_piece('넥타이 (선택)', (other['name_ko'], other['hex']), 5, 'tie'))
    if tpo == 'casual':
        shoe_label = profile[gender][3]
    elif tpo == 'business_formal':
        shoe_label = '닫힌 정장화' if female else '정장 구두'
    else:
        shoe_label = '로퍼'
    pieces.append(_piece(shoe_label,
                         _shoe_color(pieces, tpo, pants),
                         15 if female else (7 if tpo == 'casual' else 6), 'shoes'))
    role = 'Daily' if variant == 0 else 'Trend'
    return {'title': f"{role} · {accent[0]} 포인트", 'look_role': role.lower(),
            'age_band': band, 'age_weighting': 'preferred_not_required', 'items': pieces,
            'accent_slot': slot, 'description': ' · '.join(f"{x['color_name']} {x['label']}" for x in pieces)}


def build_style_contexts(duo_no, gender, casual_palette, daily_element=None, user_name=None,
                         age=None, season='autumn'):
    gender = 'female' if gender == 'female' else 'male'
    season = season if season in {'spring', 'summer', 'autumn', 'winter'} else 'autumn'
    band = age_band(age)
    profile = AGE_STYLE[band]
    result = {}
    element = {'木':'wood','火':'fire','土':'earth','金':'metal','水':'water'}.get(daily_element, daily_element)
    base = BASES.get(element, BASES['water'])
    for tpo, label in TPO_LABELS.items():
        evaluation = evaluate_duo(duo_no, gender, tpo)
        colors = [{**entry, **get_wada_color_ko(entry['hex'], entry['name'])}
                  for entry in (evaluation['color_a'], evaluation['color_b'])]
        looks = [_look(colors[i], colors[1-i], gender, tpo, base,
                       _pants_base(gender, tpo, element, i), profile, band, season, i) for i in (0, 1)]
        for color, look in zip(colors, looks):
            slot = look['accent_slot']
            color.update(item_type=slot, role=(ITEM_LABELS[slot] + ' 포인트') if slot else '오늘의 추천 색상')
            color.pop('ranked_items')
        palette = {**(casual_palette if tpo == 'casual' else {}),
                   'top': colors[0], 'bottom': colors[1], 'point': None, 'mode': 'harmony',
                   'tpo': tpo, 'gender': gender, 'style_mood': tpo, 'mood_tag': label,
                   'age_band': band, 'age_weighting': 'preferred_not_required', 'season': season,
                   'looks': looks, 'outfit_guidance': looks[0]['description'],
                   'mood_desc': (
                       f"{str(user_name).strip().removesuffix('님')}님을 위해 두 가지 코디를 제안드립니다. 오늘의 코디에 참고해 보세요."
                       if user_name and str(user_name).strip() else
                       '오늘의 코디에 참고하실 수 있도록 두 가지 차림을 제안드립니다.')}
        result[tpo] = palette
    return result
