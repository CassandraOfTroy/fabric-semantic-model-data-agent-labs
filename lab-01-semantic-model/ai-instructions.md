# AI instructions for the semantic model

Used in Lab 1, step 6. Copy the text inside the box into **Prep data for AI** > **Add AI instructions**, then select **Apply**. The limit is 10,000 characters ([AI instructions](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-instructions)).

The data agent in Lab 2 uses these instructions too. When an agent queries a semantic model, it uses the model's Prep for AI settings and ignores the agent-level instructions ([Semantic model best practices for data agent](https://learn.microsoft.com/fabric/data-science/semantic-model-best-practices)).

```text
## Business context
Contoso Pharma sells prescription medicines to hospitals, specialist clinics, retail pharmacies and wholesalers in 14 European countries.
All amounts are in EUR. The fiscal year is the calendar year. Data is available from January 2024 to September 2026.

## Terminology
- "Sales", "revenue" or "turnover" means the measure Net Sales, unless the user explicitly asks for gross sales.
- "GTN", "gross-to-net", "discount" or "rebate" means Discount Amount or Discount %.
- "Packs" or "volume" means the measure Units Sold.
- "TA" means Therapeutic Area.
- "DACH" means Germany, Austria and Switzerland (Sales Region = DACH).
- "Tender" means a hospital contract won in a public tender (Channel = Tender).
- "Key account" means Key Account = Yes.

## Rules
- For trends over time, use the Date table (Month Start or Year Month). Do not use Order Date.
- For year-over-year questions, use Net Sales YoY % and Net Sales PY.
- If the user does not give a time period, use the last full year (2025) and say so in the answer.
- Product names include the strength, for example "Zentora 100 mg tablets". If the user names only a brand, such as "Zentora", filter on Brand.
- If a question is ambiguous (for example, which metric or which period), ask one short clarifying question before answering.
```
