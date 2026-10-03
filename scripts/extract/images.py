"""Extract each recipe photo from the PDFs and crop away the receipt-paper frame."""
import importlib.util, io, re, sys
from pathlib import Path
import numpy as np
import pymupdf
from PIL import Image

SRC = Path("/home/user/marcro-meals-books")
REPO = Path("/home/user/macro-meals")
OUT = REPO / "assets/img"
OUT.mkdir(parents=True, exist_ok=True)
SHEET = Path(sys.argv[1]) if len(sys.argv) > 1 else None
PDF = {
    "macro_meals_micro_budget": "Macro Meals, Micro Budget eBook- Dave Fell (4).pdf",
    "macro_meals_micro_budget_vol2": "Macro Meals, Micro Budget Volume 2.pdf",
    "macro_prep_micro_budget": "Macro Prep Micro Budget Recipe eBook by Dave Fell.pdf",
}


# Photos where auto-detection picks out only part of the dish.
FORCE_TYPICAL = {"cheesy-bean-muffins"}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", "and")).strip("-")


def longest_run(flags):
    best, cur, start, bstart = 0, 0, 0, 0
    for i, f in enumerate(flags):
        if f:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bstart = cur, start
        else:
            cur = 0
    return bstart, bstart + best


def crop_photo(im):
    a = np.asarray(im.convert("HSV")).astype(float) / 255
    rgb = np.asarray(im).astype(float) / 255
    sat, val = a[..., 1], a[..., 2]
    # Receipt paper is light and nearly colourless; the photo is not.
    mask = (sat > 0.16) | (val < 0.55)
    rows = mask.mean(axis=1) > 0.25
    r0, r1 = longest_run(rows)
    h, w = mask.shape
    if r1 - r0 < 0.2 * h:
        return None
    cols = mask[r0:r1].mean(axis=0) > 0.25
    c0, c1 = longest_run(cols)
    if (c1 - c0) < 0.3 * w or (r1 - r0) > 0.8 * h:
        return None  # detection failed
    pr, pc = int((r1 - r0) * 0.03), int((c1 - c0) * 0.03)
    return (c0 + pc) / w, (r0 + pr) / h, (c1 - pc) / w, (r1 - pr) / h


def main():
    seen, done, sheet, pending = set(), 0, [], []
    for mod, pdf in PDF.items():
        spec = importlib.util.spec_from_file_location(mod, REPO / "scripts/books" / f"{mod}.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        doc = pymupdf.open(SRC / pdf)
        for r in m.RECIPES:
            rid = slug(r["title"])
            if rid in seen:
                rid = f"{rid}-{slug(m.BOOK)}"
            seen.add(rid)
            ph = r.get("photo") or {}
            if not ph.get("xref"):
                continue
            info = doc.extract_image(ph["xref"])
            im = Image.open(io.BytesIO(info["image"])).convert("RGB")
            pending.append((mod, rid, im, None if rid in FORCE_TYPICAL else crop_photo(im)))
    # Pale food can blend into the paper; fall back to the book's typical photo position.
    typical = {}
    for mod in PDF:
        boxes = np.array([b for m_, _, _, b in pending if m_ == mod and b])
        typical[mod] = tuple(np.median(boxes, axis=0)) if len(boxes) else (0, 0, 1, 1)
    area = lambda b: (b[2] - b[0]) * (b[3] - b[1])
    for mod, rid, im, box in pending:
        if box and area(box) < 0.5 * area(typical[mod]):
            box = None  # only part of the dish was detected
        if not box:
            print("fallback crop:", rid)
        x0, y0, x1, y1 = box or typical[mod]
        w, h = im.size
        c = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        c.thumbnail((1000, 1000), Image.LANCZOS)
        c.save(OUT / f"{rid}.jpg", "JPEG", quality=80, optimize=True, progressive=True)
        done += 1
        if SHEET:
            t = c.copy()
            t.thumbnail((160, 160))
            sheet.append((rid, t))
    print("saved", done)
    if SHEET and sheet:
        cols = 16
        rows = (len(sheet) + cols - 1) // cols
        s = Image.new("RGB", (cols * 164, rows * 164), "white")
        for i, (_, t) in enumerate(sheet):
            s.paste(t, ((i % cols) * 164 + 2, (i // cols) * 164 + 2))
        s.save(SHEET)


main()
