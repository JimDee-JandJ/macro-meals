(async () => {
  const grid = document.getElementById('grid');
  const count = document.getElementById('count');
  const search = document.getElementById('search');
  const sortSel = document.getElementById('sort');
  const mealChips = document.getElementById('meal-chips');
  const ingredientChips = document.getElementById('ingredient-chips');
  const bookSel = document.getElementById('book');
  const bookWrap = document.getElementById('book-wrap');
  const minProtein = document.getElementById('min-protein');
  const maxKcal = document.getElementById('max-kcal');
  const minProteinOut = document.getElementById('min-protein-out');
  const maxKcalOut = document.getElementById('max-kcal-out');
  const clearBtn = document.getElementById('clear');
  const vegOnly = document.getElementById('veg-only');

  let recipes;
  try {
    recipes = await MM.loadRecipes();
  } catch (e) {
    grid.innerHTML = '<p class="empty">Recipes could not be loaded. If you opened this file directly, run it through a local web server or GitHub Pages.</p>';
    return;
  }
  recipes.forEach(r => { r._m = MM.recipeMacros(r); });

  const MEAL_ORDER = ['Breakfast', 'Mains', 'Meal prep', 'Snacks'];
  const uniq = key => [...new Set(recipes.map(r => r[key]).filter(Boolean))];
  const meals = uniq('meal').sort((a, b) => {
    const ia = MEAL_ORDER.indexOf(a), ib = MEAL_ORDER.indexOf(b);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib) || a.localeCompare(b);
  });
  const ingredients = uniq('mainIngredient').sort();
  const books = uniq('book').sort();

  const state = { meal: 'All', ingredient: 'All' };

  function renderChips(el, values, key) {
    el.innerHTML = ['All', ...values].map(v =>
      `<button type="button" class="chip" aria-pressed="${state[key] === v}" data-value="${MM.esc(v)}">${MM.esc(v)}</button>`
    ).join('');
    el.onclick = e => {
      const btn = e.target.closest('.chip');
      if (!btn) return;
      state[key] = btn.dataset.value;
      renderChips(el, values, key);
      render();
    };
  }
  renderChips(mealChips, meals, 'meal');
  renderChips(ingredientChips, ingredients, 'ingredient');

  if (books.length > 1) {
    bookSel.innerHTML = '<option value="All">All books</option>' +
      books.map(b => `<option>${MM.esc(b)}</option>`).join('');
  } else {
    bookWrap.hidden = true;
  }

  const maxKcalInData = Math.ceil(Math.max(...recipes.map(r => r._m.kcal)) / 50) * 50;
  maxKcal.max = Math.max(maxKcalInData, 400);
  maxKcal.value = maxKcal.max;

  function tile(r) {
    const m = r._m;
    const meta = [
      r.price != null && `£${r.price.toFixed(2)} per serving`,
      r.servings > 1 && `Makes ${r.servings}`
    ].filter(Boolean).join(' · ');
    return `<a class="card" href="recipe.html?id=${encodeURIComponent(r.id)}">
      <div class="card-img">${MM.imageHtml(r)}<span class="badge">${MM.esc(r.meal)}</span>${r.vegetarian ? `<span class="badge veg" title="${r.vegetarian === 'VG' ? 'Vegan' : 'Vegetarian'}">${MM.esc(r.vegetarian)}</span>` : ''}</div>
      <div class="card-body">
        <h3>${MM.esc(r.title)}</h3>
        <p class="meta">${MM.esc(meta)}</p>
        <div class="macros">
          <div class="macro kcal"><strong>${MM.round(m.kcal)}</strong><span>kcal</span></div>
          <div class="macro p"><strong>${MM.round(m.protein)}g</strong><span>protein</span></div>
          <div class="macro c"><strong>${MM.round(m.carbs)}g</strong><span>carbs</span></div>
          <div class="macro f"><strong>${MM.round(m.fat)}g</strong><span>fat</span></div>
        </div>
        ${MM.splitBarHtml(m)}
        <p class="per">Per serving</p>
      </div>
    </a>`;
  }

  function render() {
    const q = search.value.trim().toLowerCase();
    const book = bookSel.value || 'All';
    const minP = +minProtein.value;
    const maxK = +maxKcal.value;
    minProteinOut.textContent = minP ? `${minP}g+` : 'Any';
    maxKcalOut.textContent = maxK >= +maxKcal.max ? 'Any' : `${maxK} kcal`;

    let list = recipes.filter(r =>
      (state.meal === 'All' || r.meal === state.meal) &&
      (state.ingredient === 'All' || r.mainIngredient === state.ingredient) &&
      (book === 'All' || r.book === book) &&
      (!vegOnly.checked || r.vegetarian) &&
      r._m.protein >= minP &&
      (maxK >= +maxKcal.max || r._m.kcal <= maxK) &&
      (!q || r.title.toLowerCase().includes(q) ||
        r.ingredients.some(i => i.name.toLowerCase().includes(q)))
    );

    const sorters = {
      title: (a, b) => a.title.localeCompare(b.title),
      'protein-desc': (a, b) => b._m.protein - a._m.protein,
      'kcal-asc': (a, b) => a._m.kcal - b._m.kcal,
      'kcal-desc': (a, b) => b._m.kcal - a._m.kcal,
      'price-asc': (a, b) => (a.price ?? 99) - (b.price ?? 99),
      ratio: (a, b) => (b._m.protein / b._m.kcal) - (a._m.protein / a._m.kcal)
    };
    list.sort(sorters[sortSel.value] || sorters.title);

    count.textContent = `${list.length} recipe${list.length === 1 ? '' : 's'}`;
    grid.innerHTML = list.length ? list.map(tile).join('') : '<p class="empty">No recipes match those filters.</p>';
  }

  [search, sortSel, bookSel, minProtein, maxKcal, vegOnly].forEach(el => el.addEventListener('input', render));
  clearBtn.addEventListener('click', () => {
    search.value = '';
    bookSel.value = 'All';
    vegOnly.checked = false;
    minProtein.value = 0;
    maxKcal.value = maxKcal.max;
    state.meal = 'All';
    state.ingredient = 'All';
    renderChips(mealChips, meals, 'meal');
    renderChips(ingredientChips, ingredients, 'ingredient');
    render();
  });

  render();
})();
