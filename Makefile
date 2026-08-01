.PHONY: build-macos

build-macos:
	PYTHON_BIN=$(CURDIR)/.venv/bin/python ./build_macos.sh
