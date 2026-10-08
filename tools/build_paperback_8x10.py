"""KDP paperback wrap cover: They Say They Wore Them (8x10, 226 pages, B&W white paper).

Run from the repo root:  python3 tools/build_paperback_8x10.py
Back and spine are vector text (fonts embedded); the front is the supplied artwork
upscaled to 300 dpi with mirrored bleed.
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Frame
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

DPI = 300
PAGES = 226
BLEED = 0.125
TW, TH = 8.0, 10.0
SPINE = round(PAGES * 0.002252, 3)          # white paper, B&W -> 0.509"
W_IN = 2 * BLEED + 2 * TW + SPINE           # 16.759"
H_IN = 2 * BLEED + TH                       # 10.25"
SX0, SX1 = BLEED + TW, BLEED + TW + SPINE   # spine edges
BAND = 0.67                                 # navy band height above trim bottom (from front art)
OUT = 'TSTWT_paperback_8x10_226p_cover'
px = lambda i: int(round(i * DPI))
pt = lambda i: i * 72

FONTS = 'tools/fonts/'
for name, f in [('B4', 'Barlow-400'), ('B4i', 'Barlow-400i'), ('B5', 'Barlow-500'), ('B5i', 'Barlow-500i'),
                ('B6', 'Barlow-600'), ('B7', 'Barlow-700'), ('BC6', 'BarlowCondensed-600'),
                ('BC7', 'BarlowCondensed-700'), ('BC8', 'BarlowCondensed-800')]:
    pdfmetrics.registerFont(TTFont(name, FONTS + f + '.ttf'))
addMapping('B4', 0, 0, 'B4'); addMapping('B4', 1, 0, 'B7'); addMapping('B4', 0, 1, 'B4i'); addMapping('B4', 1, 1, 'B7')

rgb = lambda r, g, b: Color(r / 255, g / 255, b / 255)
WHITE = rgb(252, 252, 252)
NAVY = rgb(11, 17, 38)        # title ink
BAND_C = (5, 27, 57)          # bottom band
BANDC = rgb(*BAND_C)
TEAL = rgb(0, 121, 154)
CYAN = rgb(60, 190, 225)      # "Academy" cyan, readable on navy
GREY = rgb(70, 78, 96)

# ---------------- front artwork -> 300 dpi with bleed ----------------
src = Image.open('source/TSTWT_front_8x10.jpg').convert('RGB')
assert src.size == (1600, 2000)
up = src.resize((px(TW), px(TH)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
def keyed(box):
    # crop from the navy band with the band colour keyed out to alpha
    p = np.asarray(src.crop(box)).astype(float)
    al = np.clip((np.sqrt(((p - np.array(BAND_C)) ** 2).sum(2)) - 40) * 2.2, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([p.astype(np.uint8), al]), 'RGBA')

# the supplied art has "Academy" ~0.05" from the trim; rebuild the band so it sits in the safe zone
k = px(TW) / src.width
band_top = int(round(1867 * k))
up.paste(BAND_C, (0, band_top, up.width, up.height))
grp = keyed((505, 1874, 1100, 1994))
grp = grp.resize((int(grp.width * k * 0.8), int(grp.height * k * 0.8)), Image.LANCZOS)
gx = int((505 + 1100) / 2 * k - grp.width / 2)
gy = up.height - px(0.135) - grp.height
assert gy >= band_top
up.paste(grp, (gx, gy), grp)
a = np.asarray(up)
b = px(BLEED)
fw, fh = px(TW + BLEED), px(H_IN)
a = np.pad(a, ((b, fh - b - a.shape[0]), (0, fw - a.shape[1]), (0, 0)), mode='symmetric')
Image.fromarray(a).save('front_300.jpg', quality=96, subsampling=0, dpi=(DPI, DPI))

# logo from the front band, background keyed out
logo = keyed((515, 1868, 648, 1996))
logo = logo.resize((logo.width * 3, logo.height * 3), Image.LANCZOS)
logo.save('logo.png')

# ---------------- PDF ----------------
c = canvas.Canvas(OUT + '.pdf', pagesize=(pt(W_IN), pt(H_IN)), initialFontName='B4')
c.setTitle('PAPERBACK_8.000x10.000_226_BW_WHITE'); c.setAuthor('Dr. Enzo Pasciuti')

# background: back + spine white, navy band across back and spine
c.setFillColor(WHITE); c.rect(0, 0, pt(SX1), pt(H_IN), stroke=0, fill=1)
c.setFillColor(BANDC); c.rect(0, 0, pt(SX1) + 1, pt(BLEED + BAND), stroke=0, fill=1)
c.drawImage(ImageReader('front_300.jpg'), pt(SX1), 0, pt(W_IN - SX1), pt(H_IN))

# ---------------- back cover ----------------
L, R = BLEED + 0.7, BLEED + TW - 0.7
CW = R - L
top = BLEED + TH - 0.62

c.setFillColor(TEAL); c.setFont('B7', 10.5)
c.drawString(pt(L), pt(top), 'FOR ORTHODONTISTS, DENTISTS AND THE TEAMS WHO SUPPORT THEM'.replace('', ' ')[1:-1])

def lines(y, parts, size, lead, font='BC8'):
    for line in parts:
        x = pt(L)
        for txt, col in line:
            c.setFillColor(col); c.setFont(font, size); c.drawString(x, pt(y), txt)
            x += pdfmetrics.stringWidth(txt, font, size)
        y -= lead
    return y

y = lines(top - 0.62, [[('EVERY PATIENT SAYS THEY WORE THEM.', NAVY)],
                       [('THE TEETH ', TEAL), ('TELL A DIFFERENT STORY.', TEAL)]], 34, 0.5)
c.setStrokeColor(TEAL); c.setLineWidth(2.2)
c.line(pt(L), pt(y + 0.22), pt(L + 0.9), pt(y + 0.22))

body = ParagraphStyle('body', fontName='B4', fontSize=11.2, leading=15.6, textColor=NAVY, spaceAfter=8.5)
lead = ParagraphStyle('lead', parent=body, fontName='B5', fontSize=12.4, leading=17)
head = ParagraphStyle('head', parent=body, fontName='BC7', fontSize=14, leading=17, textColor=TEAL, spaceBefore=3, spaceAfter=5)
bul = ParagraphStyle('bul', parent=body, leftIndent=16, bulletIndent=0, spaceAfter=4.5, bulletFontName='B7',
                     bulletColor=TEAL, bulletFontSize=13)
close = ParagraphStyle('close', parent=body, fontName='B5i', fontSize=12.4, leading=17, textColor=TEAL, spaceBefore=6)

story = [
    Paragraph('Clear aligners only move teeth when they are in the mouth. Yet wear time, the single variable '
              'that decides whether a treatment plan becomes a result, is the one clinicians control least and measure worst.', lead),
    Paragraph('Patients are not simply lazy, and most are not lying on purpose. They are human, and human behaviour follows '
              'predictable patterns: optimism about their own habits, the pull of the present moment, the wish to give the '
              'answer the doctor wants to hear, and motivation that fades as soon as the novelty does.', body),
    Paragraph('In <b>They Say They Wore Them</b>, Dr. Enzo Pasciuti brings the psychology of behaviour into the operatory, '
              'explaining why compliance breaks down and how to design treatment so that it doesn’t.', body),
    Paragraph('INSIDE YOU WILL DISCOVER', head),
]
for t in ['Why patients overestimate their wear time, and how to recognise non-compliance before it derails a case',
          'The psychological drivers that make motivation rise and fall over the course of treatment',
          'How to communicate expectations at consultation, delivery and every check-up',
          'Practical clinical protocols for monitoring, refinements and getting off-track cases back on course',
          'How to build a practice system where compliance becomes the default, not the exception']:
    story.append(Paragraph(t, bul, bulletText='\u2022'))
story.append(Paragraph('Because the best treatment plan in the world only works if the aligners are actually worn.', close))

AUTH_TOP = BLEED + BAND + 1.95
f = Frame(pt(L), pt(AUTH_TOP + 0.25), pt(CW), pt(y - AUTH_TOP - 0.05), leftPadding=0, rightPadding=0,
          topPadding=0, bottomPadding=0, showBoundary=0)
left = f.addFromList(story, c)
assert not story, 'back copy overflows its frame'

# author block (kept clear of the barcode zone, bottom-right)
c.setStrokeColor(rgb(205, 212, 222)); c.setLineWidth(0.8)
c.line(pt(L), pt(AUTH_TOP + 0.08), pt(R), pt(AUTH_TOP + 0.08))
c.setFillColor(NAVY); c.setFont('BC7', 13.5); c.drawString(pt(L), pt(AUTH_TOP - 0.2), 'ABOUT THE AUTHOR')
auth = ParagraphStyle('auth', parent=body, fontSize=10.4, leading=14.2, textColor=GREY)
af = Frame(pt(L), pt(BLEED + BAND + 0.18), pt(CW * 0.66), pt(1.52), leftPadding=0, rightPadding=0,
           topPadding=0, bottomPadding=0)
ast = [Paragraph('<b>Dr. Enzo Pasciuti</b> is the founder of Pasciuti Orthodontics and of the Enzo Pasciuti Academy, '
                 'where clinicians learn to combine sound biomechanics with an understanding of the people wearing '
                 'the appliances. This book distils that approach into a method any practice can apply from Monday morning.', auth)]
af.addFromList(ast, c); assert not ast, 'author copy overflows'

# back band: subject line in white
c.setFillColor(rgb(255, 255, 255)); c.setFont('B6', 9)
c.drawString(pt(L), pt(BLEED + BAND / 2 - 0.04),
             'CLEAR ALIGNER THERAPY  ·  PATIENT PSYCHOLOGY  ·  CLINICAL PROTOCOLS')

# ---------------- spine ----------------
cx = (SX0 + SX1) / 2
def spine_text(y_start, parts, size, font):
    # reads top to bottom (letter tops face the front cover)
    cap = pdfmetrics.getFont(font).face.capHeight / 1000 * size
    c.saveState(); c.translate(pt(cx), pt(y_start)); c.rotate(-90)
    x = 0
    for txt, col in parts:
        c.setFillColor(col); c.setFont(font, size); c.drawString(x, -cap / 2, txt)
        x += pdfmetrics.stringWidth(txt, font, size)
    c.restoreState()
    return x / 72

t_parts = [('THEY SAY THEY ', NAVY), ('WORE', TEAL), (' THEM', NAVY)]
tl = spine_text(BLEED + TH - 0.45, t_parts, 23, 'BC8')
a_parts = [('DR. ENZO PASCIUTI', NAVY)]
aw = sum(pdfmetrics.stringWidth(t, 'B6', 12) for t, _ in a_parts) / 72
spine_text(BLEED + BAND + 0.3 + aw, a_parts, 12, 'B6')
assert BLEED + TH - 0.45 - tl > BLEED + BAND + 0.3 + aw + 0.4, 'spine text collides'
lw = 0.30
c.drawImage(ImageReader('logo.png'), pt(cx - lw / 2), pt(BLEED + (BAND - lw) / 2 + 0.01), pt(lw), pt(lw), mask='auto')
c.showPage(); c.save()

# ---------------- previews ----------------
import subprocess, os
subprocess.run(['pdftoppm', '-r', '100', '-png', '-singlefile', OUT + '.pdf', 'prev'], check=True)
img = Image.open('prev.png').convert('RGB'); img.save(OUT.replace('_cover', '_preview') + '.png')
s = img.width / W_IN
g = img.copy(); d = ImageDraw.Draw(g, 'RGBA')
q = lambda v: int(round(v * s))
H = img.height
for box in [(0, 0, q(W_IN), q(BLEED)), (0, H - q(BLEED), q(W_IN), H), (0, 0, q(BLEED), H), (q(W_IN - BLEED), 0, q(W_IN), H)]:
    d.rectangle(box, fill=(255, 0, 0, 80))                                   # bleed (trimmed)
for x0, x1 in [(BLEED + 0.125, BLEED + TW - 0.125), (SX1 + 0.125, W_IN - BLEED - 0.125)]:
    d.rectangle([q(x0), q(BLEED + 0.125), q(x1), H - q(BLEED + 0.125)], outline=(255, 160, 0, 255), width=2)  # safe
d.rectangle([q(SX0), 0, q(SX1), H], outline=(0, 200, 0, 255), width=2)     # spine
d.rectangle([q(SX0 + 0.0625), 0, q(SX1 - 0.0625), H], outline=(0, 200, 0, 140), width=1)
bx1, by1 = BLEED + TW - 0.25, BLEED + 0.25                                   # KDP barcode 2" x 1.2"
d.rectangle([q(bx1 - 2), H - q(by1 + 1.2), q(bx1), H - q(by1)], fill=(255, 255, 255, 200), outline=(0, 0, 255, 255), width=2)
d.text((q(bx1 - 1.75), H - q(by1 + 0.7)), 'KDP BARCODE AREA', fill=(0, 0, 255, 255))
g.save(OUT.replace('_cover', '_guide_preview') + '.png')
for tmp in ('front_300.jpg', 'logo.png', 'prev.png'):
    os.remove(tmp)
print(f'{W_IN:.3f} x {H_IN:.3f} in, spine {SPINE} in, {px(W_IN)}x{px(H_IN)} px @ {DPI} dpi')
