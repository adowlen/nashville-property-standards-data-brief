"""Build stats.json and derived CSV panels for the Nashville property
standards brief. All shares use the full stated population as denominator
(nullable-denominator rule); not-determined shares are printed alongside.
"""
import json
import pathlib
import re
from collections import Counter

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def norm_apn(x):
    return re.sub(r"[^A-Z0-9]", "", str(x).upper().strip())


def norm_addr(x):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(x).upper().strip())
    return re.sub(r"\s+", " ", s).strip()


def pct(n, d):
    return round(n / d * 100, 1) if d else None


ps = pd.read_csv(DATA / "property_standards_raw.csv.gz", low_memory=False)
st = pd.read_csv(DATA / "str_permits_raw.csv.gz", low_memory=False, dtype=str, keep_default_na=False)
pull_log = json.loads((DATA / "pull_log.json").read_text())
N = len(ps)
assert N == pull_log["property_standards"]["server_count"] == pull_log["property_standards"]["local_rows"]
assert len(st) == pull_log["str_permits"]["server_count"] == pull_log["str_permits"]["local_rows"]

d = pd.to_datetime(ps["Date_Received"], unit="ms", utc=True).dt.tz_convert("America/Chicago")
ps["year"] = d.dt.year
ps["month"] = d.dt.strftime("%Y-%m")
ps["apn"] = ps["Property_APN"].map(norm_apn)
ps["addr"] = ps["Property_Address"].map(norm_addr)

# STR parcel classes (parcel basis, statuses from the permit file as pulled)
st_par = st["Parcel"].map(norm_apn)
issued_par = set(st.loc[st["Permit_Status"] == "ISSUED", "Parcel"].map(norm_apn))
expired_par = set(st.loc[st["Permit_Status"] == "EXPIRED", "Parcel"].map(norm_apn))
ever_par = set(st_par)
ps["pclass"] = ps["apn"].map(lambda a: "issued" if a in issued_par else
                             "expired_not_issued" if a in (expired_par - issued_par) else
                             "other_status_only" if a in ever_par else "no_str_record")


def class_block(mask):
    sub = ps[mask]
    c = Counter(sub["pclass"])
    return {"cases": int(len(sub)),
            "no_str_record": int(c["no_str_record"]), "no_str_record_pct": pct(c["no_str_record"], len(sub)),
            "issued": int(c["issued"]), "issued_pct": pct(c["issued"], len(sub)),
            "expired_not_issued": int(c["expired_not_issued"]), "expired_not_issued_pct": pct(c["expired_not_issued"], len(sub)),
            "other_status_only": int(c["other_status_only"]), "other_status_only_pct": pct(c["other_status_only"], len(sub))}


host = ps["Reported_Problem"] == "host - no strp"
str_sub = ps["Subtype_Description"] == "Short Term Rental Property"

status_c = Counter(ps["Status"].astype(str))
subtype_c = Counter(ps["Subtype_Description"].astype(str))
source_c = Counter(ps["Complaint_Source"].astype(str))
zip_known = ~(ps["ZIP"].isna() | (ps["ZIP"].astype(str).str.strip().isin(["0", "0.0", ""])))
dist_known = ps["Cncl_Dist"].notna()

addr_counts = ps["addr"].value_counts()
repeat_addrs = addr_counts[addr_counts >= 2]
apn_counts = ps["apn"].value_counts()

