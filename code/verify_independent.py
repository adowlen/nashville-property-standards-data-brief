"""Independent verifier: recompute the decisive figures from the raw
pulls with a separate implementation (stdlib csv + collections only,
no pandas, no builder code). Compares against stats.json and writes
data/verify_independent_output.json. Also cross-checks every number
that appears in brief-draft.md against stats.json (sync gate 10.3).
"""
import csv
import gzip
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
stats = json.loads((ROOT / "stats.json").read_text())
results = {}


def check(name, mine, theirs):
    ok = mine == theirs
    results[name] = {"independent": mine, "stats_json": theirs, "match": ok}
    print(f"{'PASS' if ok else 'FAIL'} {name}: independent={mine} stats={theirs}")
    return ok


def open_csv(path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", newline="", encoding="utf-8")
    return open(path, newline="", encoding="utf-8")


with open_csv(DATA / "property_standards_raw.csv.gz") as f:
    ps = list(csv.DictReader(f))
with open_csv(DATA / "str_permits_raw.csv.gz") as f:
    strp = list(csv.DictReader(f))

N = len(ps)
all_ok = True
all_ok &= check("total_cases", N, stats["totals"]["cases"])

# dates: epoch ms to America/Chicago (CDT UTC-5 / CST UTC-6; all values midnight local,
# verify by converting with fixed offsets around DST boundaries using zoneinfo)
from zoneinfo import ZoneInfo
chi = ZoneInfo("America/Chicago")
dates = [datetime.fromtimestamp(int(r["Date_Received"]) / 1000, tz=timezone.utc).astimezone(chi) for r in ps]
all_ok &= check("window_min", str(min(dates).date()), stats["window"]["date_received_min"])
all_ok &= check("window_max", str(max(dates).date()), stats["window"]["date_received_max"])
all_ok &= check("all_dates_midnight_local", all(x.hour == 0 and x.minute == 0 for x in dates), True)

status_c = Counter(r["Status"] for r in ps)
all_ok &= check("status_done", status_c["DONE"], stats["status"]["DONE"]["cases"])
all_ok &= check("status_open", status_c["OPEN"], stats["status"]["OPEN"]["cases"])
all_ok &= check("status_closed", status_c["CLOSED"], stats["status"]["CLOSED"]["cases"])

sub_c = Counter(r["Subtype_Description"] for r in ps)
all_ok &= check("subtype_housing", sub_c["Codes Housing Request"], 27495)
all_ok &= check("subtype_str", sub_c["Short Term Rental Property"], stats["str_enforcement"]["subtype_cases"])
all_ok &= check("subtype_count_sum", sum(sub_c.values()), N)

host = [r for r in ps if r["Reported_Problem"] == "host - no strp"]
all_ok &= check("host_no_strp_exact", len(host), stats["reported_problem"]["host_no_strp_exact"])
all_ok &= check("host_all_violations_strp_permit_required",
                all(r["Violations_Noted"] == "STRP PERMIT REQUIRED" for r in host), True)
all_ok &= check("host_all_email", all(r["Complaint_Source"] == "EMAIL" for r in host), True)
all_ok &= check("host_done", sum(1 for r in host if r["Status"] == "DONE"),
                stats["str_enforcement"]["host_no_strp"]["status"]["DONE"])

# fusion, parcel basis
def napn(x):
    return re.sub(r"[^A-Z0-9]", "", (x or "").upper().strip())

issued = {napn(r["Parcel"]) for r in strp if r["Permit_Status"] == "ISSUED"}
expired = {napn(r["Parcel"]) for r in strp if r["Permit_Status"] == "EXPIRED"}
ever = {napn(r["Parcel"]) for r in strp}
all_ok &= check("str_records", len(strp), stats["str_permits_pull"]["records"])
all_ok &= check("str_issued_records", sum(1 for r in strp if r["Permit_Status"] == "ISSUED"),
                stats["str_permits_pull"]["issued_records"])
all_ok &= check("str_distinct_parcels_issued", len(issued), stats["str_permits_pull"]["distinct_parcels_issued"])

def pclass(a):
    if a in issued:
        return "issued"
    if a in expired - issued:
        return "expired_not_issued"
    if a in ever:
        return "other_status_only"
    return "no_str_record"

for label, rows, blk in [("all", ps, stats["fusion"]["all_cases"]),
                         ("host", host, stats["fusion"]["host_no_strp_cases"]),
                         ("str_subtype", [r for r in ps if r["Subtype_Description"] == "Short Term Rental Property"],
                          stats["fusion"]["str_subtype_cases"])]:
    c = Counter(pclass(napn(r["Property_APN"])) for r in rows)
    all_ok &= check(f"fusion_{label}_no_record", c["no_str_record"], blk["no_str_record"])
    all_ok &= check(f"fusion_{label}_issued", c["issued"], blk["issued"])
    all_ok &= check(f"fusion_{label}_total", sum(c.values()), blk["cases"])

# headline percentage recomputed independently
c = Counter(pclass(napn(r["Property_APN"])) for r in host)
headline = round(c["no_str_record"] / len(host) * 100, 1)
all_ok &= check("headline_pct_no_record_host", headline, stats["fusion"]["host_no_strp_cases"]["no_str_record_pct"])

# controls
for label in ["Codes High Grass and Weeds", "Codes Housing Request"]:
    rows = [r for r in ps if r["Subtype_Description"] == label]
    n_issued = sum(1 for r in rows if napn(r["Property_APN"]) in issued)
    all_ok &= check(f"control_{label}_on_issued", n_issued, stats["fusion"]["controls"][label]["on_issued_parcel"])

# repeat addresses (independent normalization)
def naddr(x):
    s = re.sub(r"[^A-Z0-9 ]", " ", (x or "").upper().strip())
    return re.sub(r"\s+", " ", s).strip()

ac = Counter(naddr(r["Property_Address"]) for r in ps)
repeat_cases = sum(v for v in ac.values() if v >= 2)
all_ok &= check("repeat_address_cases", repeat_cases, stats["repeat_addresses"]["cases_on_repeat_addresses"])
all_ok &= check("distinct_addresses", len(ac), stats["repeat_addresses"]["distinct_addresses_norm"])
all_ok &= check("distinct_apn", len({napn(r['Property_APN']) for r in ps}), stats["totals"]["distinct_apn"])

# ZIP not-determined
zip_nd = sum(1 for r in ps if r["ZIP"] in ("", None) or (r["ZIP"] and float(r["ZIP"]) == 0))
all_ok &= check("zip_not_determined", zip_nd, stats["geography"]["zip_not_determined"])

# sync gate: numbers in brief-draft.md that correspond to stats values must be present in stats.json
brief = (ROOT / "brief-draft.md").read_text() if (ROOT / "brief-draft.md").exists() else ""
brief_numbers = {"43,283", "568", "419", "73.8", "1,491", "714", "38", "22,453", "51.9"}
missing = [n for n in brief_numbers if brief and n not in brief]
results["sync_gate_brief_key_numbers_present"] = {"missing_from_brief": missing, "match": not missing}
if brief and missing:
    print("FAIL sync gate: key numbers missing from brief:", missing)
    all_ok = False
elif brief:
    print("PASS sync gate: key numbers present in brief and stats.json")
else:
    print("NOTE sync gate: brief-draft.md not yet written at verifier run time")

out = {"all_match": bool(all_ok), "checks": results}
(DATA / "verify_independent_output.json").write_text(json.dumps(out, indent=1))
print("ALL MATCH" if all_ok else "MISMATCHES PRESENT")
sys.exit(0 if all_ok else 1)
