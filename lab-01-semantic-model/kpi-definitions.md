# KPI definitions

The three KPIs that you add to the model in [Lab 1, step 4](README.md#step-4--add-the-business-kpis-to-the-model). Use this page to:

- check what Copilot wrote in step 4b, or
- create a KPI by hand, if Copilot isn't available: select the table **Sales**, then **Home** > **New measure**. Paste the formula into the formula bar, press **Enter**, then set the properties from the table.

To create all measures at once with DAX query view, use [measures.dax](measures.dax) and [measures-time-intelligence.dax](measures-time-intelligence.dax) ([step 4, other way](README.md#4b-discount--and-net-sales-yoy--with-copilot)).

| KPI | Business question | Format | Display folder |
| --- | --- | --- | --- |
| Net Sales | How much do we sell? | Currency, **€ Euro (€ 123)**, 0 decimal places | KPIs |
| Discount % | How much discount do we give? | Percentage, 1 decimal place | KPIs |
| Net Sales YoY % | Are we growing? | Percentage, 1 decimal place | KPIs |

## Net Sales

Net sales in EUR after discounts and rebates. Use for any question about sales or revenue.

```dax
Net Sales = SUM ( Sales[net_sales_eur] )
```

## Discount %

Discounts and rebates as a share of gross sales. The gross-to-net (GTN) rate.

```dax
Discount % = DIVIDE ( SUM ( Sales[discount_eur] ), SUM ( Sales[gross_sales_eur] ) )
```

`DIVIDE` returns a blank instead of an error when gross sales are 0 ([DIVIDE function vs. divide operator](https://learn.microsoft.com/dax/best-practices/dax-divide-function-operator)).

## Net Sales YoY %

Net sales growth compared with the same period one year earlier.

```dax
Net Sales YoY % =
VAR CurrentSales = [Net Sales]
VAR PriorSales = CALCULATE ( [Net Sales], SAMEPERIODLASTYEAR ( 'Date'[date] ) )
RETURN
    DIVIDE ( CurrentSales - PriorSales, PriorSales )
```

Copilot may write `DATEADD ( 'Date'[Date], -1, YEAR )` instead of `SAMEPERIODLASTYEAR ( 'Date'[date] )`. Both return the same dates, one year earlier ([SAMEPERIODLASTYEAR](https://learn.microsoft.com/dax/sameperiodlastyear-function-dax)). Both use the Date table, which has one row per day ([Date tables](https://learn.microsoft.com/power-bi/guidance/model-date-tables)).

## Expected values

| Check | Value |
| --- | --- |
| Net Sales, 2025 | €293,801,286 (a card shows €294M) |
| Net Sales YoY %, 2025 | 10.0 % |
| Discount %, 2025 | 10.4 % |
| Net Sales YoY %, 2026 | −26.8 %. The data ends in September 2026, so nine months of 2026 are compared with all twelve months of 2025 |

All checks: [expected-values.csv](expected-values.csv).

## After step 5

Step 5 renames the columns, for example `net_sales_eur` to **Net Sales EUR**. The formulas update automatically: **Net Sales** then reads `SUM ( Sales[Net Sales EUR] )`. You don't need to change anything.

The instructor's `REF_Sales_Model` has seven more measures (for example **Units Sold** and **Net Sales YTD**). The two DAX files create all ten. Lab 1 and Lab 2 need only these three.
