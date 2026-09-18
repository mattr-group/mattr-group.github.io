#!/usr/bin/env python3
"""Rebuild data/publications.json from a public ORCID record.

ORCID gives the list of works and their DOIs. Crossref is then asked for the
full metadata, because ORCID summaries usually carry no author list.

No API keys and no dependencies beyond the standard library. Both APIs ask
that automated callers identify themselves, which is what CONTACT_EMAIL does.

    python3 scripts/update_publications.py
    python3 scripts/update_publications.py --orcid 0000-0003-0075-0103
"""

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ORCID_ID = "0000-0003-0075-0103"          # Pete Lally
CONTACT_EMAIL = "p.lally@imperial.ac.uk"  # sent to Crossref as the polite-pool contact
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "publications.json"

KEEP_TYPES = {"journal-article", "proceedings-article", "posted-content", "book-chapter"}
MAX_AUTHORS = 12          # longer lists are truncated with "et al."
REQUEST_PAUSE = 0.2       # seconds between Crossref calls


def fetch_json(url, accept="application/json", tries=3):
    req = urllib.request.Request(url, headers={
        "Accept": accept,
        "User-Agent": f"MATTR-site/1.0 (mailto:{CONTACT_EMAIL})",
    })
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == tries - 1:
                raise
        except urllib.error.URLError:
            if attempt == tries - 1:
                raise
        time.sleep(2 ** attempt)
    return None


def orcid_works(orcid_id):
    """Return [{'doi': str|None, 'title': str, 'year': int|None, 'venue': str}]."""
    data = fetch_json(f"https://pub.orcid.org/v3.0/{orcid_id}/works")
    out = []
    for group in (data or {}).get("group", []):
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        s = summaries[0]
        doi = None
        for ident in (group.get("external-ids") or {}).get("external-id", []):
            if (ident.get("external-id-type") or "").lower() == "doi":
                doi = (ident.get("external-id-value") or "").strip().lower()
                break
        title = (((s.get("title") or {}).get("title") or {}).get("value") or "").strip()
        year = None
        pub = s.get("publication-date") or {}
        if pub.get("year", {}).get("value"):
            try:
                year = int(pub["year"]["value"])
            except (TypeError, ValueError):
                year = None
        venue = ((s.get("journal-title") or {}).get("value") or "").strip()
        if title:
            out.append({"doi": doi, "title": title, "year": year, "venue": venue})
    return out


def crossref(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    data = fetch_json(url)
    return (data or {}).get("message")


def authors_from(msg):
    names = []
    for a in msg.get("author") or []:
        family = (a.get("family") or "").strip()
        given = (a.get("given") or "").strip()
        if family and given:
            initials = "".join(p[0] for p in given.replace("-", " ").split() if p)
            names.append(f"{family} {initials}")
        elif family:
            names.append(family)
        elif a.get("name"):
            names.append(a["name"].strip())
    if len(names) > MAX_AUTHORS:
        names = names[:MAX_AUTHORS] + ["et al."]
    return ", ".join(names)


def year_from(msg):
    for key in ("published-print", "published-online", "issued", "created"):
        parts = (msg.get(key) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            return int(parts[0][0])
    return None


def detail_from(msg):
    vol = (msg.get("volume") or "").strip()
    page = (msg.get("page") or "").strip().replace("-", "\u2013")
    if vol and page:
        return f"{vol}:{page}"
    return vol or page or ""


def build(orcid_id):
    works = orcid_works(orcid_id)
    if not works:
        raise SystemExit(f"No works returned for ORCID {orcid_id}. Nothing written.")

    entries, seen = [], set()
    for w in works:
        doi = w["doi"]
        if doi and doi in seen:
            continue

        entry = None
        if doi:
            time.sleep(REQUEST_PAUSE)
            try:
                msg = crossref(doi)
            except Exception as exc:                      # keep going on one bad DOI
                print(f"  crossref failed for {doi}: {exc}", file=sys.stderr)
                msg = None
            if msg:
                if msg.get("type") and msg["type"] not in KEEP_TYPES:
                    continue
                title = " ".join((msg.get("title") or [w["title"]])[0].split())
                venue = " ".join(((msg.get("container-title") or [w["venue"]]) or [""])[0].split())
                entry = {
                    "year": year_from(msg) or w["year"],
                    "title": title,
                    "authors": authors_from(msg),
                    "venue": venue,
                    "detail": detail_from(msg),
                    "doi": doi,
                }

        if entry is None:                                  # no DOI, or Crossref had nothing
            entry = {
                "year": w["year"],
                "title": w["title"],
                "authors": "",
                "venue": w["venue"],
                "detail": "",
            }
            if doi:
                entry["doi"] = doi

        if not entry.get("year") or not entry.get("title"):
            continue
        if doi:
            seen.add(doi)
        entries.append(entry)

    entries.sort(key=lambda e: (-e["year"], e["title"].lower()))
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orcid", default=os.environ.get("ORCID_ID", ORCID_ID))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    entries = build(args.orcid)
    out = pathlib.Path(args.out)
    new = json.dumps(entries, indent=2, ensure_ascii=False) + "\n"
    old = out.read_text(encoding="utf-8") if out.exists() else ""
    if new == old:
        print(f"{len(entries)} publications, unchanged.")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(new, encoding="utf-8")
    print(f"{len(entries)} publications written to {out}.")


if __name__ == "__main__":
    main()
