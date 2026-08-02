.PHONY: build-macos run screenshots

build-macos:
	PYTHON_BIN="$(CURDIR)/.venv/bin/python" ./build_macos.sh

run:
	.venv/bin/python src/cv_builder/main.py

screenshots:
	.venv/bin/python tools/capture_ui_screens.py