stats = {
    "pull_date": "2026-11-01",
    "proposed_repo": "nashville-property-standards-data-brief",
    "decision_hook": {
        "event": "Metro Council special meeting, Thursday, November 5, 2026, 6:30 PM",
        "verification": "VERIFIED from a primary source: Nashville.gov news release dated October 2, 2026, 'Metro Council to Meet Thursday, November 5 Due to November 3 Election' (https://www.nashville.gov/departments/council/news/metro-council-meet-thursday-november-5-due-november-3-election): Vice Mayor Angie E. Henderson called a special meeting of the Metro Council for Thursday, November 5, 2026 at 6:30 PM because the November 3, 2026 general election falls on the regular meeting date; associated committee meetings November 4-5, 2026.",
        "board_meeting": "Property Standards and Appeals Board meeting, Wednesday, November 4, 2026, 3:00 PM, Metro Office Building, as listed on the Nashville.gov event list (checked 2026-11-01). The board's Nashville.gov board page states it hears and acts upon appeals of orders issued by the department as it administers the Property Standards Code.",
        "caveat": "No property-standards or STR item is asserted to be on the November 5 Council meeting agenda in this brief. The November 4 board meeting is directly on-topic by the board's stated function; no specific case on its agenda is asserted.",
    },
    "window": {"date_received_min": str(d.min().date()), "date_received_max": str(d.max().date()),
               "note": "Date_Received is date-only (all values midnight America/Chicago). 2023 is a partial year starting October 26, 2023 and 2026 runs through October 29, 2026."},
    "totals": {
        "cases": N,
        "distinct_apn": int(ps["apn"].nunique()),
        "distinct_addresses_norm": int(ps["addr"].nunique()),
        "distinct_request_nbr": int(ps["Request_Nbr"].nunique()),
        "request_nbr_duplicate_rows": int(N - ps["Request_Nbr"].nunique()),
        "distinct_owners_as_recorded": int(ps["Property_Owner"].nunique(dropna=True)),
    },
    "status": {k: {"cases": int(v), "pct_of_all_cases": pct(v, N)} for k, v in status_c.most_common()},
    "status_by_year": {str(y): {k: int(v) for k, v in Counter(g["Status"]).items()}
                       for y, g in ps.groupby("year")},
    "open_by_year": {str(y): int((g["Status"] == "OPEN").sum()) for y, g in ps.groupby("year")},
    "open_share_by_year_pct": {str(y): pct((g["Status"] == "OPEN").sum(), len(g)) for y, g in ps.groupby("year")},
    "cases_by_year": {str(y): int(v) for y, v in Counter(ps["year"]).items()},
    "subtypes": [{"subtype": k, "cases": int(v), "pct_of_all_cases": pct(v, N)} for k, v in subtype_c.most_common()],
    "complaint_sources": [{"source": k, "cases": int(v), "pct_of_all_cases": pct(v, N)} for k, v in source_c.most_common()],
    "reported_problem": {
        "unique_values": int(ps["Reported_Problem"].nunique(dropna=True)),
        "null_cases": int(ps["Reported_Problem"].isna().sum()),
        "note": "Reported_Problem is free text (intake shorthand and pasted hubNashville text); exact-string counts only are reported, with near-miss variants counted in the audit.",
        "top_exact": [{"value": k, "cases": int(v)} for k, v in Counter(ps["Reported_Problem"].astype(str)).most_common(12)],
        "host_no_strp_exact": int(host.sum()),
        "host_expired_strp_exact": int((ps["Reported_Problem"] == "host - expired strp").sum()),
        "host_family_normalized_variants_total": int((ps["Reported_Problem"].astype(str).str.lower().str.replace(" ", "", regex=False) == "host-nostrp").sum()),
    },
    "violations_noted": {
        "null_cases": int(ps["Violations_Noted"].isna().sum()),
        "strp_permit_required_exact": int((ps["Violations_Noted"] == "STRP PERMIT REQUIRED").sum()),
        "strp_permit_required_containing": int(ps["Violations_Noted"].astype(str).str.contains("STRP PERMIT REQUIRED", case=False).sum()),
        "top_exact": [{"value": k, "cases": int(v)} for k, v in Counter(ps["Violations_Noted"].astype(str)).most_common(8)],
    },
    "geography": {
        "district_top": [{"district": int(k), "cases": int(v), "pct_of_all_cases": pct(v, N)}
                         for k, v in Counter(ps.loc[dist_known, "Cncl_Dist"]).most_common(8)],
        "district_not_determined": int((~dist_known).sum()),
        "zip_top": [{"zip": str(int(k)), "cases": int(v), "pct_of_all_cases": pct(v, N)}
                    for k, v in Counter(ps.loc[zip_known, "ZIP"]).most_common(8)],
        "zip_not_determined": int((~zip_known).sum()),
        "zip_not_determined_note": "ZIP is null on 2 cases and carries the sentinel value 0 on 5 cases; those 7 are unknown and stay in every population denominator.",
    },
    "repeat_addresses": {
        "distinct_addresses_norm": int(len(addr_counts)),
        "addresses_with_1_case": int((addr_counts == 1).sum()),
        "addresses_with_2_cases": int((addr_counts == 2).sum()),
        "addresses_with_3_to_5_cases": int(((addr_counts >= 3) & (addr_counts <= 5)).sum()),
        "addresses_with_6_plus_cases": int((addr_counts >= 6).sum()),
        "repeat_addresses_2_plus": int(len(repeat_addrs)),
        "cases_on_repeat_addresses": int(repeat_addrs.sum()),
        "cases_on_repeat_addresses_pct": pct(int(repeat_addrs.sum()), N),
        "cases_on_6_plus_addresses": int(addr_counts[addr_counts >= 6].sum()),
        "max_cases_one_address": int(addr_counts.max()),
        "distinct_apn_with_2_plus_cases": int((apn_counts >= 2).sum()),
        "cases_on_repeat_apn": int(apn_counts[apn_counts >= 2].sum()),
    },
    "str_permits_pull": {
        "records": int(len(st)),
        "status_counter": dict(Counter(st["Permit_Status"]).most_common()),
        "issued_records": int((st["Permit_Status"] == "ISSUED").sum()),
        "distinct_parcels_ever": int(len(ever_par)),
        "distinct_parcels_issued": int(len(issued_par)),
        "distinct_parcels_expired_not_issued": int(len(expired_par - issued_par)),
        "vintage_note": "Fresh pull 2026-11-01 from the same ArcGIS view used for the 2026-10-14 STR permits brief (17,612 records on 2026-10-13; 17,634 on 2026-11-01). Applicant and contact phone columns were dropped at pull time and never used.",
    },
    "fusion": {
        "join_key": "Property Standards Property_APN = STR permits Parcel, alphanumeric-normalized; both files use the same 11-character standard and 14-character condo parcel formats; APN present on 100 percent of rows in both files",
        "distinct_ps_apn_matching_any_str_parcel": int(len(set(ps["apn"]) & ever_par)),
        "distinct_ps_apn_total": int(ps["apn"].nunique()),
        "all_cases": class_block(ps.index == ps.index),
        "str_subtype_cases": class_block(str_sub),
        "host_no_strp_cases": class_block(host),
        "address_control": {
            "cases_address_match_any_str": int(ps["addr"].isin(set(st["Address"].map(norm_addr))).sum()),
            "cases_apn_or_address_match": int((ps["apn"].isin(ever_par) | ps["addr"].isin(set(st["Address"].map(norm_addr)))).sum()),
            "cases_both_match": int((ps["apn"].isin(ever_par) & ps["addr"].isin(set(st["Address"].map(norm_addr)))).sum()),
        },
        "controls": {label: {"cases": int((ps["Subtype_Description"] == label).sum()),
                             "on_issued_parcel": int(ps.loc[ps["Subtype_Description"] == label, "apn"].isin(issued_par).sum()),
                             "on_issued_parcel_pct": pct(int(ps.loc[ps["Subtype_Description"] == label, "apn"].isin(issued_par).sum()),
                                                         int((ps["Subtype_Description"] == label).sum()))}
                     for label in ["Codes High Grass and Weeds", "Codes Housing Request", "Codes Sign Request"]},
        "layering_admission": "Without the STR permits layer, the brief could not state what share of unpermitted-STR complaints sit on parcels with no permit record at all, or compare STR enforcement geography against the permitted footprint; the layer is retained for that claim.",
    },
    "str_enforcement": {
        "subtype_cases": int(str_sub.sum()),
        "subtype_pct_of_all": pct(int(str_sub.sum()), N),
        "subtype_status": {k: int(v) for k, v in Counter(ps.loc[str_sub, "Status"]).items()},
        "subtype_done_pct": pct(int((ps.loc[str_sub, "Status"] == "DONE").sum()), int(str_sub.sum())),
        "subtype_complaint_source_top": [{"source": k, "cases": int(v)} for k, v in Counter(ps.loc[str_sub, "Complaint_Source"]).most_common(4)],
        "subtype_email_share_pct": pct(int((ps.loc[str_sub, "Complaint_Source"] == "EMAIL").sum()), int(str_sub.sum())),
        "all_cases_email_share_pct": pct(int((ps["Complaint_Source"] == "EMAIL").sum()), N),
        "subtype_by_year": {str(y): int(v) for y, v in Counter(ps.loc[str_sub, "year"]).items()},
        "subtype_district_top": [{"district": int(k), "cases": int(v)} for k, v in Counter(ps.loc[str_sub, "Cncl_Dist"].dropna()).most_common(6)],
        "subtype_zip_top": [{"zip": str(int(k)), "cases": int(v)} for k, v in Counter(ps.loc[str_sub, "ZIP"].dropna()).most_common(6)],
        "subtype_violations_strp_permit_required_containing": int(ps.loc[str_sub, "Violations_Noted"].astype(str).str.contains("STRP PERMIT REQUIRED", case=False).sum()),
        "host_no_strp": {
            "cases": int(host.sum()),
            "distinct_apn": int(ps.loc[host, "apn"].nunique()),
            "parcels_with_2_plus_host_cases": int((ps.loc[host, "apn"].value_counts() >= 2).sum()),
            "cases_on_2_plus_host_parcels": int(ps.loc[host, "apn"].value_counts().loc[lambda s: s >= 2].sum()),
            "status": {k: int(v) for k, v in Counter(ps.loc[host, "Status"]).items()},
            "done_pct": pct(int((ps.loc[host, "Status"] == "DONE").sum()), int(host.sum())),
            "complaint_source_all_email": bool((ps.loc[host, "Complaint_Source"] == "EMAIL").all()),
            "violations_noted_all_strp_permit_required": bool((ps.loc[host, "Violations_Noted"] == "STRP PERMIT REQUIRED").all()),
            "by_year": {str(y): int(v) for y, v in Counter(ps.loc[host, "year"]).items()},
            "last_activity_result_top": [{"result": k, "cases": int(v)} for k, v in Counter(ps.loc[host, "Last_Act__Result"].astype(str)).most_common(4)],
        },
        "monthly_subtype_recent": {k: int(v) for k, v in sorted(Counter(ps.loc[str_sub, "month"]).items())[-14:]},
        "monthly_volatility_note": "Monthly STR-subtype counts swing from 3 (2026-05) to 102 (2026-07) in the last 14 months, consistent with batch intake; no month-to-month trend is claimed.",
    },
}
# unit-agreement asserts: every class block sums to its population
for blk in ["all_cases", "str_subtype_cases", "host_no_strp_cases"]:
    b = stats["fusion"][blk]
    assert b["no_str_record"] + b["issued"] + b["expired_not_issued"] + b["other_status_only"] == b["cases"], blk
