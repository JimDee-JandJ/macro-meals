// Shared helpers for the directory and recipe pages.
const MM = (() => {
  const MACROS = ['kcal', 'protein', 'carbs', 'fat'];

  async function loadRecipes() {
    const res = await fetch('assets/data/recipes.json');
    if (!res.ok) throw new Error('Could not load recipes');
    return res.json();
  }

  // Each ingredient lists its macros for its default quantity, so a quantity
  // change scales them linearly. Fixed ingredients carry no macros.
  function ingredientMacros(ing, qty) {
    const out = { kcal: 0, protein: 0, carbs: 0, fat: 0 };
    if (ing.fixed || !ing.qty) return out;
    const ratio = qty / ing.qty;
    MACROS.forEach(m => { out[m] = (ing[m] || 0) * ratio; });
    return out;
  }

  // Macros per serving for the given quantities (defaults to the book's).
  function recipeMacros(recipe, quantities) {
    const total = { kcal: 0, protein: 0, carbs: 0, fat: 0 };
    recipe.ingredients.forEach((ing, i) => {
      const qty = quantities ? quantities[i] : ing.qty;
      const m = ingredientMacros(ing, qty);
      MACROS.forEach(k => { total[k] += m[k]; });
    });
    const servings = recipe.servings || 1;
    MACROS.forEach(k => { total[k] /= servings; });
    return total;
  }

  function round(n) { return Math.round(n); }

  // Share of calories from each macro, for the split bar.
  function split(m) {
    const p = m.protein * 4, c = m.carbs * 4, f = m.fat * 9;
    const sum = p + c + f || 1;
    return { protein: (p / sum) * 100, carbs: (c / sum) * 100, fat: (f / sum) * 100 };
  }

  function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, ch => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]
    ));
  }

  function imageHtml(recipe) {
    if (recipe.image) {
      return `<img src="assets/img/${esc(recipe.image)}" alt="${esc(recipe.title)}" loading="lazy">`;
    }
    return `<div class="img-placeholder" aria-hidden="true"><span>${esc(recipe.mainIngredient || recipe.meal || '')}</span></div>`;
  }

  function splitBarHtml(m) {
    const s = split(m);
    return `<div class="split-bar" title="Calories from protein / carbs / fat">
      <span class="p" style="width:${s.protein}%"></span><span class="c" style="width:${s.carbs}%"></span><span class="f" style="width:${s.fat}%"></span>
    </div>`;
  }

  const TARGETS_KEY = 'macro-meals:targets';
  function loadTargets() {
    try { return JSON.parse(localStorage.getItem(TARGETS_KEY)) || null; } catch { return null; }
  }
  function saveTargets(t) {
    try { localStorage.setItem(TARGETS_KEY, JSON.stringify(t)); } catch { /* storage unavailable */ }
  }

  return { MACROS, loadRecipes, ingredientMacros, recipeMacros, round, split, esc, imageHtml, splitBarHtml, loadTargets, saveTargets };
})();
