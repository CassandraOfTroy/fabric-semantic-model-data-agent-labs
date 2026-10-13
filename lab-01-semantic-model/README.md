# Lab 1 – Build a semantic model on the shared lakehouse and an AI-powered report

**Time:** 120 minutes · **Level:** beginner · **Tools:** browser only

You build a star-schema semantic model on the shared lakehouse, entirely in the Fabric portal. Copilot helps at every step. Then you create a report and use Power BI's AI visuals to find why sales dropped.

The model uses **Direct Lake**: it reads the lakehouse tables in place, with no copy. Everyone builds their own model on the same data.

![Lab 1 flow: shared lakehouse, Direct Lake, semantic model P07_Sales_Model, report P07_Sales_Report. Lab steps 1 to 9 under each stage. Copilot helps at steps 4, 5, 7 and 8.](../docs/images/use-case-1-semantic-model.png)

| Step | What you do | Min |
| --- | --- | ---: |
| 0 | Welcome, your ID, naming rules | 10 |
| [1](#step-1--explore-the-data) | Explore the data | 5 |
| [2](#step-2--create-the-semantic-model) | Create the semantic model | 10 |
| [3](#step-3--tables-relationships-and-date-table) | Tables, relationships and date table | 10 |
| [4](#step-4--measures-with-dax-query-view-and-copilot) | Measures with DAX query view and Copilot | 15 |
| [5](#step-5--clean-up-the-model-with-copilot) | Clean up the model with Copilot | 10 |
| [6](#step-6--prep-data-for-ai) | Prep data for AI | 10 |
| [7](#step-7--create-the-report-with-copilot) | Create the report with Copilot, add a verified answer | 15 |
| [8](#step-8--ai-visuals) | AI visuals: anomalies, forecast, key influencers, decomposition tree | 20 |
| [9](#step-9--secure-and-govern) | Secure and govern | 10 |

## Before you start

- You have your participant ID, for example `P07`. Replace `P07` with your ID everywhere in this guide.
- You're a Contributor in the workspace **ContosoPharma_Workshop**. Its folder **00_Shared** holds the shared lakehouse **LH_ContosoPharma** that everyone builds on.
- You have read the [naming rules](../docs/naming-and-etiquette.md).

Files used in this lab: [measures.dax](measures.dax) · [measures-time-intelligence.dax](measures-time-intelligence.dax) (fallback) · [copilot-prompts.md](copilot-prompts.md) · [ai-instructions.md](ai-instructions.md) · [expected-values.csv](expected-values.csv) · [best-practices-checklist.md](best-practices-checklist.md)

---

## Step 1 – Explore the data

1. Go to <https://app.fabric.microsoft.com> and open the workspace **ContosoPharma_Workshop**.
2. Open the folder **00_Shared**, then the lakehouse **LH_ContosoPharma**.
3. In the **Explorer**, expand **Tables**. Select `fact_sales` to preview the rows. Then look at `dim_customer`, `dim_product` and `dim_date`.

> Look, don't change: everyone builds on this lakehouse. Don't rename, delete or load anything here.

✅ **Check:** you see 6 tables. Lab 1 uses the 4 tables `fact_sales`, `dim_customer`, `dim_product` and `dim_date`. The other two are for Lab 2.

> **Why this design:** `fact_sales` holds the numbers. The `dim_` tables describe them (who, what, when). That is a **star schema**, the recommended shape for Power BI models ([Star schema](https://learn.microsoft.com/power-bi/guidance/star-schema)).

## Step 2 – Create the semantic model

1. In the workspace, open your folder **P07**.
2. Select **+ New item**, search for **Semantic model** and select it.
3. Select **OneLake catalog**, then the lakehouse **LH_ContosoPharma**.
4. Enter the name `P07_Sales_Model` and check that the workspace is **ContosoPharma_Workshop**.
5. Select the tables `dim_customer`, `dim_date`, `dim_product` and `fact_sales`, then select **OK**.
6. The model opens in the web model editor. If nothing opens, allow pop-ups for the Fabric portal and try again.
7. If the model isn't in your folder: in the workspace, select **…** > **Move to** > **P07** > **Move here**.

✅ **Check:** select the `fact_sales` table. In **Properties** > **Advanced**, **Storage mode** is **Direct Lake**.

> **Why Direct Lake:** the model reads the Delta tables in OneLake directly. It doesn't copy the data, and it doesn't need a scheduled refresh: changes in the lakehouse appear in the model automatically. Queries run in the same in-memory engine as Import mode, so reports stay fast ([Direct Lake overview](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview)).

Learn more: [Direct Lake in web modeling](https://learn.microsoft.com/fabric/fundamentals/direct-lake-web-modeling)

## Step 3 – Tables, relationships and date table

1. At the top right, switch from **Viewing** to **Editing**.
   > Changes in the web editor save automatically and can't be undone. Version history keeps the last five versions ([Version history](https://learn.microsoft.com/power-bi/transform-model/service-semantic-model-version-history)).
2. Rename the tables: select each table in the **Data** pane, then change **Name** in **Properties**.

   | Old name | New name |
   | --- | --- |
   | `fact_sales` | `Sales` |
   | `dim_customer` | `Customer` |
   | `dim_product` | `Product` |
   | `dim_date` | `Date` |

3. Select **Manage relationships** > **New relationship**. Create these three relationships, each with **Cardinality** = **Many to one (\*:1)** and **Cross-filter direction** = **Single**:

   | From table, column | To table, column |
   | --- | --- |
   | `Sales`, `customer_key` | `Customer`, `customer_key` |
   | `Sales`, `product_key` | `Product`, `product_key` |
   | `Sales`, `order_date` | `Date`, `date` |

   The lakehouse has no relationships, so you create them yourself. For Direct Lake models, web modeling doesn't check cardinality for you, so set it exactly as shown ([Direct Lake overview – limitations](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#considerations-and-limitations)).
4. In the **Data** pane, right-click **Date** > **Mark as date table** > **Mark as date table**. Select the `date` column and save.
5. Select **File** > **Options**. If **Auto date/time** is on, turn it off ([Model options](https://learn.microsoft.com/power-bi/transform-model/service-model-options)). Your Date table replaces the hidden automatic date tables ([Date tables](https://learn.microsoft.com/power-bi/guidance/model-date-tables)).

✅ **Check:** the diagram shows a star. **Sales** is in the middle, with three many-to-one lines.

## Step 4 – Measures with DAX query view and Copilot

1. In a new browser tab, open your folder, select **…** next to `P07_Sales_Model`, then **Write DAX queries**.
2. Paste the whole content of [measures.dax](measures.dax) and select **Run**.
3. Select **Update model with changes**. This adds 8 measures to the **Sales** table. The `///` lines become the measure descriptions ([DAX query view](https://learn.microsoft.com/power-bi/transform-model/dax-query-view)).
4. **Copilot:** open a new query tab, press **Ctrl+I**, and use the two prompts from [copilot-prompts.md – step 4](copilot-prompts.md#step-4--copilot-in-dax-query-view). Select **Run**, then **Keep query**. Compare the DAX with the reference at the end of `measures.dax`, then select **Update model with changes** ([Write DAX queries with Copilot](https://learn.microsoft.com/dax/dax-copilot)).

   **No Copilot?** Paste [measures-time-intelligence.dax](measures-time-intelligence.dax) into a new tab, select **Run**, then **Update model with changes**.

✅ **Check:** for 2025, **Net Sales** = 293,801,286 and **Net Sales YoY %** = 10.0 %. All expected values are in [expected-values.csv](expected-values.csv).

> **Best practice:** use explicit measures for every number, and use **DIVIDE** for ratios ([DIVIDE vs /](https://learn.microsoft.com/dax/best-practices/dax-divide-function-operator)).

## Step 5 – Clean up the model with Copilot

*Copilot in web modeling is in preview.*

1. Go back to the model editor tab and refresh the browser. Make sure you're in **Editing** mode, then select **Copilot** on the ribbon.
2. Accept the permission prompt. Copilot saves a restore point of your model ([Copilot in web modeling](https://learn.microsoft.com/power-bi/transform-model/copilot-web-modeling)).
3. Run prompts **5a** to **5e** from [copilot-prompts.md](copilot-prompts.md#step-5--copilot-in-web-modeling-preview) one at a time. Read each proposal before you accept it.

✅ **Check:** column names are readable (for example **Therapeutic Area**). The **Sales** table shows only **Channel** and measures in three folders. **Month Name** sorts January to December.

**If Copilot isn't available**, do the same by hand in **Properties** (about 10 minutes). Steps 6–8 need these names:

1. Rename the visible columns with the mapping in [prompt 5b](copilot-prompts.md#step-5--copilot-in-web-modeling-preview): every **Customer**, **Product** and **Date** column, plus `channel` → **Channel** in **Sales**.
2. Hide all other **Sales** columns and every key column. Search the **Data** pane for `key`, Ctrl+select the results, and set **Is hidden** to on.
3. Set **Sort by column** of **Month Name** to **Month Number**.
4. Format **Net Sales** as currency and **Discount %** as a percentage.

**If something goes wrong:** select **File** > **Version history** and restore the version from before the Copilot session.

## Step 6 – Prep data for AI

*Preview.* These settings make Copilot, and the data agent in Lab 2, answer more reliably ([Prepare your data for AI](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai)).

1. In your folder, select `P07_Sales_Model` to open its details page. On the ribbon, select **Prep data for AI**. If the tabs are disabled, select **Turn on Q&A** first.
2. On the **Simplify data schema** tab, keep only the fields that AI should use:
   - **Customer:** Customer Name, Customer Type, City, Country, Sales Region, Key Account
   - **Product:** Product Name, Brand, Therapeutic Area, Formulation, Launch Date
   - **Date:** Date, Year, Quarter, Year Quarter, Month Name, Year Month, Month Start
   - **Sales:** Channel and all measures

   ([AI data schema](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-data-schema))
3. On the **Add AI instructions** tab, paste the text from [ai-instructions.md](ai-instructions.md) ([AI instructions](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-instructions)).
4. Select **Apply**. Changes can take a few minutes to reach Copilot.

## Step 7 – Create the report with Copilot

1. In the model editor, select **New report** on the ribbon. The report canvas opens in a new tab.
2. Select **Copilot** and paste the report prompt from [copilot-prompts.md – step 7](copilot-prompts.md#step-7--copilot-in-the-report). Review the page, then refine it with a follow-up prompt ([Create reports with Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-create-reports)).
3. Select **File** > **Save**. Name the report `P07_Sales_Report`, save it in **ContosoPharma_Workshop**, and move it to your folder **P07**.
4. **Verified answer:** stay in edit mode and select the **Net Sales by Therapeutic Area** chart. Select **…** > **Set up a verified answer**. Add these trigger phrases:
   - *Which therapeutic area sells the most?*
   - *Net sales by therapeutic area*
   - *Show sales by TA*
   - *Compare therapeutic areas by revenue*
   - *What is our biggest therapeutic area?*

   Select **Apply** ([Verified answers](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-verified-answers)).

> Copilot report creation needs the model's **Q&A** switch on. It doesn't work if implicit measures are disabled. Copilot can't apply styling or formatting changes ([Create reports with Copilot – limitations](https://learn.microsoft.com/power-bi/create-reports/copilot-create-reports#considerations-and-limitations)).

## Step 8 – AI visuals

Add a page named **AI insights**.

### 8.1 Anomaly detection

1. Add a **Line chart**: **X-axis** = Date > **Month Start**, **Y-axis** = **Net Sales**.
2. In **Filters on this visual**, set **Country** = *Germany* and **Product Name** = *Zentora 100 mg tablets*.
3. With the chart selected, open **Analytics** in the **Visualizations** pane, then **Anomalies** > **Add**.
4. Select the May 2026 point. The **Anomalies** pane explains the possible causes. Add **Customer Type**, **Channel** and **City** to **Explain by**.

✅ **Check:** May 2026 is flagged below the expected range, and July 2026 above it.

Anomaly detection works only on line charts with a date axis, no legend and at least four points. It can't be combined with a forecast ([Anomaly detection](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-anomaly-detection)).

### 8.2 Forecast

1. Add another line chart, **Month Start** × **Net Sales**, filtered to **Brand** = *Viraquel* (an antiviral with winter peaks).
2. Select **Analytics** > **Forecast** > on. Set **Forecast length** to 6 months and select **Apply** ([Analytics pane – forecast](https://learn.microsoft.com/power-bi/transform-model/desktop-analytics-pane#forecast)).

### 8.3 Key influencers – what drives discounts?

1. Add a **Key influencers** visual:
   - **Analyze:** **Discount %**
   - **Explain by:** **Channel**, **Customer Type**, **Sales Region**, **Key Account**, **Therapeutic Area**
   - **Expand by:** **Customer Name**
2. Read the **Key influencers** tab, then the **Top segments** tab.

✅ **Check:** **Channel** = *Tender* is the strongest influencer of a higher discount.

For a measure, the analysis runs at the level of the **Explain by** and **Expand by** fields ([Key influencers](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-influencers#analyze-a-metric-that-is-a-measure-or-a-summarized-column)).

### 8.4 Decomposition tree – where do sales come from?

1. Add a **Decomposition tree**:
   - **Analyze:** **Net Sales**
   - **Explain by:** **Sales Region**, **Country**, **Therapeutic Area**, **Brand**, **Channel**, **Customer Type**
2. Select **+** next to **Net Sales**, then **High value**. The lightbulb marks an AI split. Continue for 2–3 levels, then try **Low value** on a node ([Decomposition tree](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-decomposition-tree)).

### 8.5 Narrative with Copilot (if time allows)

1. In **Visualizations**, select **Narrative**. It opens in Copilot mode.
2. Use the prompt from [copilot-prompts.md – step 8](copilot-prompts.md#step-8--narrative-visual-with-copilot) and select **Create** ([Narrative visual with Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-create-narrative)).

Save the report.

> **Q&A** is being retired. Microsoft recommends Copilot instead ([Q&A for business users](https://learn.microsoft.com/power-bi/explore-reports/end-user-q-and-a)). This lab doesn't use the Q&A visual.

**Bridge to Lab 2:** open the **Copilot** pane and ask the question from [copilot-prompts.md](copilot-prompts.md#bridge-to-lab-2--copilot-pane). The model shows *what* happened. The *why* (a stock-out after quality complaints) sits in lakehouse tables that aren't in the model. Lab 2 answers it.

## Step 9 – Secure and govern

1. **RLS role:** in the model editor, select **Manage roles** > **New**. Name it `DACH`. Under **Select tables**, choose **Customer**. Under **Filter data**, set **Sales Region** equals `DACH`. Select **Save** ([Edit semantic models – RLS](https://learn.microsoft.com/power-bi/transform-model/service-edit-data-models#define-row-level-security-roles-and-rules)).
2. **Test the role:** in your folder, select **…** next to the model > **Security**. Then select **…** next to **DACH** > **Test as role**. The report shows DACH countries only. Select **Back to Row-Level Security**.
   > RLS restricts only users with the **Viewer** role. As a Contributor you normally see all data, so use **Test as role** ([Row-level security](https://learn.microsoft.com/fabric/security/service-admin-row-level-security)).
3. **Sensitivity label:** select **…** next to the model > **Settings** > **Sensitivity label**, and choose the label the instructor gives you. Reports created from the model inherit it ([Apply sensitivity labels](https://learn.microsoft.com/fabric/enterprise/powerbi/service-security-apply-data-sensitivity-labels), [Information protection](https://learn.microsoft.com/fabric/governance/information-protection)).
4. **Endorse:** in the model **Settings**, expand **Endorsement**, select **Promoted**, then **Apply** ([Endorse content](https://learn.microsoft.com/power-bi/collaborate-share/service-endorse-content)).
5. **Instructor demo:**
   - **Audit trail:** Microsoft Purview Audit shows `ApplyChangeToPowerBIModel`, `SensitivityLabelApplied` and `CopilotInteraction` records for this lab ([Operation list](https://learn.microsoft.com/fabric/admin/operation-list)).
   - **DLP policy tip** on a semantic model, if the instructor configured a policy ([DLP for Fabric](https://learn.microsoft.com/purview/dlp-powerbi-get-started)).
   - The model setting **Allow any person with only read permissions to use AI…** ([Use Copilot with semantic models](https://learn.microsoft.com/power-bi/create-reports/copilot-semantic-models)).

   More in [governance/README.md](../governance/README.md).

## Wrap-up

Go through the [best-practices checklist](best-practices-checklist.md). In Lab 2 you build a data agent on `P07_Sales_Model` and two lakehouse tables.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| No **Copilot** button | The workspace must be on a paid F2+ or P1+ capacity, with Copilot enabled by the admin. Use the manual fallback and continue ([Copilot overview](https://learn.microsoft.com/power-bi/create-reports/copilot-introduction)) |
| **LH_ContosoPharma** isn't listed in the OneLake catalog | Ask the instructor to check that you're a Contributor in **ContosoPharma_Workshop** |
| The model editor doesn't open after **OK** | Allow pop-ups for the Fabric portal, then open the model from your folder with **…** > **Open data model** |
| The model opens read-only | Switch from **Viewing** to **Editing** at the top right |
| **Prep data for AI** tabs are disabled | Select **Turn on Q&A** |
| Copilot can't create a report page | Turn the model's Q&A switch on, and don't disable implicit measures |
| **Anomalies** is unavailable | Remove any legend or second measure. The X-axis must be a date |
| You broke the model | **File** > **Version history** > restore, or continue with `REF_Sales_Model` in the folder **REF** |
