"""
Generate the governance demo table for the Purview DLP and DSPM demo: customer bank accounts with IBANs.

All values are synthetic. The IBANs have valid check digits so that Microsoft Purview recognizes them as
the sensitive information type "International Banking Account Number (IBAN)". The bank codes and account
numbers are random and don't belong to real banks or accounts. Customer names match dim_customer.

The table is used only in the instructor's governance demo (folder GOV), not in Lab 1 or Lab 2.

Usage:
    python scripts/generate_governance_demo_data.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

SEED = 2026
ROOT = Path(__file__).resolve().parent.parent

# Country code -> BBAN layout: "n" = digit, "a" = upper-case letter (ISO 13616 lengths)
BBAN = {
    "AT": "n" * 16, "BE": "n" * 12, "CH": "n" * 17, "DE": "n" * 18, "DK": "n" * 14, "ES": "n" * 20,
    "FR": "n" * 23, "GB": "aaaa" + "n" * 14, "IE": "aaaa" + "n" * 14, "IT": "a" + "n" * 22,
    "NL": "aaaa" + "n" * 10, "NO": "n" * 11, "PT": "n" * 21, "SE": "n" * 20,
}
BIC_BANKS = ["CTPH", "MDPH", "EUPH", "NRPH"]


def iban(country: str, rng: random.Random) -> str:
    bban = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") if c == "a" else str(rng.randint(0, 9))
                   for c in BBAN[country])
    numeric = "".join(str(int(ch, 36)) for ch in bban + country + "00")
    check = 98 - int(numeric) % 97
    return f"{country}{check:02d}{bban}"


def is_valid(value: str) -> bool:
    rearranged = value[4:] + value[:4]
    return int("".join(str(int(ch, 36)) for ch in rearranged)) % 97 == 1


def main():
    rng = random.Random(SEED)
    customers = list(csv.DictReader(open(ROOT / "data" / "dim_customer.csv", encoding="utf-8")))
    rows = []
    for c in customers:
        code = c["country_code"]
        account = iban(code, rng)
        assert is_valid(account)
        rows.append({
            "customer_key": int(c["customer_key"]),
            "customer_name": c["customer_name"],
            "country": c["country"],
            "account_holder": c["customer_name"],
            "iban": account,
            "bic": f"{rng.choice(BIC_BANKS)}{code}{rng.choice(['2X', '3A', '5B', '8C'])}",
            "payment_terms_days": rng.choice([30, 45, 60, 90]),
            "direct_debit_mandate": rng.choice(["Yes", "No"]),
        })

    out = ROOT / "data" / "governance"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "customer_bank_accounts.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    schema = pa.schema([
        ("customer_key", pa.int32()), ("customer_name", pa.string()), ("country", pa.string()),
        ("account_holder", pa.string()), ("iban", pa.string()), ("bic", pa.string()),
        ("payment_terms_days", pa.int32()), ("direct_debit_mandate", pa.string()),
    ])
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, out / "customer_bank_accounts.parquet", compression="snappy")
    print(f"customer_bank_accounts: {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
