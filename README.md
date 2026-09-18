# MATTR group site

**Setting it up for the first time? Read `SETUP.md` first.** Two files in this
folder have names starting with a dot, and browser uploads drop them.


A single static page for the MATTR group (Dr Pete Lally, Department of
Bioengineering, Imperial College London). No build step, no framework, no
server. `index.html` loads its content from the files in `data/`, or from a
Google Sheet if you point it at one.

```
index.html                     the page
data/people.json               members, if you are not using a sheet
data/people-sheet-template.csv column layout for the Google Sheet route
data/publications.json         rebuilt weekly from ORCID
data/themes.json               the five research threads
photos/                        member photographs
scripts/update_publications.py the ORCID and Crossref fetcher
.github/workflows/             the weekly job that runs it
```

## 1. Put it online

1. Create a repository, for example `mattr-group/mattr-group.github.io`, and
   commit these files at the top level.
2. Settings, Pages, Source: Deploy from a branch, `main`, `/ (root)`.
3. The site appears at `https://<owner>.github.io/<repo>/` within a minute or
   two. An Imperial subdomain can be pointed at it later with a CNAME.

To check it locally first, run `python3 -m http.server` in this folder and
open `http://localhost:8000`. Opening `index.html` by double-clicking will
not load the JSON files, because browsers block file reads from `file://`;
the page falls back to a built-in stub, which is expected.

## 2. Let the group edit the member list

Two options. Pick one.

### Option A, Google Sheet, nobody needs GitHub

1. Import `data/people-sheet-template.csv` into a new Google Sheet.
2. File, Share, Publish to web. Choose the sheet, format
   **Comma-separated values (.csv)**, publish, copy the link.
3. Paste that link into `CONFIG.peopleSheetCSV` near the top of the script in
   `index.html`, and commit.
4. Share the sheet with the group with edit rights.

Anyone who edits the sheet changes the site. Google caches the published CSV
for a few minutes, so an edit shows up on the next load rather than instantly.

Columns:

| column  | what goes in it |
|---------|-----------------|
| `order` | sort position, 10, 20, 30, leaves gaps for inserts |
| `role`  | `pi`, `phd`, `postdoc`, `msc`, `alumni`. Drives the filter buttons |
| `name`  | as it should appear |
| `title` | position line, for example `PhD student, since 2024` |
| `about` | two or three sentences on the work |
| `photo` | file name in `photos/`, or a full URL. Empty gives a generated pattern |
| `links` | `Label \| address`, several separated by `;` |
| `flag`  | `yes` marks the entry as needing a check |

Anything with a comma in it needs quoting, which the Sheet handles for you.

### Option B, edit `data/people.json`

Same fields as the sheet, one object per person. Fine if everyone is
comfortable opening a pull request, and it keeps the history in one place.
Leave `CONFIG.peopleSheetCSV` empty to use this route.

## 3. Publications update themselves

`scripts/update_publications.py` reads Pete's public ORCID record for the list
of works and their DOIs, then asks Crossref for the title, authors, journal,
volume and pages of each. It writes `data/publications.json` and the workflow
commits the file only when something actually changed.

The workflow runs every Monday, and on demand from the Actions tab. Run it by
hand once after the first push to confirm it works:

```bash
python3 scripts/update_publications.py
```

Notes:

- No API keys. Both services are public. The script identifies itself with
  `CONTACT_EMAIL`, which is what Crossref asks automated callers to do.
- Works with no DOI, conference abstracts mostly, keep whatever ORCID holds
  and appear without an author list.
- Datasets, preprint records and anything Crossref types outside
  `KEEP_TYPES` are skipped. Widen that set if preprints should show.
- The list is only as complete as the ORCID record. Anything missing there is
  missing here, which is a good reason to keep ORCID tidy.
- To track more than one person's output, run the script once per ORCID and
  merge, or switch the source to a group Zotero library.

## 4. Things still open

- No photographs yet.
- The Join us section has no current openings in it.

## Note on repository naming

GitHub gives one user or organisation site per account, served from a
repository named exactly `<owner>.github.io`, plus unlimited project sites
served from any other repository at `<owner>.github.io/<repo>/`.

All paths in `index.html` are relative, so the page works unchanged either
way. No base URL to configure.

Two settings to check after the first push:

- Settings, Pages, Source: Deploy from a branch, `main`, `/ (root)`.
- Settings, Actions, General, Workflow permissions: **Read and write**.
  Without it the weekly publications job runs but cannot push its commit.

`.nojekyll` is included so Pages serves the files as they are instead of
running them through Jekyll.
