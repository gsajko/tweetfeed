clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

test: clean ## Run the tests.
	@pytest --cov tweetfeed --cov-report=term-missing --cov-fail-under 95
	# @pytest --cov tweetfeed --cov app --cov-report=term-missing --cov-fail-under 95
	@echo "The tests pass! ✨ 🍰 ✨"

lint: ## Run the code linter.
	@poetry run pylint --fail-under=9.5 app tweetfeed --reports=n
	@echo "The lint pass! ✨ 🍰 ✨"

mypy:
	@poetry run mypy tweetfeed app


style:
	black .
	flake8 --exclude=notebooks/*
	isort .

great-expectations:
	@poetry run great_expectations checkpoint run tweets
	@echo "The great_expectations pass! ✨ 🍰 ✨"

check: great-expectations test lint style 
# check: test lint style mypy data