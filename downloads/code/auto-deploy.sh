#!/bin/bash
path_html=		# set your vimwiki html path
cd $path_html
git checkout gh-pages
git add *.html
git commit -m"syn at `date`"
git push origin gh-pages
