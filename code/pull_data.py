"""Pull the full Nashville Property Standards Violations layer and the
Nashville STR permits layer fresh on 2026-11-01, paginated by ObjectId.
Saves small derived-friendly raw CSVs (full attribute pull for PS;
STR pull drops applicant/contact phone columns, as in the 2026-10-14 package).
"""
import json
import pathlib
import requests
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PS_URL = "https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Property_Standards_Violations_2/FeatureServer/0"
STR_URL = "https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Residential_Short_Term_Rental_Permits_view/FeatureServer/0"
PULL_DATE = "2026-11-01"


def server_count(url):
    r = requests.get(url + "/query", params={"where": "1=1", "returnCountOnly": "true", "f": "json"}, timeout=60)
    r.raise_for_status()
    return r.json()["count"]


def service_meta(url):
    r = requests.get(url, params={"f": "json"}, timeout=60)
    r.raise_for_status()
    j = r.json()
    return {"name": j.get("name"), "editingInfo": j.get("editingInfo"),
            "fields": [f["name"] for f in j.get("fields", [])]}


def pull_all(url, drop_cols=()):
    count = server_count(url)
    rows = []
    offset = 0
    page = 2000
    while True:
        r = requests.get(url + "/query", params={
            "where": "1=1", "outFields": "*", "orderByFields": "ObjectId ASC",
            "resultOffset": offset, "resultRecordCount": page,
            "f": "json", "returnGeometry": "false"}, timeout=120)
        r.raise_for_status()
        feats = r.json().get("features", [])
        if not feats:
            break
        rows.extend(f["attributes"] for f in feats)
        offset += len(feats)
        if len(rows) >= count:
            break
    df = pd.DataFrame(rows)
    for c in drop_cols:
        if c in df.columns:
            df = df.drop(columns=[c])
    assert len(df) == count, f"local {len(df)} != server {count}"
    return df, count


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    log = {"pull_date": PULL_DATE}
    ps, ps_count = pull_all(PS_URL)
    ps.to_csv(DATA / "property_standards_raw.csv.gz", index=False, compression="gzip")
    log["property_standards"] = {"url": PS_URL + "/query", "service": service_meta(PS_URL),
                                  "server_count": ps_count, "local_rows": int(len(ps))}
    phone_cols = [c for c in pd.read_csv(
        pathlib.Path(__file__).resolve().parent.parent.parent / "str-permits-brief-2026-10-14" / "data" / "nashville_str_permits_2026-10-13.csv",
        nrows=0).columns]  # not used for dropping; drop list below is explicit
    drop = ["Applicant_Home_Phone", "Applicant_Mobile_Phone", "Applicant_Work_Phone",
            "Applicant_Work_Phone_Ext", "Contact_Home_Phone", "Contact_Mobile_Phone",
            "Contact_Work_Phone", "Contact_Work_Phone_Ext"]
    strp, str_count = pull_all(STR_URL, drop_cols=drop)
    strp.to_csv(DATA / "str_permits_raw.csv.gz", index=False, compression="gzip")
    log["str_permits"] = {"url": STR_URL + "/query", "service": service_meta(STR_URL),
                          "server_count": str_count, "local_rows": int(len(strp)),
                          "dropped_columns": drop}
    (DATA / "pull_log.json").write_text(json.dumps(log, indent=1))
    print(json.dumps({k: (v.get("server_count"), v.get("local_rows")) if isinstance(v, dict) else v
                      for k, v in log.items()}, indent=1))


if __name__ == "__main__":
    main()
