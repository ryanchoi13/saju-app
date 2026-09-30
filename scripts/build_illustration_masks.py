"""Offline mask preparation. Requires Pillow, numpy, scipy and the original Higgsfield PNGs.
Never run against lossy screenshots or recolored output.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,io
from scipy.ndimage import grey_closing, gaussian_filter, binary_closing, binary_fill_holes, binary_dilation, distance_transform_edt, label
import argparse
p=argparse.ArgumentParser();p.add_argument('--sources',type=Path,required=True);args=p.parse_args()
OUT=Path(__file__).resolve().parents[1]/'assets/dalha-illustrations'
specs=[[r['id']] for r in json.loads((OUT/'provenance.json').read_text())]
for spec in specs:
 key=spec[0]
 a=np.asarray(Image.open(args.sources/f'{key}.png').convert('RGB').resize((768,768))).astype(float)
 r,g,b=a.transpose(2,0,1);y,x=np.indices(r.shape)
 rose=(r-g>12)&(r-b>10)&(abs(g-b)<24)&(y<440)
 blue=(b-r>9)&(b-g>2)&(r<210)
 green=(g-r>0)&(g-b>6)&(r<210)
 leather=(r-g>14)&(g-b>10)&((.2126*r+.7152*g+.0722*b)<155)
 brown=leather&(y>350)&(x<440)
 bag=(r-g>10)&(g-b>6)&(x>430)
 # Neutral cast shadows are warmer (R >= G) than the sage fabric.
 slots=['outerColor','topColor','bottomColor','shoeColor'];masks=[green,rose,blue,brown]
 if key=='f-formal-a':slots=['outerColor','topColor','shoeColor','bagColor'];masks=[blue,rose,brown,bag]
 if key=='f-formal-b':slots=['outerColor','topColor','shoeColor','bagColor'];masks=[green,blue,brown|(leather&(y>540)),bag&(y<540)]
 lum=.2126*r+.7152*g+.0722*b;local=grey_closing(lum,size=(7,7));layers=np.zeros((*r.shape,3),dtype=np.uint8);regions=[]
 for i,raw in enumerate(masks):
  cc,count=label(raw);sizes=np.bincount(cc.ravel());good=np.where(sizes>18)[0];good=good[good!=0];raw=np.isin(cc,good)
  assert raw.sum()>100,(key,i)
  med=np.percentile(lum[raw],65)
  # Fill tiny gaps and holes such as buttons, but not large garment openings.
  closed=binary_closing(raw,iterations=1)
  holes=binary_fill_holes(closed)&~closed;hcc,_=label(holes);hs=np.bincount(hcc.ravel());small=np.where((hs>0)&(hs<700))[0];small=small[small!=0]
  m=closed|np.isin(hcc,small)|raw
  m|=binary_dilation(m,iterations=2)&(lum<220)&(lum>8)
  m&=layers[:,:,0]==0
  # Distinguish outer boundary from interior construction lines.
  outer=distance_transform_edt(m)<=3.2
  ln=np.clip((local-lum-1)/max(med*.33,18),0,1)
  # Outer line coverage also detects original dark antialiased contour pixels.
  ln=np.maximum(ln,np.where(outer,np.clip((med-lum)/(med*.48),0,1),0))
  clean=gaussian_filter(local*m,1)/np.maximum(gaussian_filter(m.astype(float),1),1e-6)
  sh=gaussian_filter((clean<med*.9).astype(float),.4)
  layers[:,:,0][m]=i+1;layers[:,:,1][m]=np.rint(ln[m]*255).astype('uint8');layers[:,:,2][m]=np.rint(sh[m]*127).astype('uint8')+outer[m].astype('uint8')*128
  regions.append({'id':i+1,'name':slots[i],'base':np.median(a[raw],axis=0).round().astype(int).tolist(),'pixels':int(m.sum())})

 buf=io.BytesIO();Image.fromarray(layers).save(buf,format='PNG');(OUT/f'{key}-layers.png').write_bytes(buf.getvalue())
 buf=io.BytesIO();Image.fromarray(a.astype('uint8')).save(buf,format='WEBP',quality=94);(OUT/f'{key}.webp').write_bytes(buf.getvalue())
