"""Final user menu edits. Element assignments remain editorial interpretations.

Changes apply only to the general pool; paused diet definitions remain intact.
Sources for availability: https://www.slowcali.co.kr/bbs/content.php?co_id=menu
https://pokeallday.co.kr/ and https://www.goobne.co.kr/main
"""
from dataclasses import replace

# Renames preserve their existing grade unless GRADES overrides it below.
RENAMES = {
 '매콤한 치킨카레':'치킨카레', '오이냉국 정식':'오이냉국',
 '매운 어묵탕':'어묵탕', '재첩국과 따뜻한 쌀밥':'재첩국',
 '김국과 따뜻한 쌀밥':'김국', '짜파게티':'짜장라면',
 '하얀짬뽕':'백짬뽕', '닭다리살구이':'오븐구이 치킨',
 '고등어구이와 채소 반찬':'고등어구이', '갈치조림과 나물 반찬':'갈치조림',
 '문어숙회정식':'문어숙회', '참치타다키':'참치회', '광어회':'생선회',
 '화덕피자':'콤비네이션피자', '치즈샌드위치':'햄치즈 샌드위치',
 '아보카도 토스트':'아보카도 샌드위치',
 '자몽차와 에그타르트':'홍차와 에그타르트',
}
# None means removal; otherwise the destination already exists in the pool.
MERGES = {
 '된장국과 밥·달걀말이':'된장국', '콩나물국과 밥·두부구이':'콩나물국',
 '찐만두·달걀국':'만둣국', '닭한마리':'삼계탕', '닭가슴살구이':'오븐구이 치킨',
 '불고기버거':'햄버거', '치즈버거':'햄버거',
 '에그 샐러드 샌드위치':None, '콜슬로 샌드위치':None,
}
GRADES = {
 '밤밥':1, '된장국':3, '만둣국':3, '홍합탕':2, '김국':1,
 '콩비지찌개':3, '매운 소고기 쌀국수':2, '해물볶음우동':2,
 '생선가스':2, '아보카도 샌드위치':2, '콤비네이션피자':3,
}
# New name, grade, closest template, explicit ingredient and cuisine.
ADDITIONS = (
 ('오야코동',1,'연어덮밥','chicken','japanese'),
 ('전복죽',3,'소고기죽','seafood','korean'),
 ('달걀국',2,'연두부국','egg_dairy','korean'),
 ('해장국',3,'뼈해장국','beef','korean'),
 ('양파수프',1,'양송이스프','vegetable','western'),
 ('메밀국수',3,'메밀 비빔국수','noodle_wheat','korean'),
 ('우육면',2,'양지 소고기 쌀국수','beef','chinese'),
 ('볶음짬뽕',2,'해물볶음우동','seafood','chinese'),
 ('어향가지튀김',2,'어향가지','vegetable','chinese'),
 ('치킨가스',2,'경양식 돈가스','chicken','western'),
 ('계란초밥',1,'유부초밥','egg_dairy','japanese'),
 ('초새우초밥',1,'연어초밥','seafood','japanese'),
 ('파인애플피자',1,'고구마피자','noodle_wheat','western'),
 ('시푸드피자',2,'페퍼로니피자','seafood','western'),
 ('닭가슴살 포케',2,'연어 포케','chicken','western'),
 ('소고기 포케',2,'연어 포케','beef','western'),
 ('블루베리 검은콩 스무디',1,'그린 스무디','tofu_bean','western'),
)
# Correct renamed/new classification before any substring-based fallback.
CATEGORIES = {
 '오야코동':'rice_bowl', '우육면':'chinese_noodles',
 '볶음짬뽕':'chinese_noodles', '치킨가스':'cutlet',
 '참치회':'raw_fish', '생선회':'raw_fish',
 '오븐구이 치킨':'chicken', '어향가지튀김':'vegetable_meal',
 '홍차와 에그타르트':'snack',
}


def apply_catalog_revision(pool, build_group):
    original = {m.name:m for m in pool}
    result=[]
    for item in pool:
        if item.name in MERGES:
            continue
        name=RENAMES.get(item.name,item.name)
        if name != item.name:
            rebuilt=build_group(item.element,item.group,' '.join(sorted(item.seasons)),
                                ' '.join(sorted(item.periods)),' '.join(sorted(item.tags)),name)[0]
            # A rename alone must not silently reset reviewed ranking metadata.
            item=replace(rebuilt,popularity=item.popularity,familiarity=item.familiarity,
                         accessibility=item.accessibility,age_groups=item.age_groups)
            if name=='홍차와 에그타르트':item=replace(item,ingredient='egg_dairy')
            if name=='치킨카레':item=replace(item,tags=item.tags-{'spicy'})
        result.append(replace(item,popularity=GRADES.get(name,item.popularity)))
    for name,grade,template,ingredient,cuisine in ADDITIONS:
        base=original[template]
        # New dish tags use a nearby existing recipe family, not clinical evidence.
        item=build_group(base.element,base.group,' '.join(sorted(base.seasons)),
                         ' '.join(sorted(base.periods)),' '.join(sorted(base.tags)),name)[0]
        result.append(replace(item,popularity=grade,ingredient=ingredient,cuisine=cuisine,
                              familiarity=3))
    names=[m.name for m in result]
    if len(names)!=len(set(names)):
        raise ValueError('Duplicate menu after catalog revision')
    for target in MERGES.values():
        if target is not None and target not in names:
            raise ValueError('Missing merge destination: '+target)
    return tuple(result)
