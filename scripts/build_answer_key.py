"""
Compute the expected answers for the lab test questions from the generated CSV files.

Writes:
    lab-01-semantic-model/expected-values.csv          numbers to check your measures in Lab 1
    lab-02-data-agent/testing/answer-key.csv           test questions with expected answers (instructor, Lab 2)
    lab-02-data-agent/testing/ground_truth.csv         question/expected_answer pairs for the evaluation SDK
    lab-02-data-agent/testing/business-test-sheet.csv  test sheet for the business-user persona (no answers)

Usage:
    python scripts/build_answer_key.py
"""

from __future__ import annotations

import calendar
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def read(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def eur_m(value: float) -> str:
    return f"EUR {value / 1e6:,.1f} M"


def eur_k(value: float) -> str:
    return f"EUR {value / 1e3:,.0f} k"


def write(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path.relative_to(ROOT)} ({len(rows)} rows)")


def main():
    customers = {r["customer_key"]: r for r in read("dim_customer.csv")}
    products = {r["product_key"]: r for r in read("dim_product.csv")}
    sales = read("fact_sales.csv")
    inventory = read("inventory_weekly.csv")
    complaints = read("quality_complaints.csv")

    net_by_year = defaultdict(float)
    gross_by_year, disc_by_year = defaultdict(float), defaultdict(float)
    ta_2025, ta_year = defaultdict(float), defaultdict(float)
    country_2026, channel_disc = defaultdict(float), defaultdict(lambda: [0.0, 0.0])
    de_zentora = defaultdict(float)
    for s in sales:
        c, p = customers[s["customer_key"]], products[s["product_key"]]
        year, ym = s["order_date"][:4], s["order_date"][:7]
        net, gross, disc = float(s["net_sales_eur"]), float(s["gross_sales_eur"]), float(s["discount_eur"])
        net_by_year[year] += net
        gross_by_year[year] += gross
        disc_by_year[year] += disc
        ta_year[(p["therapeutic_area"], year)] += net
        if year == "2025":
            ta_2025[p["therapeutic_area"]] += net
            channel_disc[s["channel"]][0] += disc
            channel_disc[s["channel"]][1] += gross
        if year == "2026":
            country_2026[c["country"]] += net
        if c["country_code"] == "DE" and p["product_name"] == "Zentora 100 mg tablets" and year == "2026":
            de_zentora[ym] += net

    yoy_2025 = net_by_year["2025"] / net_by_year["2024"] - 1
    imm_growth = ta_year[("Immunology", "2025")] / ta_year[("Immunology", "2024")] - 1
    top_ta = max(ta_2025, key=ta_2025.get)
    top3 = sorted(country_2026.items(), key=lambda kv: kv[1], reverse=True)[:3]
    disc_txt = ", ".join(f"{k} {v[0] / v[1]:.1%}" for k, v in sorted(channel_disc.items(), key=lambda kv: kv[1][0] / kv[1][1]))

    is_story = lambda r: r["country_code"] == "DE" and r["product_name"] == "Zentora 100 mg tablets"  # noqa: E731
    apr_complaints = sum(1 for r in complaints if is_story(r) and r["received_date"].startswith("2026-04"))
    stockout_weeks = [r["week_ending_date"] for r in inventory if is_story(r) and r["stock_status"] == "Stock-out"]
    batch_2026 = defaultdict(int)
    for r in complaints:
        if r["received_date"].startswith("2026"):
            batch_2026[r["batch_number"]] += 1
    top_batch = max(batch_2026, key=batch_2026.get)
    story_text = sorted({r["description"] for r in complaints if r["batch_number"] == top_batch})
    monthly_txt = ", ".join(f"{calendar.month_abbr[int(k[5:])]}: {eur_k(v)}" for k, v in sorted(de_zentora.items()))

    write(ROOT / "lab-01-semantic-model" / "expected-values.csv", [
        {"check": "Net Sales, year 2025", "expected": eur_m(net_by_year["2025"]), "exact": f"{net_by_year['2025']:.2f}"},
        {"check": "Net Sales, year 2024", "expected": eur_m(net_by_year["2024"]), "exact": f"{net_by_year['2024']:.2f}"},
        {"check": "Net Sales YoY %, year 2025", "expected": f"{yoy_2025:.1%}", "exact": f"{yoy_2025:.6f}"},
        {"check": "Discount %, year 2025", "expected": f"{disc_by_year['2025'] / gross_by_year['2025']:.1%}",
         "exact": f"{disc_by_year['2025'] / gross_by_year['2025']:.6f}"},
        {"check": "Net Sales, Germany + Zentora 100 mg tablets, May 2026", "expected": eur_k(de_zentora["2026-05"]),
         "exact": f"{de_zentora['2026-05']:.2f}"},
    ])

    key = [
        ("Q01", "Business user", "Semantic model", "What were total net sales in 2025?", eur_m(net_by_year["2025"])),
        ("Q02", "Business user", "Semantic model", "Which therapeutic area had the highest net sales in 2025?",
         f"{top_ta} ({eur_m(ta_2025[top_ta])})"),
        ("Q03", "Business user", "Semantic model", "How much did Immunology net sales grow in 2025 compared with 2024?",
         f"{imm_growth:.1%} ({eur_m(ta_year[('Immunology', '2024')])} to {eur_m(ta_year[('Immunology', '2025')])})"),
        ("Q04", "Business user", "Semantic model", "What are the top 3 countries by net sales in 2026?",
         "; ".join(f"{k} ({eur_m(v)})" for k, v in top3)),
        ("Q05", "Business user", "Semantic model", "What was the discount % by channel in 2025?", disc_txt),
        ("Q06", "Business user", "Lakehouse", "How many quality complaints were received for Zentora 100 mg tablets in Germany in April 2026?",
         str(apr_complaints)),
        ("Q07", "Business user", "Lakehouse", "In which weeks was Zentora 100 mg tablets out of stock in Germany?",
         f"{len(stockout_weeks)} weeks: week ending {stockout_weeks[0]} to week ending {stockout_weeks[-1]}"),
        ("Q08", "Business user", "Lakehouse", "Which batch had the most quality complaints in 2026?",
         f"{top_batch} ({batch_2026[top_batch]} complaints)"),
        ("Q09", "Business user", "Semantic model", "Show monthly net sales of Zentora 100 mg tablets in Germany in 2026 as a line chart.",
         f"Line chart. {monthly_txt}"),
        ("Q10", "Business user", "Both", "Why did net sales of Zentora 100 mg tablets in Germany drop in May 2026?",
         f"Net sales fell from {eur_k(de_zentora['2026-04'])} (April) to {eur_k(de_zentora['2026-05'])} (May). "
         f"Germany was out of stock from week ending {stockout_weeks[0]} to {stockout_weeks[-1]}, after {apr_complaints} "
         f"packaging complaints in April 2026 on batch {top_batch} ({'; '.join(story_text)})."),
    ]
    write(ROOT / "lab-02-data-agent" / "testing" / "answer-key.csv", [
        {"id": i, "persona": p, "expected_source": s, "question": q, "expected_answer": a, "result": "", "notes": ""}
        for i, p, s, q, a in key
    ])
    write(ROOT / "lab-02-data-agent" / "testing" / "ground_truth.csv", [
        {"question": q, "expected_answer": a} for _i, _p, s, q, a in key if not q.startswith("Show ")
    ])

    good_looks_like = {
        "Q01": "One EUR amount for calendar year 2025, based on net sales",
        "Q02": "One therapeutic area with its 2025 net sales",
        "Q03": "A growth percentage with the 2024 and 2025 values",
        "Q04": "Three countries ranked, with amounts and the period (January to September 2026)",
        "Q05": "A percentage for each of the three channels",
        "Q06": "One count of complaints, using the lakehouse",
        "Q07": "A list or range of weeks with stock status Stock-out",
        "Q08": "One batch number with its complaint count",
        "Q09": "A line chart by month, with no gaps from January to September 2026",
        "Q10": "Combines sales (model) with stock-out and complaints (lakehouse) for the same product, country and period",
        "Q11": "Asks one clarifying question (which metric or which period) before it runs any query",
        "Q12": "Run as a user in the DACH RLS role: returns no France data",
    }
    extra = [
        ("Q11", "None: clarifying question expected", "How are we doing in DACH?"),
        ("Q12", "Semantic model (RLS test)", "What were net sales in France in 2025?"),
    ]
    sheet = [{"id": i, "expected_source": s, "question": q} for i, _p, s, q, _a in key] + [
        {"id": i, "expected_source": s, "question": q} for i, s, q in extra
    ]
    write(ROOT / "lab-02-data-agent" / "testing" / "business-test-sheet.csv", [
        {**row, "what_good_looks_like": good_looks_like[row["id"]], "source_used": "", "visual_shown": "",
         "result_pass_partial_fail": "", "feedback_for_developer": ""}
        for row in sheet
    ])


if __name__ == "__main__":
    main()
