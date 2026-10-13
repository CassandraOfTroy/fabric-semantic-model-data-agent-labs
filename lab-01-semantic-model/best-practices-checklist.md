# Semantic model checklist

Use this list when you build any semantic model. Each item links to the Microsoft Learn guidance.

## Model design

| ✓ | Practice | Why | Source |
| --- | --- | --- | --- |
| ☐ | Build a **star schema**: fact tables surrounded by dimension tables, joined by one-to-many, single-direction relationships | Simpler and faster DAX, and predictable filtering | [Star schema](https://learn.microsoft.com/power-bi/guidance/star-schema) |
| ☐ | **Add only the tables and columns you need.** Leave out unused tables and columns | Each capacity size limits the memory per Direct Lake model; above it, queries slow down | [Direct Lake overview – limitations](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#considerations-and-limitations) |
| ☐ | **Give related columns the same data type** in the lakehouse, for example date to date | Direct Lake relationships need matching data types | [Direct Lake overview – limitations](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#considerations-and-limitations) |
| ☐ | Use a **date table**, mark it as the date table, and turn off **Auto date/time** (**File** > **Options**) | Correct time intelligence without hidden tables | [Date tables](https://learn.microsoft.com/power-bi/guidance/model-date-tables), [Model options](https://learn.microsoft.com/power-bi/transform-model/service-model-options) |
| ☐ | Create an **explicit measure** for every number in a report, and hide the numeric fact columns | One governed definition of each metric | [Star schema – measures](https://learn.microsoft.com/power-bi/guidance/star-schema#measures) |
| ☐ | Use **DIVIDE** for ratios | Handles division by zero | [DIVIDE vs /](https://learn.microsoft.com/dax/best-practices/dax-divide-function-operator) |
| ☐ | Use **business-friendly names** with no underscores or cryptic abbreviations | Report authors and Copilot see these names | [Optimize your model for Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-evaluate-data) |
| ☐ | Add **descriptions** to tables, columns and measures. Keep them under 200 characters | Copilot uses only the first 200 characters | [Optimize your model for Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-evaluate-data) |
| ☐ | **Hide** keys and technical columns. Set **Sort by column**, **Data category**, **Format** and **Display folder** | A clean field list for report authors and AI | [End-to-end tutorial – phase 3](https://learn.microsoft.com/power-bi/create-reports/tutorial-end-to-end-power-bi#phase-3-build-the-power-bi-semantic-model-in-model-view) |

## AI readiness

| ✓ | Practice | Why | Source |
| --- | --- | --- | --- |
| ☐ | Keep the model's **Q&A** setting on, and don't disable implicit measures | Prep data for AI and Copilot report creation depend on them | [Create reports with Copilot – limitations](https://learn.microsoft.com/power-bi/create-reports/copilot-create-reports#considerations-and-limitations) |
| ☐ | **AI data schema**: select only the fields AI should use | Less ambiguity. For example, the AI picks *Net Sales* rather than *Gross Sales* | [AI data schema](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-data-schema) |
| ☐ | **AI instructions**: a glossary and business rules (up to 10,000 characters) | Teaches company terms such as "GTN" or "DACH" | [AI instructions](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-instructions) |
| ☐ | **Verified answers** for the top questions, with 5–7 trigger phrases each | Consistent answers in Copilot and in data agents | [Verified answers](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-verified-answers), [Data agent best practices](https://learn.microsoft.com/fabric/data-science/semantic-model-best-practices) |
| ☐ | Mark the model **Approved for Copilot** when it's ready | Removes the warning shown on answers in standalone Copilot | [Prepare your data for AI](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai#mark-your-model-as-approved-for-copilot) |
| ☐ | Decide on **Allow any person with only read permissions to use AI…** (model settings > Copilot) | Turn it off for models that aren't curated yet | [Use Copilot with semantic models](https://learn.microsoft.com/power-bi/create-reports/copilot-semantic-models) |

## Security and lifecycle

| ✓ | Practice | Why | Source |
| --- | --- | --- | --- |
| ☐ | Define **RLS roles** and check them with **Test as role**. RLS applies only to users with the **Viewer** role | Same data security in reports, Copilot and data agents | [Row-level security](https://learn.microsoft.com/fabric/security/service-admin-row-level-security) |
| ☐ | Apply a **sensitivity label** to the model. Reports created from it inherit the label | Protection follows the data when it's exported | [Information protection](https://learn.microsoft.com/fabric/governance/information-protection) |
| ☐ | **Endorse** the model (Promoted, or Certified by the data owner) | Users find the trusted model | [Endorse content](https://learn.microsoft.com/power-bi/collaborate-share/service-endorse-content) |
| ☐ | Use **version history** for web edits, and Git integration for team development | Web edits save automatically and can't be undone | [Version history](https://learn.microsoft.com/power-bi/transform-model/service-semantic-model-version-history) |
