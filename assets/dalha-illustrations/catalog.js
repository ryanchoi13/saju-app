// Exact garment matching keeps unsupported recommendations on the SVG renderer.
export const illustrations=[
  {
    "id": "f-casual-a",
    "gender": "female",
    "top": "니트",
    "bottom": "데님 바지",
    "outer": "블루종",
    "shoe": "운동화",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "topColor",
      "bottomColor",
      "shoeColor"
    ],
    "enabled": true,
    "suit": false,
    "tuck": "out"
  },
  {
    "id": "f-casual-b",
    "gender": "female",
    "top": "긴팔 티셔츠",
    "bottom": "미디 스커트",
    "outer": "가디건",
    "shoe": "앵클부츠",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "topColor",
      "bottomColor",
      "shoeColor"
    ],
    "enabled": true,
    "suit": false,
    "tuck": "in"
  },
  {
    "id": "f-business-a",
    "gender": "female",
    "top": "니트",
    "bottom": "슬랙스",
    "outer": "블레이저",
    "shoe": "로퍼",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "topColor",
      "bottomColor",
      "shoeColor"
    ],
    "enabled": true,
    "suit": false,
    "tuck": "out"
  },
  {
    "id": "f-business-b",
    "gender": "female",
    "top": "긴팔 캐주얼 셔츠",
    "bottom": "미디 스커트",
    "outer": "가디건",
    "shoe": "플랫슈즈",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "topColor",
      "bottomColor",
      "shoeColor"
    ],
    "enabled": true,
    "suit": false,
    "tuck": "in"
  },
  {
    "id": "f-formal-a",
    "gender": "female",
    "top": "긴팔 정장 셔츠",
    "bottom": "수트 바지",
    "outer": "수트 재킷",
    "shoe": "낮은 굽 펌프스",
    "bag": "핸드백",
    "dress": "",
    "slots": [
      "outerColor",
      "topColor",
      "shoeColor",
      "bagColor"
    ],
    "enabled": true,
    "suit": true,
    "tuck": "in"
  },
  {
    "id": "f-formal-b",
    "gender": "female",
    "top": "",
    "bottom": "",
    "outer": "블레이저",
    "shoe": "플랫슈즈",
    "bag": "핸드백",
    "dress": "긴팔 원피스",
    "slots": [
      "outerColor",
      "topColor",
      "shoeColor",
      "bagColor"
    ],
    "enabled": true,
    "suit": false,
    "tuck": "out"
  },
  {
    "id": "m-casual-a",
    "gender": "male",
    "top": "맨투맨",
    "bottom": "데님 바지",
    "outer": "블루종",
    "shoe": "운동화",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "topColor",
      "bottomColor",
      "shoeColor"
    ],
    "enabled": true,
    "suit": false,
    "tuck": "out"
  },
  {
    "id": "m-casual-b",
    "gender": "male",
    "top": "후드티",
    "bottom": "데님 바지",
    "outer": "블루종",
    "shoe": "운동화",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "topColor",
      "bottomColor",
      "shoeColor"
    ],
    "enabled": true,
    "suit": false,
    "tuck": "out"
  },
  {
    "id": "m-business-a",
    "gender": "male",
    "top": "니트",
    "bottom": "슬랙스",
    "outer": "블레이저",
    "shoe": "로퍼",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "topColor",
      "bottomColor",
      "shoeColor"
    ],
    "enabled": true,
    "suit": false,
    "tuck": "out"
  },
  {
    "id": "m-business-b",
    "gender": "male",
    "top": "긴팔 캐주얼 셔츠",
    "bottom": "면바지",
    "outer": "블루종",
    "shoe": "더비 구두",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "topColor",
      "bottomColor",
      "shoeColor"
    ],
    "enabled": true,
    "suit": false,
    "tuck": "in"
  },
  {
    "id": "06",
    "gender": "male",
    "top": "긴팔 정장 셔츠",
    "bottom": "수트 바지",
    "outer": "수트 재킷",
    "shoe": "옥스퍼드",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "accessoryColor",
      "topColor",
      "shoeColor"
    ],
    "enabled": true,
    "tie": true,
    "tuck": "in",
    "suit": true
  },
  {
    "id": "10",
    "gender": "male",
    "top": "긴팔 정장 셔츠",
    "bottom": "수트 바지",
    "outer": "수트 재킷",
    "shoe": "옥스퍼드",
    "bag": "",
    "dress": "",
    "slots": [
      "outerColor",
      "accessoryColor",
      "topColor",
      "shoeColor"
    ],
    "enabled": true,
    "tie": true,
    "tuck": "in",
    "suit": true
  }
];
const hex=v=>typeof v==='string'&&/^#[a-f0-9]{6}$/i.test(v);
export function selectIllustration(look){
 const s=look?.garment_spec;if(!s||look.renderer!=='approved-svg-5')return null;
 if(s.overOuter||s.knitNeck||s.outerMode==='carry'||s.outerOpen===false||s.trouserExtraLength||s.watchCaseColor)return null;
 // Cold-weather/extra-layer looks must retain the original recommendation rendering.
 if(look.season==='winter'||['cold','freezing'].includes(look.weather_fit?.thermal_band))return null;
 if((look.items||[]).some(i=>i.category!=='tie'&&i.color_parts))return null;
 for(const entry of illustrations){
  if(!entry.enabled||s.tuck!==entry.tuck)continue;
  if(entry.suit&&s.bottomColor?.toLowerCase()!==s.outerColor?.toLowerCase())continue;
  if(['gender','top','bottom','outer','shoe','bag','dress'].some(k=>(s[k]||'')!==entry[k]))continue;
  if(entry.outerLabelPattern&&!look.items?.some(i=>['outer','mid'].includes(i.category)&&entry.outerLabelPattern.test(i.display_label||'')))continue;
  const accessories=s.accessories||[];
  if(entry.tie){
   if(accessories.length!==1||accessories[0]!=='넥타이')continue;
   if(s.bottomColor?.toLowerCase()!==s.outerColor?.toLowerCase())continue;
   if(entry.id===(Number(look.age)>=50?'06':'10'))continue;
  }else if(accessories.length)continue;
  const tie=(s.accessoryItems||[]).find(i=>i.name==='넥타이');
  if(tie&&!['solid','stripe'].includes(tie.pattern||'solid'))continue;
  const colours=entry.slots.map(k=>k==='accessoryColor'?(tie?.parts?.body?.hex||tie?.color||s[k]):s[k]);
  if(!colours.every(hex))continue;
  let stripe=null;
  if(tie?.pattern==='stripe'){
   if(!hex(tie.parts?.pattern?.hex))continue;
   stripe={region:2,color:tie.parts.pattern.hex};
  }
  return {...entry,colours,stripe};
 }
 return null;
}
