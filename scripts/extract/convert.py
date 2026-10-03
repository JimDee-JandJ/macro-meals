"""Turn drafts.json into book files for macro-meals/scripts/books/."""
import json, re, sys
sys.path.insert(0, "/home/user/macro-meals/scripts")
from nutrition import FOODS

FRAC = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1 / 3, "⅔": 2 / 3}

# Seasonings and other things with no meaningful macros.
FIXED = re.compile(
    r"\b(salt|pepper(?!s\b)(?! ?,? ?(diced|sliced))|paprika|cumin|garlic powder|garlic granules|onion powder|chilli powder|chilli flakes|"
    r"oregano|cinnamon|mixed herbs|italian herbs|garam masala|cajun|5 spice|five spice|vanilla extract|baking powder|sweetener|"
    r"\bwater\b|\bice\b|coffee|stock cube|lazy|easy garlic|easy chilli|ginger|worcestershire|basil|coriander|parsley|dill|"
    r"msg|rub\b|seasonings?\b(?! packet)|cayenne|thyme|rosemary|chilli paste|sea salt|sesame seeds|frylight|spray oil|"
    r"cloves? (of )?garlic|garlic, |head of garlic|jalapeño juice|mustard)",
    re.I,
)
NOT_FIXED_OVERRIDE = re.compile(r"(seasoning packet|packet .*seasoning|seasoning \(|taco seasoning|fajita seasoning|peri peri seasoning|"
                                r"bbq seasoning|salt n pepper seasoning|garlic & rosemary seasoning|chilli con carne seasoning|"
                                r"lemon (\+|&) herb|smokey bbq|bell pepper|red pepper|green pepper|yellow pepper|\bpeppers?\b,|"
                                r"^\d+ (red |green |yellow )?peppers?\b|peppers, )", re.I)

