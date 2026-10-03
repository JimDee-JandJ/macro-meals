"""Build assets/data/recipes.json from the book files in scripts/books/.

Each ingredient's macros are estimated from nutrition.FOODS, then scaled per
macro so the recipe's totals match the numbers printed in the book exactly.
The site uses the per-ingredient values to recalculate macros when an
ingredient's quantity is changed.

Run:  python3 scripts/build_recipes.py
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from nutrition import FOODS  # noqa: E402

MACROS = ("kcal", "protein", "carbs", "fat")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", "and")).strip("-")


def estimate(qty, food):
    basis, *values = FOODS[food]
    return [v * qty / basis for v in values]


def build_recipe(book, r, warnings):
    servings = r["servings"]
    scalable, raw = [], []
    for ing in r["ingredients"]:
        if len(ing) == 1:
            continue
        qty, unit, food, name = ing
        scalable.append(ing)
        raw.append(estimate(qty, food))

    targets = [m * servings for m in r["macros"]]
    totals = [sum(col) for col in zip(*raw)]
    factors = [t / s if s else 0 for t, s in zip(targets, totals)]
    for macro, f in zip(MACROS, factors):
        if not 0.6 <= f <= 1.6:
            warnings.append(f"{r['title']}: {macro} estimate off by x{f:.2f}")

    ingredients = []
    raw_iter = iter(raw)
    for ing in r["ingredients"]:
        if len(ing) == 1:
            ingredients.append({"name": ing[0], "fixed": True})
            continue
        qty, unit, food, name = ing
        est = next(raw_iter)
        entry = {"name": name, "qty": qty, "unit": unit}
        for macro, value, f in zip(MACROS, est, factors):
            entry[macro] = round(value * f, 2)
        ingredients.append(entry)

    return {
        "id": slug(r["title"]),
        "title": r["title"],
        "book": book,
        "meal": r["meal"],
        "mainIngredient": r["main"],
        "vegetarian": r.get("veg"),
        "servings": servings,
        "price": r.get("price"),
        "shop": r.get("shop"),
        "description": r.get("description"),
        "image": r.get("image"),
        "macros": dict(zip(MACROS, r["macros"])),
        "ingredients": ingredients,
        "instructions": r["steps"],
        "tips": r.get("tips") or None,
        "swaps": r.get("swaps") or None,
    }


def main():
    recipes, warnings = [], []
    for path in sorted((HERE / "books").glob("*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for r in mod.RECIPES:
            recipes.append(build_recipe(mod.BOOK, r, warnings))

    ids = [r["id"] for r in recipes]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit(f"Duplicate recipe ids: {', '.join(sorted(dupes))}")

    out = ROOT / "assets" / "data" / "recipes.json"
    out.write_text(json.dumps(recipes, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(recipes)} recipes to {out.relative_to(ROOT)}")
    for w in warnings:
        print("  check:", w)


if __name__ == "__main__":
    main()
