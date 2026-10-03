"""Write scripts/books/*.py from parsed.json."""
import json, re, sys, pprint

P = json.load(open(sys.argv[1]))
OUT = "/home/user/macro-meals/scripts/books/"

BOOKS = {
    "b1": ("macro_meals_micro_budget", "Macro Meals, Micro Budget"),
    "b2": ("macro_meals_micro_budget_vol2", "Macro Meals, Micro Budget Vol. 2"),
    "b3": ("macro_prep_micro_budget", "Macro Prep, Micro Budget"),
}
SKIP = {("b2", 8), ("b2", 71), ("b2", 72)}
TITLES = {
    ("b1", 10): "Nutella & Banana Protein Oats",
    ("b1", 12): "Lemon-Blueberry Cheesecake Overnight Weetabix",
    ("b1", 24): "Banana-Mocha Protein Smoothie",
    ("b1", 26): "High-Protein Chocolate French Toast Bites",
    ("b1", 49): "Crispy Honey-Sriracha Chicken Wraps",
    ("b1", 51): "Protein PB&J Quesadilla",
    ("b1", 65): "Chicken Wrap Pizzas",
    ("b1", 71): "World's Easiest & Healthiest Chicken Dinner",
    ("b1", 107): "High-Protein Tropical Smoothie Bowl",
    ("b2", 13): "PB&J Baked Oats",
    ("b2", 15): "Tiramisu Overnight Wheat-Bics",
    ("b2", 29): "Meatball Subs",
    ("b3", 16): "Raspberry Bakewell Overnight Oats",
    ("b3", 51): "Cajun 'Beef' & Egg Burrito",
    ("b3", 57): "Jalapeño Popper Bagels",
    ("b3", 78): "'Chicken' Fajita Pasta",
}
SERVINGS_FIX = {("b1", 95): 4}
DESCRIPTION = {
    ("b1", 95): "Makes 24 pinwheels. Macros are per serving of 6.",
    ("b1", 57): "Makes 8 tacos. Macros are per taco.",
    ("b1", 65): "Makes one tomato pizza (474 kcal) and one BBQ pizza (459 kcal). Macros shown are for the BBQ pizza.",
}
MACRO_FIX = {("b2", 14): dict(kcal=407, p=36, c=56, f=4)}
INGREDIENT_FIX = {
    ("b2", 17): [
        (6, "crumpet", "crumpet", "Crumpets"), (2, "egg", "egg", "Eggs"), (150, "ml", "milk_semi", "Light milk"),
        (65, "g", "protein_powder", "Vanilla protein powder"),
        (100, "g", "blueberries", "Frozen blueberries (blueberry & chocolate bake)"),
        (8, "g", "choc_chips", "Milk chocolate, 1 square (blueberry & chocolate bake)"),
        (10, "g", "maple_syrup", "Maple syrup (blueberry & chocolate bake)"),
        (100, "g", "raspberries", "Frozen raspberries (raspberry & Biscoff bake)"),
        (10, "g", "biscoff_spread", "Biscoff spread (raspberry & Biscoff bake)"),
        (1, "biscuit", "biscoff_biscuit", "Biscoff biscuit, crushed (raspberry & Biscoff bake)"),
        (1, "banana", "banana", "Banana, sliced (banana & peanut butter bake)"),
        (8, "g", "powdered_pb", "Powdered peanut butter (banana & peanut butter bake)"),
    ],
}
LINE_FIX = {
    ("b1", 38, "Banana chips"): [(1, "banana", "banana", "Banana"), ("10g dark chocolate chips (optional, not in the macros)",)],
    ("b2", 46, "Biscoff + 10g Biscoff spread"): [(1, "biscuit", "biscoff_biscuit", "Biscoff biscuit"), (10, "g", "biscoff_spread", "Biscoff spread")],
}
SNACKY = re.compile(r"crumble|tiramisu|bars|brownie|cookie|hot chocolate|iced coffee|smoothie bowl", re.I)
BREAKFASTY = re.compile(r"pancake|omelette|breakfast", re.I)


