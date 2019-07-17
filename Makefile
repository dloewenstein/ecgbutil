libfiles    := $(wildcard lib/*)
release_lib := $(patsubst lib/%,release/lib/%, $(libfiles))

all: release/ecgbutil.exe rlib icon
rlib: $(release_lib)
icon: release/ecgbutil.ico

release/ecgbutil.exe: main.py
	pyinstaller --distpath ./release --clean --onefile --name ecgbutil $<

release/lib/%: lib/% release/lib
	cp $< $@

release/ecgbutil.ico: ecgbutil.ico
	cp $< $@

release/lib:
	mkdir -p $@

.PHONY: rlib icon
