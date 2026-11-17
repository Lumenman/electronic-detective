"""Printable suspect cards (vector re-draw + portraits from the scan) and a blank Case Fact Sheet.

python print/make_print.py   ->  print/cards.pdf, print/case_fact_sheet.pdf
Scan is assumed 300 dpi at 1:1 (page 592x790 pt = 2470x3294 px), so card size comes from it.
"""
import io, os
import numpy as np, pymupdf
from PIL import Image, ImageOps
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = os.path.join(HERE, '..', 'materials', 'electronic_detective_cards.pdf')
MM = 72 / 25.4
PX = 25.4 / 300                       # mm per scan pixel

# ---------------------------------------------------------------- data
SUSPECTS = [  # name, occupation, status, private questions (13, 14 on every card)
    ("LENNY LITTLE", "Bartender", "Married to #11, Ivy Little", (1, 2, 9)),
    ("AL FAROOK", "Tycoon", "Playboy", (2, 3, 9)),
    ("PEPE PEREZ", "Flamenco Dancer", "Married to #13, Piper Perez", (3, 4, 5)),
    ("TONY RACHETI", "Promoter", "Married to #14, Dina Racheti", (4, 5, 9)),
    ("MICKEY O'MALLEY", "Retired Cop", "Single", (1, 4, 9)),
    ("MAX FINEFLUGLE", "Producer", "Married to #16, Joan Fineflugle", (5, 6, 12)),
    ("RIPP RAPP", "Dockworker", "Single", (2, 5, 12)),
    ("BUSTER BAILEY", "Basketball Player", "Single", (3, 5, 12)),
    ("ROCKY ROLL", "Musician", "Married to #19, Candy Roll", (1, 5, 12)),
    ("LING TONG", "Restaurant Owner", "Bachelor", (7, 8, 12)),
    ("IVY LITTLE", "Landlady", "Married to #1, Lenny Little", (6, 7, 11)),
    ("LUCY TUMBLE", "Secretary", "Still Looking", (2, 6, 11)),
    ("PIPER PEREZ", "Latin Singer", "Married to #3, Pepe Perez", (3, 7, 11)),
    ("DINA RACHETI", "Socialite", "Married to #4, Tony Racheti", (1, 6, 11)),
    ("EILEEN STELLAR", "Actress", "Eligible", (4, 7, 11)),
    ("JOAN FINEFLUGLE", "Accountant", "Married to #6, Max Fineflugle", (6, 8, 10)),
    ("ROSE PETTLE", "Gossip Columnist", "Unattached", (2, 7, 10)),
    ("DORIS DILL", "Lady Newscaster", "Not Looking", (1, 8, 10)),
    ("CANDY ROLL", "Groupie", "Married to #9, Rocky Roll", (3, 8, 10)),
    ("SING WONG", "Waitress", "Single", (4, 8, 10)),
]
# question -> (text with **bold** parts, answer kind)
QUESTIONS = {
    1: ("Did the murderer go to the **EAST SIDE**?", "yn"),
    2: ("Did a **MALE** do it?", "yn"),
    3: ("What **AREA** did the murderer go to?", "area2"),
    4: ("Was the **MURDER WEAPON** a .38?", "yn"),
    5: ("Where was the .38 hidden?", "place"),
    6: ("Where was the .45 hidden?", "place"),
    7: ("Which **PLACE** contained only 3 suspects?", "place"),
    8: ("Did the murderer go to **PLACE** A, B or C?", "yn"),
    9: ("Were you on the **EAST SIDE**?", "yn"),
    10: ("Which **AREA** were you in?", "area"),
    11: ("Were you at **PLACE** A, B or C?", "yn"),
    12: ("Were you where a **WEAPON** was hidden?", "yn"),
    13: ("Are an odd-numbered suspect's **PRINTS** on the .38?", "prints"),
    14: ("Are an odd-numbered suspect's **PRINTS** on the .45?", "prints"),
}

