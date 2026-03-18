.PHONY: html serve clean publish deploy preview

html:
	pelican content -s pelicanconf.py -o output

serve:
	pelican content -s pelicanconf.py -o output -l

clean:
	rm -rf output

publish:
	pelican content -s publishconf.py -o output
	cp -r static output/
	pelican content -s publishconf.py -o output
	cp -r static/images output/ && cp -r static/* output/static/

preview:
	make clean && make html && make serve

deploy: publish
	ghp-import -n -p -f output
