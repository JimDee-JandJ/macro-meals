(async () => {
  const root = document.getElementById('recipe');
  const id = new URLSearchParams(location.search).get('id');

  let recipes;
  try {
    recipes = await MM.loadRecipes();
  } catch (e) {
    root.innerHTML = '<p class="empty">Recipes could not be loaded.</p>';
    return;
  }
  const recipe = recipes.find(r => r.id === id);
  if (!recipe) {
    root.innerHTML = '<p class="empty">Recipe not found. <a href="index.html">Back to all recipes</a></p>';
    return;
  }
  document.title = `${recipe.title} · Macro Meals`;

  const ings = recipe.ingredients;
  const servings = recipe.servings || 1;
  // ratio[i] is the user's tweak to one ingredient; whole scales everything.
  const state = { ratio: ings.map(() => 1), whole: 1 };
  const original = MM.recipeMacros(recipe);

  const isWeight = u => u === 'g' || u === 'ml';
  const stepFor = ing => isWeight(ing.unit) ? (ing.qty >= 50 ? 5 : 1) : 0.25;
  const qtyOf = i => ings[i].qty * state.ratio[i] * state.whole;
  const quantities = () => ings.map((ing, i) => ing.fixed ? 0 : qtyOf(i));

  function fmtQty(ing, q) {
    if (isWeight(ing.unit)) return `${Math.round(q)}${ing.unit}`;
    const n = Math.round(q * 4) / 4;
    const unit = n === 1 ? ing.unit : (ing.unit.endsWith('s') ? ing.unit : `${ing.unit}s`);
    return `${n} ${unit}`;
  }
  const fmtDelta = (now, was, unit) => {
    const d = Math.round(now) - Math.round(was);
    if (!d) return '';
    return `<span class="delta ${d > 0 ? 'up' : 'down'}">${d > 0 ? '+' : ''}${d}${unit}</span>`;
  };

  const time = [
    recipe.prep && `<li><span>Prep</span>${MM.esc(recipe.prep)}</li>`,
    recipe.cook && `<li><span>Cook</span>${MM.esc(recipe.cook)}</li>`,
    `<li><span>Makes</span>${servings}</li>`,
    recipe.price != null && `<li><span>Per serving</span>£${recipe.price.toFixed(2)}</li>`,
    recipe.shop && `<li><span>Shop</span>${MM.esc(recipe.shop)}</li>`
  ].filter(Boolean).join('');
  const vegLabel = { V: 'Vegetarian', VG: 'Vegan' }[recipe.vegetarian];

  root.innerHTML = `
    <nav class="crumbs"><a href="index.html">All recipes</a> <span>/</span> ${MM.esc(recipe.meal)}</nav>
    <header class="recipe-head">
      <div class="recipe-intro">
        <p class="eyebrow">${MM.esc(recipe.book)}</p>
        <h1>${MM.esc(recipe.title)}</h1>
        ${recipe.description ? `<p class="lede">${MM.esc(recipe.description)}</p>` : ''}
        <ul class="facts">${time}</ul>
        <div class="tags">
          <span class="tag">${MM.esc(recipe.meal)}</span>
          <span class="tag">${MM.esc(recipe.mainIngredient)}</span>
          ${vegLabel ? `<span class="tag">${vegLabel}</span>` : ''}
        </div>
      </div>
      <div class="recipe-img">${MM.imageHtml(recipe)}</div>
    </header>

    <div class="recipe-layout">
      <div class="recipe-main">
        <section class="panel">
          <div class="panel-head">
            <h2>Ingredients</h2>
            <button type="button" class="link-btn" id="reset">Reset to original</button>
          </div>
          <div class="whole">
            <label for="whole">Scale whole recipe</label>
            <input type="range" id="whole" min="0.25" max="3" step="0.05" value="1">
            <output id="whole-out">100%</output>
          </div>
          <p class="hint">Drag a slider to change one ingredient. The macros update as you go.${servings > 1 ? ` Amounts are for the whole batch (makes ${servings}); the macro totals are per serving.` : ''}</p>
          <ul class="ing-list" id="ing-list"></ul>
        </section>

        <section class="panel">
          <h2>Method</h2>
          <ol class="steps">${recipe.instructions.map(s => `<li>${MM.esc(s)}</li>`).join('')}</ol>
          ${recipe.tips || recipe.swaps ? `<div class="notes">
            ${recipe.tips ? `<div class="note"><h3>Tips</h3><p>${MM.esc(recipe.tips)}</p></div>` : ''}
            ${recipe.swaps ? `<div class="note"><h3>Swaps</h3><p>${MM.esc(recipe.swaps)}</p></div>` : ''}
          </div>` : ''}
          <p class="hint" id="method-note" hidden>The method shows the book's original amounts. Use the ingredient list above for your adjusted quantities.</p>
        </section>
      </div>

      <aside class="recipe-side">
        <section class="panel sticky">
          <h2>Macros <small>per serving</small></h2>
          <div id="macro-summary"></div>
          <div class="targets">
            <h3>Your targets for this meal</h3>
            <div class="target-inputs">
              ${MM.MACROS.map(k => `
                <label><span>${k === 'kcal' ? 'Calories' : k[0].toUpperCase() + k.slice(1)}</span>
                  <input type="number" min="0" inputmode="numeric" data-target="${k}" placeholder="–">
                  <em>${k === 'kcal' ? 'kcal' : 'g'}</em></label>`).join('')}
            </div>
            <div id="target-bars"></div>
            <div class="fit-btns">
              <button type="button" class="btn" data-fit="kcal">Fit to calories</button>
              <button type="button" class="btn" data-fit="protein">Fit to protein</button>
            </div>
            <p class="hint">Targets are saved in this browser. "Fit" scales the whole recipe to hit that number.</p>
          </div>
        </section>
      </aside>
    </div>
    <div class="mobile-bar" id="mobile-bar" aria-live="polite"></div>`;

  const list = document.getElementById('ing-list');
  const whole = document.getElementById('whole');
  const wholeOut = document.getElementById('whole-out');
  const summary = document.getElementById('macro-summary');
  const bars = document.getElementById('target-bars');
  const methodNote = document.getElementById('method-note');
  const mobileBar = document.getElementById('mobile-bar');
  const targetInputs = [...document.querySelectorAll('[data-target]')];

  list.innerHTML = ings.map((ing, i) => {
    if (ing.fixed) {
      return `<li class="ing fixed"><div class="ing-top"><span class="ing-name">${MM.esc(ing.name)}</span></div></li>`;
    }
    const step = stepFor(ing);
    return `<li class="ing" data-i="${i}">
      <div class="ing-top">
        <span class="ing-name">${MM.esc(ing.name)}</span>
        <span class="ing-qty" id="q${i}"></span>
      </div>
      <input type="range" min="0" step="${step}" aria-label="${MM.esc(ing.name)} quantity" id="s${i}">
      <div class="ing-macros" id="m${i}"></div>
    </li>`;
  }).join('');

  let targets = MM.loadTargets() || {};
  targetInputs.forEach(inp => { if (targets[inp.dataset.target]) inp.value = targets[inp.dataset.target]; });

  function render() {
    wholeOut.textContent = `${Math.round(state.whole * 100)}%`;
    whole.value = state.whole;

    ings.forEach((ing, i) => {
      if (ing.fixed) return;
      const slider = document.getElementById(`s${i}`);
      const q = qtyOf(i);
      slider.max = Math.max(ing.qty * 3 * Math.max(1, state.whole), q);
      slider.value = q;
      document.getElementById(`q${i}`).innerHTML = fmtQty(ing, q) +
        (Math.abs(q - ing.qty) > 1e-6 ? ` <s>${fmtQty(ing, ing.qty)}</s>` : '');
      const m = MM.ingredientMacros(ing, q);
      document.getElementById(`m${i}`).textContent =
        `${MM.round(m.kcal)} kcal · ${MM.round(m.protein)}P · ${MM.round(m.carbs)}C · ${MM.round(m.fat)}F`;
    });

    const m = MM.recipeMacros(recipe, quantities());
    const changed = MM.MACROS.some(k => Math.round(m[k]) !== Math.round(original[k]));
    methodNote.hidden = !changed;

    summary.innerHTML = `
      <div class="big-kcal"><strong>${MM.round(m.kcal)}</strong> kcal ${fmtDelta(m.kcal, original.kcal, '')}</div>
      <div class="macro-grid">
        <div class="mg p"><span>Protein</span><strong>${MM.round(m.protein)}g</strong>${fmtDelta(m.protein, original.protein, 'g')}</div>
        <div class="mg c"><span>Carbs</span><strong>${MM.round(m.carbs)}g</strong>${fmtDelta(m.carbs, original.carbs, 'g')}</div>
        <div class="mg f"><span>Fat</span><strong>${MM.round(m.fat)}g</strong>${fmtDelta(m.fat, original.fat, 'g')}</div>
      </div>
      ${MM.splitBarHtml(m)}
      <p class="split-legend">${(() => { const s = MM.split(m); return `${Math.round(s.protein)}% protein · ${Math.round(s.carbs)}% carbs · ${Math.round(s.fat)}% fat`; })()}</p>
      ${changed ? `<p class="orig">Book original: ${MM.round(original.kcal)} kcal · ${MM.round(original.protein)}P · ${MM.round(original.carbs)}C · ${MM.round(original.fat)}F</p>` : ''}`;

    mobileBar.innerHTML = `
      <div><strong>${MM.round(m.kcal)}</strong><span>kcal</span></div>
      <div class="p"><strong>${MM.round(m.protein)}g</strong><span>protein</span></div>
      <div class="c"><strong>${MM.round(m.carbs)}g</strong><span>carbs</span></div>
      <div class="f"><strong>${MM.round(m.fat)}g</strong><span>fat</span></div>`;

    bars.innerHTML = MM.MACROS.filter(k => targets[k] > 0).map(k => {
      const pct = (m[k] / targets[k]) * 100;
      const diff = Math.round(m[k] - targets[k]);
      const unit = k === 'kcal' ? ' kcal' : 'g';
      const label = k === 'kcal' ? 'Calories' : k[0].toUpperCase() + k.slice(1);
      const status = Math.abs(pct - 100) <= 5 ? 'on' : pct > 100 ? 'over' : 'under';
      return `<div class="tbar ${status}">
        <div class="tbar-top"><span>${label}</span><span>${diff === 0 ? 'On target' : `${diff > 0 ? '+' : ''}${diff}${unit}`}</span></div>
        <div class="tbar-track"><span style="width:${Math.min(pct, 100)}%"></span></div>
      </div>`;
    }).join('');
  }

  list.addEventListener('input', e => {
    const li = e.target.closest('.ing');
    if (!li || e.target.type !== 'range') return;
    const i = +li.dataset.i;
    state.ratio[i] = +e.target.value / (ings[i].qty * state.whole || 1);
    render();
  });

  whole.addEventListener('input', () => { state.whole = +whole.value; render(); });

  document.getElementById('reset').addEventListener('click', () => {
    state.ratio = ings.map(() => 1);
    state.whole = 1;
    render();
  });

  targetInputs.forEach(inp => inp.addEventListener('input', () => {
    const v = parseFloat(inp.value);
    targets[inp.dataset.target] = v > 0 ? v : undefined;
    MM.saveTargets(targets);
    render();
  }));

  document.querySelectorAll('[data-fit]').forEach(btn => btn.addEventListener('click', () => {
    const k = btn.dataset.fit;
    const target = targets[k];
    if (!(target > 0)) {
      document.querySelector(`[data-target="${k}"]`).focus();
      return;
    }
    const current = MM.recipeMacros(recipe, quantities())[k];
    if (current > 0) {
      state.whole = Math.min(3, Math.max(0.25, state.whole * (target / current)));
      render();
    }
  }));

  render();
})();
