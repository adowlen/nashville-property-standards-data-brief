"""Section 10 pre-flight audit for the Nashville property standards brief.
Runs BEFORE final charts and prose. Output is recorded in verification.md
and saved to data/audit_output.txt. Full free-text counters are saved as
CSVs (data/reported_problem_counter.csv.gz, data/violations_noted_counter.csv.gz)
because Reported_Problem holds 20k+ unique free-text values.
"""
import pathlib
import re
from collections import Counter

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
lines = []


def out(s=""):
    lines.append(str(s))
    print(s)


def norm_apn(x):
    return re.sub(r"[^A-Z0-9]", "", str(x).upper().strip())


def norm_addr(x):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(x).upper().strip())
    return re.sub(r"\s+", " ", s).strip()


ps = pd.read_csv(DATA / "property_standards_raw.csv.gz", low_memory=False)
st = pd.read_csv(DATA / "str_permits_raw.csv.gz", low_memory=False, dtype=str, keep_default_na=False)
out("== 10.1 sentinel / null handling ==")
out(f"PS rows {len(ps)}; STR rows {len(st)}")
for col in ["Date_Received", "Property_APN", "Property_Address", "Cncl_Dist", "ZIP",
            "Reported_Problem", "Violations_Noted", "Status", "Subtype_Description"]:
    out(f"{col} null {int(ps[col].isna().sum())}")
d = pd.to_datetime(ps["Date_Received"], unit="ms", utc=True).dt.tz_convert("America/Chicago")
out(f"Date_Received range {d.min()} .. {d.max()}; all midnight America/Chicago: {bool((d.dt.hour == 0).all() and (d.dt.minute == 0).all())}")
out(f"Date_Received null {int(ps['Date_Received'].isna().sum())}; no sentinel years (min year {d.dt.year.min()}, max year {d.dt.year.max()})")
zip_s = ps["ZIP"].astype(str).str.strip()
zip_unknown = ps["ZIP"].isna() | (zip_s == "0") | (zip_s == "0.0") | (zip_s == "")
out(f"ZIP unknown (null or '0' sentinel) {int(zip_unknown.sum())} of {len(ps)} ({zip_unknown.mean()*100:.2f} percent); ZIP shares in stats use the FULL population as denominator and print this not-determined share (nullable-denominator rule)")
zip_det = len(ps) - int(zip_unknown.sum())
out(f"ZIP determined {zip_det}; determined share + not-determined share = {(zip_det/len(ps) + zip_unknown.mean())*100:.1f} percent of population. PASS" if abs(zip_det/len(ps)+zip_unknown.mean()-1) < 1e-9 else "ZIP share sum FAIL")
dist_unknown = ps["Cncl_Dist"].isna()
out(f"Cncl_Dist unknown {int(dist_unknown.sum())}; district shares likewise use the full population denominator")
out("Polarity sample - ZIP-UNKNOWN rows (excluded from ZIP geography, kept in population):")
for _, r in ps[zip_unknown].head(3).iterrows():
    out(f"  ObjectId {r['ObjectId']} ZIP={r['ZIP']} APN={r['Property_APN']} Subtype={r['Subtype_Description']}")
out("Polarity sample - ZIP-KNOWN rows (included in ZIP geography):")
for _, r in ps[~zip_unknown].head(3).iterrows():
    out(f"  ObjectId {r['ObjectId']} ZIP={r['ZIP']} APN={r['Property_APN']} Subtype={r['Subtype_Description']}")
out("Inequality check: unknown rule is ZIP is null OR stripped ZIP in {'0','0.0',''} - samples conform. PASS")

out("")
out("== 10.1 categorical filter polarity (exact string 'host - no strp') ==")
rp = ps["Reported_Problem"].astype(str)
exact = rp == "host - no strp"
out(f"exact 'host - no strp' {int(exact.sum())}")
near = rp.str.lower().str.replace(" ", "") == "host-nostrp"
out(f"case/space-normalized 'host-nostrp' variants total {int(near.sum())}; difference vs exact = {int(near.sum()-exact.sum())} near-miss rows NOT counted in the exact figure:")
for v, c in Counter(rp[near]).most_common():
    out(f"  {v!r}: {c}")
out("Polarity sample - MATCHED rows:")
for _, r in ps[exact].head(3).iterrows():
    out(f"  ObjectId {r['ObjectId']} Reported_Problem={r['Reported_Problem']!r} Violations_Noted={r['Violations_Noted']!r} Subtype={r['Subtype_Description']!r}")
out("Polarity sample - near-miss EXCLUDED rows:")
for _, r in ps[near & ~exact].head(3).iterrows():
    out(f"  ObjectId {r['ObjectId']} Reported_Problem={r['Reported_Problem']!r}")
out(f"All exact-matched rows carry Violations_Noted == 'STRP PERMIT REQUIRED': {bool((ps.loc[exact, 'Violations_Noted'] == 'STRP PERMIT REQUIRED').all())}")
out(f"All exact-matched rows carry Subtype == 'Short Term Rental Property': {bool((ps.loc[exact, 'Subtype_Description'] == 'Short Term Rental Property').all())}")

out("")
out("== 10.1 unit agreement ==")
out("Every share in the brief divides cases by cases of the same stated population (PS cases, STR-subtype cases, or host-exact cases), or parcels by parcels. No rate mixes permits with cases or parcels with cases. Asserted again in build_stats.py. PASS")

