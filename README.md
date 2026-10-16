# font-coverage-plan

Parse real standalone SFNT cmap format4/12 mappings, report per-font corpus gaps and choose a deterministic greedy fallback order with code-point evidence.

For: Localization engineers checking a text corpus against locally available OpenType/TrueType fonts before packaging a fallback set. A font family name does not prove nominal coverage for a corpus, and coverage union can conceal missing code points or inconsistent cmap choice.

## Quickstart

Python 3.10 or newer. No runtime packages or network requests. The initial wheel build needs setuptools from the normal Python package registry.

```sh
git clone https://github.com/nripankadas07/font-coverage-plan.git
cd font-coverage-plan
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/font-coverage-plan --make-example example-work
.venv/bin/font-coverage-plan --corpus example-work/corpus.txt example-work/latin.ttf example-work/accent.ttf
```

The structural synthetic example covers four unique code points ABé🙂 using Latin then accent. The files demonstrate cmap analysis and cannot be rendered as complete fonts.

Windows: use `.venv\Scripts\python.exe` and `.venv\Scripts\font-coverage-plan.exe` instead. Windows is documented but has not been executed in this release's Linux CI.

## Input and result contract

UTF-8 corpus <=2 MiB with 1..4096 distinct counted code points, plus 1..16 distinct font paths. Standalone TTF/OTF SFNT only, <=32 MiB each; cmap/maxp required, <=256 SFNT tables, <=64 encoding records, <=8192 format4 segments or100000 format12 groups. Choose one preferred Unicode encoding in order (3,10),(0,6),(0,4),(3,1),(0,3),(0,2),(0,1),(0,0); preferred unsupported formats fail rather than silently substituting a different encoding. Glyph0 means missing; queried glyph indices must fit maxp.numGlyphs. Control/format and line/paragraph separator categories are ignored; ordinary spaces count. No normalization. Greedy selection maximizes remaining unique code points, breaking ties by input order.

Output is JSON on stdout. Exit 0 means complete/no findings; exit 1 means a valid report with missing coverage, prices, capacity, or capture findings, where applicable. SQLite extraction has no exit-1 state. Exit 2 means invalid input or an I/O failure, with an error on stderr and no partial report. `--help` describes command options. Inputs stay local; review output before sharing it.

## Limits

Nominal cmap mapping only. No shaping, ligature/variation-selector handling, glyph appearance/outline validation, font licensing advice, optimal set-cover claim, WOFF/WOFF2/TTC support or font modification. A mapped glyph may still render poorly or be blank. Synthetic example files contain only structural cmap/maxp data, no outlines; they are not renderable fonts. Real-font mapping checks against FontTools cover only two installed fonts and stated code points.

## Verify

```sh
python3 -m unittest -v test_behavior
python3 -m compileall -q .
python3 -m pip wheel --no-deps --wheel-dir dist .
python3 -m venv /tmp/font-coverage-plan-check
/tmp/font-coverage-plan-check/bin/python -m pip install --no-deps dist/*.whl
python3 verify_installed.py /tmp/font-coverage-plan-check/bin/python
```

The installed-command check runs outside the checkout. See [validation](VALIDATION.md), [research and tradeoffs](RESEARCH.md), [contributing](CONTRIBUTING.md), [support](SUPPORT.md) and [security](SECURITY.md).

Original implementation and synthetic fixtures, developed with AI assistance and reviewed through executable checks. MIT license. No customer/adoption claims, copied competitor implementation, or performance-superiority claim.
