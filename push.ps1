git add .gitignore
git rm -r --cached output/
git add .
git commit -m "Configure Matrix CI for Semesters 1-5"
git remote remove origin
git remote add origin https://github.com/vishnuu-kr/ktu_notes.git
git branch -M main
git push -u origin main --force
