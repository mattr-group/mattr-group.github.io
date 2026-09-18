# Setup, and one thing that goes wrong

This folder is a complete GitHub Pages site. Two of its files have names
beginning with a dot:

```
.github/workflows/update-publications.yml
.nojekyll
```

**GitHub's drag-and-drop upload in the browser silently skips those.** Files
and folders whose names start with a dot never reach the file picker, so an
upload that looks successful leaves the site without its weekly publications
job. If you have already uploaded this way, check whether the repository shows
a `.github` folder. If it does not, use one of the two routes below.

## Route 1, push with git (keeps everything)

```bash
cd mattr-site
git init -b main
git add -A
git commit -m "MATTR group site"
git remote add origin https://github.com/<owner>/<owner>.github.io.git
git push -u origin main
```

If the repository already has commits in it:

```bash
git fetch origin
git reset --soft origin/main
git add -A
git commit -m "Add workflow and .nojekyll"
git push -u origin main
```

## Route 2, create the two files in the browser

In the repository, **Add file, Create new file**. Type the full path into the
filename box; typing `/` creates the folders as you go.

1. Path `.github/workflows/update-publications.yml`, contents copied from the
   file of that name in this folder.
2. Path `.nojekyll`, contents empty. Commit it as it is.

## Then

1. Settings, Pages, Source: Deploy from a branch, `main`, `/ (root)`.
2. Settings, Actions, General, Workflow permissions: **Read and write**.
   Without this the publications job runs and then fails to push, quietly.
3. Actions tab, Update publications, Run workflow. This is the one step nobody
   has tested against the live ORCID and Crossref APIs yet, so watch it once.

Everything else, including how the group edits the member list, is in
`README.md`.