# ---------------------------------------------------------------- colours
def rgb(h): return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
BLACK, WHITE = (0, 0, 0), (1, 1, 1)
CREAM, MAGENTA = WHITE, rgb('#CC3273')   # originals are white card stock (scan looks cream from ageing)
KEY, KEY_DARK, KEY_LIGHT = rgb('#3FA7C4'), rgb('#1F6F88'), rgb('#7CCBE0')
CUT = (0.55, 0.55, 0.55)

# ---------------------------------------------------------------- scan -> card crops
def scan_cards():
    """Return 20 card crops (PIL) in order 1..20, found by the cream colour of the card stock."""
    doc = pymupdf.open(SCAN)
    out = []
    for i, page in enumerate(doc):
        im = Image.open(io.BytesIO(doc.extract_image(page.get_images()[0][0])['image'])).convert('RGB')
        a = np.asarray(im).astype(int)
        m = ((a[..., 0] - a[..., 2]) > 14) | (a.max(2) < 90)
        m = ndimage.binary_closing(m, iterations=6)
        m = ndimage.binary_opening(ndimage.binary_fill_holes(m), iterations=15)
        objs = [s for s in ndimage.find_objects(ndimage.label(m)[0])
                if (s[0].stop - s[0].start) * (s[1].stop - s[1].start) > 200000]
        for s in [s for s in objs if s[0].stop - s[0].start > 1000]:   # two touching cards -> split
            objs.remove(s)
            rows = m[s].mean(1)
            mid = s[0].start + 700 + int(np.argmin(rows[700:900]))
            objs += [(slice(s[0].start, mid), s[1]), (slice(mid, s[0].stop), s[1])]
        objs.sort(key=lambda s: (round(s[0].start / 400), s[1].start))
        out += [im.crop((s[1].start, s[0].start, s[1].stop, s[0].stop)) for s in objs]
    assert len(out) == 20, f'expected 20 cards in scan, found {len(out)}'
    return out

def portraits(card):
    """Two portrait images (left: face, right: profile) cut out of a card crop."""
    a = np.asarray(card).astype(int)
    h, w, _ = a.shape
    nc = np.abs(a - np.array([235, 222, 205])).sum(2) > 90
    reg = np.zeros_like(nc)
    reg[int(.12 * h):int(.55 * h), int(.05 * w):int(.52 * w)] = True
    lab = ndimage.label(ndimage.binary_opening(nc & reg, iterations=4))[0]
    ps = sorted(ndimage.find_objects(lab), key=lambda q: -(q[0].stop - q[0].start) * (q[1].stop - q[1].start))[:2]
    res = []
    for q in sorted(ps, key=lambda q: q[1].start):
        bw, bh = q[1].stop - q[1].start, q[0].stop - q[0].start
        assert 190 < bw < 250 and 240 < bh < 290, f'odd portrait box {bw}x{bh}'
        k = 5  # inset: drop scan edge / slight rotation slivers
        crop = card.crop((q[1].start + k, q[0].start + k, q[1].stop - k, q[0].stop - k))
        res.append(ImageOps.autocontrast(crop, cutoff=0.3))
    return res

