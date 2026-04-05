.PHONY: build build-js build-py clean serve deploy fmt lint

build: build-js build-py

build-js:
	npm install
	npm run build

build-py:
	uv run python build.py

clean:
	rm -rf output static/dist

serve: build-py
	npx vite

deploy: build
	rsync -av output/ fmor.in:/data/fmor.in/htdocs

test:
	uv run --extra dev pytest

fmt:
	uvx ruff format .
	uvx ruff check --fix .
	npm run fmt

lint:
	uvx ruff check .
	npm run lint
