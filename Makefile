.PHONY: html serve clean publish

html:
	pelican content -s pelicanconf.py -o output

serve:
	pelican content -s pelicanconf.py -o output -l

clean:
	rm -rf output

publish:
	pelican content -s publishconf.py -o output

preview:
	make clean && make html && make serve
