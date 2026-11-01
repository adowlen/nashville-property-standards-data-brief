"""Data-drawn charts for the Nashville property standards brief.
Brand palette: dark charcoal, amber, teal. Every chart prints its
population and measure on the graphic itself (framing standard).
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
stats = json.loads((ROOT / "stats.json").read_text())
CH = ROOT / "charts"
CH.mkdir(exist_ok=True)
CHARCOAL = "#23272b"; AMBER = "#f5a800"; TEAL = "#2a9d8f"; LIGHT = "#e8e4da"; GREY = "#8a8f98"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": CHARCOAL,
                     "axes.edgecolor": CHARCOAL, "axes.labelcolor": CHARCOAL,
                     "xtick.color": CHARCOAL, "ytick.color": CHARCOAL})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(CH / name, dpi=200, facecolor="white")
    plt.close(fig)
    print(name)


# 1. Cases by subtype (top 8)
subs = stats["subtypes"][:8][::-1]
fig, ax = plt.subplots(figsize=(9, 4.8))
ax.barh([s["subtype"] for s in subs], [s["cases"] for s in subs],
        color=[AMBER if s["subtype"] == "Short Term Rental Property" else TEAL for s in subs])
for i, s in enumerate(subs):
    ax.text(s["cases"] + 500, i, f"{s['cases']:,} ({s['pct_of_all_cases']}%)", va="center", fontsize=9)
ax.set_xlim(0, 31000)
ax.set_xlabel("Cases received Oct 26, 2023 to Oct 29, 2026")
ax.set_title("Nashville property standards cases by case type\n(Subtype_Description) - population: all 43,283 cases as pulled Nov 1, 2026\nShares of cases, not of properties",
             fontsize=11, loc="left")
ax.spines[["top", "right"]].set_visible(False)
save(fig, "chart_cases_by_subtype.png")

# 2. Fusion: permit-record class by population
pops = [("All property standards cases\n(n = 43,283 cases)", stats["fusion"]["all_cases"]),
        ("STR case type\n(n = 1,491 cases)", stats["fusion"]["str_subtype_cases"]),
        ("'host - no strp' complaints\n(n = 568 cases, exact string)", stats["fusion"]["host_no_strp_cases"])]
keys = [("no_str_record", "No STR permit record on the parcel", CHARCOAL),
        ("expired_not_issued", "Permit record, expired only", GREY),
        ("other_status_only", "Permit record, other status only", LIGHT),
        ("issued", "Currently issued STR permit (ISSUED)", AMBER)]
fig, ax = plt.subplots(figsize=(9, 4.6))
labels = [p[0] for p in pops]
left = [0.0] * len(pops)
for key, lab, col in keys:
    vals = [p[1][key] / p[1]["cases"] * 100 for p in pops]
    ax.barh(labels, vals, left=left, color=col, label=lab)
    for i, (v, p) in enumerate(zip(vals, pops)):
        if v >= 5:
            ax.text(left[i] + v / 2, i, f"{v:.1f}%", ha="center", va="center", fontsize=9,
                    color="white" if col in (CHARCOAL, GREY) else CHARCOAL)
    left = [l + v for l, v in zip(left, vals)]
ax.set_xlim(0, 100)
ax.set_xlabel("Share of cases in each population, by the STR permit record on the case parcel (APN join)")
ax.set_title("Cases fused to the STR permits layer on parcel (APN)\nPermit status as recorded in the permits file pulled Nov 1, 2026\nCase shares, three separate populations",
             fontsize=11, loc="left")
ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "chart_str_fusion_by_population.png")

# 3. Cases by district: overall vs STR case type (two labeled scopes, grouped)
dist_all = {d["district"]: d["cases"] for d in stats["geography"]["district_top"]}
str_top = stats["str_enforcement"]["subtype_district_top"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [1.4, 1]})
items = sorted(dist_all.items(), key=lambda kv: kv[1])[::-1]
a1.barh([f"District {k}" for k, _ in items][::-1], [v for _, v in items][::-1], color=TEAL)
a1.set_title("All cases: top council districts\n(n = 43,283 cases)", fontsize=10, loc="left")
a1.set_xlabel("Cases")
items2 = sorted(str_top, key=lambda x: x["cases"])
a2.barh([f"District {x['district']}" for x in items2], [x["cases"] for x in items2], color=AMBER)
a2.set_title("STR case type only: top districts\n(n = 1,491 cases)", fontsize=10, loc="left")
a2.set_xlabel("Cases")
for ax in (a1, a2):
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Case counts by council district - two different populations, shown separately\nCounts are cases received Oct 26, 2023 to Oct 29, 2026; no per-housing-unit rate is shown (no district housing denominator in the sources)",
             fontsize=10)
save(fig, "chart_districts_two_scopes.png")

# 4. Status by received year
years = ["2023", "2024", "2025", "2026"]
open_pct = [stats["open_share_by_year_pct"][y] for y in years]
counts = [stats["cases_by_year"][y] for y in years]
fig, ax = plt.subplots(figsize=(8.5, 4.2))
bars = ax.bar(years, open_pct, color=AMBER)
for b, v, c in zip(bars, open_pct, counts):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v}% open\n(n = {c:,} cases)", ha="center", fontsize=9)
ax.set_ylim(0, 21)
ax.set_ylabel("Share OPEN at Nov 1, 2026 pull (%)")
ax.set_xlabel("Year the case was received (2023 starts Oct 26; 2026 runs through Oct 29)")
ax.set_title("Open share rises for recent cases - a snapshot pattern, not a resolution rate\nPopulation: all 43,283 cases, grouped by received year; Status as recorded at pull time",
             fontsize=11, loc="left")
ax.spines[["top", "right"]].set_visible(False)
save(fig, "chart_open_share_by_year.png")
print("charts done")