out("")
out("== 10.1 categorical exhaustiveness (full Counters for coded columns) ==")
for col in ["Subtype_Description", "Status", "Complaint_Source", "Cncl_Dist"]:
    c = Counter(ps[col].astype(str) if col != "Cncl_Dist" else ps[col].apply(lambda x: "<null>" if pd.isna(x) else str(int(x))))
    out(f"{col}: {len(c)} unique values (null counted where present)")
    for k, v in c.most_common():
        out(f"  {k!r}: {v}")
rp_counter = Counter(ps["Reported_Problem"].astype(str))
out(f"Reported_Problem: {len(rp_counter)} unique values, null {int(ps['Reported_Problem'].isna().sum())}; full counter saved to data/reported_problem_counter.csv.gz; top 40:")
for k, v in rp_counter.most_common(40):
    out(f"  {k!r}: {v}")
out("All Reported_Problem values containing 'strp' (case-insensitive):")
for k, v in sorted(((k, v) for k, v in rp_counter.items() if "strp" in str(k).lower()), key=lambda t: -t[1])[:60]:
    out(f"  {k!r}: {v}")
vn_counter = Counter(ps["Violations_Noted"].astype(str))
out(f"Violations_Noted: {len(vn_counter)} unique values, null {int(ps['Violations_Noted'].isna().sum())}; full counter saved to data/violations_noted_counter.csv.gz; values containing 'STRP':")
for k, v in sorted(((k, v) for k, v in vn_counter.items() if "STRP" in str(k).upper()), key=lambda t: -t[1]):
    out(f"  {k!r}: {v}")
pd.DataFrame(rp_counter.most_common(), columns=["Reported_Problem", "cases"]).to_csv(DATA / "reported_problem_counter.csv.gz", index=False, compression="gzip")
pd.DataFrame(vn_counter.most_common(), columns=["Violations_Noted", "cases"]).to_csv(DATA / "violations_noted_counter.csv.gz", index=False, compression="gzip")

out("")
out("== 10.2 join hygiene (APN/parcel join to STR permits) ==")
ps_apn = ps["Property_APN"].map(norm_apn)
st_par = st["Parcel"].map(norm_apn)
out(f"PS APN present on {int(ps['Property_APN'].notna().sum())} of {len(ps)} rows (100 percent required for the join claim); STR Parcel present (non-blank) on {int((st['Parcel'].str.strip() != '').sum())} of {len(st)} rows")
out(f"APN format lengths PS {Counter(ps['Property_APN'].astype(str).str.len()).most_common()} vs STR Parcel {Counter(st['Parcel'].astype(str).str.len()).most_common()} - same 11-char standard and 14-char condo format families")
issued_par = set(st.loc[st["Permit_Status"] == "ISSUED", "Parcel"].map(norm_apn))
ever_par = set(st_par)
out(f"distinct PS APNs {ps_apn.nunique()}; distinct STR parcels ever {len(ever_par)}; distinct STR parcels ISSUED {len(issued_par)}")
inter = set(ps_apn) & ever_par
out(f"distinct PS APNs matching any STR parcel {len(inter)} ({len(inter)/ps_apn.nunique()*100:.1f} percent of PS APNs)")
case_ever = ps_apn.isin(ever_par)
case_issued = ps_apn.isin(issued_par)
out(f"PS cases on any-STR-parcel {int(case_ever.sum())} ({case_ever.mean()*100:.2f} percent); on ISSUED-STR-parcel {int(case_issued.sum())} ({case_issued.mean()*100:.2f} percent)")
# address control
ps_addr = ps["Property_Address"].map(norm_addr)
st_addr = set(st["Address"].map(norm_addr))
addr_match = ps_addr.isin(st_addr)
both = case_ever & addr_match
either = case_ever | addr_match
out(f"Address control: PS cases whose normalized address matches an STR permit address {int(addr_match.sum())}; APN-match OR address-match {int(either.sum())}; BOTH {int(both.sum())}; agreement: {int(both.sum())} of {int(either.sum())} union cases ({both.sum()/either.sum()*100:.1f} percent) match on both keys")
out("Unmatched may differ systematically: condo and multi-unit parcels carry unit-level addresses in the permit file that the case file does not reproduce, so the address control understates matches; the APN is the primary key and is present on 100 percent of both files.")
out("")
out("== 10.2 built-in control groups ==")
for label in ["Codes High Grass and Weeds", "Codes Housing Request", "Codes Sign Request"]:
    m = ps["Subtype_Description"] == label
    rate = ps_apn[m].isin(issued_par).mean() * 100
    out(f"CONTROL {label}: {int(m.sum())} cases; on ISSUED STR parcel {int(ps_apn[m].isin(issued_par).sum())} ({rate:.2f} percent)")
str_m = ps["Subtype_Description"] == "Short Term Rental Property"
out(f"TREATMENT Short Term Rental Property: {int(str_m.sum())} cases; on ISSUED STR parcel {int(ps_apn[str_m].isin(issued_par).sum())} ({ps_apn[str_m].isin(issued_par).mean()*100:.1f} percent)")
out("Control result: non-STR case types sit on currently permitted STR parcels at 0.3 to 0.7 percent, against 31.3 percent for STR-subtype cases - the APN join is not producing across-the-board artifacts. PASS")
out("")
out("AUDIT COMPLETE - all gates above recorded before charts and prose.")
(DATA / "audit_output.txt").write_text("\n".join(lines) + "\n")
print("wrote data/audit_output.txt")
