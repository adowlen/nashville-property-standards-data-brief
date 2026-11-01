# Source audit: Nashville property standards brief (2026-11-01)

Every figure in brief-draft.md, traced to its derivation. Counts were
produced by code/build_stats.py and are stored in stats.json; the
independent recomputation is in verification-ledger-independent.md.

## The datasets

1. Property standards cases (primary)
- Name: Property Standards Violations (service title: Property Standards Requests), Metro Nashville open data, owner NashvilleOpenData
- ArcGIS Hub item: 038de0cf3d35435c8c563b731265c036, discovered 2026-11-01 via the ArcGIS portal search API and the Nashville Hub (datanashvillegov-nashville.hub.arcgis.com)
- Endpoint used: https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Property_Standards_Violations_2/FeatureServer/0
- Pull: 2026-11-01, paginated query ordered by ObjectId, 43,283 records; server count confirmed with returnCountOnly before download and equal to the local count. Service data last edit 2026-11-01 (editingInfo timestamp in data/pull_log.json).
- Saved copy: data/property_standards_raw.csv.gz (all 20 fields)
- Fields relied on: Date_Received, Property_APN, Property_Address, Property_Owner (distinct count only), Complaint_Source, Reported_Problem, Status, Cncl_Dist, Last_Activity_Date, Last_Act__Result, Violations_Noted, ZIP, Subtype_Description, Request_Nbr, ObjectId

2. STR permits (fusion layer)
- Name: Residential Short Term Rental Permits (Metro Nashville open data), the same ArcGIS view used for the 2026-10-14 STR permits brief (package: hidden_files/str-permits-brief-2026-10-14/, whose sources.md identifies the dataset and whose local copy is dated 2026-10-13)
- Endpoint used: https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Residential_Short_Term_Rental_Permits_view/FeatureServer/0
- Pull: fresh, 2026-11-01, paginated by ObjectId, 17,634 records (17,612 in the 2026-10-13 pull); server count equal to local count. The 8 applicant and contact phone columns were dropped at pull time and never used, as in the 2026-10-14 package.
- Saved copy: data/str_permits_raw.csv.gz
- Fields relied on: Parcel, Permit_Status, Address (control join only)

3. Decision hook (verified from primary sources, 2026-11-01)
- Metro Council special meeting, Thursday, November 5, 2026, 6:30 PM: Nashville.gov news release dated October 2, 2026, "Metro Council to Meet Thursday, November 5 Due to November 3 Election", https://www.nashville.gov/departments/council/news/metro-council-meet-thursday-november-5-due-november-3-election (Metropolitan Council Office): Vice Mayor Angie E. Henderson called a special meeting of the Metro Council for Thursday, November 5, 2026 at 6:30 PM because the November 3, 2026 general election falls on the regular meeting date; associated committee meetings are held November 4-5, 2026. The brief asserts no STR or property-standards item on that meeting's agenda.
- Property Standards and Appeals Board meeting, Wednesday, November 4, 2026, 3:00 PM, Metro Office Building: as listed on the Nashville.gov event list, checked 2026-11-01. The board's function, per its Nashville.gov board page (https://www.nashville.gov/departments/codes/boards/property-standards-and-appeals-board): it hears and acts upon appeals of orders issued by the department as it administers the requirements of the Property Standards Code, and can uphold, overturn, modify or extend an order, or place special conditions on its orders. The brief asserts no specific case on the board's November 4 agenda.

4. Official definitions
- Property standards case process and violation categories: Metro Codes Department pages at nashville.gov (Property Standard Code Violation Types; Property Standards Violation Investigation and Resolution Process), read 2026-11-01. Chapter 16.24 of the Metro Code of Ordinances outlines property standards violations in Davidson County. Used for context in the Who can act section only; no figure derives from these pages.
- STRP terminology: the layer's own strings (Subtype_Description "Short Term Rental Property", Violations_Noted "STRP PERMIT REQUIRED") are printed verbatim; STRP is the permit program's own abbreviation as recorded in both files.

## Figure-by-figure audit

1. **43,283 cases; window October 26, 2023 to October 29, 2026**
   Server count = downloaded rows = 43,283. Date_Received (epoch ms, converted to America/Chicago) min and max; all values midnight local (date-only). Yearly counts 1,936 / 13,807 / 13,936 / 13,604 sum to 43,283. stats.json: totals, window, cases_by_year.

2. **Status DONE 40,245 (93.0 percent), OPEN 2,988 (6.9 percent), CLOSED 50 (0.1 percent)**
   Status value counts over all 43,283 cases; no null Status values. Shares on the full population. stats.json: status.

3. **28,863 distinct parcels; 29,031 distinct normalized addresses; 43,281 distinct request numbers**
   Distinct counts of Property_APN (as recorded; alphanumeric-normalized count is identical), normalized Property_Address (uppercase, punctuation to space, whitespace collapsed), and Request_Nbr. stats.json: totals.

4. **Case types: Housing Request 27,495 (63.5 percent), High Grass and Weeds 8,075 (18.7 percent), PS Audit 3,824 (8.8 percent), STR 1,491 (3.4 percent), CA Codes Case 999, Sign Request 692**
   Subtype_Description value counts (18 values, full counter in data/audit_output.txt). stats.json: subtypes.

5. **Complaint sources: HUB 16,462 (38.0 percent), INSPECTOR REPORTED 16,100 (37.2 percent), PHONE 4,217 (9.7 percent), Audit 3,800 (8.8 percent), EMAIL 1,872 (4.3 percent)**
   Complaint_Source value counts (18 values, full counter in the audit output). stats.json: complaint_sources.

