"""Draft-extract recipes from the Dave Fell PDFs using text positions."""
import json, re, sys
import pymupdf

SRC = "/home/user/marcro-meals-books/"
BOOKS = {
    "b1": ("Macro Meals, Micro Budget eBook- Dave Fell (4).pdf", "paired"),
    "b2": ("Macro Meals, Micro Budget Volume 2.pdf", "single"),
    "b3": ("Macro Prep Micro Budget Recipe eBook by Dave Fell.pdf", "paired"),
}
QTY_START = re.compile(r"^(\d|½|¼|¾|⅓|⅔|one |two |dash|pinch|handful|splash|a |half|1/2|optional|\*)", re.I)


def lines_of(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t:
                continue
            s = max(l["spans"], key=lambda s: len(s["text"].strip()))
            x0, y0, x1, y1 = l["bbox"]
            out.append(dict(t=t, x=x0, y=y0, x1=x1, size=s["size"], font=s["font"]))
    return out


def title_of(ls):
    heads = [l for l in ls if "UniSans" in l["font"] and l["size"] > 12]
    heads.sort(key=lambda l: (round(l["y"] / 4), l["x"]))
    t = " ".join(l["t"] for l in heads)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def section_of(text):
    pass


def group_ingredients(ing_lines, prices):
    # Join fragments that sit on the same baseline (e.g. a quantity set apart from its name).
    rows = []
    for l in sorted(ing_lines, key=lambda l: (l["y"], l["x"])):
        if rows and abs(rows[-1]["y"] - l["y"]) < 2.5:
            rows[-1] = dict(rows[-1], t=rows[-1]["t"] + " " + l["t"])
        else:
            rows.append(dict(l))
    items = []
    for l in rows:
        t = l["t"]
        priced = any(abs(p["y"] - l["y"]) < 6 for p in prices)
        always = items and (t.startswith(("(", "+")) or (t[0].islower() and not QTY_START.match(t)))
        cont = items and (items[-1].count("(") > items[-1].count(")")
                          or re.search(r"(Frozen|Fresh|Chopped|&|\bof|Ready-Made|natural|protein|passionfruit|fat|Chocolate|Vanilla|Plum|,)$", items[-1]))
        if always or (cont and not priced and not QTY_START.match(t)):
            items[-1] += " " + t
        else:
            items.append(t)
    return [re.sub(r"\s+", " ", i).strip() for i in items]


def steps_from(step_lines, nums):
    nums = sorted(nums, key=lambda n: n["y"])
    step_lines = sorted(step_lines, key=lambda l: l["y"])
    if not nums:
        return [" ".join(l["t"] for l in step_lines)]
    steps = [[] for _ in nums]
    for l in step_lines:
        idx = 0
        for i, n in enumerate(nums):
            if l["y"] >= n["y"] - 8:
                idx = i
        steps[idx].append(l["t"])
    return [re.sub(r"\s+", " ", " ".join(s)).strip() for s in steps if s]


def macros_paired(ls):
    txt = "\n".join(l["t"] for l in ls)
    m = {}
    for key, pat in [("kcal", r"kcals?\s*(\d+)"), ("p", r"\bP\s*(\d+)\s*g"), ("c", r"\bc\s*(\d+)\s*g"), ("f", r"\bf\s*(\d+)\s*g")]:
        r = re.search(pat, txt, re.I)
        m[key] = int(r.group(1)) if r else None
    return m


def common(ls, d):
    txt = "\n".join(l["t"] for l in ls)
    r = re.search(r"\(MAKES\s*(\d+)", txt, re.I)
    d.setdefault("servings", int(r.group(1)) if r else None)
    r = re.search(r"Cost per (?:serve|wrap|burger|taco|portion|serving)[^£]*£\s*([\d.]+)", txt, re.I)
    if r:
        d["price"] = float(r.group(1))
    r = re.search(r"SHOP:\s*(.+)", txt)
    if r:
        d["shop"] = r.group(1).strip()
    veg = [l["t"] for l in ls if "FakeReceipt" in l["font"] and l["t"].strip().upper() in ("V", "VG") and l["size"] >= 13]
    if veg:
        d["veg"] = veg[0].upper()


def photo_xref(page):
    infos = page.get_image_info(xrefs=True)
    best = None
    for info in infos:  # content-stream order: later = drawn on top
        w = info["bbox"][2] - info["bbox"][0]
        h = info["bbox"][3] - info["bbox"][1]
        if w * h > 0.15 * page.rect.width * page.rect.height and info["xref"]:
            best = info["xref"]
    return best


def tips_swaps(ls, d):
    heads = sorted([l for l in ls if "FakeReceipt" in l["font"] and re.match(r"^(TIPS|SWAPS)", l["t"])], key=lambda l: l["y"])
    body = [l for l in ls if "Acumin" in l["font"]]
    for i, h in enumerate(heads):
        y_end = heads[i + 1]["y"] if i + 1 < len(heads) else 9999
        txt = " ".join(l["t"] for l in sorted(body, key=lambda l: l["y"]) if h["y"] < l["y"] < y_end and l["y"] > 600)
        key = "tips" if h["t"].startswith("TIPS") else "swaps"
        if txt:
            d[key] = re.sub(r"\s+", " ", txt).strip()


def parse_paired(doc, i):
    photo, rec = doc[i], doc[i + 1]
    pl, rl = lines_of(photo), lines_of(rec)
    d = dict(page=i + 1)
    d["title"] = title_of(pl) or title_of(rl)
    d["macros"] = macros_paired(pl)
    r = re.search(r"£\s*([\d.]+)", "\n".join(l["t"] for l in pl))
    d["price"] = float(r.group(1)) if r else None
    common(pl, d)
    common(rl, d)
    prices = [l for l in rl if re.match(r"^£\s*\d", l["t"]) and 150 < l["x"] < 290]
    shop = [l for l in rl if l["t"].startswith("SHOP")]
    total = [l for l in rl if l["t"].startswith("TOTAL")]
    y0 = shop[0]["y"] + 5 if shop else 150
    y1 = total[0]["y"] if total else 680
    ing = [l for l in rl if "Acumin" in l["font"] and l["x"] < 150 and y0 < l["y"] < y1 and not l["t"].startswith(("Total cost", "Cost per", "*"))]
    d["ingredients"] = group_ingredients(ing, prices)
    nums = [l for l in rl if "FakeReceipt" in l["font"] and re.fullmatch(r"\d{1,2}", l["t"]) and l["size"] >= 15 and 240 < l["x"] < 330]
    steps = [l for l in rl if "Acumin" in l["font"] and l["x"] >= 270 and l["y"] < 690]
    d["steps"] = steps_from(steps, nums)
    tips_swaps(rl, d)
    d["photo_xref"] = photo_xref(photo)
    return d


def parse_single(doc, i):
    p = doc[i]
    ls = lines_of(p)
    d = dict(page=i + 1)
    d["title"] = title_of(ls)
    hdr = [l for l in ls if l["t"].startswith("Calories")]
    m = {}
    if hdr:
        hy = hdr[0]["y"]
        nums = sorted([l for l in ls if "FakeReceipt" in l["font"] and re.fullmatch(r"\d+", l["t"]) and abs(l["y"] - (hy - 16)) < 8], key=lambda l: l["x"])
        vals = [int(n["t"]) for n in nums]
        if len(vals) == 4:
            m = dict(kcal=vals[0], p=vals[1], c=vals[2], f=vals[3])
    d["macros"] = m
    common(ls, d)
    prices = [l for l in ls if re.match(r"^£\s*\d", l["t"]) and 240 < l["x"] < 320]
    hy = hdr[0]["y"] if hdr else 200
    tc = [l for l in ls if l["t"].startswith(("Total cost", "TOTAL"))]
    y1 = min(l["y"] for l in tc) if tc else 470
    ing = [l for l in ls if "Acumin" in l["font"] and l["x"] < 230 and hy + 8 < l["y"] < y1 and not l["t"].startswith(("(excl", "(MAKES", "Total cost", "Cost per"))]
    d["ingredients"] = group_ingredients(ing, prices)
    meth = [l for l in ls if l["t"] == "METHOD"]
    my = meth[0]["y"] if meth else 500
    nums = [l for l in ls if "FakeReceipt" in l["font"] and re.fullmatch(r"\d{1,2}", l["t"]) and l["x"] < 40 and l["y"] > my]
    steps = [l for l in ls if "Acumin" in l["font"] and 35 < l["x"] < 330 and l["y"] > my + 5]
    d["steps"] = steps_from(steps, nums)
    tip = sorted([l for l in ls if "Acumin" in l["font"] and l["x"] > 330 and l["y"] > 540], key=lambda l: l["y"])
    txt = re.sub(r"\s+", " ", " ".join(l["t"] for l in tip))
    r = re.search(r"TIPS?\s*-\s*(.*?)(?=SWAPS?\s*-|$)", txt)
    if r:
        d["tips"] = r.group(1).strip()
    r = re.search(r"SWAPS?\s*-\s*(.*)$", txt)
    if r:
        d["swaps"] = r.group(1).strip()
    d["photo_xref"] = photo_xref(p)
    return d


def main():
    out = {}
    for key, (fname, kind) in BOOKS.items():
        doc = pymupdf.open(SRC + fname)
        recs, section = [], None
        for i, page in enumerate(doc):
            txt = page.get_text()
            if "Click on each recipe" in txt:
                ls = lines_of(page)
                big = [l["t"] for l in ls if l["size"] > 20]
                if big:
                    section = big[0]
                continue
            if kind == "paired" and re.search(r"kcals?\s*\d", txt, re.I) and i + 1 < len(doc):
                d = parse_paired(doc, i)
            elif kind == "single" and "Calories" in txt and "protein" in txt:
                d = parse_single(doc, i)
            else:
                continue
            d["section"] = section
            recs.append(d)
        out[key] = recs
        print(key, len(recs), file=sys.stderr)
    json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)


main()
