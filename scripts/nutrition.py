"""Reference nutrition values used to split a recipe's macros across its ingredients.

Each entry is (basis, kcal, protein, carbs, fat):
  basis 100 -> values per 100 g / 100 ml
  basis 1   -> values per item (one egg, one wrap, ...)

These are typical UK supermarket label values. They only need to be roughly
right: build_recipes.py calibrates every recipe so its totals match the book.
"""

FOODS = {
    # Grains, bread & wraps
    "oats":               (100, 375, 13, 60, 7.5),
    "wheat_biscuit":      (1, 68, 2.2, 13, 0.4),
    "tortilla":           (1, 190, 5.5, 31, 4.5),
    "mini_tortilla":      (1, 95, 2.7, 16, 2),
    "bagel_thin":         (1, 130, 5, 23, 1.5),
    "brioche_bun":        (1, 170, 5, 28, 4.5),
    "sandwich_thin":      (1, 100, 4, 17.5, 1),
    "english_muffin":     (1, 135, 5.5, 25, 1.2),
    "wholemeal_bread":    (100, 235, 10, 40, 2.5),
    "panini_roll":        (1, 230, 8, 44, 2),
    "pasta_dry":          (100, 355, 12.5, 71, 1.5),
    "egg_noodles_dry":    (100, 360, 12, 70, 2.5),
    "noodles_ready":      (100, 157, 5.3, 30, 1.9),
    "cornflakes":         (100, 378, 7, 84, 0.9),
    "cornflour":          (100, 350, 0.6, 87, 0.1),

    # Protein
    "protein_powder":     (100, 400, 78, 8, 6),
    "chicken_breast":     (100, 110, 24, 0, 1.5),
    "chicken_cooked":     (100, 150, 31, 0.5, 2),
    "beef_mince_5":       (100, 125, 21.5, 0, 4.5),
    "beef_steak_thin":    (100, 130, 22, 0, 4.5),
    "bacon_medallion":    (1, 32, 5.5, 0.2, 1.1),
    "bacon_rasher_rf":    (1, 45, 6, 0.3, 2.2),
    "chicken_chipolata":  (1, 40, 4.5, 1, 2),
    "skinny_sausage":     (1, 60, 7, 2.5, 2.5),
    "egg":                (1, 70, 6.3, 0.3, 4.8),
    "egg_large":          (1, 78, 6.5, 0.5, 5.5),
    "egg_white":          (1, 17, 3.6, 0.2, 0.1),

    # Dairy
    "almond_milk":        (100, 13, 0.4, 0.1, 1.1),
    "oat_milk":           (100, 46, 1, 6.5, 1.5),
    "greek_yog_ff":       (100, 57, 10, 4, 0.2),
    "yog_ff":             (100, 56, 5.6, 7.8, 0.2),
    "protein_yoghurt":    (1, 120, 20, 9, 0.4),
    "cottage_cheese_ff":  (100, 68, 12.5, 3.8, 0.3),
    "mozzarella":         (100, 300, 23, 2, 22),
    "cheddar":            (100, 416, 25, 0.1, 35),
    "cheddar_rf":         (100, 300, 30, 0.5, 20),
    "parmesan":           (100, 390, 34, 1, 28),
    "light_cream_cheese": (100, 150, 7.5, 4, 11),
    "light_spread":       (100, 400, 0.3, 0.6, 44),

    # Fruit
    "banana":             (1, 105, 1.3, 27, 0.4),
    "blueberries":        (100, 57, 0.7, 14.5, 0.3),
    "raspberries":        (100, 53, 1.2, 12, 0.7),
    "mixed_berries":      (100, 45, 0.9, 8, 0.3),
    "peaches_tinned":     (100, 54, 0.4, 13, 0.1),
    "avocado":            (100, 160, 2, 1.9, 14.7),

    # Veg
    "onion":              (1, 60, 1.6, 13, 0.2),
    "pepper":             (1, 40, 1.6, 6.4, 0.5),
    "carrot":             (1, 25, 0.5, 5.5, 0.2),
    "carrot_grated":      (100, 36, 0.7, 7.5, 0.3),
    "tomato":             (1, 15, 0.6, 2.6, 0.2),
    "cherry_tomatoes":    (100, 18, 0.9, 3, 0.2),
    "tomatoes":           (100, 18, 0.9, 3, 0.2),
    "salad_leaves":       (100, 20, 1.5, 2.5, 0.3),
    "romaine":            (1, 42, 3, 8, 0.75),
    "cucumber":           (100, 12, 0.6, 2, 0.1),
    "mushrooms":          (100, 20, 2.5, 1, 0.4),
    "spring_onions":      (100, 30, 1.8, 5, 0.5),
    "sweetcorn":          (100, 85, 2.9, 15, 1.4),
    "potatoes":           (100, 75, 2, 16, 0.2),
    "baby_potatoes_herb": (100, 95, 2, 15, 3),
    "mixed_veg":          (100, 45, 2.8, 6, 0.5),
    "green_beans":        (100, 25, 1.8, 3.2, 0.3),
    "stir_fry_veg":       (100, 35, 1.8, 5, 0.4),
    "baked_beans":        (100, 78, 4.9, 12.5, 0.3),
    "kidney_beans":       (100, 100, 7, 15, 0.6),
    "chopped_tomatoes":   (100, 22, 1.2, 3.8, 0.2),

    # Sauces, spreads & sweet things
    "biscoff_spread":     (100, 584, 1.4, 57, 38),
    "biscoff_biscuit":    (1, 38, 0.5, 5.7, 1.5),
    "choc_hazelnut":      (100, 539, 6, 57, 31),
    "peanut_butter":      (100, 610, 25, 13, 50),
    "cocoa":              (100, 350, 22, 14, 21),
    "choc_chips":         (100, 520, 6, 55, 30),
    "honey":              (100, 304, 0.3, 82, 0),
    "jam":                (100, 250, 0.4, 60, 0.1),
    "light_mayo":         (100, 270, 0.7, 7, 27),
    "ketchup":            (100, 110, 1.3, 25, 0.2),
    "bbq_sauce":          (100, 150, 0.8, 35, 0.3),
    "sriracha":           (100, 100, 2, 20, 1),
    "salsa":              (100, 40, 1.3, 7, 0.3),
    "tomato_puree":       (100, 80, 4.5, 13, 0.3),
    "pasta_sauce":        (100, 50, 1.5, 8, 1),
    "soy_sauce":          (100, 60, 8, 5, 0),
    "gravy":              (100, 30, 0.5, 5, 0.5),
    "seasoning_pack":     (1, 90, 2, 17, 1.5),
    "snp_seasoning":      (100, 280, 8, 50, 3),
}
