.PHONY: build clean serve

build:
	uv run python build.py

clean:
	rm -rf output

serve: build
	cd output && uv run python -m http.server 8000

deploy: clean build
	rsync -av output/ fmor.in:/data/fmor.in
