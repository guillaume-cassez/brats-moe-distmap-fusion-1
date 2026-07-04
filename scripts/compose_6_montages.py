"""Compose 6 patient × 4 model 2×2 montages from captures_24/ for paper insertion.

Output : figures/patient_C{1..6}_4models.png.
Layout per patient :
  GT       | Baseline
  DistMap  | CC-Consensus (= fusion)
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import numpy as np

CAPS = Path(__file__).resolve().parents[1] / "figures" / "captures_24"
OUT  = Path(__file__).resolve().parents[1] / "figures"

# (case, patient_short, label_fr, label_en)
PATIENTS = [
    ("C1", "00048-001", "DistMap échoue",     "DistMap fails"),
    ("C2", "01437-000", "DistMap sauve",      "DistMap rescues"),
    ("C3", "01428-000", "Filtre ~ baseline",  "Filter ~ baseline"),
    ("C4", "00017-001", "Filtre ~ distmap",   "Filter ~ distmap"),
    ("C5", "01530-000", "Consensus casse",    "Consensus breaks"),
    ("C6", "00540-000", "Consensus synergie", "Clean synergy"),
]
MODELS_ORDER = [
    ("gt",       "Vérité terrain"),
    ("baseline", "Baseline"),
    ("distmap",  "DistMap"),
    ("fusion",   "CC-Consensus"),
]

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FS_LABEL  = 36

def _bright_bbox(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Bbox of bright (brain/tumor) pixels, masking the top-left UI toolbar."""
    arr = np.asarray(img)
    bright = arr.mean(axis=2) > 80
    bright[:350, :466] = False  # mask toolbar
    rows = np.where(bright.any(axis=1))[0]
    cols = np.where(bright.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return None
    return cols[0], rows[0], cols[-1], rows[-1]


def common_square_crop(images: list[Image.Image]) -> tuple[int, int, int, int]:
    """Compute one square crop usable for ALL given images.

    Take the UNION bbox of bright content across all images so every model
    rendering of the same patient is cropped at the same offset and same scale,
    avoiding the visual mismatch where GT (less content) was zoomed-in and
    predictions (more content) were zoomed-out.
    """
    bboxes = [b for b in (_bright_bbox(im) for im in images) if b is not None]
    if not bboxes:
        W, H = images[0].size
        side = min(W, H)
        return (W - side) // 2, (H - side) // 2, side, side
    x0 = min(b[0] for b in bboxes)
    y0 = min(b[1] for b in bboxes)
    x1 = max(b[2] for b in bboxes)
    y1 = max(b[3] for b in bboxes)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    side = max(x1 - x0, y1 - y0) + 80  # padding
    W, H = images[0].size
    side = min(side, W, H)
    half = side // 2
    L = max(0, min(W - side, cx - half))
    T = max(0, min(H - side, cy - half))
    return L, T, side, side


def make_montage(case, pid, label_fr):
    raw_images = [Image.open(CAPS / f"{pid}_{key}.png").convert("RGB")
                  for key, _ in MODELS_ORDER]
    L, T, sw, sh = common_square_crop(raw_images)
    cells = []
    for (key, name), img in zip(MODELS_ORDER, raw_images):
        cells.append((name, img.crop((L, T, L + sw, T + sh))))
    w = h = sw
    BAND = 50
    canvas = Image.new("RGB", (w * 2, (h + BAND) * 2), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(FONT_PATH, FS_LABEL)
    except Exception:
        font = ImageFont.load_default()
    positions = [(0, 0), (w, 0), (0, h + BAND), (w, h + BAND)]
    for (name, img), (x, y) in zip(cells, positions):
        draw.rectangle([x, y, x + w, y + BAND], fill="black")
        bbox = draw.textbbox((0, 0), name, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((x + (w - tw) // 2, y + (BAND - th) // 2 - 4), name, fill="white", font=font)
        canvas.paste(img, (x, y + BAND))
    out_path = OUT / f"patient_{case}_{pid}_4models.png"
    canvas.save(out_path, optimize=True)
    print(f"  {out_path.name}  {canvas.size}  {out_path.stat().st_size//1024} KiB")
    return out_path

print("Composing 6 montages...")
for case, pid, lf, le in PATIENTS:
    make_montage(case, pid, lf)
print("Done.")
