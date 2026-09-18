// Side / slightly elevated view. Each shoe has its own upper, opening and sole.
export function shoeDrawing(name,gender,fill){
 const female=gender==='female';
 const rgb=fill.slice(1).match(/../g).map(n=>parseInt(n,16));
 const mix=(target,t)=>'#'+rgb.map((n,i)=>Math.round(n*(1-t)+target[i]*t).toString(16).padStart(2,'0')).join('');
 const dark=rgb.reduce((a,b)=>a+b,0)<250,edge=dark?'#55595c':'#7d7d78',detail=dark?'#6f7376':'#979990';
 const sole=mix([30,32,35],.24),inside=mix([20,23,25],.25);
 const p=(d,c=fill)=>`<path data-layer="fabric" d="${d}" fill="${c}" stroke="${edge}" stroke-width="1.25" stroke-linejoin="round" stroke-linecap="round"/>`;
 const l=d=>`<path data-layer="detail" d="${d}" fill="none" stroke="${detail}" stroke-width="1" stroke-linejoin="round" stroke-linecap="round"/>`;
 if(name==='부츠'||name==='앵클부츠'){
  const tall=name==='부츠',top=tall?35:106,front=female?119:111,back=female?161:168;
  return p(`M25 186 Q61 192 103 185 L123 177 L127 193 L166 193 L170 175 L170 167 Q124 165 100 171 L27 178 Z`,sole)
   +p(`M${front} ${top} Q${(front+back)/2} ${top+5} ${back} ${top} L${back-5} 128 Q${back-9} 151 171 164 L170 177 L129 178 Q98 192 31 187 Q14 186 20 175 Q26 165 58 162 L96 155 Q111 150 113 131 Z`)
   +l(`M${front+1} ${top+8} Q${(front+back)/2} ${top+13} ${back-1} ${top+8} M146 ${top+14} L143 136 Q142 151 149 162 M113 132 Q121 145 137 147 M25 181 Q75 187 123 173`);
 }
 if(name==='샌들'){
  if(female)return '<g data-variant="female-strap-sandal">'+p('M23 177 Q64 184 111 172 Q151 159 177 165 L177 174 Q148 174 115 183 Q65 197 26 188 Q19 186 23 177 Z',sole)
   +p('M24 176 Q42 166 64 167 Q95 171 117 161 Q150 151 174 159 Q183 161 177 166 Q151 165 115 177 Q68 191 26 182 Q20 181 24 176 Z',mix([244,240,230],.35))
   +p('M46 170 Q51 148 66 147 Q78 150 85 175 L76 180 Q66 158 61 158 Q55 158 54 181 L45 181 Z')
   +p('M139 164 Q153 148 157 128 Q165 122 173 128 L174 160 L165 162 L165 134 Q161 153 150 167 Z')
   +p('M127 133 Q147 139 166 128 L169 135 Q149 148 127 140 Z')
   +l('M150 136 L155 134 L157 140 L152 142 Z')+'</g>';
  // Men's sandal uses a broader sport-sandal silhouette rather than the
  // narrow toe-post/ankle-strap shape used for the women's drawing.
  return '<g data-variant="male-sport-sandal">'+p('M18 176 Q67 186 116 175 L178 163 L183 180 Q129 199 31 193 Q15 191 18 176 Z',sole)
   +p('M22 171 Q48 160 78 160 Q108 162 132 151 Q157 140 176 151 L178 164 Q145 177 110 182 Q62 190 27 182 Q18 180 22 171 Z',mix([238,236,229],.25))
   +p('M43 165 Q57 145 78 145 Q92 147 108 159 L99 171 Q83 157 72 157 Q61 158 54 172 Z')
   +p('M104 153 Q120 137 144 136 Q159 137 171 147 L164 158 Q151 149 139 149 Q125 150 115 162 Z')
   +p('M145 139 Q154 121 170 124 L176 134 L171 153 L160 154 L163 135 Q157 135 153 145 Z')
   +l('M51 166 L99 166 M112 156 L164 153 M25 183 Q90 195 180 172')+'</g>';
 }
 if(name==='플랫슈즈'||name==='낮은 굽 펌프스'){
  const heel=name==='낮은 굽 펌프스';
  let s=p(heel?'M26 180 Q77 190 127 166 L153 166 L172 170 L168 192 L138 192 L135 181 Q95 195 30 188 Z':'M25 179 Q88 184 173 168 L173 177 Q110 198 31 188 Z',sole);
  s+=p('M24 170 Q34 159 67 153 L110 148 Q139 141 158 123 Q175 128 175 166 Q159 178 121 183 L42 187 Q18 185 24 170 Z');
  s+=p('M78 152 Q115 150 158 126 Q167 134 164 151 Q132 168 94 167 Q82 165 78 152 Z',inside);
  return s+l('M29 177 Q49 182 64 179');
 }
 if(name==='운동화')return p('M19 177 Q74 188 119 176 L177 166 L181 181 Q127 200 35 194 Q18 192 19 177 Z',mix([240,238,231],.8))
  +p(`M20 173 Q28 157 53 155 Q74 153 94 135 L116 117 Q123 114 131 128 Q148 143 170 126 Q179 135 178 166 Q140 182 104 185 L37 185 Q18 184 20 173 Z`)
  +p('M132 128 Q151 136 169 126 L173 136 Q152 151 137 141 Z',inside)
  +l('M35 165 Q58 163 74 178 M142 153 L163 150 M23 184 Q91 197 178 174')
  +`<g data-part="shoelaces" stroke="${dark?'#b1b4b5':'#777b7c'}" stroke-width="1.35" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M88 145 L120 148 M112 157 L96 137 M96 137 L127 140 M120 148 L104 129 M104 129 L126 132 M115 134 Q95 132 104 124 Q110 122 115 134 Q125 121 130 127 Q134 134 115 134 M115 134 L110 145 M115 134 L128 145"/></g>`;
 // Women's penny loafer: lower vamp, softly rounded toe and a slim low sole.
 if(name==='로퍼'&&female)return p('M27 176 Q77 185 122 173 L148 166 L173 165 L172 180 L150 184 L147 178 Q94 192 35 187 Q26 185 27 176 Z',sole)
  +p('M27 173 Q33 163 60 161 Q84 159 106 144 Q117 137 128 148 Q149 151 167 136 Q175 143 174 165 Q148 179 105 183 L42 183 Q25 182 27 173 Z')
  +p('M121 145 Q143 151 167 138 Q171 143 169 153 Q147 165 129 156 Z',inside)
  +l('M42 165 Q68 159 92 150 Q103 154 110 165 Q81 178 42 176')
  +p('M92 149 Q106 152 122 158 L117 165 Q101 161 87 157 Z')
  +l('M101 156 L110 159');
 // Men's low shoes retain a higher instep and a defined low heel.
 const derby=name==='더비 구두',loafer=name==='로퍼';
 const throat=derby?105:111;
 let s=p('M20 178 Q70 190 113 177 L144 164 L178 163 L177 184 L147 189 L142 180 Q93 197 27 189 Z',sole);
 s+=p(`M20 173 Q25 163 51 158 Q78 153 ${throat} 124 Q114 118 123 130 Q143 145 170 123 Q180 135 178 166 Q161 178 134 181 Q81 192 29 183 Q16 181 20 173 Z`);
 s+=p('M124 131 Q143 140 170 123 Q174 130 172 141 Q149 155 134 146 Z',inside);
 if(loafer){s+=l('M38 164 Q65 151 92 142 Q111 152 119 166 Q74 181 38 177 Z');s+=p('M91 139 L125 151 L119 161 L84 151 Z')+l('M101 147 L112 151');}
 else if(derby){s+=p('M88 143 L104 121 L123 138 L111 161 L100 167 Z')+l('M104 126 L106 147 L100 160 M97 136 L117 146 M92 144 L112 154 M132 152 Q141 166 158 174');}
 else{s+=l('M99 138 L116 152 L127 141 M94 143 L112 157 M99 136 L117 150 M104 130 L122 144 M71 155 Q82 166 83 184');}
 return s;
}