# (pattern, food key, grams per counted item for per-100g foods, unit label for counted items)
RULES = [
    (r"protein (yog(h)?urt|pouch)|cheesecake protein|yoghurt pouch|peach & passionfruit|mango, passionfruit", "protein_yoghurt", None, "pot"),
    (r"vanilla protein yog", "protein_yoghurt_g", None, None),
    (r"protein pudding", "protein_pudding", None, "pudding"),
    (r"powdered (pb|peanut)|peanut butter \(i used powdered|peanut putter|powdered pb", "powdered_pb", None, None),
    (r"protein noodles", "protein_noodles", None, None),
    (r"protein wrap", "protein_wrap", None, "wrap"),
    (r"protein( powder)?\b|\bvanilla protein\b|choc(olate)? protein", "protein_powder", 25, "scoop"),
    (r"greek|yog(h)?urt", "greek_yog_ff", 60, None),
    (r"cottage", "cottage_cheese", None, None),
    (r"cream cheese|cheese triangle", "cream_cheese", 17, None),
    (r"single cream", "single_cream", None, None),
    (r"coconut milk", "coconut_milk_light", 400, "tin"),
    (r"almond milk|milk.*almond", "almond_milk", None, None),
    (r"oat milk|milk.*\boat\b", "oat_milk", None, None),
    (r"semi|light milk|square milk", "milk_semi", None, None),
    (r"milk", "milk_skimmed", None, None),
    (r"ice cream", "ice_cream_lowcal", None, None),
    (r"feta", "feta", None, None),
    (r"parmesan|grana padano", "parmesan", None, None),
    (r"cheese single|cheese slice|slices? (of )?cheese|light cheese slices|light cheese triangles", "cheese_slice", None, "slice"),
    (r"mozzarella", "mozzarella", 25, None),
    (r"low.?fat ch|reduced.?fat ch|30% less fat|light cheese|low fat cheese|reduced fat cheese|lighter cheese", "cheddar_rf", None, None),
    (r"cheddar|cheese", "cheddar", None, None),
    (r"liquid egg white", "egg_white_liquid", None, None),
    (r"egg white", "egg_white", None, "egg white"),
    (r"large eggs?(?! noodles)", "egg_large", None, "egg"),
    (r"\beggs?\b(?! noodles)", "egg", None, "egg"),
    (r"seasoning|packet (lemon|smokey|peri)", "seasoning_pack", None, "packet"),
    (r"ready.made mash|\bmash\b", "mash", None, None),
    (r"mini fillets|chicken breast|chicken\b(?! (stock|gravy|seasoning|sausage|chipolata|mince|thigh))|sizzle steak", "chicken_breast", 150, None),
    (r"pre-?cooked chicken|cooked chicken|chicken, cooked", "chicken_cooked", None, None),
    (r"chicken thigh", "chicken_thigh", None, None),
    (r"chicken mince", "chicken_mince", None, None),
    (r"chipolata", "chicken_chipolata", None, "chipolata"),
    (r"chicken sausage", "chicken_sausage", None, "sausage"),
    (r"skinny sausage", "skinny_sausage", None, "sausage"),
    (r"quorn chicken|quorn pieces", "quorn_pieces", None, None),
    (r"quorn mince", "quorn_mince", None, None),
    (r"meatball", "meatballs_skinny", None, None),
    (r"pork mince", "pork_mince_5", None, None),
    (r"pork patt", "pork_patty", None, "patty"),
    (r"diced beef|lean diced", "beef_diced_lean", None, None),
    (r"steak mince|beef mince|5% mince|lean mince|\bmince\b", "beef_mince_5", None, None),
    (r"steak", "beef_steak_thin", None, None),
    (r"medallion", "bacon_medallion", None, "medallion"),
    (r"bacon|rash", "bacon_rasher_rf", None, "rasher"),
    (r"chorizo", "chorizo", None, None),
    (r"\bham\b", "ham", 26, None),
    (r"tuna", "tuna_tin", None, "tin"),
    (r"prawn", "prawns", None, None),
    (r"muesli", "muesli", None, None),
    (r"granola", "granola", None, None),
    (r"rice krispie", "rice_krispies", None, None),
    (r"rice cake", "rice_cake", None, "rice cake"),
    (r"\boats?\b", "oats", None, None),
    (r"wheat bisc|weetabix|wheat-bics", "wheat_biscuit", None, "biscuit"),
    (r"crumpet", "crumpet", None, "crumpet"),
    (r"croissant", "croissant", None, "croissant"),
    (r"bagel", "bagel_thin", None, "bagel thin"),
    (r"english muffin", "english_muffin", None, "muffin"),
    (r"warburtons|thins\b", "sandwich_thin", None, "thin"),
    (r"panini", "panini_roll", None, "roll"),
    (r"hot dog roll", "hotdog_roll", None, "roll"),
    (r"brioche", "brioche_bun", None, "bun"),
    (r"\bbuns?\b|\brolls?\b", "bun_wholemeal", None, "bun"),
    (r"wholemeal bread|slices? of bread|\bbread\b", "bread_slice", None, "slice"),
    (r"mini tortilla", "mini_tortilla", None, "tortilla"),
    (r"tortilla|wraps?\b", "tortilla", None, "wrap"),
    (r"gnocchi", "gnocchi", None, None),
    (r"lasagne sheet", "lasagne_sheet", 22, None),
    (r"udon", "udon", None, None),
    (r"maggi|noodle packet", "instant_noodles", None, "packet"),
    (r"egg noodles.*dry|dry.*egg noodles", "egg_noodles_dry", None, None),
    (r"noodles", "noodles_ready", None, None),
    (r"arborio|risotto", "rice_dry", None, None),
    (r"packet (white )?rice|rice \(250g\)|packet white rice|microwave rice", "rice_cooked", None, None),
    (r"\brice\b", "rice_dry", None, None),
    (r"pasta sauce|bolognese sauce|lasagne sauce|chilli con carne sauce|tomato pasta sauce", "jar_sauce", None, None),
    (r"lemon & herb sauce|peri peri (garlic )?sauce|white sauce|cheese sauce", "light_sauce", None, None),
    (r"macaroni|spaghetti|\bpasta\b(?! water)", "pasta_dry", None, None),
    (r"plain.*flour|self.raising|\bflour\b", "flour", None, None),
    (r"cornflour", "cornflour", None, None),
    (r"cornflakes", "cornflakes", None, None),
    (r"ground almond|flaked almond", "ground_almonds", None, None),
    (r"peanut butter|\bpb\b", "peanut_butter", None, None),
    (r"biscoff spread", "biscoff_spread", None, None),
    (r"biscoff", "biscoff_biscuit", None, "biscuit"),
    (r"nutella|nutokka", "choc_hazelnut", None, None),
    (r"cocoa", "cocoa", None, None),
    (r"white choc|choc(olate)? chips|dark choc|dark chocolate|chocolate", "choc_chips", None, None),
    (r"coconut oil", "coconut_oil", None, None),
    (r"olive oil", "olive_oil", None, None),
    (r"olive spread|light butter|\bbutter\b", "light_spread", None, None),
    (r"sugar.free maple|sugar free syrup", "maple_syrup_sf", None, None),
    (r"maple syrup|maple", "maple_syrup", None, None),
    (r"honey", "honey", None, None),
    (r"\bjam\b", "jam", None, None),
    (r"meringue", "meringue_nest", None, "nest"),
    (r"banana chips", "banana_chips", 30, None),
    (r"banana", "banana", None, "banana"),
    (r"blueberr", "blueberries", None, None),
    (r"raspberr", "raspberries", None, None),
    (r"strawberr", "strawberries", None, None),
    (r"mixed berr|berry medley|frozen berries|berries", "mixed_berries", None, None),
    (r"tropical smoothie|tropical mix", "tropical_mix", None, None),
    (r"mango", "mango", None, None),
    (r"pineapple", "pineapple", None, None),
    (r"apples?\b", "apple", None, "apple"),
    (r"peach", "peaches_tinned", None, None),
    (r"avocado", "avocado", 150, None),
    (r"light mayo|lighter than light|mayo", "light_mayo", None, None),
    (r"ketchup", "ketchup", None, None),
    (r"bbq sauce", "bbq_sauce", None, None),
    (r"sweet chilli", "sweet_chilli", None, None),
    (r"hoisin", "hoisin", None, None),
    (r"sriracha|fiery mayo", "sriracha", None, None),
    (r"salsa", "salsa", None, None),
    (r"tomato pur", "tomato_puree", None, None),
    (r"red pesto", "pesto_red", None, None),
    (r"pesto", "pesto_green", None, None),
    (r"chipotle paste", "chipotle_paste", None, None),
    (r"curry paste|tikka|thai curry paste", "curry_paste", None, None),
    (r"mayflower|curry sauce", "curry_sauce_mix", None, None),
    (r"soy", "soy_sauce", None, None),
    (r"vinegar", "vinegar", None, None),
    (r"lemon juice", "lemon_juice", None, None),
    (r"passata", "passata", None, None),
    (r"chopped tom", "chopped_tomatoes", 400, "tin"),
    (r"sun.?dried", "sundried_tomatoes", None, None),
    (r"roasted red pepper", "roasted_peppers", None, None),
    (r"gravy granules", "gravy_granules", None, None),
    (r"gravy", "gravy", None, None),
    (r"stock", "stock", None, None),
    (r"seasoning|packet (lemon|smokey|peri)", "seasoning_pack", None, "packet"),
    (r"taco beans", "taco_beans", 400, "tin"),
    (r"kidney beans", "kidney_beans", 240, "tin"),
    (r"black beans", "black_beans", 240, "tin"),
    (r"chickpea", "chickpeas", 240, "tin"),
    (r"baked beans", "baked_beans", None, None),
    (r"lentil", "lentils_dry", None, None),
    (r"sweetcorn", "sweetcorn", None, None),
    (r"sweet potato", "sweet_potato", 250, None),
    (r"baby potatoes|herby baby", "potatoes", None, None),
    (r"potato", "potatoes", 235, None),
    (r"\bpeas\b", "peas", None, None),
    (r"broccoli", "broccoli", 300, None),
    (r"cauliflower", "cauliflower", 600, None),
    (r"spinach|rocket", "spinach", None, None),
    (r"watercress", "watercress", None, None),
    (r"leek", "leeks", None, None),
    (r"courgette", "courgette", None, None),
    (r"mushroom", "mushrooms", None, None),
    (r"stir fry", "stir_fry_veg", None, None),
    (r"mixed veg|vegetable|veg mix|frozen veg|frozen mixed", "mixed_veg", None, None),
    (r"green beans", "green_beans", None, None),
    (r"carrot", "carrot", None, "carrot"),
    (r"red cabbage|pickled cabbage", "red_cabbage", None, None),
    (r"gherkin", "gherkins", None, None),
    (r"jalape", "jalapenos", 170, None),
    (r"spring onion", "spring_onions", None, None),
    (r"crispy onion", "crispy_onions", None, None),
    (r"onions?\b", "onion", None, "onion"),
    (r"peppers?\b", "pepper", None, "pepper"),
    (r"cherry|plum tomato|baby plum", "cherry_tomatoes", None, None),
    (r"tomato", "tomato", None, "tomato"),
    (r"cucumber", "cucumber", 300, None),
    (r"romaine|gem lettuce", "romaine", None, "head"),
    (r"lettuce|salad", "salad_leaves", None, None),
]
RULES = [(re.compile(p, re.I), k, g, u) for p, k, g, u in RULES]