6. **Violations noted: HIGH WEEDS 8,564; OPEN STORAGE, JUNK, TRASH, DEBRIS 6,154; PARKING ON GRASS 5,639; STRP PERMIT REQUIRED exact 1,146, containing 1,157**
   Violations_Noted exact-string counts and one contains count (case-insensitive substring "STRP PERMIT REQUIRED"). Violations_Noted is null on 62 cases. A case can carry a combined string, so exact-string counts are case counts per string, not shares. stats.json: violations_noted. Full counter: data/violations_noted_counter.csv.gz.

7. **Reported_Problem: 21,721 distinct values, 86 null; top exact strings JUNK TRASH DEBRIS 3,432, PARKING ON GRASS 2,676, HIGH GRASS/WEEDS 1,712, PROBLEM REPORTED 1,009, "host - no strp" 568**
   Exact-string counts only. Full counter: data/reported_problem_counter.csv.gz. stats.json: reported_problem.

8. **ZIP: 37013 7,226 (16.7 percent), 37211 6,267 (14.5 percent), 37115 3,260, 37207 3,091; not determined 7**
   ZIP value counts; shares on the full 43,283 population (nullable-denominator rule). ZIP null on 2 cases and sentinel 0 on 5. District: 29 with 2,571 (5.9 percent), 11 with 2,427, 16 with 2,382; district null on 2. stats.json: geography.

9. **Repeat addresses: 8,201 addresses with 2 or more cases; 22,453 cases (51.9 percent) at repeat addresses; 332 addresses with 6 or more cases holding 2,541 cases; max 39**
   Group by normalized address (item 3 method). Repeat parcels (APN): 8,253 parcels with 2 or more cases holding 22,673 cases. No address, parcel, or owner is named in the brief (standards section 12.1). stats.json: repeat_addresses.

10. **Open share by received year: 2023 1.7 percent (33 of 1,936), 2024 1.5 percent (209 of 13,807), 2025 2.6 percent (366 of 13,936), 2026 17.5 percent (2,380 of 13,604)**
    Status at pull time grouped by received year. Reported as a snapshot pattern; no duration field is used. stats.json: open_by_year, open_share_by_year_pct, status_by_year.

11. **STR case type: 1,491 cases; EMAIL source 1,463 (98.1 percent); DONE 1,382 (92.7 percent), OPEN 109; STRP PERMIT REQUIRED recorded on 1,156 (77.5 percent); by year 77 / 551 / 519 / 344; monthly range 3 (2026-05) to 102 (2026-07)**
    Filter Subtype_Description == "Short Term Rental Property" (exact string from the full counter). stats.json: str_enforcement.

12. **STR geography: districts 21 (191), 17 (184), 5 (132); ZIPs 37207 (179), 37208 (173), 37209 (143), 37203 (128)**
    Cncl_Dist and ZIP value counts within the item 11 filter. stats.json: str_enforcement.subtype_district_top, subtype_zip_top.

13. **"host - no strp" exact 568; normalized variants 586; all 568 EMAIL, all STR case type, all Violations_Noted exactly STRP PERMIT REQUIRED; DONE 522 (91.9 percent), OPEN 46; 540 distinct parcels; 25 parcels with 2 or more holding 53 cases; Violation Resolved 518**
    Exact string equality on Reported_Problem. The variant total (586) counts values equal after lowercasing and removing all spaces; the 18 near-miss rows are listed in the audit output and excluded from the 568. The October 29 sampled count of 572 does not reproduce in the November 1 full pull; the exact full-pull count is 568 and is the figure used. stats.json: reported_problem, str_enforcement.host_no_strp; audit polarity section.

14. **STR permits file: 17,634 records; ISSUED 7,010; distinct parcels ever 10,742; ISSUED parcels 5,466; expired-not-issued parcels 4,417**
    Permit_Status value counts and distinct normalized Parcel counts from the fresh pull. Status counter: EXPIRED 8,053; ISSUED 7,010; CANCELLED 2,277; REVOKED 164; DENIED-D 40; PENDING 37; EXPIREEXT 29; HOLD 18; REFUNDED 3; VOID 2; OK TO PAY 1. stats.json: str_permits_pull.

15. **Fusion classes (derived, parcel join)**
    Join: case Property_APN = permit Parcel, alphanumeric-normalized; APN present on 100 percent of rows in both files; both files use 11-character standard and 14-character condo formats. Parcel classes per case parcel: issued (parcel in the ISSUED parcel set), expired_not_issued, other_status_only, no_str_record. Results: all cases 714 / 868 / 199 / 41,502; STR cases 466 / 288 / 104 / 633; host cases 38 / 79 / 32 / 419. Shares: host no-record 419 of 568 = 73.8 percent (headline); STR issued 466 of 1,491 = 31.3 percent; all-cases issued 714 of 43,283 = 1.6 percent. Distinct case parcels matching any permit parcel: 1,378 of 28,863 (4.8 percent). Method label: derived. Limit: permit status as of the November 1, 2026 pull, not as of each case's received date; printed in the brief's definitions and Finding 8. stats.json: fusion; panel: data/str_fusion_panel.csv.

16. **Controls (derived)**
    Same join on non-STR case types: Codes High Grass and Weeds on issued parcels 41 of 8,075 (0.51 percent); Codes Housing Request 182 of 27,495 (0.66 percent); Codes Sign Request 2 of 692 (0.29 percent, small group, flagged). Address control: normalized-address match to any permit address 1,637 cases; parcel-or-address union 1,802; both keys 1,616 (89.7 percent of the union). stats.json: fusion.controls, fusion.address_control; audit section 10.2.
