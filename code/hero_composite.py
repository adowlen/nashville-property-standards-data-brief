"""Composite the headline figure over the generated hero illustration.
Adapted from the Denver street occupancy package (2026-10-30).
The hero illustration itself is generated separately and placed in
hero_source/ by the parent run; this script composites the headline
text from hero-headline.txt over a scrimmed field. If no illustration
is present it exits without writing hero.png (hero stays pending).
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(__file__).resolve().parent.parent
cands = sorted((root / "hero_source").glob("*.webp")) + \
        sorted((root / "hero_source").glob("*.png")) + \
        sorted((root / "hero_source").glob("*.jpg")) if (root / "hero_source").exists() else []
if not cands:
    raise SystemExit("no hero illustration in hero_source/ - hero stays pending")
img = Image.open(cands[0]).convert("RGB")
W, H = img.size

# Left-side gradient scrim: the generated illustration carries its
# clean dark field on the left third (QA adaptation, 2026-11-01 -
# the art's narrative scene sits right, so the headline goes left,
# not in a top band).
band = int(W * 0.58)
overlay = Image.new("L", (band, 1))
for xx in range(band):
    t = xx / band
    overlay.putpixel((xx, 0), int(205 * (1 - t) ** 1.6))
overlay = overlay.resize((band, H))
scrim = Image.new("RGB", (band, H), (10, 13, 16))
img.paste(scrim, (0, 0), overlay)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(p, size)


def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


MAXW = int(W * 0.44)
headline = "73.8%"
d.text((56, int(H * 0.16)), headline, font=font(int(H * 0.105)), fill=(245, 168, 0))
sub_f = font(int(H * 0.030), bold=False)
y = int(H * 0.16) + int(H * 0.135)
sub = ("of Nashville's 568 'host - no strp' unpermitted-STR complaints sit on parcels "
       "with no STR permit record at all in the Metro permits file")
for line in wrap(sub, sub_f, MAXW):
    d.text((58, y), line, font=sub_f, fill=(242, 242, 242))
    y += int(H * 0.044)
src_f = font(int(H * 0.021), bold=False)
srcline = ("Machine Readable - Nashville Property Standards Violations layer and STR permits file, "
           "pulled Nov 1, 2026 - 43,283 property standards cases")
for line in wrap(srcline, src_f, MAXW):
    d.text((58, y + 8), line, font=src_f, fill=(150, 210, 200))
    y += int(H * 0.032)
img.save(root / "hero.png")
print("hero", img.size, "from", cands[0].name)
