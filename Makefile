PYTHON ?= python3

.PHONY: build test validate check data charts
build:
	$(PYTHON) scripts/build.py
test:
	$(PYTHON) -m unittest discover -s tests -v
	node tests/test_chart_viewport.js
	node tests/test_chart_options.js
validate:
	$(PYTHON) scripts/validate_snapshot.py
check: test validate build
data:
	$(PYTHON) scripts/update_data.py
charts:
	$(PYTHON) scripts/render_daily.py
