# Copilot prompts for Lab 1

Copy and paste each prompt. Always review what Copilot proposes before you accept it: AI output can be wrong.

## Step 4 – Copilot in DAX query view

Open a new query tab, press **Ctrl+I** (or select **Copilot**), and enter:

```text
Write a measure called Net Sales YoY % that returns the year-over-year percentage change of [Net Sales] compared with [Net Sales PY]. Show it by year.
```

```text
Write a measure called Net Sales YTD that uses TOTALYTD and the 'Date'[date] column. Show it by month for 2026.
```

Select **Run** to check the result, then **Keep query**. Compare the result with the reference answers at the end of [measures.dax](measures.dax). Source: [Write DAX queries with Copilot](https://learn.microsoft.com/dax/dax-copilot).

## Step 5 – Copilot in web modeling (preview)

Open the model in **Editing mode** and select **Copilot** on the ribbon. When Copilot asks for permission to change the model, accept. Copilot then saves a restore point in version history ([Copilot in web modeling](https://learn.microsoft.com/power-bi/transform-model/copilot-web-modeling)).

**5a. Review (no changes)**

```text
Review my semantic model against Power BI modeling best practices. List the issues by priority. Don't change anything yet.
```

**5b. Business-friendly names.** Use this exact mapping, so that everyone's model looks the same:

```text
Rename the columns exactly as listed. Don't change anything else.
Sales: sales_line_id -> Sales Line ID, order_date -> Order Date, customer_key -> Customer Key, product_key -> Product Key, channel -> Channel, units -> Units, unit_price_eur -> Unit Price EUR, gross_sales_eur -> Gross Sales EUR, discount_eur -> Discount EUR, net_sales_eur -> Net Sales EUR.
Customer: customer_key -> Customer Key, customer_name -> Customer Name, customer_type -> Customer Type, city -> City, country -> Country, country_code -> Country Code, sales_region -> Sales Region, key_account -> Key Account.
Product: product_key -> Product Key, product_name -> Product Name, brand -> Brand, therapeutic_area -> Therapeutic Area, formulation -> Formulation, launch_date -> Launch Date, list_price_eur -> List Price EUR.
Date: date -> Date, year -> Year, quarter -> Quarter, year_quarter -> Year Quarter, month_number -> Month Number, month_name -> Month Name, year_month -> Year Month, month_start_date -> Month Start, week_ending_date -> Week Ending.
```

**5c. Hide technical fields, sort, categorize**

```text
Make these changes:
1. Hide every column in the Sales table except Channel.
2. Hide Customer Key, Product Key, Country Code, Month Number, List Price EUR and Week Ending.
3. Sort Month Name by Month Number.
4. Set the data category of City to City and of Country to Country/Region.
5. Set Summarize by to None for Year and Month Number.
```

**5d. Formats and display folders**

```text
Format Net Sales, Gross Sales, Discount Amount, Net Sales PY and Net Sales YTD as currency in EUR with no decimals.
Format Discount % and Net Sales YoY % as a percentage with one decimal.
Format Units Sold and Active Customers as whole numbers with a thousands separator. Format Net Price per Unit as EUR with two decimals.
Put the measures in display folders: Sales (Net Sales, Gross Sales, Discount Amount, Discount %), Time intelligence (Net Sales PY, Net Sales YoY %, Net Sales YTD), Volume and price (Units Sold, Net Price per Unit, Active Customers).
```

**5e. Descriptions** (Copilot reads only the first 200 characters of a description – [Optimize your model for Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-evaluate-data))

```text
Write a short business description, under 150 characters, for each table and for each visible column. Apply them.
```

For a single measure, you can also select the measure, then **Create with Copilot** under **Description**, then **Keep it** ([Measure descriptions with Copilot](https://learn.microsoft.com/power-bi/transform-model/desktop-measure-copilot-descriptions)).

## Step 7 – Copilot in the report

In the report, select **Edit**, then **Copilot** ([Create reports with Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-create-reports)).

```text
Create a page called Sales overview with: cards for Net Sales, Net Sales YoY % and Discount %; a line chart of Net Sales by Month Start; a bar chart of Net Sales by Therapeutic Area; a bar chart of Net Sales by Country; and a slicer for Year.
```

Edit the page in follow-up prompts, for example:

```text
Change the Net Sales by Country chart to a column chart sorted from highest to lowest.
```

## Step 8 – Narrative visual with Copilot

Use the **Narrative** visual in Copilot mode ([Narrative visual with Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-create-narrative)):

```text
Give an executive summary of this page in 3 bullet points. Mention the largest anomaly and the main driver of discounts.
```

## Bridge to Lab 2 – Copilot pane

```text
Why did net sales of Zentora 100 mg tablets in Germany drop in May 2026?
```

The semantic model contains sales only. Copilot can describe *what* happened, but the cause sits in data that isn't in the model (stock and quality complaints). Copilot in the report pane also doesn't do anomaly detection, forecasting or key influencers ([Ask data questions with Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-ask-data-question)). In Lab 2, a data agent combines the model with the lakehouse tables to answer *why*.
