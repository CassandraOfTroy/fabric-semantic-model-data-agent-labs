"""
Generate the Contoso Pharma synthetic dataset used in both hands-on labs.

All company, product, customer and batch names are fictional. The script uses
only the Python standard library and a fixed seed, so every run produces the
same files.

Usage:
    python scripts/generate_data.py               # writes CSV files to ./data
    python scripts/generate_data.py --out <dir>   # writes CSV files to <dir>
"""

from __future__ import annotations

import argparse
import calendar
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261012
SALES_START = date(2024, 1, 1)
SALES_END = date(2026, 9, 30)
CALENDAR_END = date(2026, 12, 31)

# Storyline used in both labs (see data/README.md).
STORY_COUNTRY = "DE"
STORY_PRODUCT_KEY = 1  # Zentora 100 mg tablets
STORY_BATCH = "ZT100-2603B"
STORY_SALES_FACTOR = {(2026, 4): 0.92, (2026, 5): 0.22, (2026, 6): 0.40, (2026, 7): 1.75, (2026, 8): 1.05}
STOCKOUT_FIRST_WEEK = date(2026, 5, 3)
STOCKOUT_LAST_WEEK = date(2026, 6, 14)
TENDER_COUNTRY, TENDER_PRODUCT_KEY, TENDER_MONTH = "FR", 3, (2025, 2)

