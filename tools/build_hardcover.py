from PIL import Image, ImageDraw
import numpy as np
def spad(a,pads,step=50):
    # reflect in small steps so only the text-free edge band is ever mirrored
    (t,b),(l,r)=pads
    while t or b or l or r:
        st,sb,sl,sr=[min(v,step) for v in (t,b,l,r)]
        a=np.pad(a,((st,sb),(sl,sr),(0,0)),mode='symmetric')
        t,b,l,r=t-st,b-sb,l-sl,r-sr
    return a
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
DPI=300
PAGES=186
WRAP=0.591; BX=0.197; BY=0.236; TW=6.0; TH=9.0
SPINE=round(PAGES*0.002252+0.189,3)      # 0.608"
BOARD_W=TW+BX; BOARD_H=TH+BY
W_IN=2*WRAP+2*BOARD_W+SPINE; H_IN=10.417
px=lambda i: int(round(i*DPI))
W,H=px(W_IN),px(H_IN)
src=np.asarray(Image.open('source_paperback.png').convert('RGB'))
SP_L,SP_R=1836,1965                      # cyan spine cols in source
back,front=src[:,:SP_L],src[:,SP_R:]
cyan=np.array([105,198,213],np.uint8)
top=px(WRAP+BY/2)-37                     # source trim top (37.5px bleed) -> board trim top
bot=H-top-src.shape[0]
xb_spine=px(WRAP+BOARD_W); xf_spine=px(WRAP+BOARD_W+SPINE)
# back: trim right edge sits BX inside the board (away from the hinge)
back_trim_r=px(WRAP+BOARD_W-BX)
bl=back_trim_r-back.shape[1]
B=spad(back,((top,bot),(bl,xb_spine-back_trim_r)))
# front: trim left edge sits BX inside the board
front_trim_l=px(WRAP+BOARD_W+SPINE+BX)
F=spad(front,((top,bot),(front_trim_l-xf_spine,W-front_trim_l-front.shape[1])))
S=np.tile(cyan,(H,xf_spine-xb_spine,1))
strip=src[:,1840:1961]
x0=(S.shape[1]-strip.shape[1])//2
S[top:top+src.shape[0],x0:x0+strip.shape[1]]=strip
out=np.concatenate([B,S,F],axis=1)
assert out.shape[:2]==(H,W),out.shape
img=Image.fromarray(out)
img.save('hc.jpg',quality=97,subsampling=0,dpi=(DPI,DPI))
c=canvas.Canvas('ARRIVE_hardcover_6x9_186p_cover.pdf',pagesize=(W_IN*72,H_IN*72))
c.setTitle('HARDCOVER_6.000x9.000_186_BW_WHITE'); c.setAuthor('Giuseppe Nicola Molinari')
c.drawImage(ImageReader('hc.jpg'),0,0,W_IN*72,H_IN*72); c.save()
# guide preview
g=img.copy(); d=ImageDraw.Draw(g,'RGBA')
def r(x0,y0,x1,y1,col): d.rectangle([px(x0),px(y0),px(x1),px(y1)],outline=col,width=5)
d.rectangle([0,0,W,px(WRAP)],fill=(255,0,0,70)); d.rectangle([0,H-px(WRAP),W,H],fill=(255,0,0,70))
d.rectangle([0,0,px(WRAP),H],fill=(255,0,0,70)); d.rectangle([W-px(WRAP),0,W,H],fill=(255,0,0,70))
for x in (WRAP+BOARD_W-0.394, WRAP+BOARD_W+SPINE):
    d.rectangle([px(x),px(WRAP),px(x+0.394),H-px(WRAP)],fill=(255,200,0,80))
r(WRAP+BOARD_W,0,WRAP+BOARD_W+SPINE,H_IN,(0,255,0,255))
g.resize((W//4,H//4)).save('hc_guides_preview.png')
print(f'{W_IN:.3f} x {H_IN:.3f} in, spine {SPINE}, px {W}x{H}')
