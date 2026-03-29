.PHONY: build clean serve fmt

build:
	uv run python build.py

clean:
	rm -rf output

serve: build
	cd output && uvx python -m http.server 8000

deploy: build
	rsync -av output/ fmor.in:/data/fmor.in/htdocs

fmt:
	uvx ruff format .
	uvx ruff check --fix .
	npx prettier --write "templates/**/*.html" "static/**/*.css" "static/**/*.js"
