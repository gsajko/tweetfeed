clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

test: clean ## Run the tests.
	@python -m pytest --cov tweetfeed -v --cov-report html --disable-warnings
	@echo "The tests pass! ✨ 🍰 ✨"

lint: ## Run the code linter.
	@pylint --fail-under=9.0 app tweetfeed --reports=n
	@echo "The lint pass! ✨ 🍰 ✨"

mypy:
	@mypy tweetfeed app


style:
	black .
	flake8
	isort .

great-expectations:
	@great_expectations checkpoint run tweets
	@great_expectations checkpoint run preds
	@echo "The great_expectations pass! ✨ 🍰 ✨"

# DVC
dvc:
	dvc add data/dataset.json
	dvc add data/predictions.csv
	dvc add data/seen.csv
	dvc push

check: great-expectations test lint style mypy
bare_check: test lint style # if no prediction data is available

# check: test lint style mypy data