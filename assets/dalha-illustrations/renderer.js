/** Colour renderer v4. No networking, model calls, geometry edits or coordinate resampling.
 * Mask red channel: 0 = keep source, n = slot n, 100+n = the lighter inside of slot n
 * (rolled-up jeans cuff, 2026-10-15) painted with slot n's colour mixed toward warm white. */
export const INSIDE_OFFSET=100,INSIDE_MIX=.6,INSIDE_WHITE=[246,243,236];
const penFor=t=>{const L=t[0]*.2126+t[1]*.7152+t[2]*.0722;return {edge:t.map(v=>L>=100?v*.67:Math.max(v*.50,13)),detail:t.map(v=>L>=100?v*.77:Math.max(v*.63,18))}};
export function recolor(original,layers,colors){
 if(original.length!==layers.length || original.length%4)throw new Error('RGBA buffers must have matching lengths');
 const palette=colors.map(hex=>{if(!/^#[0-9a-f]{6}$/i.test(hex))throw new Error('Invalid colour');return [1,3,5].map(k=>parseInt(hex.slice(k,k+2),16))});
 const inside=palette.map(t=>t.map((v,c)=>v+(INSIDE_WHITE[c]-v)*INSIDE_MIX));
 const pens=palette.map(penFor),insidePens=inside.map(penFor);
 const out=new Uint8ClampedArray(original);
 for(let p=0;p<out.length;p+=4){let id=layers[p];if(!id)continue;const isInside=id>INSIDE_OFFSET;if(isInside)id-=INSIDE_OFFSET;id-=1;if(!palette[id])throw new Error('Missing region colour');const colour=isInside?inside[id]:palette[id],pen0=isInside?insidePens[id]:pens[id];const line=layers[p+1]/255,shade=(layers[p+2]%128)/127,pen=layers[p+2]>=128?pen0.edge:pen0.detail;for(let c=0;c<3;c++)out[p+c]=Math.round(colour[c]*(1-.13*shade)*(1-line)+pen[c]*line)}
 return out;
}
