# Build targets for On Top (the Google Fonts project template's, for this repository).
# build.py writes sources/OnTop-Regular.ufo from the Python geometry and builds fonts/ from it with
# gftools builder (sources/config.yaml).

help:
	@echo "  make build:  draws the glyphs, writes the UFO and builds the fonts into fonts/"
	@echo "  make test:   tests the fonts with fontspector (googlefonts profile)"
	@echo "  make check:  checks the approved glyphs, the outlines and the fit to the logo"

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || python3 -m venv venv
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

build: venv
	. venv/bin/activate; python build.py

test: build
	which fontspector || (echo "fontspector not found. Install it with 'cargo binstall fontspector'." && exit 1)
	mkdir -p out/fontspector
	fontspector --profile googlefonts -l warn --full-lists --succinct --html out/fontspector/fontspector-report.html --ghmarkdown out/fontspector/fontspector-report.md fonts/ttf/OnTop-Regular.ttf || echo "fontspector reported problems: see out/fontspector/"

check: build
	. venv/bin/activate; python tools/lint_outlines.py fonts/ttf/OnTop-Regular.ttf
	. venv/bin/activate; python tools/fit_report.py fonts/ttf/OnTop-Regular.ttf reference/on-top.png

clean:
	rm -rf venv
	find . -name "*.pyc" -delete

.PHONY: help venv build test check clean