DELI = dict(meal="Snacks", tags=["Deli container", "5 mins or less"], servings=1, price=None, shop=None, tips=None, swaps=None,
            photo=None, description="From the Deli Container snack series.")
DELI_STEPS = ["Slice the cucumber thinly using a mandoline.", "Combine all the ingredients in a deli container.",
              "Put a lid on and shake it all up."]
EXTRA = {"b2": [
    dict(DELI, title="Apple & Cinnamon Deli Pot", main="Veggie", veg="V", macros=(266, 11, 45, 4),
         ingredients=[(2, "apple", "apple", "Apples of choice"), (60, "g", "greek_yog_ff", "Greek yoghurt (2 tbsp)"),
                      (10, "g", "powdered_pb", "Powdered peanut butter, made into a loose PB"), ("1 tsp cinnamon",),
                      ("5g sugar-free maple syrup (optional)",)],
         steps=["Slice the apples thinly.", "Combine all the ingredients in the deli container.", "Put a lid on and shake it all up."],
         tips="Best eaten fresh rather than prepped ahead.",
         swaps="Swap the apple for pear or mango. Use regular peanut butter if you don't have powdered, but note it will increase the calorie count."),
    dict(DELI, title="Cucumber Salad Deli Pot", main="Veggie", veg="V", macros=(123, 7, 22, 1),
         ingredients=[(1, "cucumber", "cucumber", "Whole cucumber", 300), (60, "g", "greek_yog_ff", "Greek yoghurt (2 tbsp)"),
                      (10, "g", "jalapenos", "Diced jalapeños"), (40, "g", "gherkins", "Diced gherkins"),
                      ("Salt, pepper, chilli flakes, garlic powder, soy sauce and sriracha",)],
         steps=DELI_STEPS, tips="Best eaten fresh, not ideal for prepping more than a few hours ahead.",
         swaps="Add a pinch of dried dill or mint for extra freshness. Swap the gherkins for capers if you prefer."),
    dict(DELI, title="Eton Mess Deli Pot", main="Veggie", veg="V", macros=(174, 6, 37, 1),
         ingredients=[(200, "g", "strawberries", "Strawberries"), (60, "g", "greek_yog_ff", "Greek yoghurt (2 tbsp)"),
                      (15, "g", "jam", "Low-sugar jam"), (1, "nest", "meringue_nest", "Meringue nest")],
         steps=["Slice the strawberries thinly.", "Combine all the ingredients in the deli container.", "Put a lid on and shake it all up."],
         tips="Add the meringue just before eating; it goes soft quickly once it touches the yoghurt and fruit.",
         swaps="Swap the strawberries for raspberries, mixed berries or any soft fruit you like."),
    dict(DELI, title="Tuna Salad Deli Pot", main="Fish", veg=None, macros=(222, 31, 16, 4),
         ingredients=[(1, "cucumber", "cucumber", "Whole cucumber", 300), (60, "g", "greek_yog_ff", "Greek yoghurt (2 tbsp)"),
                      (10, "ml", "lemon_juice", "Lemon juice"), (10, "g", "mustard", "American mustard"),
                      (0.33, "onion", "onion", "Red onion"), (1, "tin", "tuna_tin", "Tuna, drained"), (50, "g", "sweetcorn", "Sweetcorn, drained")],
         steps=["Slice the cucumber and red onion thinly using a mandoline.", "Combine all the ingredients in the deli container.", "Put a lid on and shake it all up."],
         tips="Drain the tuna well to stop the salad going watery. A little extra lemon juice or mustard makes a big difference.",
         swaps="Swap the tuna for tinned salmon or diced cooked chicken."),
    dict(DELI, title="Jalapeño Popper Deli Pot", main="Pork", veg=None, macros=(251, 31, 18, 8),
         ingredients=[(1, "cucumber", "cucumber", "Whole cucumber", 300), (60, "g", "greek_yog_ff", "Greek yoghurt (2 tbsp)"),
                      (10, "g", "jalapenos", "Jalapeños"), (10, "g", "sriracha", "Sriracha"),
                      (4, "medallion", "bacon_medallion", "Bacon medallions"), (8, "g", "parmesan", "Parmesan"),
                      ("MSG (or salt), pepper, cajun seasoning and garlic powder",)],
         steps=["Air fry the bacon medallions for 6 minutes until crispy, then dice finely.",
                "Slice the cucumber thinly using a mandoline and combine everything in a deli container.", "Put a lid on and shake it all up."],
         tips="Drain the jalapeños well so the yoghurt doesn't go watery. Adjust the sriracha to taste.",
         swaps="Swap the jalapeños for pickled chillies or diced green pepper for a milder version."),
    dict(DELI, title="Chipotle Chicken Deli Pot", main="Chicken", veg=None, macros=(258, 26, 17, 9),
         ingredients=[(1, "cucumber", "cucumber", "Whole cucumber", 300), (60, "g", "greek_yog_ff", "Greek yoghurt (2 tbsp)"),
                      (15, "g", "jalapenos", "Jalapeños"), (10, "g", "sriracha", "Sriracha"),
                      (100, "g", "chicken_cooked", "Cooked chipotle chicken"), ("MSG (or salt), pepper, paprika and garlic powder",)],
         steps=DELI_STEPS, tips="Use pre-cooked chicken to keep it quick. A squeeze of lime just before eating makes a real difference.",
         swaps="Swap the chicken for turkey breast or tinned tuna."),
    dict(DELI, title="Spicy Beef Deli Pot", main="Beef", veg=None, macros=(216, 29, 14, 4),
         ingredients=[(1, "cucumber", "cucumber", "Whole cucumber", 300), (60, "g", "greek_yog_ff", "Greek yoghurt (2 tbsp)"),
                      (10, "g", "jalapenos", "Jalapeños"), (10, "g", "sriracha", "Sriracha"), (15, "ml", "soy_sauce", "Soy sauce"),
                      (100, "g", "beef_mince_5", "Cooked, seasoned 5% beef mince"), ("MSG (or salt), pepper, paprika and garlic powder",)],
         steps=DELI_STEPS, tips="Best eaten fresh, not ideal for prepping more than a few hours ahead.",
         swaps="Swap the beef for chicken, pork or tofu. Use more or less sriracha to adjust the heat."),
    dict(DELI, title="Spicy Pork Deli Pot", main="Pork", veg=None, macros=(218, 27, 13, 6),
         ingredients=[(1, "cucumber", "cucumber", "Whole cucumber", 300), (60, "g", "greek_yog_ff", "Greek yoghurt (2 tbsp)"),
                      (10, "g", "jalapenos", "Jalapeños, sliced"), (15, "g", "red_cabbage", "Pickled cabbage"),
                      (10, "g", "sriracha", "Sriracha"), ("5g fresh coriander",),
                      (100, "g", "pork_mince_5", "Cooked, seasoned 5% pork mince"), ("MSG (or salt), pepper and garlic powder",)],
         steps=DELI_STEPS, tips="Best eaten fresh, not ideal for prepping more than a few hours ahead.",
         swaps="Swap the pork for chicken, beef or tofu. Gochujang, sambal oelek or harissa all work in place of sriracha."),
]}