DROP = re.compile(r"^(& PRICE|INGREDIENTS|Enjoy!?|Get creative!?|Put a lid on.*|Then combine.*|Slice the .*|Air-fry your .*|TIP-.*|SWAP-.*|"
                  r"Packet|Powder|Sauce|Seasoning|Mash|With rice .*|\*rinse.*|\*to mix.*|.*:)$", re.I)

GRAM_ALT = {"protein_yoghurt": "protein_yoghurt_g", "carrot": "carrot_grated", "tomato": "tomatoes", "onion": "onion_g", "apple": "apple_g", "banana": "banana_g"}
UNIT_WORDS = r"(?:kg|g|ml|l|litre|litres|tbsp|tbsps|tsp|tsps|scoops?|tins?|jars?|packs?|packets?|bags?|tubs?|slices?|cloves?|heads?|rashers?|rash|serve|squares?|pints?|shots?|handfuls?|large|medium|small|whole|x)"
QTY = re.compile(r"^(?P<num>\d+(?:\.\d+)?(?:/\d+)?|[½¼¾⅓⅔])(?:\s*-\s*\d+)?\s*(?P<unit>" + UNIT_WORDS + r")?\b\.?\s*(?P<rest>.*)$", re.I)
PAREN_G = re.compile(r"\((?:[^)\d]*)(?P<g>\d+(?:\.\d+)?)\s*(?P<u>g|ml|kg)\b[^)]*\)", re.I)


