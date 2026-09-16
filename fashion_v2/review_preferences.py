"""Bounded outfit preferences from the 13–18 user review.

These are explicit reviewed input scopes, not population preferences. They
constrain structure and A/B placement before scoring, never replace final SVGs.
Original daily colors and the original 24-color research pool stay unchanged.
"""

def apply_review_preferences(look, a, b):
    gender, tpo, age = look['gender'], look['tpo'], look.get('age')
    number = look['recommendation_number']
    pair = (a['hex'].upper(), b['hex'].upper())
    band = look.get('weather_fit', {}).get('thermal_band')
    cold = band in {'cold', 'freezing'} or (not band and look['season'] == 'winter')
    hot = band in {'warm', 'hot', 'very_hot'} or (not band and look['season'] == 'summer')

    def change(category, **values):
        item = next(i for i in look['items'] if i['category'] == category)
        item.update(values)

    def policy(name, targets):
        look['review_preference'] = name
        look['color_targets'] = targets

    if (gender == 'male' and tpo == 'casual' and age is not None and 20 <= age < 30
            and hot and pair == ('#EAC744', '#70468A')):
        change('top', label='반팔 티셔츠', base_color='white', material='cotton_jersey')
        change('bottom', label='면바지', base_color='beige', material='cotton')
        change('shoes', label='운동화', base_color='white')
        policy('young-summer-yellow-purple', {
            'A': None, 'B': {'category': 'top'} if number == 1 else None})
    if (gender == 'female' and tpo == 'casual' and age is not None and 10 <= age < 20
            and cold and pair == ('#265AC6', '#DDB6BC')):
        change('bottom', label='데님 바지', base_color='navy', material='winter_denim')
        if number == 2:
            outer = next(i for i in look['items'] if i['category'] in {'coat', 'outer'})
            outer.update(category='outer', label='패딩', base_color='black', material='insulated_padding')
        policy('teen-winter-blue-pink', {
            'A': {'category': 'bottom', 'tone': 'navy' if number == 1 else 'denim'},
            'B': {'category': 'outer' if number == 1 else 'top'}})
    if (gender == 'male' and tpo == 'casual' and age is not None and 50 <= age < 60
            and cold and number == 2 and pair == ('#BC3F43', '#A7CEDF')):
        change('top', label='니트', display_label='목폴라 니트', neck='turtleneck')
        change('bottom', label='면바지', base_color='beige', material='winter_cotton')
        look['review_assumptions'] = ['겨울 체감온도 조건에 따라 반바지는 긴바지 의도로 해석. 확인 전 가정.']
        policy('fifties-winter-red-blue', {
            'A': {'category': 'top'}, 'B': {'category': 'coat', 'tone': 'navy'}})
    if gender == 'female' and tpo == 'business_formal' and age is not None and 50 <= age < 60:
        for item in look['items']:
            if item['category'] == 'dress' or (item['category'] == 'bottom' and '스커트' in item['label']):
                item['hem_length'] = 'knee'
        if any(i['category'] == 'dress' for i in look['items']) and pair == ('#355B48', '#70468A'):
            look['items'].append(dict(category='accessory', label='시계', base_color='forest',
                                      material='watch', wear_mode='worn', watch_case_hex='#EAC744',
                                      display_label='시계 (노란 줄·테두리)'))
            policy('fifties-formal-green-purple', {
                'A': {'category': 'accessory'}, 'B': {'category': 'bag'}})
    # Reinitialize only pre-color base fields after structural choices.
    return look