def meal_and_tags(key, sec, title):
    sec = (sec or "").upper()
    tags = []
    if key == "b3":
        tags.append("Meal prep")
    if "BREAKFAST" in sec:
        meal = "Breakfast"
    elif "SNACK" in sec:
        meal = "Snacks"
    else:
        meal = "Mains"
    if "MEAL PREP" in sec:
        tags.append("Meal prep")
    if "SLOW" in sec:
        tags.append("Slow cooker")
    if "ONE" in sec and "DISH" in sec:
        tags.append("One dish")
    if "5 MIN" in sec:
        tags.append("5 mins or less")
    if meal == "Mains" and SNACKY.search(title):
        meal = "Snacks"
    if meal == "Mains" and BREAKFASTY.search(title):
        meal = "Breakfast"
    return meal, tags


def main_ingredient(title, parsed):
    keys = [p[2] for p in parsed if len(p) >= 4]
    t = title.lower()
    def has(*ks):
        return any(k in keys for k in ks)
    if "quorn" in " ".join(str(p) for p in parsed).lower() or "'chicken'" in t or "'beef'" in t or "veggie" in t or "meatless" in t:
        return "Veggie"
    if has("chicken_breast", "chicken_cooked", "chicken_thigh", "chicken_mince") or "chicken" in t:
        return "Chicken"
    if has("tuna_tin", "prawns") or "tuna" in t or "paella" in t:
        return "Fish"
    if has("beef_mince_5", "beef_steak_thin", "beef_diced_lean", "meatballs_skinny") or "beef" in t or "steak" in t:
        return "Beef"
    if has("bacon_medallion", "bacon_rasher_rf", "ham", "chorizo", "skinny_sausage", "chicken_chipolata", "chicken_sausage", "pork_mince_5", "pork_patty"):
        return "Pork"
    if has("oats", "muesli"):
        return "Oats"
    if has("wheat_biscuit"):
        return "Weetabix"
    if has("egg", "egg_large", "egg_white_liquid") and sum(1 for k in keys if k.startswith("egg")) and ("egg" in t or "quiche" in t or "omelette" in t or "breakfast" in t):
        return "Eggs"
    if has("pasta_dry", "gnocchi"):
        return "Pasta"
    if has("protein_powder"):
        return "Protein powder"
    if has("baked_beans", "kidney_beans", "lentils_dry", "chickpeas"):
        return "Veggie"
    return "Other"


