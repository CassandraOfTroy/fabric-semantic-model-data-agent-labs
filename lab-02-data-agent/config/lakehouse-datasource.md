# Lakehouse data source configuration

Used in Lab 2, step A3. **Build agent with AI** (preview) can generate this configuration for you. Use this file as the reference, or as the manual fallback.

Lakehouses support data source instructions, a data source description and example queries. Semantic models don't: they use Prep for AI instead ([Add and configure data sources](https://learn.microsoft.com/fabric/data-science/data-agent-add-datasources)).

## Data source description

The agent uses the description to decide whether a question belongs to this source ([Configure your data agent](https://learn.microsoft.com/fabric/data-science/data-agent-configurations#data-source-description)).

```text
Supply and quality data for Contoso Pharma: weekly stock per country and product (inventory_weekly) and product quality complaints (quality_complaints). Use for stock, stock-outs, backorders, days of supply, complaints, batches and complaint severity. Contains no sales data.
```

## Data source instructions

These instructions are sent with every query to this source. Template: General knowledge, Table descriptions, When asked about ([Configure your data agent](https://learn.microsoft.com/fabric/data-science/data-agent-configurations#data-source-instructions)).

```text
## General knowledge
- Two tables in schema dbo: inventory_weekly and quality_complaints. There are no joins between them; filter each one by product_name, brand, country and dates.
- Product and country names are identical to the sales semantic model, for example product_name 'Zentora 100 mg tablets' and country 'Germany'.
- Weeks end on Sunday (week_ending_date). Data runs from 2024-01-07 to 2026-09-27 for stock and to 2026-09-30 for complaints.

## Table descriptions
- inventory_weekly: one row per country, product and week. stock_units = packs on hand at week end. avg_weekly_demand_units = expected weekly demand. days_of_supply = stock divided by daily demand. backorder_units = packs ordered but not delivered. stock_status: 'OK' (21 or more days of supply), 'Low' (under 21 days), 'Stock-out' (no stock).
- quality_complaints: one row per complaint. complaint_category, description (short free text), severity ('Minor', 'Major', 'Critical'), batch_number, status ('Open', 'Closed'), closed_date and days_to_close.

## When asked about
- "Out of stock" or "stock-out": filter stock_status = 'Stock-out'.
- A month: filter the date column between the first and the last day of that calendar month.
- A brand (for example "Zentora"): filter brand. A specific strength: filter product_name.
- The cause of a sales drop: return the stock_status by week and the complaints by category and batch for that product and country, in the same month and the month before.
```

## Example queries

Add these with **Example queries** > **Add or Edit Example Queries** for `LH_ContosoPharma`. Each query is validated against the selected schema, and only valid queries are used. For each question, the agent retrieves the three most relevant examples ([Example queries](https://learn.microsoft.com/fabric/data-science/data-agent-example-queries)).

The examples deliberately differ from the test questions in [../testing](../testing), so the test stays fair.

**1. Which batches had the most quality complaints in the last 90 days?**

```sql
-- "Last 90 days" counts back from the latest complaint date in the table
SELECT TOP 10 batch_number, product_name, country, COUNT(*) AS complaints
FROM dbo.quality_complaints
WHERE received_date >= DATEADD(day, -90, (SELECT MAX(received_date) FROM dbo.quality_complaints))
GROUP BY batch_number, product_name, country
ORDER BY complaints DESC;
```

**2. Show the number of complaints by category and severity for Immunara in 2025.**

```sql
SELECT complaint_category, severity, COUNT(*) AS complaints
FROM dbo.quality_complaints
WHERE brand = 'Immunara'                 -- brand covers all strengths
  AND received_date >= '2025-01-01' AND received_date < '2026-01-01'
GROUP BY complaint_category, severity
ORDER BY complaints DESC;
```

**3. Which products had the lowest days of supply last week?**

```sql
-- "Last week" = the most recent week_ending_date in the table
SELECT TOP 5 country, product_name, days_of_supply, stock_status
FROM dbo.inventory_weekly
WHERE week_ending_date = (SELECT MAX(week_ending_date) FROM dbo.inventory_weekly)
ORDER BY days_of_supply ASC;
```

**4. In which weeks was Viraquel low on stock in Italy?**

```sql
SELECT week_ending_date, product_name, stock_status, days_of_supply, backorder_units
FROM dbo.inventory_weekly
WHERE brand = 'Viraquel' AND country = 'Italy'
  AND stock_status <> 'OK'               -- 'Low' or 'Stock-out'
ORDER BY week_ending_date;
```

**5. What is the average number of days to close a complaint, by category, in 2026?**

```sql
SELECT complaint_category,
       AVG(CAST(days_to_close AS FLOAT)) AS avg_days_to_close,
       COUNT(*) AS closed_complaints
FROM dbo.quality_complaints
WHERE status = 'Closed'
  AND received_date >= '2026-01-01' AND received_date < '2027-01-01'
GROUP BY complaint_category
ORDER BY avg_days_to_close DESC;
```
