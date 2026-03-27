.PHONY: build clean serve

build:
	uv run python build.py

clean:
	rm -rf output

serve: build
	cd output && python -m http.server 8000
