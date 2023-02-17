.DEFAULT: help

help:
	@echo "make help"
	@echo "    display this help statement"
	@echo "make run-hours"
	@echo "    run the application in location hours mode in devel"
	@echo "make run-closure-alerts"
	@echo "    run the application in location closure alerts mode in devel"
	@echo "make test"
	@echo "    run associated test suite with pytest"
	@echo "make lint"
	@echo "    lint project files using the flake8 linter"

run-hours:
	export ENVIRONMENT=location_hours_devel; \
	python3 main.py

run-closure-alerts:
	export ENVIRONMENT=location_closure_alerts_devel; \
	python3 main.py

test:
	pytest

lint:
	flake8 --exclude *env