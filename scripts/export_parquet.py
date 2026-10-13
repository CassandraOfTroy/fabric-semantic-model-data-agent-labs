"""
Write typed Parquet copies of the lab CSV files, for upload to the lakehouse.

Parquet files carry their column types, so the lakehouse "Load to tables" action creates
Delta tables with correct numbers and dates. No notebook or schema setup is needed.

Requires pyarrow:   pip install pyarrow

Usage:
    python scripts/export_parquet.py      # reads data/*.csv, writes data/parquet/*.parquet
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

DATA = Path(__file__).resolve().parent.parent / "data"

S, I32, I64, F64, D = pa.string(), pa.int32(), pa.int64(), pa.float64(), pa.date32()
MONEY, PRICE = pa.decimal128(14, 2), pa.decimal128(12, 2)

SCHEMAS = {
    "dim_customer": {"customer_key": I32, "customer_name": S, "customer_type": S, "city": S, "country": S,
                     "country_code": S, "sales_region": S, "key_account": S},
    "dim_product": {"product_key": I32, "product_name": S, "brand": S, "therapeutic_area": S, "formulation": S,
                    "launch_date": D, "list_price_eur": PRICE},
    "dim_date": {"date": D, "year": I32, "quarter": S, "year_quarter": S, "month_number": I32, "month_name": S,
                 "year_month": S, "month_start_date": D, "week_ending_date": D},
    "fact_sales": {"sales_line_id": I64, "order_date": D, "customer_key": I32, "product_key": I32, "channel": S,
                   "units": I32, "unit_price_eur": PRICE, "gross_sales_eur": MONEY, "discount_eur": MONEY,
                   "net_sales_eur": MONEY},
    "inventory_weekly": {"week_ending_date": D, "country": S, "country_code": S, "product_name": S, "brand": S,
                         "therapeutic_area": S, "stock_units": I32, "avg_weekly_demand_units": I32,
                         "days_of_supply": F64, "backorder_units": I32, "stock_status": S},
    "quality_complaints": {"complaint_id": S, "received_date": D, "country": S, "country_code": S,
                           "product_name": S, "brand": S, "therapeutic_area": S, "batch_number": S,
                           "complaint_category": S, "description": S, "severity": S, "status": S,
                           "closed_date": D, "days_to_close": I32},
}


def main():
    out = DATA / "parquet"
    out.mkdir(exist_ok=True)
    for table, columns in SCHEMAS.items():
        options = pacsv.ConvertOptions(column_types=columns, strings_can_be_null=False,
                                       null_values=[""], quoted_strings_can_be_null=False)
        data = pacsv.read_csv(DATA / f"{table}.csv", convert_options=options)
        missing = set(columns) ^ set(data.column_names)
        if missing:
            raise SystemExit(f"{table}: column mismatch {sorted(missing)}")
        pq.write_table(data.select(list(columns)), out / f"{table}.parquet", compression="snappy")
        print(f"{table + '.parquet':<28} {data.num_rows:>7,} rows")


if __name__ == "__main__":
    main()
