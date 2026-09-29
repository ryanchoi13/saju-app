/** Colour renderer v3. No networking, model calls, geometry edits or coordinate resampling. */
export function recolor(original,layers,colors){
 if(original.length!==layers.length || original.length%4)throw new Error('RGBA buffers must have matching lengths');
 const palette=colors.map(hex=>{if(!/^#[0-9a-f]{6}$/i.test(hex))throw new Error('Invalid colour');return [1,3,5].map(k=>parseInt(hex.slice(k,k+2),16))});
 const pens=palette.map(t=>{const L=t[0]*.2126+t[1]*.7152+t[2]*.0722;return {edge:t.map(v=>L>=100?v*.67:Math.max(v*.50,13)),detail:t.map(v=>L>=100?v*.77:Math.max(v*.63,18))}});
 const out=new Uint8ClampedArray(original);
 for(let p=0;p<out.length;p+=4){const id=layers[p]-1;if(id<0)continue;if(!palette[id])throw new Error('Missing region colour');const line=layers[p+1]/255,shade=(layers[p+2]%128)/127,pen=layers[p+2]>=128?pens[id].edge:pens[id].detail;for(let c=0;c<3;c++)out[p+c]=Math.round(palette[id][c]*(1-.13*shade)*(1-line)+pen[c]*line)}
 return out;
}
