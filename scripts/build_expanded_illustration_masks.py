"""Prepare the expanded Higgsfield sources using Pillow, numpy and scipy."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,io
from scipy.ndimage import grey_closing,gaussian_filter,binary_closing,binary_fill_holes,binary_dilation,distance_transform_edt,label,median_filter
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mark_denim_cuffs import DENIM_CUFFS,mark_cuffs
# 2026-10-18 (#188): drawings whose trouser cast shadow carries blue spill along the leg edge.
SHADOW_FRINGE_NEUTRAL=('all-065',)
def neutral_shadow_fringe(a,layers,slots):
 """The trouser's cast shadow is a ~6px blue-grey strip beside the leg. The hue-based mask
 takes its inner half into the trouser slot (jagged edge) and leaves the rest blue in slot 0.
 Fix: return the shadow-toned pixels (low saturation, mid luminance, not a drawn line) to
 slot 0, mark the new trouser edge as contour, then grey the whole strip at its own luminance.
 The shadow stays unrecoloured (neutral) in every palette."""
 bottom=[s['field'] for s in slots].index('bottomColor')+1
 hsv=np.asarray(Image.fromarray(np.rint(a).astype('uint8')).convert('HSV')).astype(float)
 h=hsv[:,:,0]*360/255;sat=hsv[:,:,1]/255;v=hsv[:,:,2];lum=a@[.2126,.7152,.0722]
 blue=(h>=190)&(h<250);slot=layers[:,:,0]%100
 tone=blue&(sat<.24)&(lum>=90)&(lum<=140)
 for _ in range(4):  # peel inwards from the outside, at most 4px
  edge=(slot==bottom)&(distance_transform_edt(slot==bottom)<=1)&binary_dilation(layers[:,:,0]==0)
  back=edge&tone&(layers[:,:,1]<60)
  if not back.any():break
  layers[back]=0;slot=layers[:,:,0]%100
 m=slot==bottom;contour=m&(distance_transform_edt(m)<=2.3);layers[:,:,2][contour]|=128
 zone=(distance_transform_edt(slot!=bottom)<=8)&(layers[:,:,0]==0)&blue&(v<235)
 out=a.copy();out[zone]=lum[zone][:,None]
 return out,Image.fromarray(np.rint(out).astype('uint8'))
p=argparse.ArgumentParser();p.add_argument('--workdir',type=Path,required=True);args=p.parse_args()
R=args.workdir;OUT=Path(__file__).resolve().parents[1]/'assets/dalha-illustrations';P=R/'previews';P.mkdir(exist_ok=True)
requests=json.loads((OUT/'expansion-provenance.json').read_text())
ranges={'green':(78,163),'rose':(330,360),'blue':(201,245),'brown':(10,40),'yellow':(40,76),'violet':(245,295),'cyan':(163,201),'magenta':(295,330),'scarlet':(0,10)}
pal={'outerColor':'#B52C34','topColor':'#E4DED0','bottomColor':'#526C85','shoeColor':'#762C40','bagColor':'#363C40','overOuter.color':'#CBBCA0','tie.body':'#435466','watch.strap':'#987239','watch.case':'#D8B84A','watch.dial':'#355B48','legLayerColor':'#3E3A45'}
checks=[]
for q in requests:
 key=q['id'];path=R/'originals'/f'{key}.png'
 if not path.exists():continue
 im=Image.open(path).convert('RGB').resize((768,768),Image.Resampling.LANCZOS);a=np.asarray(im).astype(float);hsv=np.asarray(im.convert('HSV')).astype(float);h=hsv[:,:,0]*360/255;s=hsv[:,:,1]/255;v=hsv[:,:,2]
 r,g,b=a.transpose(2,0,1);lum=.2126*r+.7152*g+.0722*b;local=grey_closing(lum,size=(7,7));layers=np.zeros((*r.shape,3),dtype='uint8')
 counts=[]
 # A bag's brown handles/side panels belong to the bag, never to footwear.
 bag_trim=np.zeros(r.shape,bool)
 if q['shape'].get('bag'):
  br=(h>=10)&(h<40)&(s>.20)&(v>25)&(v<249)
  ye=(h>=40)&(h<76)&(s>.20)&(v>25)&(v<249)
  yc,_=label(ye);sizes=np.bincount(yc.ravel());sizes[0]=0;seed=yc==int(sizes.argmax())
  cc,_=label(binary_dilation(br|ye,iterations=3));labels=np.unique(cc[seed]);labels=labels[labels!=0]
  bag_trim=br&np.isin(cc,labels)
 for i,slot in enumerate(q['slots']):
  lo,hi=ranges[slot['source']];raw=(h>=lo)&(h<hi)&(s>.20)&(v>25)&(v<249)
  if slot['source']=='brown':raw&=~bag_trim
  if slot['source']=='yellow':raw|=bag_trim
  if slot['source']=='rose':raw|=(h<8)&(s>.20)&(v>25)&(v<249)
  cc,n=label(raw);sizes=np.bincount(cc.ravel());good=np.where(sizes>20)[0];good=good[good!=0];raw=np.isin(cc,good)
  if raw.sum()<60:raise ValueError((key,slot,int(raw.sum())))
  med=np.percentile(lum[raw],65);closed=binary_closing(raw,iterations=1)
  holes=binary_fill_holes(closed)&~closed;cc,n=label(holes);sizes=np.bincount(cc.ravel());good=np.where((sizes>0)&(sizes<160))[0];good=good[good!=0];m=closed|raw|np.isin(cc,good)
  m|=binary_dilation(m,iterations=1)&(lum<190)&(s>.15)
  m&=layers[:,:,0]==0
  # Running shoes (2026-10-14) have two-tone mesh panels at ~0.85-0.9 of the base; only the collar opening (<0.78) is shadow.
  runner=slot['field']=='shoeColor' and q['shape'].get('shoe')=='운동화'
  if runner:  # drop specks on neighbouring garment outlines; a shoe is one large piece
   cc,n=label(m);sizes=np.bincount(cc.ravel());good=np.where(sizes>=300)[0];good=good[good!=0];m=np.isin(cc,good)
  outer=distance_transform_edt(m)<=2.3;ln=np.clip((local-lum-1)/max(med*.33,18),0,1);ln=np.maximum(ln,np.where(outer,np.clip((med-lum)/(med*.48),0,1),0))
  clean=gaussian_filter(local*m,1)/np.maximum(gaussian_filter(m.astype(float),1),1e-6)
  sh=median_filter(clean<med*(.80 if runner else .90),size=3).astype(float)
  layers[:,:,0][m]=i+1;layers[:,:,1][m]=np.rint(ln[m]*255).astype('uint8');layers[:,:,2][m]=np.rint(sh[m]*127).astype('uint8')+outer[m].astype('uint8')*128
  counts.append(int(m.sum()))
 if key in SHADOW_FRINGE_NEUTRAL:  # 2026-10-18: grey out blue spill in the neutral trouser cast shadow
  a,im=neutral_shadow_fringe(a,layers,q['slots'])
 buf=io.BytesIO();Image.fromarray(layers).save(buf,format='PNG');(OUT/f'{key}-layers.png').write_bytes(buf.getvalue())
 buf=io.BytesIO();im.save(buf,format='WEBP',quality=94,method=4);(OUT/f'{key}.webp').write_bytes(buf.getvalue())
 for mode in ['contrast','light','dark']:
  result=a.copy()
  for i,slot in enumerate(q['slots']):
   c=pal[slot['field']] if mode=='contrast' else '#e3ddcf' if mode=='light' else '#26334b'
   target=np.array([int(c[z:z+2],16) for z in (1,3,5)],float);L=target@[.2126,.7152,.0722]
   m=layers[:,:,0]==i+1;ln=layers[:,:,1]/255.;sh=(layers[:,:,2]%128)/127.;outer=layers[:,:,2]>=128
   edge=target*.67 if L>=100 else np.maximum(target*.50,13);detail=target*.77 if L>=100 else np.maximum(target*.63,18);pen=np.where(outer[:,:,None],edge,detail)
   result[m]=(target*(1-.13*sh[:,:,None])*(1-ln[:,:,None])+pen*ln[:,:,None])[m]
  assert np.array_equal(result[layers[:,:,0]==0],a[layers[:,:,0]==0])
  Image.fromarray(np.rint(result).astype('uint8')).save(P/f'{key}-{mode}.jpg')
 checks.append({'id':key,'pixels':counts,'max_region':int(layers[:,:,0].max())})
 if key in DENIM_CUFFS:mark_cuffs(key)  # 2026-10-15: lighter inside of rolled jeans cuffs (after previews)
