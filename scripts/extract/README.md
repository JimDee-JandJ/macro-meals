# Book extraction

These scripts turn the Dave Fell PDFs (kept in the private `marcro-meals-books` repo, never here) into the
book files in `scripts/books/` and the photos in `assets/img/`.

```
pip install pymupdf pillow numpy
python3 extract.py drafts.json      # read recipe pages by text position
python3 convert.py drafts.json parsed.json   # parse quantities, match ingredients to nutrition.py
python3 emit.py parsed.json         # write scripts/books/*.py (manual fixes live in emit.py)
python3 images.py                   # extract and crop each recipe photo
python3 ../build_recipes.py         # build assets/data/recipes.json
```

`extract.py` and `images.py` expect the PDFs at `/home/user/marcro-meals-books/`; change `SRC` if they live elsewhere.
`build_recipes.py` prints a "check" line when a recipe's ingredient estimate is far from the book's totals, which
usually means an ingredient was misread.
