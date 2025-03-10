.DEFAULT: help

help:
	@echo "make help"
	@echo "    display this help statement"
	@echo "make run-hours"
	@echo "    run the application in location hours mode in devel"
	@echo "make run-closure-alert"
	@echo "    run the application in location closure alert mode in devel"
	@echo "make test"
	@echo "    run associated test suite with pytest"
	@echo "make lint"
	@echo "    lint project files using the flake8 linter"

run-hours:
	export ENVIRONMENT=devel; \
	export MODE=LOCATION_HOURS; \
	python3 main.py

run-closure-alert:
	export ENVIRONMENT=devel; \
	export MODE=LOCATION_CLOSURE_ALERT; \
	python3 main.py

test:
	pytest

lint:
	black ./ --check --exclude="(env/)|(tests/)"