# Nashville Property Standards Violations - a Machine Readable data brief

Of the 568 property standards cases in Nashville's layer whose reported problem is recorded with the exact string "host - no strp", 419 (73.8 percent) sit on parcels that have no short-term rental permit record of any status in Metro's STR permits file, and 38 (6.7 percent) sit on parcels with a currently issued STR permit. Cases received October 26, 2023 to October 29, 2026; both layers pulled November 1, 2026.

Part of Machine Readable: https://adowlen.github.io/machine-readable/

Repository: https://github.com/adowlen/nashville-property-standards-data-brief

## Contents

- brief-draft.md - the brief (publishable text)
- stats.json - every figure used in the brief, produced by code/build_stats.py
- verification.md - Section 10 pre-flight audit record and methods checklist (AUDIT PASSED)
- verification-ledger-independent.md - the independent verifier's recomputation ledger
- reviewer-notes.md - claims most likely challenged, checks not completed, flags
- sources.md - dataset citations and the per-figure source audit
- social-drafts.md - LinkedIn draft (held for a future Friday synthesis under the Friday-only rule; Machine Readable never posts to X)
- hero-headline.txt - the headline figure and story description for the hero illustration
- hero.png - hero graphic (generated illustration in hero_source/hero-art.webp, headline figure composited by code/hero_composite.py over a left-side gradient scrim; viewed during QA in the morning run: narrative Nashville street scene with an inspector and a suitcase on a lit porch, headline fully legible on the scrimmed dark field)
- charts/ - chart_cases_by_subtype.png, chart_str_fusion_by_population.png, chart_districts_two_scopes.png, chart_open_share_by_year.png
- data/ - property_standards_raw.csv.gz and str_permits_raw.csv.gz (full pulls, gzipped; gunzip to obtain the CSVs), district_panel.csv, subtype_panel.csv, str_fusion_panel.csv, reported_problem_counter.csv.gz, violations_noted_counter.csv.gz, pull_log.json, audit_output.txt, verify_independent_output.json
- code/ - pull_data.py, build_stats.py, audit_section10.py, verify_independent.py, charts.py, hero_composite.py

## Dependencies (match code imports)

Python standard library (csv, gzip, json, re, collections, datetime, zoneinfo, pathlib, sys); matplotlib; pandas; Pillow; requests.

## Reuse and citation

Licensed CC-BY-4.0 (see LICENSE). Cite as: Machine Readable, "Nashville property standards: 73.8 percent of unpermitted-STR complaints sit on parcels with no STR permit record at all" (2026), https://github.com/adowlen/nashville-property-standards-data-brief
