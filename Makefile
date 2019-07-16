libfiles    := $(wildcard lib/*)
release_lib := $(patsubst lib/%,release/lib/%, $(libfiles))

all: release/ecgbutil.exe rlib
rlib: $(release_lib)

release/ecgbutil.exe: main.py
	pyinstaller --distpath ./release --clean --onefile --name ecgbutil $<

release/lib/%: lib/% release/lib
	cp $< $@

release/lib:
	mkdir -p $@

.PHONY: rlib
