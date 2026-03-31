.PHONY: build build-js build-py clean serve deploy fmt

build: build-js build-py

build-js:
	npm run build

build-py:
	uv run python build.py

clean:
	rm -rf output static/dist

serve: build
	cd output && uvx python -m http.server 8000

deploy: build
	rsync -av output/ fmor.in:/data/fmor.in/htdocs

fmt:
	uvx ruff format .
	uvx ruff check --fix .
	npx prettier --write "templates/**/*.html" "src/**/*.{ts,vue}"
