.PHONY: html serve clean publish deploy

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

deploy: publish
	ghp-import -n -p -f output

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

.PHONY: deploy

deploy: publish
	ghp-import -n -p -f output

	ghp-import -n -p -f output

	git add .
	echo "Deploying to gh-pages"
	# Switch to gh-pages branch, create if doesn't exist
	git branch -f gh-pages origin/gh-pages || git checkout --orphan gh-pages
	git checkout gh-pages
	# Clear the branch
	git rm -rf . || true
	# Move the generated files to root
	cp -r output/* .
	# Add all the files from output
	git add .
	git commit -m "Site update via Pelican" || echo "No changes to commit"
	git push origin gh-pages
	# Go back to the main branch
	git checkout main || git checkout master
	make publish
