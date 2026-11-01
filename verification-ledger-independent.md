# Independent verification ledger - Nashville property standards brief (2026-11-01)

Verifier: code/verify_independent.py, a separate implementation using
only the Python standard library (csv, gzip, collections, zoneinfo)
reading the two raw pulls directly. It shares no code with
code/build_stats.py (pandas). Run after stats.json was built, and
re-run after brief-draft.md was written for the sync gate.
Full machine output: data/verify_independent_output.json.

## Result: ALL MATCH (33 of 33 figure checks, plus the sync gate)

Reproduced exactly:
- Total cases 43,283; window October 26, 2023 to October 29, 2026; all Date_Received values midnight America/Chicago
- Status: DONE 40,245; OPEN 2,988; CLOSED 50
- Case types: Codes Housing Request 27,495; Short Term Rental Property 1,491; subtype counts sum to 43,283
- "host - no strp" exact string: 568; all 568 record Violations_Noted exactly STRP PERMIT REQUIRED; all 568 arrived by EMAIL; DONE among them 522
- STR permits: 17,634 records; ISSUED 7,010; distinct ISSUED parcels 5,466
- Fusion classes, all three populations (all cases / STR case type / host exact): no-record, issued, and population totals all reproduce, including the headline 419 of 568 (73.8 percent) with no STR permit record
- Controls: Codes High Grass and Weeds on issued parcels 41; Codes Housing Request 182
- Repeat addresses: 22,453 cases at addresses with 2 or more cases; distinct normalized addresses 29,031; distinct APNs 28,863
- ZIP not-determined count 7 (null or sentinel 0)

Corrected figures:
- The tasked sampled count of 572 "host - no strp" records (live sample, October 29, 2026) does not reproduce in the full November 1, 2026 pull: the exact-string count is 568. The brief uses 568 and prints the discrepancy in Finding 7. Case-and-spacing-normalized variants total 586.

Caveated figures (reproduced, with limits printed in the brief):
- All fusion figures use permit status at the November 1, 2026 pull, not as of each case's received date; direction of the timing effect is stated in the brief.
- Open-share-by-year figures are snapshot shares at pull time, not resolution rates.
- District and ZIP figures are case counts and shares of cases only; no exposure denominator exists in the sources.

Sync gate (section 10.3): the verifier asserts the brief's key numbers (43,283; 568; 419; 73.8; 1,491; 714; 38; 22,453; 51.9) are present in brief-draft.md and equal to stats.json values. Result on the final re-run: PASS.