COUNTRIES = [
    # code, name, sales region, size factor, price index, cities
    ("DE", "Germany", "DACH", 1.60, 1.00, ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt"]),
    ("AT", "Austria", "DACH", 0.45, 0.97, ["Vienna", "Graz", "Linz"]),
    ("CH", "Switzerland", "DACH", 0.55, 1.12, ["Zurich", "Basel", "Geneva"]),
    ("FR", "France", "Western Europe", 1.40, 0.90, ["Paris", "Lyon", "Marseille", "Toulouse"]),
    ("BE", "Belgium", "Western Europe", 0.50, 0.92, ["Brussels", "Antwerp", "Ghent"]),
    ("NL", "Netherlands", "Western Europe", 0.60, 0.93, ["Amsterdam", "Rotterdam", "Utrecht"]),
    ("IT", "Italy", "Southern Europe", 1.20, 0.86, ["Milan", "Rome", "Naples", "Turin"]),
    ("ES", "Spain", "Southern Europe", 1.10, 0.85, ["Madrid", "Barcelona", "Valencia", "Seville"]),
    ("PT", "Portugal", "Southern Europe", 0.40, 0.82, ["Lisbon", "Porto"]),
    ("SE", "Sweden", "Nordics", 0.50, 0.95, ["Stockholm", "Gothenburg", "Malmo"]),
    ("DK", "Denmark", "Nordics", 0.35, 0.98, ["Copenhagen", "Aarhus"]),
    ("NO", "Norway", "Nordics", 0.35, 1.02, ["Oslo", "Bergen"]),
    ("GB", "United Kingdom", "UK & Ireland", 1.30, 0.88, ["London", "Manchester", "Birmingham", "Leeds"]),
    ("IE", "Ireland", "UK & Ireland", 0.30, 0.95, ["Dublin", "Cork"]),
]
BIG_COUNTRIES = {"DE", "FR", "IT", "ES", "GB"}

H, SC, RP, W = "Hospital", "Specialty Clinic", "Retail Pharmacy", "Wholesaler"
TYPE_SIZE = {H: 1.0, SC: 0.6, RP: 0.35, W: 2.2}

PRODUCTS = [
    # key, name, brand, therapeutic area, formulation, launch, list price EUR, base units, customer types, trend, batch code
    (1, "Zentora 100 mg tablets", "Zentora", "Oncology", "Tablet", date(2019, 3, 1), 2450.00, 22, [H, SC, RP, W], "base", "ZT100"),
    (2, "Zentora 250 mg tablets", "Zentora", "Oncology", "Tablet", date(2020, 9, 1), 5600.00, 9, [H, SC, RP, W], "base", "ZT250"),
    (3, "Onkivex 400 mg infusion", "Onkivex", "Oncology", "Infusion", date(2021, 5, 1), 3900.00, 14, [H], "base", "OKX400"),
    (4, "Immunara 150 mg pen", "Immunara", "Immunology", "Pre-filled pen", date(2022, 2, 1), 1250.00, 26, [H, SC, RP, W], "growth", "IM150"),
    (5, "Immunara 300 mg pen", "Immunara", "Immunology", "Pre-filled pen", date(2024, 6, 1), 2300.00, 12, [H, SC, RP, W], "growth", "IM300"),
    (6, "Neurovanta 20 mg capsules", "Neurovanta", "Neuroscience", "Capsule", date(2018, 11, 1), 310.00, 70, [H, SC, RP, W], "base", "NV20"),
    (7, "Neurovanta 40 mg capsules", "Neurovanta", "Neuroscience", "Capsule", date(2018, 11, 1), 540.00, 45, [H, SC, RP, W], "base", "NV40"),
    (8, "Cardiqa 5 mg tablets", "Cardiqa", "Cardiovascular", "Tablet", date(2014, 4, 1), 38.00, 900, [H, RP, W], "decline", "CQ5"),
    (9, "Cardiqa 10 mg tablets", "Cardiqa", "Cardiovascular", "Tablet", date(2014, 4, 1), 64.00, 650, [H, RP, W], "decline", "CQ10"),
    (10, "Ocularis 2 mg injection", "Ocularis", "Ophthalmology", "Intravitreal injection", date(2020, 1, 1), 890.00, 30, [H, SC], "base", "OC2"),
    (11, "Ocularis 4 mg injection", "Ocularis", "Ophthalmology", "Intravitreal injection", date(2021, 7, 1), 1520.00, 16, [H, SC], "base", "OC4"),
    (12, "Viraquel 75 mg capsules", "Viraquel", "Infectious Diseases", "Capsule", date(2017, 10, 1), 45.00, 520, [H, RP, W], "seasonal", "VQ75"),
]

SEASONALITY = {1: 1.80, 2: 1.70, 3: 1.30, 4: 1.00, 5: 0.80, 6: 0.60, 7: 0.55, 8: 0.60, 9: 0.80, 10: 1.10, 11: 1.40, 12: 1.75}
CHANNEL_DISCOUNT = {"Direct": 0.03, "Wholesale": 0.09, "Tender": 0.16}
TYPE_DISCOUNT = {H: 0.02, SC: 0.005, RP: 0.0, W: 0.01}
REGION_DISCOUNT = {"DACH": 0.0, "Western Europe": 0.005, "Southern Europe": 0.025, "Nordics": -0.01, "UK & Ireland": 0.01}

COMPLAINT_TEXT = {
    "Packaging": ["Carton damaged on receipt", "Blister difficult to open", "Seal partially open"],
    "Product appearance": ["Tablet discoloured", "Broken tablets in blister", "Capsule deformed"],
    "Labeling": ["Label smudged", "Leaflet in wrong language", "Expiry date hard to read"],
    "Shipping damage": ["Box crushed in transit", "Temperature logger alarm on delivery"],
    "Device malfunction": ["Pen did not activate", "Needle cap hard to remove"],
    "Missing leaflet": ["Patient leaflet missing"],
}
STORY_COMPLAINT_TEXT = ["Blister seal not intact", "Blister foil torn on receipt", "Tablets loose in carton, blister seal open"]


def month_iter(start: date, end: date):
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def months_between(year: int, month: int, base_year: int, base_month: int) -> int:
    return (year - base_year) * 12 + (month - base_month)


def poisson(rng: random.Random, lam: float) -> int:
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def trend_factor(trend: str, year: int, month: int) -> float:
    t = months_between(year, month, 2024, 1)
    if trend == "growth":
        return 1.0 + 0.022 * t
    if trend == "decline":
        after = months_between(year, month, 2025, 6)
        return 1.0 + 0.004 * t if after <= 0 else max(0.45, 1.0 - 0.035 * after)
    if trend == "seasonal":
        return SEASONALITY[month] * (1.0 + 0.002 * t)
    return 1.0 + 0.004 * t


def build_customers():
    customers, key = [], 1001
    for code, country, region, _size, _price, cities in COUNTRIES:
        templates = [
            (f"{cities[0]} Teaching Hospital", H, cities[0], True, 1.4),
            (f"{cities[1 % len(cities)]} General Hospital", H, cities[1 % len(cities)], False, 0.9),
            (f"{cities[-1]} Specialist Clinic", SC, cities[-1], False, 1.0),
            (f"{cities[0]} Central Pharmacy", RP, cities[0], False, 1.0),
            (f"{cities[1 % len(cities)]} Market Pharmacy", RP, cities[1 % len(cities)], False, 1.0),
            (f"{cities[2 % len(cities)]} Station Pharmacy", RP, cities[2 % len(cities)], False, 1.0),
            (f"{country} Pharma Distribution", W, cities[0], code in BIG_COUNTRIES, 1.0),
        ]
        if code in BIG_COUNTRIES:
            templates.append((f"{country} Healthcare Logistics", W, cities[1], False, 0.8))
        for name, ctype, city, key_account, size in templates:
            customers.append({
                "customer_key": key, "customer_name": name, "customer_type": ctype, "city": city,
                "country": country, "country_code": code, "sales_region": region,
                "key_account": "Yes" if key_account else "No", "_size": size,
            })
            key += 1
    return customers


def build_dates():
    rows, d = [], SALES_START
    while d <= CALENDAR_END:
        rows.append({
            "date": d.isoformat(), "year": d.year, "quarter": f"Q{(d.month - 1) // 3 + 1}",
            "year_quarter": f"{d.year}-Q{(d.month - 1) // 3 + 1}", "month_number": d.month,
            "month_name": calendar.month_name[d.month], "year_month": f"{d.year}-{d.month:02d}",
            "month_start_date": d.replace(day=1).isoformat(),
            "week_ending_date": (d + timedelta(days=6 - d.weekday())).isoformat(),
        })
        d += timedelta(days=1)
    return rows


def build_sales(rng, customers):
    country = {c[0]: c for c in COUNTRIES}
    rows, line_id = [], 1
    expected = {}  # (country_code, product_key, year, month) -> expected units without noise or storyline
    for year, month in month_iter(SALES_START, SALES_END):
        days_in_month = calendar.monthrange(year, month)[1]
        last_day = min(days_in_month, SALES_END.day) if (year, month) == (SALES_END.year, SALES_END.month) else days_in_month
        for p in PRODUCTS:
            pkey, _name, _brand, _ta, _form, launch, list_price, base, types, trend, _code = p
            if date(year, month, 1) < launch.replace(day=1):
                continue
            for c in customers:
                if c["customer_type"] not in types:
                    continue
                code = c["country_code"]
                _, _, region, csize, price_index, _ = country[code]
                mean_units = base * TYPE_SIZE[c["customer_type"]] * c["_size"] * csize * trend_factor(trend, year, month)
                expected[(code, pkey, year, month)] = expected.get((code, pkey, year, month), 0.0) + mean_units
                story = STORY_SALES_FACTOR.get((year, month), 1.0) if (code == STORY_COUNTRY and pkey == STORY_PRODUCT_KEY) else 1.0
                units_total = mean_units * story * rng.lognormvariate(0.0, 0.18)
                n_lines = 2 if c["customer_type"] in (H, W) else 1
                for i in range(n_lines):
                    units = max(1, round(units_total / n_lines * rng.uniform(0.8, 1.2)))
                    if c["customer_type"] == W:
                        channel = "Wholesale"
                    elif c["customer_type"] == H:
                        channel = "Tender" if rng.random() < 0.35 else "Direct"
                    else:
                        channel = "Direct"
                    pct = (CHANNEL_DISCOUNT[channel] + TYPE_DISCOUNT[c["customer_type"]] + REGION_DISCOUNT[region]
                           + (0.015 if c["key_account"] == "Yes" else 0.0) + rng.gauss(0.0, 0.008))
                    if trend == "decline" and months_between(year, month, 2025, 6) > 0:
                        pct += 0.06
                    pct = min(max(pct, 0.0), 0.35)
                    unit_price = round(list_price * price_index, 2)
                    gross = round(units * unit_price, 2)
                    discount = round(gross * pct, 2)
                    rows.append({
                        "sales_line_id": line_id,
                        "order_date": date(year, month, rng.randint(1, last_day)).isoformat(),
                        "customer_key": c["customer_key"], "product_key": pkey, "channel": channel,
                        "units": units, "unit_price_eur": f"{unit_price:.2f}", "gross_sales_eur": f"{gross:.2f}",
                        "discount_eur": f"{discount:.2f}", "net_sales_eur": f"{gross - discount:.2f}",
                    })
                    line_id += 1
    # One-off hospital tender in France (positive anomaly for the anomaly-detection exercise).
    tender_customer = next(c for c in customers if c["country_code"] == TENDER_COUNTRY and c["customer_type"] == H)
    p = next(x for x in PRODUCTS if x[0] == TENDER_PRODUCT_KEY)
    unit_price = round(p[6] * country[TENDER_COUNTRY][4], 2)
    units = 420
    gross = round(units * unit_price, 2)
    discount = round(gross * 0.20, 2)
    rows.append({
        "sales_line_id": line_id, "order_date": date(*TENDER_MONTH, 18).isoformat(),
        "customer_key": tender_customer["customer_key"], "product_key": TENDER_PRODUCT_KEY, "channel": "Tender",
        "units": units, "unit_price_eur": f"{unit_price:.2f}", "gross_sales_eur": f"{gross:.2f}",
        "discount_eur": f"{discount:.2f}", "net_sales_eur": f"{gross - discount:.2f}",
    })
    rows.sort(key=lambda r: (r["order_date"], r["sales_line_id"]))
    return rows, expected


def build_inventory(rng, expected):
    country = {c[0]: c for c in COUNTRIES}
    rows = []
    first = SALES_START + timedelta(days=6 - SALES_START.weekday())
    last = SALES_END - timedelta(days=(SALES_END.weekday() + 1) % 7)
    blips = {("IT", 12): (date(2025, 1, 12), date(2025, 1, 26)), ("ES", 4): (date(2025, 9, 14), date(2025, 9, 21))}
    for code, cname, *_ in COUNTRIES:
        for p in PRODUCTS:
            pkey, pname, brand, ta, *_rest = p
            dos, backorder = rng.uniform(35, 55), 0
            week = first
            while week <= last:
                monthly = expected.get((code, pkey, week.year, week.month), 0.0)
                if monthly == 0:
                    week += timedelta(days=7)
                    continue
                weekly_demand = monthly / 4.345
                dos = min(70.0, max(24.0, dos + rng.gauss(0.0, 3.0)))
                days = dos
                if (code, pkey) in blips and blips[(code, pkey)][0] <= week <= blips[(code, pkey)][1]:
                    days = rng.uniform(9, 16)
                if code == STORY_COUNTRY and pkey == STORY_PRODUCT_KEY:
                    if week == date(2026, 4, 26):
                        days = 9.0
                    elif STOCKOUT_FIRST_WEEK <= week <= STOCKOUT_LAST_WEEK:
                        days = 0.0
                        backorder += round(weekly_demand * 0.75)
                    elif week == date(2026, 6, 21):
                        days, backorder = 6.0, round(backorder * 0.55)
                    elif week == date(2026, 6, 28):
                        days, backorder = 18.0, round(backorder * 0.2)
                    elif week >= date(2026, 7, 5):
                        backorder = 0
                stock = round(weekly_demand / 7 * days)
                status = "Stock-out" if stock == 0 else ("Low" if days < 21 else "OK")
                rows.append({
                    "week_ending_date": week.isoformat(), "country": cname, "country_code": code,
                    "product_name": pname, "brand": brand, "therapeutic_area": ta, "stock_units": stock,
                    "avg_weekly_demand_units": round(weekly_demand), "days_of_supply": round(days, 1),
                    "backorder_units": backorder, "stock_status": status,
                })
                week += timedelta(days=7)
    rows.sort(key=lambda r: (r["week_ending_date"], r["country_code"], r["product_name"]))
    return rows


def build_complaints(rng):
    rows = []
    country = {c[0]: c for c in COUNTRIES}

    def make(received, code, p, batch, category, text, severity):
        status, closed, days = "Open", "", ""
        close_days = int(min(90, max(2, rng.lognormvariate(math.log(14), 0.6))))
        if received + timedelta(days=close_days) <= SALES_END and not (SALES_END - received).days < 10:
            status, closed, days = "Closed", (received + timedelta(days=close_days)).isoformat(), close_days
        rows.append({
            "received_date": received.isoformat(), "country": country[code][1], "country_code": code,
            "product_name": p[1], "brand": p[2], "therapeutic_area": p[3], "batch_number": batch,
            "complaint_category": category, "description": text, "severity": severity,
            "status": status, "closed_date": closed, "days_to_close": days,
        })

    for year, month in month_iter(SALES_START, SALES_END):
        days_in_month = calendar.monthrange(year, month)[1]
        for code, _name, _region, csize, *_ in COUNTRIES:
            for p in PRODUCTS:
                if date(year, month, 1) < p[5].replace(day=1):
                    continue
                for _ in range(poisson(rng, 0.30 * csize)):
                    received = date(year, month, rng.randint(1, days_in_month))
                    if received > SALES_END:
                        continue
                    if p[4] in ("Tablet", "Capsule"):
                        cats, weights = ["Packaging", "Product appearance", "Labeling", "Shipping damage", "Missing leaflet"], [30, 25, 15, 20, 10]
                    else:
                        cats, weights = ["Device malfunction", "Packaging", "Labeling", "Shipping damage", "Product appearance"], [30, 25, 15, 20, 10]
                    category = rng.choices(cats, weights)[0]
                    batch_month = date(year, month, 1) - timedelta(days=rng.randint(30, 90))
                    batch = f"{p[10]}-{batch_month:%y%m}{rng.choice('ACD')}"
                    severity = rng.choices(["Minor", "Major", "Critical"], [68, 27, 5])[0]
                    make(received, code, p, batch, category, rng.choice(COMPLAINT_TEXT[category]), severity)
    story = next(x for x in PRODUCTS if x[0] == STORY_PRODUCT_KEY)
    for _ in range(46):
        received = date(2026, 3, 30) + timedelta(days=rng.randint(0, 29))
        severity = "Critical" if rng.random() < 0.2 else "Major"
        make(received, STORY_COUNTRY, story, STORY_BATCH, "Packaging", rng.choice(STORY_COMPLAINT_TEXT), severity)
    rows.sort(key=lambda r: (r["received_date"], r["country_code"], r["product_name"]))
    for i, r in enumerate(rows, start=1):
        r_id = f"QC-{r['received_date'][:4]}-{i:05d}"
        r.update({"complaint_id": r_id})
    return [{"complaint_id": r["complaint_id"], **{k: v for k, v in r.items() if k != "complaint_id"}} for r in rows]


def write_csv(path: Path, rows: list[dict]):
    fields = [k for k in rows[0].keys() if not k.startswith("_")]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{path.name:<24} {len(rows):>7,} rows")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data"), help="output folder")
    out = Path(parser.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    customers = build_customers()
    products = [{
        "product_key": p[0], "product_name": p[1], "brand": p[2], "therapeutic_area": p[3],
        "formulation": p[4], "launch_date": p[5].isoformat(), "list_price_eur": f"{p[6]:.2f}",
    } for p in PRODUCTS]
    sales, expected = build_sales(rng, customers)
    write_csv(out / "dim_customer.csv", customers)
    write_csv(out / "dim_product.csv", products)
    write_csv(out / "dim_date.csv", build_dates())
    write_csv(out / "fact_sales.csv", sales)
    write_csv(out / "inventory_weekly.csv", build_inventory(rng, expected))
    write_csv(out / "quality_complaints.csv", build_complaints(rng))


if __name__ == "__main__":
    main()
