# Macro Meals

A clean, filterable recipe site with full macro breakdowns and adjustable ingredients.

- **Directory** (`index.html`): every tile shows calories, protein, carbs and fat per serving. Filter by meal, main ingredient, minimum protein, maximum calories and vegetarian, and sort by protein, calories, protein per calorie or price.
- **Recipe page** (`recipe.html?id=…`): each ingredient has a slider, and the macros recalculate as you drag. A "Scale whole recipe" slider scales everything at once. Enter your meal targets (saved in your browser) to see how the recipe compares, and use **Fit to calories** or **Fit to protein** to scale it to a target.

## Recipes

Recipes come from `scripts/books/` (one file per book) and are built into `assets/data/recipes.json`:

```
python3 scripts/build_recipes.py
```

Each ingredient's macros are estimated from `scripts/nutrition.py`, then calibrated so the recipe's totals match the numbers printed in the book exactly. The book's numbers are what the tiles show. The per-ingredient split is what makes the sliders work.

Current books:

- *Macro Meals, Micro Budget*, Dave Fell (35 recipes so far; the last few meal prep recipes and the snacks section are still to come)

## Photos

Put photos in `assets/img/` and set `image="file.jpg"` on a recipe in its book file. Recipes without a photo show a placeholder.

## Publishing with GitHub Pages

1. Go to **Settings → Pages** in this repository.
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Set the branch to **main** and the folder to **/ (root)**, then click **Save**.
4. The site will be live at `https://jimdee-jandj.github.io/macro-meals/` within a minute or two.
