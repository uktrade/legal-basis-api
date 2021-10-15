.PHONY: build
build:
	docker-build

.PHONY: deploy
deploy:
	cf push

.PHONY: docker-build
docker-build:
	docker-compose build

.PHONY: test
test: docker-build
	DJANGO_ENV=test docker-compose run --rm web pytest /code

.PHONY: lint-migrations
lint-migrations: docker-build
	docker-compose run --rm web /code/manage.py lintmigrations --exclude-apps axes sites

.PHONY: check-flake8
check-flake8:
	flake8 --exclude venv .

.PHONY: lint-types
lint-types:
	mypy server tests/**/*.py

.PHONY: lint-dotenv
lint-dotenv: docker-build
	docker-compose run --rm web dotenv-linter /code/config/.env /code/config/sample.env

.PHONY: lint-pip
lint-pip:
	pip check

.PHONY: lint-code-quality
lint-code-quality:
	xenon --max-absolute A --max-modules A --max-average A server -e **/adobe.py

.PHONY: lint
lint:
	lint-migrations flake8 lint-types lint-dotenv lint-pip lint-code-quality