def fix_ingredients(key, r):
    if (key, r["page"]) in INGREDIENT_FIX:
        return INGREDIENT_FIX[(key, r["page"])]
    out = []
    for p in r["parsed"]:
        rep = LINE_FIX.get((key, r["page"], p[3] if len(p) > 3 else p[0]))
        out.extend(rep if rep else [tuple(p)])
    return out


def emit(key):
    mod, book = BOOKS[key]
    recs = []
    for r in P[key]:
        if (key, r["page"]) in SKIP:
            continue
        title = TITLES.get((key, r["page"]), r["title"])
        m = MACRO_FIX.get((key, r["page"]), r["macros"])
        meal, tags = meal_and_tags(key, r.get("section"), title)
        rec = dict(
            title=title, meal=meal, main=main_ingredient(title, r["parsed"]),
            tags=tags, veg=r.get("veg"), servings=SERVINGS_FIX.get((key, r["page"]), r.get("servings") or 1),
            description=DESCRIPTION.get((key, r["page"])),
            macros=(m["kcal"], m["p"], m["c"], m["f"]), price=r.get("price"), shop=r.get("shop"),
            ingredients=fix_ingredients(key, r),
            steps=r["steps"], tips=r.get("tips"), swaps=r.get("swaps"),
            photo=dict(page=r["page"], xref=r.get("photo_xref")),
        )
        if rec["main"] in ("Chicken", "Beef", "Pork", "Fish"):
            rec["veg"] = None
        elif rec["main"] == "Other" and rec["veg"]:
            rec["main"] = "Veggie"
        recs.append(rec)
    recs.extend(EXTRA.get(key, []))
    body = pprint.pformat(recs, width=120, sort_dicts=False)
    src = (f'"""{book} — Dave Fell.\n\nExtracted from the PDF, then reviewed. Macros and prices are per serving as printed;\n'
           f'ingredient quantities are for the whole batch (`servings` portions).\n"""\n\n'
           f'BOOK = {book!r}\n\nRECIPES = {body}\n')
    open(OUT + mod + ".py", "w").write(src)
    print(mod, len(recs))


for k in BOOKS:
    emit(k)