assert sum(v["cases"] for v in stats["status"].values()) == N
assert sum(x["cases"] for x in stats["subtypes"]) == N
assert sum(x["cases"] for x in stats["complaint_sources"]) == N
(ROOT / "stats.json").write_text(json.dumps(stats, indent=1))

# derived panels (small CSVs only)
panel_dist = ps.groupby(ps["Cncl_Dist"]).agg(cases=("ObjectId", "size"),
                                              open_cases=("Status", lambda s: int((s == "OPEN").sum())),
                                              str_subtype_cases=("Subtype_Description", lambda s: int((s == "Short Term Rental Property").sum())),
                                              host_no_strp_cases=("Reported_Problem", lambda s: int((s == "host - no strp").sum()))).reset_index()
panel_dist.to_csv(DATA / "district_panel.csv", index=False)
panel_sub = ps.groupby("Subtype_Description").agg(cases=("ObjectId", "size"),
                                                  open_cases=("Status", lambda s: int((s == "OPEN").sum())),
                                                  done_cases=("Status", lambda s: int((s == "DONE").sum()))).reset_index().sort_values("cases", ascending=False)
panel_sub.to_csv(DATA / "subtype_panel.csv", index=False)
fusion_rows = []
for label, mask in [("all_cases", ps.index == ps.index), ("str_subtype", str_sub), ("host_no_strp_exact", host)] + \
                   [(f"control_{lbl}", ps["Subtype_Description"] == lbl) for lbl in ["Codes High Grass and Weeds", "Codes Housing Request"]]:
    b = class_block(mask)
    b["population"] = label
    fusion_rows.append(b)
pd.DataFrame(fusion_rows).to_csv(DATA / "str_fusion_panel.csv", index=False)
print(json.dumps({"cases": N, "host": int(host.sum()), "str_subtype": int(str_sub.sum()),
                  "fusion_all": stats["fusion"]["all_cases"], "fusion_host": stats["fusion"]["host_no_strp_cases"]}, indent=1))
print("wrote stats.json + district_panel.csv + subtype_panel.csv + str_fusion_panel.csv")