def num(s):
    if s in FRAC:
        return FRAC[s]
    if "/" in s:
        a, b = s.split("/")
        return float(a) / float(b)
    return float(s)


def clean_name(s):
    s = re.sub(r"\(£[\d.]+\)", "", s)
    s = re.sub(r"\(excl\.[^)]*\)?", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ,-")
    s = re.sub(r"^(of|drained|tsp)\s+", "", s, flags=re.I)
    s = re.sub(r"\bsauc\b", "sauce", s)
    m = re.match(r"^\(([^)]*)\)\s*(.+)$", s)  # "(1 bag) Frozen raspberries" -> "Frozen raspberries (1 bag)"
    if m:
        s = f"{m.group(2)} ({m.group(1)})"
    s = re.sub(r"\)\s+powder into a thick paste$", ")", s)
    return s[:1].upper() + s[1:]


def parse_ingredient(line):
    line = re.sub(r"^\*?optional:\s*", "", line, flags=re.I).strip()
    if DROP.match(line) or len(line) < 3:
        return None
    m = QTY.match(line)
    if not m:
        pg = PAREN_G.search(line)
        low0 = line.lower()
        rule = next(((k, g, u) for rx, k, g, u in RULES if rx.search(low0)), None)
        if pg and rule and FOODS[rule[0]][0] == 100 and not FIXED.search(low0):
            return (float(pg["g"]), "ml" if pg["u"].lower() == "ml" else "g", rule[0], clean_name(PAREN_G.sub("", line)))
        return (clean_name(line),)
    n, unit, rest = num(m["num"]), (m["unit"] or "").lower(), m["rest"]
    low = re.sub(r"\(excl\.[^)]*\)?", "", line.lower())
    if re.search(r"\bwater\b(?!cress)|\bice\b(?! cream)|coffee|\bshots?\b", low) and not re.search(r"milk|coconut|protein|banana", low):
        return (clean_name(line),)
    big = unit in ("g", "ml", "kg") and n >= 50
    if FIXED.search(low) and not NOT_FIXED_OVERRIDE.search(low) and not big:
        return (clean_name(line),)
    rule = next(((k, g, u) for rx, k, g, u in RULES if rx.search(low)), None)
    if not rule:
        return ("UNMAPPED " + clean_name(line),)
    key, each_g, label = rule
    basis = FOODS[key][0]
    pg = PAREN_G.search(rest)
    name = clean_name(PAREN_G.sub("", rest) if pg else rest)
    if unit in ("g", "ml", "kg", "l", "litre", "litres"):
        q = n * (1000 if unit in ("kg", "l", "litre", "litres") else 1)
        u = "ml" if unit in ("ml", "l", "litre", "litres") else "g"
        if basis == 1:
            if key in GRAM_ALT:
                return (q, u, GRAM_ALT[key], name)
            return (q, u, key, name, "per-item food given in grams")
        return (q, u, key, name)
    if pg and basis == 100:
        g = float(pg["g"]) * (1000 if pg["u"].lower() == "kg" else 1)
        return (g, "ml" if pg["u"].lower() == "ml" else "g", key, name)
    if unit in ("pint", "pints") and basis == 100:
        return (n * 568, "ml", key, name)
    if unit in ("square", "squares") and basis == 100:
        return (n * 50, "ml", key, name)
    if unit in ("tbsp", "tbsps"):
        return (n * 15, "g", key, name) if basis == 100 else (n, "tbsp", key, name)
    if unit in ("tsp", "tsps"):
        return (n * 5, "g", key, name) if basis == 100 else (n, "tsp", key, name)
    if basis == 1:
        return (n, label or "item", key, name)
    if each_g:
        return (n, label or (unit if unit not in ("", "large", "medium", "small", "whole", "x") else "item"), key, name, each_g)
    return (n, unit or "item", key, name, "NEEDS WEIGHT")


def title_case(t):
    t = re.sub(r"\s+", " ", t.replace("’", "'").replace("‘", "'")).strip()
    t = re.sub(r"\bBack to contents\b", "", t, flags=re.I)
    t = re.sub(r"(?<=\w) V (?=\w)", " ", t)
    small = {"and", "or", "of", "on", "with", "the", "a", "in"}
    keep = {"BBQ", "BLT", "PB", "PB&J", "MSG"}
    words = []
    for i, w in enumerate(t.split()):
        core = w.strip("'")
        if core.upper() in keep:
            words.append(w.upper())
        elif i and core.lower() in small:
            words.append(w.lower())
        else:
            words.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")))
    return " ".join(words).strip()


def main():
    d = json.load(open(sys.argv[1]))
    out = {k: [] for k in d}
    for k, rs in d.items():
        for r in rs:
            ings, optional = [], False
            for line in r["ingredients"]:
                if re.match(r"(?i)^\*?(optional( to serve| toppings| additions)?|to serve( with)?|topping suggestions|garnish)\s*:?\s*$", line.strip()):
                    optional = True
                    continue
                if optional:
                    if not DROP.match(line.strip()) and not line.strip().endswith(":"):
                        ings.append((clean_name(line) + " (optional, not in the macros)",))
                else:
                    ings.append(parse_ingredient(line))
            r2 = dict(r)
            r2["title"] = title_case(r["title"])
            r2["parsed"] = [i for i in ings if i]
            r2["steps"] = [s for s in r["steps"] if not re.fullmatch(r"(serve (&|and) enjoy|enjoy|slice, serve,? enjoy)[!. ]*(my friends)?!*", s.strip(), re.I)]
            out[k].append(r2)
    json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
    for k, rs in out.items():
        for r in rs:
            for p in r["parsed"]:
                if len(p) == 1 and p[0].startswith("UNMAPPED") or len(p) == 5 and not isinstance(p[4], (int, float)):
                    print(k, r["page"], r["title"][:30], "|", p)


main()