def png(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()

# ---------------------------------------------------------------- drawing helpers (mm, page-relative)
class Pen:
    def __init__(self, page, ox=0, oy=0):
        self.p, self.ox, self.oy = page, ox, oy

    def pt(self, x, y): return pymupdf.Point((self.ox + x) * MM, (self.oy + y) * MM)
    def rect(self, x, y, w, h): return pymupdf.Rect(self.pt(x, y), self.pt(x + w, y + h))

    def box(self, x, y, w, h, color=BLACK, fill=None, width=0.25, radius=None):
        self.p.draw_rect(self.rect(x, y, w, h), color=color, fill=fill, width=width * MM,
                         radius=radius)

    def line(self, x0, y0, x1, y1, color=BLACK, width=0.25, dashes=None):
        self.p.draw_line(self.pt(x0, y0), self.pt(x1, y1), color=color, width=width * MM, dashes=dashes)

    def poly(self, pts, color=None, fill=None, width=0.2, close=True):
        self.p.draw_polyline([self.pt(*q) for q in pts], color=color, fill=fill, width=width * MM,
                             closePath=close)

    def text(self, x, y, s, size, bold=False, color=BLACK, align='l', sx=1.0):
        """y is the baseline; size in pt; sx < 1 squeezes the text horizontally."""
        f = 'hebo' if bold else 'helv'
        w = pymupdf.get_text_length(s, fontname=f, fontsize=size) / MM * sx
        x -= {'l': 0, 'c': w / 2, 'r': w}[align]
        morph = (self.pt(x, y), pymupdf.Matrix(sx, 1)) if sx != 1 else None
        self.p.insert_text(self.pt(x, y), s, fontname=f, fontsize=size, color=color, morph=morph)
        return x + w

    def rich(self, x, y, s, size, color=BLACK):
        """'**bold**' segments; regular parts also bold on the cards (question text is all bold)."""
        for i, part in enumerate(s.split('**')):
            if part: x = self.text(x, y, part, size, bold=True, color=color)
        return x

    def image(self, x, y, w, h, data):
        self.p.insert_image(self.rect(x, y, w, h), stream=data, keep_proportion=False)

# 7-segment font like the console LEDs:   a=top b=top-right c=bottom-right d=bottom e=bottom-left f=top-left g=mid
SEG = {'0': 'abcdef', '3': 'abcdg', '4': 'bcfg', '5': 'acdfg', 'Y': 'bcfg', 'E': 'adefg', 'S': 'acdfg',
       'N': 'abcef', 'O': 'abcdef', 'A': 'abcefg', 'b': 'cdefg', 'C': 'adef', 'd': 'bcdeg', 'F': 'aefg', ' ': ''}

def seg7(pen, x, y, s, h=2.0, color=MAGENTA, gap=None):
    """Draw string s in 7-seg; (x, y) = left baseline. Returns end x."""
    w = h * 0.55
    gap = h * 0.3 if gap is None else gap
    lw = h * 0.12
    for ch in s:
        t, mdl, b = y - h, y - h / 2, y
        segs = {'a': (x, t, x + w, t), 'b': (x + w, t, x + w, mdl), 'c': (x + w, mdl, x + w, b),
                'd': (x, b, x + w, b), 'e': (x, mdl, x, b), 'f': (x, t, x, mdl), 'g': (x, mdl, x + w, mdl)}
        for sg in SEG[ch]:
            pen.line(*segs[sg], color=color, width=lw)
        x += (w * 0.6 if ch == ' ' else w) + gap
    return x - gap

def seg7_width(s, h=2.0):
    w = h * 0.55
    return sum(w * 0.6 if c == ' ' else w for c in s) + h * 0.3 * (len(s) - 1)

def rounded(x0, y0, x1, y1, r, corners='tl tr br bl', n=6):
    """Polygon points of a rectangle with rounded corners (clockwise from top-left)."""
    c = corners.split()
    def arc(cx, cy, a0):
        return [(cx + r * np.cos(np.radians(a0 + 90 * k / n)), cy + r * np.sin(np.radians(a0 + 90 * k / n)))
                for k in range(n + 1)]
    pts = []
    pts += arc(x0 + r, y0 + r, 180) if 'tl' in c else [(x0, y0)]
    pts += arc(x1 - r, y0 + r, 270) if 'tr' in c else [(x1, y0)]
    pts += arc(x1 - r, y1 - r, 0) if 'br' in c else [(x1, y1)]
    pts += arc(x0 + r, y1 - r, 90) if 'bl' in c else [(x0, y1)]
    return pts

# ---------------------------------------------------------------- one card
CW, CH, TAB = 97.0, 64.0, 6.0          # card incl. index tab; body is CH-TAB tall (original tab ~5 mm)


NUM_PT, NUM_SX = 13.0, 0.76               # tab number: digits 3.3 mm tall (original 2.4 mm)


def tab_end(n):
    """Index tab grows with the card number up to full width on #20 (original: 14.7 mm on #1, step 4.35 mm).
    #1 starts shorter here so each step, i.e. each number's visible window, is wider: 4.74 mm."""
    return TAB1 + (n - 1) * (CW - TAB1) / 19


TAB1 = 7.0


def key(pen, x, y, s, size=6.8):
    """Blue keypad key with a bevel, like the console buttons."""
    i = size * 0.16
    pen.box(x, y, size, size, color=KEY_DARK, fill=KEY, width=0.25)
    pen.box(x + i, y + i, size - 2 * i, size - 2 * i, color=KEY_DARK, fill=KEY_LIGHT if not s else KEY, width=0.2)
    for (ax, ay), (bx, by) in [((x, y), (x + i, y + i)), ((x + size, y), (x + size - i, y + i)),
                               ((x, y + size), (x + i, y + size - i)), ((x + size, y + size), (x + size - i, y + size - i))]:
        pen.line(ax, ay, bx, by, color=KEY_DARK, width=0.2)
    if s:
        pen.text(x + size / 2, y + size * 0.72, s, size * 1.75, bold=True, color=WHITE, align='c')


def arc(cx, cy, r, a0, n=6):
    return [(cx + r * np.cos(np.radians(a0 + 90 * k / n)), cy + r * np.sin(np.radians(a0 + 90 * k / n)))
            for k in range(n + 1)]


def card_outline(n):
    """Cut path: tab on the top-left, then the card body, clockwise."""
    te = tab_end(n)
    if te >= CW - 2:                            # last card: tab is the whole top edge
        return rounded(0, 0, CW, CH, 2.0)
    return (arc(1.5, 1.5, 1.5, 180) + arc(te - 1.5, 1.5, 1.5, 270) + [(te, TAB)]
            + arc(CW - 2, TAB + 2, 2, 270) + arc(CW - 2, CH - 2, 2, 0) + arc(2, CH - 2, 2, 90))


def draw_card(pen, n, imgs):
    name, occ, status, qs = SUSPECTS[n - 1]
    te = tab_end(n)
    outline = card_outline(n)
    pen.poly(outline, fill=CREAM, color=None)
    # black index tab with the number at its right end
    pen.poly(rounded(0, 0, te, TAB, 1.5, 'tl tr'), fill=BLACK)
    # number squeezed and tight to the tab end, as on the originals: in the tray it must show past card n-1's tab
    left = pen.text(te - 0.4, TAB - 1.3, str(n), NUM_PT, bold=True, color=WHITE, align='r', sx=NUM_SX)
    left -= pymupdf.get_text_length(str(n), 'hebo', NUM_PT) / MM * NUM_SX
    assert n == 1 or left > tab_end(n - 1) + 0.3, f'card {n}: number hidden by tab of card {n - 1}'
    # portraits
    for k, im in enumerate(imgs):
        pen.image(6.9 + k * 20.5, 9.8, 18.4, 22.4, png(im))
    # keypad number
    d = f'{n:2d}'
    key(pen, 78.3, 8.9, d[0].strip())
    key(pen, 87.2, 8.9, d[1])
    # name block
    nsize = 13.5
    while pymupdf.get_text_length(name, 'hebo', nsize) / MM > CW - 47.5 - 2: nsize -= 0.25
    pen.text(47.5, 25.0, name, nsize, bold=True)
    pen.text(47.5, 28.6, occ, 7.2)
    pen.text(47.5, 31.6, status, 7.2)
    # questions
    qsize = 7.0
    y, R = 37.0, 93.6
    for q in tuple(qs) + (13, 14):
        txt, kind = QUESTIONS[q]
        pen.text(8.0, y, f'{q}.', qsize, bold=True, align='r')
        pen.rich(8.9, y, txt, qsize)
        if kind in ('area2', 'prints'):
            y += 2.9
        if kind == 'yn':
            seg7(pen, 78.3, y, 'YES'); seg7(pen, R - seg7_width('NO'), y, 'NO')
        elif kind == 'place':
            seg7(pen, 78.3, y, 'AbCdEF', gap=(R - 78.3 - seg7_width('AbCdEF', 2.0) + 5 * 0.6) / 5)
        elif kind in ('area', 'area2'):
            x = 50.5
            for dgt, word in (('3', 'Uptown'), ('4', 'Midtown'), ('5', 'Downtown')):
                x = seg7(pen, x, y, dgt) + 0.9
                x = pen.text(x, y, word, 7.0, color=MAGENTA) + 1.6
        elif kind == 'prints':
            x = pen.text(R, y, '(don\'t know)', 7.0, color=MAGENTA, align='r')
            x0 = R - pymupdf.get_text_length("(don't know)", 'helv', 7.0) / MM - 1.0
            x0 -= seg7_width('00 000 00')
            seg7(pen, x0, y, '00 000 00')
            seg7(pen, x0 - 8.5, y, 'NO')
            seg7(pen, x0 - 18.0, y, 'YES')
        y += 3.9
    assert y - 3.9 < CH - 2.5, f'card {n}: questions overflow ({y:.1f} mm)'
    # cut line on the exact outline
    pen.poly(outline, color=CUT, width=0.1)


def crop_marks(pen, x, y, w, h, gap=1.0, length=3.0):
    for cx in (x, x + w):
        for cy in (y, y + h):
            sx = -1 if cx == x else 1
            sy = -1 if cy == y else 1
            pen.line(cx + sx * gap, cy, cx + sx * (gap + length), cy, width=0.15)
            pen.line(cx, cy + sy * gap, cx, cy + sy * (gap + length), width=0.15)


def make_cards(path):
    crops = scan_cards()
    doc = pymupdf.open()
    PW, PH = 210, 297
    GX, GY = 6.0, 6.0                       # gaps between cards hold the crop marks
    cols, rows = 2, 4
    x0 = (PW - cols * CW - (cols - 1) * GX) / 2
    y0 = (PH - rows * CH - (rows - 1) * GY) / 2
    for n in range(1, 21):
        k = (n - 1) % 8
        if k == 0:
            page = doc.new_page(width=PW * MM, height=PH * MM)
            Pen(page).text(PW / 2, 5.5, 'Electronic Detective - suspect cards. Print at 100% (no "fit to page"). '
                           'Cut along the grey outline; corner marks show the card box.', 6.5, color=CUT, align='c')
        cx = x0 + (k % cols) * (CW + GX)
        cy = y0 + (k // cols) * (CH + GY)
        draw_card(Pen(page, cx, cy), n, portraits(crops[n - 1]))
        crop_marks(Pen(page), cx, cy, CW, CH)
    doc.save(path, deflate=True, garbage=3)
    return doc.page_count

# ---------------------------------------------------------------- Case Fact Sheet (A4, blank)
# Layout follows the original sheet (materials/elecdetectfs.jpg, Ideal 5A-3343); place pictograms and gun/fingerprint
# icons are left out.
PLACES = [('A', 'Art Show'), ('B', 'Box at Theatre'), ('C', 'Card Party'), ('D', 'Docks'),
          ('E', 'Embassy'), ('F', 'Factory')]
BLUE = rgb('#3B91C4')                       # sampled from the original sheet


def chk(pen, x, y, s=3.8):
    pen.box(x, y - s + 0.5, s, s, width=0.35)


def section(pen, y, num, title):
    """Big blue section number with its blue title; y = baseline of the number."""
    pen.text(12, y, num, 46, bold=True, color=BLUE)
    pen.text(27, y - 12.5, title, 10.5, bold=True, color=BLUE)


def man(pen, x, y, h=8.0):
    """Pictogram of a man, (x, y) = top centre."""
    u = h / 8
    pen.p.draw_circle(pen.pt(x, y + 0.8 * u), 0.8 * u * MM, fill=BLACK, color=None)
    pen.poly([(x - 1.3 * u, y + 1.8 * u), (x + 1.3 * u, y + 1.8 * u), (x + 1.6 * u, y + 4.6 * u), (x + 1.1 * u, y + 4.6 * u),
              (x + 0.9 * u, y + 3.2 * u), (x + 0.8 * u, y + 4.4 * u), (x + 1.0 * u, y + 8 * u), (x + 0.2 * u, y + 8 * u),
              (x, y + 5.2 * u), (x - 0.2 * u, y + 8 * u), (x - 1.0 * u, y + 8 * u), (x - 0.8 * u, y + 4.4 * u),
              (x - 0.9 * u, y + 3.2 * u), (x - 1.1 * u, y + 4.6 * u), (x - 1.6 * u, y + 4.6 * u)], fill=BLACK)


def woman(pen, x, y, h=8.0):
    """Pictogram of a woman (dress), (x, y) = top centre."""
    u = h / 8
    pen.p.draw_circle(pen.pt(x, y + 0.8 * u), 0.8 * u * MM, fill=BLACK, color=None)
    pen.poly([(x - 0.9 * u, y + 1.8 * u), (x + 0.9 * u, y + 1.8 * u), (x + 1.5 * u, y + 4.2 * u), (x + 1.1 * u, y + 4.3 * u),
              (x + 0.8 * u, y + 3.0 * u), (x + 1.5 * u, y + 5.8 * u), (x + 0.5 * u, y + 5.8 * u), (x + 0.5 * u, y + 8 * u),
              (x + 0.1 * u, y + 8 * u), (x + 0.1 * u, y + 5.8 * u), (x - 0.1 * u, y + 5.8 * u), (x - 0.1 * u, y + 8 * u),
              (x - 0.5 * u, y + 8 * u), (x - 0.5 * u, y + 5.8 * u), (x - 1.5 * u, y + 5.8 * u), (x - 0.8 * u, y + 3.0 * u),
              (x - 1.1 * u, y + 4.3 * u), (x - 1.5 * u, y + 4.2 * u)], fill=BLACK)


def num_keys(pen, x, y, n, s=4.2, size=7.5):
    """Two small key boxes with the suspect number (n=0: empty), like the keypad."""
    d = f'{n:2d}' if n else '  '
    for k in range(2):
        pen.box(x + k * (s + 0.5), y, s, s + 0.4, width=0.3)
        pen.box(x + k * (s + 0.5) + 0.6, y + 0.6, s - 1.2, s - 0.8, width=0.15)
        if d[k] != ' ':
            pen.text(x + k * (s + 0.5) + s / 2, y + s - 0.8, d[k], size, bold=True, align='c')


def make_sheet(path):
    doc = pymupdf.open()
    page = doc.new_page(width=210 * MM, height=297 * MM)
    p = Pen(page)
    L, R = 12, 198
    # header
    p.text(L, 19, 'ELECTRONIC DETECTIVE', 23, bold=True, color=BLUE)
    p.text(L, 25.5, 'CASE FACT SHEET', 12, bold=True, color=BLUE)
    p.text(105, 23.5, 'GAME', 8, bold=True)
    p.box(124, 10.5, R - 124, 9, width=0.45)
    p.text(140, 25.5, 'DETECTIVE', 9.5, bold=True)
    p.text(161, 25.5, '(your name)', 6.5)
    p.line(L, 28, R, 28, width=0.6)

    # ---- 1. murder facts
    section(p, 46, '1', 'THE MURDER FACTS')
    x = 27
    p.text(x, 37, 'WHO?', 9, bold=True, color=BLUE)
    p.text(x, 41.5, 'The victim was', 8.5)
    num_keys(p, 49, 37.6, 0)
    p.text(60, 41.5, '(name)', 6.5)
    p.box(69, 36, 62, 6.5, width=0.4)
    p.text(141, 41.5, 'The body was found at:', 8.5)
    p.box(175.5, 35.5, 7, 7, width=0.45)
    p.text(184, 41.5, 'PLACE', 8.5, bold=True)
    cols = (90, 128, 162)
    rows = [
        (49, 'SEX OF THE MURDERER?', [(0, 'Male'), (1, 'Female')]),
        (56, 'WHERE DID THE MURDERER GO?', [(0, '1. West Side'), (1, '2. East Side')]),
        (62.5, '', [(0, '3. Uptown'), (1, '4. Midtown'), (2, '5. Downtown')]),
        (69.5, 'WEAPON USED?', [(0, '.38'), (1, '.45')]),
    ]
    for y, label, opts in rows:
        p.text(x + 10, y, label, 8.5, bold=True)
        for c, s in opts:
            chk(p, cols[c], y); p.text(cols[c] + 5.5, y, s, 8.5)
    y = 76
    p.text(x + 10, y + 2.5, 'FINGERPRINTS?', 8.5, bold=True)
    for c in (0, 1):
        p.text(cols[c] - 1.5, y, 'Odd #', 8.5, align='r'); chk(p, cols[c], y)
        p.text(cols[c] - 1.5, y + 4.6, 'Even #', 8.5, align='r'); chk(p, cols[c], y + 4.6)
    # who answered Q13/14: only a same-sex suspect at the murder weapon is reliable, known only later
    p.text(cols[2], y + 1.2, 'told by #', 8.5)
    right = cols[2] + 5.5 + pymupdf.get_text_length('5. Downtown', 'helv', 8.5) / MM   # keep within 'Downtown'
    num_keys(p, right - 8.9, y + 1.2 - 3.9, 0)              # same two boxes as 'The victim was'
    p.line(L, 84, R, 84, width=0.6)

    # ---- 2. who was where
    section(p, 102, '2', 'WHO WAS WHERE?')
    p.text(27, 104.5, 'PLACE', 9.5, bold=True)
    # address: oval (side) 112.5-116.5 over box (area) 116.5-122; cartridge 125-132.2
    p.line(45.5, 112.5, 45.5, 122, width=0.3)              # bar spanning oval + box, instead of the brace
    p.text(27, 116.6, 'ADDRESS', 9.5, bold=True); p.text(27, 120.3, 'OF PLACE', 9.5, bold=True)
    p.text(46.5, 114.4, 'West Side', 5.5); p.text(46.5, 116.4, 'East Side', 5.5)
    p.text(46.5, 118.4, 'Uptown', 5.5); p.text(46.5, 120.2, 'Midtown', 5.5); p.text(46.5, 122.0, 'Downtown', 5.5)
    p.text(27, 127.7, 'WEAPON', 9.5, bold=True); p.text(27, 131.5, 'LOCATION', 9.5, bold=True)
    p.text(46.5, 129.5, '.38 - .45', 5.5)
    lx = 56
    cw = (R - lx) / 6
    for i, (letter, nm) in enumerate(PLACES):
        cx = lx + i * cw
        mid = cx + cw / 2
        p.text(mid, 90.5, letter, 13, bold=True, align='c')
        p.text(mid, 94.3, nm, 6.5, bold=True, align='c')
        p.text(mid - 3.4, 97.4, 'Men', 5.8, align='c'); p.text(mid + 3.8, 97.4, 'Women', 5.8, align='c')
        gx0, gx1, gy0, gy1 = cx + 4.0, cx + cw - 4.0, 99, 109   # 2 x 2 grid: men | women
        for gy in (gy0, (gy0 + gy1) / 2, gy1):
            p.line(gx0, gy, gx1, gy, width=0.3)
        p.line(mid, gy0, mid, gy1, width=0.3)
        man(p, cx + 2.1, gy0 - 0.4, 10); woman(p, cx + cw - 2.1, gy0 - 0.4, 10)
        p.line(mid, gy1, mid, 112, width=0.3)
        p.box(mid - 6, 112.5, 12, 4.0, width=0.35, radius=0.5)                # side
        p.box(cx + 2.2, 116.5, cw - 4.4, 5.5, width=0.35)                     # area
        p.line(mid, 122, mid, 125, width=0.3)
        bx0, bx1 = cx + 2.2, cx + cw - 2.2                                    # cartridge
        p.poly([(bx0, 125)] + arc(bx1 - 3.6, 128.6, 3.6, 270) + arc(bx1 - 3.6, 128.6, 3.6, 0)
               + [(bx0, 132.2)], color=BLACK, width=0.35)
        p.line(bx0 + 1.2, 125, bx0 + 1.2, 132.2, width=0.25)
        p.line(bx1 - 3.6, 125, bx1 - 3.6, 132.2, width=0.25)
    # fold line = boundary of sections 2 and 3 (sheet folds so 1-2 go behind, 3-4 stay in front)
    p.text(R, 138.4, 'FOLD HERE  -  sections 1-2 behind, 3-4 in front', 6.5, color=CUT, align='r')
    p.line(L, 140, R, 140, width=0.5, dashes='[2.5 1.5] 0')

    # ---- 3. who said what
    section(p, 157, '3', 'WHO SAID WHAT?')
    p.text(27, 150, 'SUSPECTS', 9, bold=True)
    top, rh = 150.5, 10.3
    half = (R - L) / 2
    p.text(52, 150, 'Men and their Statements', 6.5)
    p.text(L + half + 28, 150, 'Women and their Statements', 6.5)
    for n in range(1, 21):
        col, r = (n - 1) // 10, (n - 1) % 10
        bx = L + (13 if col == 0 else half + 1)
        y = top + 1 + r * rh
        num_keys(p, bx, y + 2.2, n)
        first, last = SUSPECTS[n - 1][0].title().replace("O'm", "O'M").split(' ', 1)
        p.text(bx + 10.5, y + 4.6, first, 7, bold=True); p.text(bx + 10.5, y + 7.6, last, 7, bold=True)
        wx = bx + 26
        we = (L + half - 2) if col == 0 else R
        p.box(wx, y + 1.2, we - wx, rh - 2.2, width=0.4)
    sec4 = top + 1 + 10 * rh + 1
    p.line(L, sec4, R, sec4, width=0.6)

    # ---- 4. who did it
    section(p, sec4 + 18, '4', 'WHO DID IT?')
    p.text(62, sec4 + 14, 'I Accuse Suspect', 10.5, bold=True)
    cx, cy, rr = 106, sec4 + 11, 8.5                                           # magnifying glass
    p.p.draw_circle(p.pt(cx, cy), rr * MM, color=BLACK, width=0.6 * MM)
    num_keys(p, cx - 6.3, cy - 3.2, 0, s=6, size=10)
    p.poly([(cx + rr - 0.2, cy - 1.2), (cx + rr + 18, cy - 2.4), (cx + rr + 18, cy + 1.8),
            (cx + rr - 0.2, cy + 1.2)], fill=BLACK)
    p.text(R, sec4 + 19.5, 'Ideal 1979, 5A-3343 - redrawn blank for personal use', 5.5, color=CUT, align='r')
    assert sec4 + 21 < 292, 'sheet overflows A4'
    doc.save(path, deflate=True, garbage=3)


if __name__ == '__main__':
    pages = make_cards(os.path.join(HERE, 'cards.pdf'))
    make_sheet(os.path.join(HERE, 'case_fact_sheet.pdf'))
    print(f'cards.pdf: {pages} pages, case_fact_sheet.pdf: 1 page')
