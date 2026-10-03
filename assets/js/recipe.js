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
  // ratio[i] is the user's tweak to one ingredient; whole is the portion size;
  // servings is how many portions are being made (more servings = more food,
  // same macros per serving).
  const state = { ratio: ings.map(() => 1), whole: 1, servings, view: 'serving', group: { protein: 1, carbs: 1, fat: 1 } };
  const original = MM.recipeMacros(recipe);
  const MAX_SERVINGS = 20;

  const isWeight = u => u === 'g' || u === 'ml';
  const stepFor = ing => isWeight(ing.unit) ? (ing.qty >= 50 ? 5 : 1) : 0.25;
  const servingFactor = () => state.servings / servings;

  // Each ingredient belongs to the macro that supplies most of its calories, so the
  // protein / carbs / fat controls can scale "the protein bits", "the carb bits", etc.
  const GROUPS = { protein: { label: 'Protein', step: 5 }, carbs: { label: 'Carbs', step: 5 }, fat: { label: 'Fat', step: 2 } };
  // Vegetables, sauces and seasonings stay put: cutting carbs should mean less rice, not less veg.
  const KEEP = /onion|pepper|tomato|mushroom|broccoli|carrot|lettuce|salad|cucumber|spinach|rocket|watercress|veg|courgette|leek|cauliflower|green bean|cabbage|gherkin|jalape|sauce|soy|vinegar|lemon|seasoning|stock|gravy|puree|purée|passata|salsa|sriracha|ketchup|mustard|spice|herb/i;
  const totals = ings.reduce((t, ing) => {
    if (!ing.fixed) MM.MACROS.forEach(k => { t[k] += ing[k] || 0; });
    return t;
  }, { kcal: 0, protein: 0, carbs: 0, fat: 0 });
  const dominant = ings.map(ing => {
    if (ing.fixed) return null;
    const cal = { protein: (ing.protein || 0) * 4, carbs: (ing.carbs || 0) * 4, fat: (ing.fat || 0) * 9 };
    const best = Object.keys(cal).reduce((a, b) => (cal[b] > cal[a] ? b : a));
    return cal[best] > 0 ? best : null;
  });
  const groupOf = dominant.map((g, i) => {
    if (!g) return null;
    const ing = ings[i];
    const share = totals[g] ? (ing[g] || 0) / totals[g] : 0;  // ignore ingredients that barely supply this macro
    return KEEP.test(ing.name) || share < 0.05 ? null : g;
  });
  const groupFactor = i => (groupOf[i] ? state.group[groupOf[i]] : 1);
  const qtyOf = i => ings[i].qty * state.ratio[i] * state.whole * servingFactor() * groupFactor(i);
  const quantities = () => ings.map((ing, i) => ing.fixed ? 0 : qtyOf(i));
  const scale = (m, f) => Object.fromEntries(MM.MACROS.map(k => [k, m[k] * f]));
  // recipeMacros divides by the book's servings; re-divide by the servings being made.
  const perServing = () => scale(MM.recipeMacros(recipe, quantities()), servings / state.servings);

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
    `<li><span>Makes</span><b id="fact-makes">${servings}</b></li>`,
    recipe.price != null && `<li><span>Per serving</span>£${recipe.price.toFixed(2)}</li>`,
    recipe.price != null && `<li><span>Batch cost</span><b id="fact-batch">£${(recipe.price * servings).toFixed(2)}</b></li>`,
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
          ${(recipe.tags || []).map(t => `<span class="tag">${MM.esc(t)}</span>`).join('')}
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
          <div class="scalers">
            <div class="servings">
              <span class="scaler-label">Servings</span>
              <div class="stepper">
                <button type="button" id="serv-down" aria-label="Fewer servings">−</button>
                <output id="serv-out" aria-live="polite">${servings}</output>
                <button type="button" id="serv-up" aria-label="More servings">+</button>
              </div>
              <span class="scaler-note">More food, same macros per serving</span>
            </div>
            <div class="whole">
              <label for="whole" class="scaler-label">Portion size</label>
              <input type="range" id="whole" min="0.25" max="3" step="0.05" value="1">
              <output id="whole-out">100%</output>
              <span class="scaler-note">Bigger or smaller plates: changes the macros per serving</span>
            </div>
          </div>
          <div class="macro-tweaks">
            <div class="tweaks-head">
              <span class="scaler-label">Adjust macros</span>
              <span class="scaler-note">Per serving. Each control changes the ingredients that are mostly that macro.</span>
            </div>
            <div class="tweaks">
              ${Object.entries(GROUPS).map(([k, g]) => `
                <div class="tweak ${k[0]}" data-group="${k}">
                  <div class="tweak-top">
                    <span class="tweak-label">${g.label}</span>
                    <div class="stepper">
                      <button type="button" data-tweak="-1" aria-label="Less ${g.label.toLowerCase()}">−</button>
                      <output id="tw-${k}">–</output>
                      <button type="button" data-tweak="1" aria-label="More ${g.label.toLowerCase()}">+</button>
                    </div>
                  </div>
                  <p class="tweak-ings" id="twi-${k}"></p>
                </div>`).join('')}
            </div>
          </div>
          <p class="hint">Drag an ingredient's slider to change just that ingredient. Amounts are for the whole batch.</p>
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
          <div class="panel-head">
            <h2>Macros</h2>
            <div class="seg" role="tablist" aria-label="Show macros">
              <button type="button" role="tab" data-view="serving" aria-selected="true">Per serving</button>
              <button type="button" role="tab" data-view="batch" aria-selected="false">Whole batch</button>
            </div>
          </div>
          <div id="macro-summary"></div>
          <div class="targets">
            <h3>Your targets for this meal <small>(per serving)</small></h3>
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
            <p class="hint">Targets are saved in this browser. "Fit" changes the portion size to hit that number.</p>
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
  const servOut = document.getElementById('serv-out');
  const servDown = document.getElementById('serv-down');
  const servUp = document.getElementById('serv-up');
  const factMakes = document.getElementById('fact-makes');
  const factBatch = document.getElementById('fact-batch');
  const segBtns = [...document.querySelectorAll('.seg [data-view]')];

  // Per-serving grams of a macro coming from one group's ingredients.
  const groupMacro = (g, macro = g) => ings.reduce((sum, ing, i) =>
    groupOf[i] === g ? sum + MM.ingredientMacros(ing, qtyOf(i))[macro] : sum, 0) / state.servings;

  Object.keys(GROUPS).forEach(g => {
    const names = ings.filter((_, i) => groupOf[i] === g).map(ing => ing.name.replace(/\s*\(.*?\)\s*/g, ' ').trim());
    const el = document.getElementById(`twi-${g}`);
    el.textContent = names.length ? `Changes: ${names.join(', ')}` : 'No ingredients are mostly ' + GROUPS[g].label.toLowerCase();
    if (!names.length) document.querySelector(`.tweak[data-group="${g}"]`).classList.add('is-empty');
  });
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
    servOut.textContent = state.servings;
    servDown.disabled = state.servings <= 1;
    servUp.disabled = state.servings >= MAX_SERVINGS;
    factMakes.textContent = state.servings;
    if (factBatch) factBatch.textContent = `£${(recipe.price * state.servings).toFixed(2)}`;
    segBtns.forEach(b => b.setAttribute('aria-selected', String(b.dataset.view === state.view)));

    ings.forEach((ing, i) => {
      if (ing.fixed) return;
      const slider = document.getElementById(`s${i}`);
      const q = qtyOf(i);
      slider.max = Math.max(ing.qty * 3 * Math.max(1, state.whole) * servingFactor() * Math.max(1, groupFactor(i)), q);
      slider.value = q;
      document.getElementById(`q${i}`).innerHTML = fmtQty(ing, q) +
        (Math.abs(q - ing.qty) > 1e-6 ? ` <s>${fmtQty(ing, ing.qty)}</s>` : '');
      const m = MM.ingredientMacros(ing, q);
      document.getElementById(`m${i}`).textContent =
        `${MM.round(m.kcal)} kcal · ${MM.round(m.protein)}P · ${MM.round(m.carbs)}C · ${MM.round(m.fat)}F`;
    });

    const m = perServing();
    Object.keys(GROUPS).forEach(g => {
      document.getElementById(`tw-${g}`).textContent = `${MM.round(m[g])}g`;
      const tw = document.querySelector(`.tweak[data-group="${g}"]`);
      tw.querySelector('[data-tweak="-1"]').disabled = tw.classList.contains('is-empty') || groupMacro(g) < 0.5;
      tw.querySelector('[data-tweak="1"]').disabled = tw.classList.contains('is-empty') || state.group[g] >= 4;
    });
    const perChanged = MM.MACROS.some(k => Math.round(m[k]) !== Math.round(original[k]));
    methodNote.hidden = !perChanged && state.servings === servings;

    // The batch view compares against the book's whole batch, so making more servings shows up here.
    const batch = state.view === 'batch';
    const shown = batch ? scale(m, state.servings) : m;
    const base = batch ? scale(original, servings) : original;
    const changed = MM.MACROS.some(k => Math.round(shown[k]) !== Math.round(base[k]));
    const caption = batch
      ? `Whole batch · ${state.servings} serving${state.servings === 1 ? '' : 's'}`
      : 'Per serving';

    summary.innerHTML = `
      <p class="view-caption">${caption}</p>
      <div class="big-kcal"><strong>${MM.round(shown.kcal)}</strong> kcal ${fmtDelta(shown.kcal, base.kcal, '')}</div>
      <div class="macro-grid">
        <div class="mg p"><span>Protein</span><strong>${MM.round(shown.protein)}g</strong>${fmtDelta(shown.protein, base.protein, 'g')}</div>
        <div class="mg c"><span>Carbs</span><strong>${MM.round(shown.carbs)}g</strong>${fmtDelta(shown.carbs, base.carbs, 'g')}</div>
        <div class="mg f"><span>Fat</span><strong>${MM.round(shown.fat)}g</strong>${fmtDelta(shown.fat, base.fat, 'g')}</div>
      </div>
      ${MM.splitBarHtml(shown)}
      <p class="split-legend">${(() => { const s = MM.split(shown); return `${Math.round(s.protein)}% protein · ${Math.round(s.carbs)}% carbs · ${Math.round(s.fat)}% fat`; })()}</p>
      ${changed ? `<p class="orig">Book ${batch ? `batch (makes ${servings})` : 'original'}: ${MM.round(base.kcal)} kcal · ${MM.round(base.protein)}P · ${MM.round(base.carbs)}C · ${MM.round(base.fat)}F</p>` : ''}`;

    mobileBar.innerHTML = `
      <div><strong>${MM.round(shown.kcal)}</strong><span>${batch ? 'batch kcal' : 'kcal'}</span></div>
      <div class="p"><strong>${MM.round(shown.protein)}g</strong><span>protein</span></div>
      <div class="c"><strong>${MM.round(shown.carbs)}g</strong><span>carbs</span></div>
      <div class="f"><strong>${MM.round(shown.fat)}g</strong><span>fat</span></div>`;

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
    state.ratio[i] = +e.target.value / (ings[i].qty * state.whole * servingFactor() * groupFactor(i) || 1);
    render();
  });

  whole.addEventListener('input', () => { state.whole = +whole.value; render(); });

  const setServings = n => {
    state.servings = Math.min(MAX_SERVINGS, Math.max(1, n));
    render();
  };
  servDown.addEventListener('click', () => setServings(state.servings - 1));
  servUp.addEventListener('click', () => setServings(state.servings + 1));

  segBtns.forEach(b => b.addEventListener('click', () => { state.view = b.dataset.view; render(); }));

  // Step a macro by a fixed number of grams per serving by scaling its ingredient group.
  document.querySelector('.tweaks').addEventListener('click', e => {
    const btn = e.target.closest('[data-tweak]');
    if (!btn || btn.disabled) return;
    const g = btn.closest('.tweak').dataset.group;
    const now = groupMacro(g);
    if (now <= 0) return;
    const want = Math.max(0, now + GROUPS[g].step * +btn.dataset.tweak);
    state.group[g] = Math.min(4, state.group[g] * (want / now));
    render();
  });

  document.getElementById('reset').addEventListener('click', () => {
    state.ratio = ings.map(() => 1);
    state.whole = 1;
    state.servings = servings;
    state.group = { protein: 1, carbs: 1, fat: 1 };
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
    const current = perServing()[k];
    if (current > 0) {
      state.whole = Math.min(3, Math.max(0.25, state.whole * (target / current)));
      render();
    }
  }));

  render();
})();
