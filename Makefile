clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

test: clean ## Run the tests.
	@pytest --cov=src --cov-report=term-missing --cov-fail-under 95
	@echo -e "The tests pass! ✨ 🍰 ✨"

lint: ## Run the code linter.
	@poetry run pylint custom_twitter_feed --reports=n

check: test lint mypy

style:
	black .
	flake8
	isort .
