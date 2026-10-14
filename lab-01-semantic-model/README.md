# Lab 1 – Build a semantic model on the shared lakehouse and an AI-powered report

**Time:** 120 minutes · **Level:** beginner · **Tools:** browser only

You build a star-schema semantic model on the shared lakehouse, entirely in the Fabric portal. Copilot helps at every step. Then you create a report and use Power BI's AI visuals to find why sales dropped.

The model uses **Direct Lake**: it reads the lakehouse tables in place, with no copy. Everyone builds their own model on the same data.

![Lab 1 flow: shared lakehouse, Direct Lake, semantic model P07_Sales_Model, report P07_Sales_Report. Lab steps 1 to 9 under each stage. Copilot helps at steps 4, 5, 7 and 8.](../docs/images/use-case-1-semantic-model.png)

| Step | What you do | Min |
| --- | --- | ---: |
| 0 | Welcome, your ID, naming rules | 10 |
| [1](#step-1--explore-the-data) | Explore the data | 5 |
| [2](#step-2--create-the-semantic-model) | Create the semantic model | 15 |
| [3](#step-3--tables-relationships-and-date-table) | Tables, relationships and date table | 10 |
| [4](#step-4--measures-with-dax-query-view-and-copilot) | Measures with DAX query view and Copilot | 15 |
| [5](#step-5--clean-up-the-model-with-copilot) | Clean up the model with Copilot | 10 |
| [6](#step-6--prep-data-for-ai) | Prep data for AI | 10 |
| [7](#step-7--create-the-report-by-hand-then-with-copilot) | Create the report by hand, then with Copilot; add a verified answer | 15 |
| [8](#step-8--ai-visuals) | AI visuals: anomalies, forecast, key influencers, decomposition tree | 10 |
| [9](#step-9--secure-and-govern) | Secure and govern | 10 |
| – | [Wrap-up](#wrap-up): checklist, Lab 2 preview, questions | 10 |

## Before you start

- You have your participant ID, for example `P07`. Replace `P07` with your ID everywhere in this guide.
- You're a Contributor in the workspace **ContosoPharma_Workshop**. Its folder **00_Shared** holds the shared lakehouse **LH_ContosoPharma** that everyone builds on.
- You have read the [naming rules](../docs/naming-and-etiquette.md).

Files used in this lab: [measures.dax](measures.dax) · [measures-time-intelligence.dax](measures-time-intelligence.dax) (fallback) · [copilot-prompts.md](copilot-prompts.md) · [ai-instructions.md](ai-instructions.md) · [expected-values.csv](expected-values.csv) · [best-practices-checklist.md](best-practices-checklist.md)

---

## Step 1 – Explore the data

1. Go to <https://app.fabric.microsoft.com> and open the workspace **ContosoPharma_Workshop**.

   ![Workshop workspace with the folders 00_Shared, GOV, P01, P02 and REF](../docs/images/ui/lab1-01-workspace.png)

2. Open the folder **00_Shared**, then the lakehouse **LH_ContosoPharma**.
3. In the **Explorer**, expand **Tables**. Select `fact_sales` to preview the rows. Then look at `dim_customer`, `dim_product` and `dim_date`.

   ![Lakehouse explorer with the six tables and a preview of fact_sales](../docs/images/ui/lab1-02-lakehouse-tables.png)

> Look, don't change: everyone builds on this lakehouse. Don't rename, delete or load anything here.

✅ **Check:** you see 6 tables. Lab 1 uses the 4 tables `fact_sales`, `dim_customer`, `dim_product` and `dim_date`. The other two are for Lab 2.

> **Why this design:** `fact_sales` holds the numbers. The `dim_` tables describe them (who, what, when). That is a **star schema**, the recommended shape for Power BI models ([Star schema](https://learn.microsoft.com/power-bi/guidance/star-schema)).

## Step 2 – Create the semantic model

1. In the workspace, open your folder **P07**.
2. Select **+ New item** > **All items**, type **Semantic model** in the filter and select the tile **Semantic model**.

   ![New item panel filtered to Semantic model](../docs/images/ui/lab1-03-new-item-semantic-model.png)

3. On **Add data to start building a report**, select **OneLake catalog**. Search for `ContosoPharma`, select **LH_ContosoPharma**, then select **Connect**. Don't select `LH_Customer_Finance`: it belongs to the trainer's DLP demo.

   ![OneLake catalog with the lakehouse LH_ContosoPharma](../docs/images/ui/lab1-04-onelake-catalog.png)

4. In **Choose tables from OneLake**, enter `P07_Sales_Model` as **Direct Lake semantic model name**. Check that **Workspace** is **ContosoPharma_Workshop**.
5. Select the tables `dim_customer`, `dim_date`, `dim_product` and `fact_sales`. Leave `inventory_weekly` and `quality_complaints` unselected. Select **Confirm**.

   ![Choose tables from OneLake with the model name, the workspace and the four tables selected](../docs/images/ui/lab1-05-new-semantic-model-dialog.png)

6. The model opens in the web model editor after about 30 seconds. If nothing opens, allow pop-ups for the Fabric portal and try again.
7. The new model is saved in the workspace root, not in your folder. In the workspace, select **…** next to `P07_Sales_Model` > **Move to** > **P07** > **Move here**.

✅ **Check:** select the `fact_sales` table. In **Properties** > **Advanced**, **Storage mode** is **Direct Lake**.

> **Why Direct Lake:** the model reads the Delta tables in OneLake directly. It doesn't copy the data, and it doesn't need a scheduled refresh: changes in the lakehouse appear in the model automatically. Queries run in the same in-memory engine as Import mode, so reports stay fast ([Direct Lake overview](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview)).

Learn more: [Direct Lake in web modeling](https://learn.microsoft.com/fabric/fundamentals/direct-lake-web-modeling)

## Step 3 – Tables, relationships and date table

1. At the top right, select **Viewing** > **Editing** (*Make any changes*). The editor remembers this choice the next time you open the model.
   > Changes in the web editor save automatically and can't be undone. Version history keeps the last five versions ([Version history](https://learn.microsoft.com/power-bi/transform-model/service-semantic-model-version-history)).
2. Rename the tables: select a table in the **Data** pane, then in **Properties** > **General** > **Name**, type the new name and press **Enter**. Each change takes a few seconds to save: wait until the new name shows in the **Data** pane before you rename the next table. If a name doesn't change, enter it again.

   | Old name | New name |
   | --- | --- |
   | `fact_sales` | `Sales` |
   | `dim_customer` | `Customer` |
   | `dim_product` | `Product` |
   | `dim_date` | `Date` |

3. On the **Home** ribbon, select **Manage relationships** > **New relationship**. For each row of the table below:
   1. **From table**: select `Sales`, then select the column header of the key column in the grid below it.
   2. **To table**: select the dimension table, then select its key column header.
   3. Check **Cardinality** = **Many to one (\*:1)** and **Cross-filter direction** = **Single**.
   4. Select **Assume referential integrity**. It's not selected by default. Wait until **Validating …** disappears, then select **Save**.

   | From table, column | To table, column |
   | --- | --- |
   | `Sales`, `customer_key` | `Customer`, `customer_key` |
   | `Sales`, `product_key` | `Product`, `product_key` |
   | `Sales`, `order_date` | `Date`, `date` |

   ![New relationship dialog: Sales product_key to Product product_key, many to one, single, Assume referential integrity selected](../docs/images/ui/lab1-06-new-relationship.png)

   *A preview of this table isn't available* is normal for Direct Lake. The info note under the options says that Direct Lake doesn't validate cardinality and cross-filter direction, so check both yourself ([Direct Lake overview – limitations](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#considerations-and-limitations)). The lakehouse has no relationships, so you create them yourself.

   ![Manage relationships with the three active relationships](../docs/images/ui/lab1-07-relationships-done.png)

4. In the **Data** pane, right-click **Date** > **Mark as date table**. Turn on **Mark as a date table**, choose the date column `date`, wait for **Validated successfully**, then select **Save** ([Mark as date table](https://learn.microsoft.com/power-bi/transform-model/desktop-date-tables)).

   ![Mark as a date table dialog with the date column validated](../docs/images/ui/lab1-07b-mark-date-table.png)

5. Select **File** > **Options**. On **Data Load**, under **Time intelligence**, clear **Auto date/time**, then select **OK**. It's on by default for a new model. Your Date table replaces the hidden automatic date tables ([Auto date/time guidance](https://learn.microsoft.com/power-bi/guidance/auto-date-time), [Date tables](https://learn.microsoft.com/power-bi/guidance/model-date-tables)).

   ![Options, Data Load, with Auto date/time cleared](../docs/images/ui/lab1-07c-options-auto-date.png)

✅ **Check:** the diagram shows **Sales** with three many-to-one lines to **Customer**, **Product** and **Date**. On the **Date** card in the diagram, the `date` column shows a calendar icon.

> **Why these rules**
>
> | Rule | Why |
> | --- | --- |
> | Star schema | Dimensions (Customer, Product, Date) filter and group, the fact table (Sales) is summarized. Simple for people and for AI ([Star schema](https://learn.microsoft.com/power-bi/guidance/star-schema)) |
> | Many-to-one | Each customer, product and date appears once in its dimension. Filters flow from the one side to the many side and totals add up without double counting ([Model relationships](https://learn.microsoft.com/power-bi/transform-model/desktop-relationships-understand)). Direct Lake also requires unique values on the one side ([Direct Lake – limitations](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#considerations-and-limitations)) |
> | Single direction | Filters flow from the dimension to the fact only: predictable and fast. Filters in both directions can create ambiguous paths and slower queries ([Bi-directional relationship guidance](https://learn.microsoft.com/power-bi/guidance/relationships-bidirectional-filtering)) |
> | Assume referential integrity | Every key in Sales exists in Customer, Product and Date. The engine then uses inner joins, and slicers don't show an extra **(Blank)** item. In Fabric you can only set this in the browser ([Assume referential integrity](https://learn.microsoft.com/power-bi/connect-data/desktop-assume-referential-integrity), [Lakehouse tutorial – relationships](https://learn.microsoft.com/fabric/data-engineering/tutorial-lakehouse-build-report#define-table-relationships)) |
> | Marked date table | Time intelligence such as prior year and year-to-date needs one row per day without gaps, and every chart uses the same calendar ([Date tables](https://learn.microsoft.com/power-bi/guidance/model-date-tables)) |
> | Auto date/time off | Otherwise Power BI adds a hidden date table for every date column: a bigger model and inconsistent calendars ([Auto date/time guidance](https://learn.microsoft.com/power-bi/guidance/auto-date-time)) |

## Step 4 – Measures with DAX query view and Copilot

1. In a new browser tab, open your folder, select **…** next to `P07_Sales_Model`, then **Open in DAX query view**.

   ![DAX query view with Run, Update model with changes and Copilot](../docs/images/ui/lab1-08-dax-query-view.png)
2. Paste the whole content of [measures.dax](measures.dax) and select **Run**.
3. Select **Update model with changes**. This adds 8 measures to the **Sales** table. The `///` lines become the measure descriptions ([DAX query view](https://learn.microsoft.com/power-bi/transform-model/dax-query-view)).
4. **Copilot:** open a new query tab, press **Ctrl+I**, and use the two prompts from [copilot-prompts.md – step 4](copilot-prompts.md#step-4--copilot-in-dax-query-view). Select **Run**, then **Keep query**. Compare the DAX with the reference at the end of `measures.dax`, then select **Update model with changes** ([Write DAX queries with Copilot](https://learn.microsoft.com/dax/dax-copilot)).

   **No Copilot?** Paste [measures-time-intelligence.dax](measures-time-intelligence.dax) into a new tab, select **Run**, then **Update model with changes**.

✅ **Check:** for 2025, **Net Sales** = 293,801,286 and **Net Sales YoY %** = 10.0 %. All expected values are in [expected-values.csv](expected-values.csv).

> **Best practice:** use explicit measures for every number, and use **DIVIDE** for ratios ([DIVIDE vs /](https://learn.microsoft.com/dax/best-practices/dax-divide-function-operator)).

## Step 5 – Clean up the model with Copilot

*Copilot in web modeling is in preview: it works today, but it can still change before general availability.*

This isn't chatting with your data. Copilot in the model editor changes the model itself: names, hidden fields, sort order, formats, display folders and descriptions ([Copilot in web modeling](https://learn.microsoft.com/power-bi/transform-model/copilot-web-modeling)).

1. Go back to the model editor tab and refresh the browser. Switch from **Viewing** to **Editing** (top right). The **Copilot** button is disabled in Viewing mode.
2. Select **Copilot** on the ribbon. The Copilot pane opens on the right.
3. Send your first prompt. Copilot asks once per session for permission to change the model: *Allow Copilot to make changes during this chat session?* Select **Allow**. Copilot then saves a restore checkpoint in version history, so you can roll back everything it did in this session.

   ![Copilot pane asking: Allow Copilot to make changes during this chat session?](../docs/images/ui/lab1-09-copilot-permission.png)

4. Paste prompts **5a** to **5e** from [copilot-prompts.md](copilot-prompts.md#step-5--copilot-in-web-modeling-preview) one at a time. After each one, read the proposal and check the **Data** pane before you send the next:

   | Prompt | What it does | Check |
   | --- | --- | --- |
   | 5a Review | Lists issues by priority, changes nothing | A list, nothing changed |
   | 5b Rename | Business names from an exact mapping | Names like **Therapeutic Area** in the Data pane |
   | 5c Hide and sort | Hides keys and technical columns, sorts months, sets data categories | **Sales** shows only **Channel** and measures |
   | 5d Format | EUR and % formats, three display folders | Folders **Sales**, **Time intelligence**, **Volume and price** |
   | 5e Describe | Descriptions under 150 characters | Hover a field to see its description |

✅ **Check:** column names are readable (for example **Therapeutic Area**). The **Sales** table shows only **Channel** and measures in three folders. **Month Name** sorts January to December.

![Copilot review (prompt 5a): missing relationships and the unmarked date table found on a model before step 3](../docs/images/ui/lab1-10-copilot-review.png)

**If Copilot isn't available**, do the same by hand in **Properties** (about 10 minutes). Steps 6–8 need these names:

1. Rename the visible columns with the mapping in [prompt 5b](copilot-prompts.md#step-5--copilot-in-web-modeling-preview): every **Customer**, **Product** and **Date** column, plus `channel` → **Channel** in **Sales**.
2. Hide all other **Sales** columns and every key column. Search the **Data** pane for `key`, Ctrl+select the results, and set **Is hidden** to on.
3. Set **Sort by column** of **Month Name** to **Month Number**.
4. Format **Net Sales** as currency and **Discount %** as a percentage.

**If something goes wrong:** select **File** > **Version history** and restore the version from before the Copilot session.

## Step 6 – Prep data for AI

*Preview.*

**Why it matters:** every AI that answers from this model knows only what the model tells it. Report Copilot and the Lab 2 data agent generate DAX against this model, and Microsoft 365 Copilot grounds its answers in the same semantic models ([Copilot in Power BI and Fabric](https://learn.microsoft.com/fabric/iq/connectors/copilot-power-bi-fabric)). Names and descriptions (step 5) help. Prep data for AI adds what AI can't guess: your terms (GTN, DACH, TA), your default period, which fields to ignore, and approved answers. These settings are used everywhere Copilot in Power BI is available ([Prepare your data for AI](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai)), and a data agent's DAX generation uses only these settings, not the agent's own instructions ([Semantic model best practices](https://learn.microsoft.com/fabric/data-science/semantic-model-best-practices)).

> **See the difference:** after step 7, ask the report Copilot pane *What was GTN in DACH last year?* Ask it again after the AI instructions have taken effect. In our dry run, the data agent without these settings answered with a question: which year did "last year" mean?

1. In your folder, select `P07_Sales_Model` to open its details page. On the ribbon, select **Prep data for AI**. If the tabs are disabled, select **Turn on Q&A** first. The dialog opens on **Get started**, with three tasks.

   ![Prep data for AI: Get started with Simplify the data schema, Verified answers and Add AI instructions](../docs/images/ui/lab1-11-prep-data-for-ai.png)

2. On **Simplify the data schema**, keep only the fields that AI should use:
   - **Customer:** Customer Name, Customer Type, City, Country, Sales Region, Key Account
   - **Product:** Product Name, Brand, Therapeutic Area, Formulation, Launch Date
   - **Date:** Date, Year, Quarter, Year Quarter, Month Name, Year Month, Month Start
   - **Sales:** Channel and all measures

   ([AI data schema](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-data-schema))

   ![Simplify the data schema with the four tables](../docs/images/ui/lab1-13-ai-data-schema.png)

3. On **Add AI instructions**, paste the text from [ai-instructions.md](ai-instructions.md). The counter shows about 1,300 of 10,000 characters ([AI instructions](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-instructions)).

   ![Add AI instructions with the workshop text pasted](../docs/images/ui/lab1-12-ai-instructions.png)

4. Select **Apply**. Changes can take a few minutes to reach Copilot.

## Step 7 – Create the report by hand, then with Copilot

You build the overview page by hand first (7a), then ask Copilot for the same page (7b). That way you know what a good page looks like and can judge what Copilot builds.

### 7a. Build the overview page yourself

1. In the model editor, select **New report** on the ribbon. The report canvas opens in a new tab, in edit mode.
2. **Cards:** in the **Visualizations** pane select **Card**, then select **Net Sales** in the **Data** pane. Add two more cards for **Net Sales YoY %** and **Discount %** ([Card visuals](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-card)).
3. **Line chart:** **X-axis** = **Month Start**, **Y-axis** = **Net Sales**.
4. **Clustered bar chart:** **Y-axis** = **Therapeutic Area**, **X-axis** = **Net Sales**. Copy it and replace **Therapeutic Area** with **Country**.
5. **Slicer:** **Year** ([Slicers](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-slicers)).
6. Rename the page **Sales overview**. Select **File** > **Save**. Name the report `P07_Sales_Report`, save it in **ContosoPharma_Workshop**, and move it to your folder **P07**.

✅ **Check:** with **2025** selected in the slicer, **Net Sales** shows 293.8 M.

![The finished Sales overview page in REF_Sales_Report: three cards, a monthly trend, and bars by therapeutic area and country](../docs/images/ui/lab1-14-report-overview.png)

### 7b. Ask Copilot for the same page, then compare

1. Select **Copilot** and paste the report prompt from [copilot-prompts.md – step 7](copilot-prompts.md#step-7--copilot-in-the-report). Copilot builds a new page ([Create reports with Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-create-reports)).
2. Compare it with your page: same visuals, same numbers, better or worse layout? Keep the better page and delete the other.
3. Refine with a follow-up prompt, for example a different chart type or sort order.
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

> **In the workshop (10 minutes):** build 8.1 and 8.3. Your instructor demonstrates 8.2 and 8.4; try them afterwards.

### 8.1 Anomaly detection

1. Add a **Line chart**: **X-axis** = Date > **Month Start**, **Y-axis** = **Net Sales**.
2. In **Filters on this visual**, set **Country** = *Germany* and **Product Name** = *Zentora 100 mg tablets*.
3. With the chart selected, open **Analytics** in the **Visualizations** pane, then **Anomalies** > **Add**.
4. Select the May 2026 point. The **Anomalies** pane explains the possible causes. Add **Customer Type**, **Channel** and **City** to **Explain by**.

✅ **Check:** May 2026 is flagged below the expected range, and July 2026 above it.

![Line chart with anomaly detection on: May 2026 flagged](../docs/images/ui/lab1-15-anomalies-on.png)

Anomaly detection works only on line charts with a date axis, no legend and at least four points. It can't be combined with a forecast ([Anomaly detection](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-anomaly-detection)).

### 8.2 Forecast

1. Add another line chart, **Month Start** × **Net Sales**, filtered to **Brand** = *Viraquel* (an antiviral with winter peaks).
2. Select **Analytics** > **Forecast** > on. Set **Forecast length** to 6 months and select **Apply** ([Analytics pane – forecast](https://learn.microsoft.com/power-bi/transform-model/desktop-analytics-pane#forecast)).

   ![Viraquel net sales with the forecast turned on](../docs/images/ui/lab1-16-forecast-on.png)

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

1. **RLS role:** in the model editor (**Editing**), select **Manage roles** on the **Home** ribbon. In **Manage security roles** > **Create**:
   1. Under **Roles**, select **+ New**. Select **…** next to **Untitled** > **Rename**, and enter `DACH`.
   2. Under **Tables**, select **Customer**.
   3. Under **Rules**, select **+ New**: **Column** = **Sales Region**, **Condition** = **Equals**, **Value** = `DACH`.
   4. Select **Save** ([Edit semantic models – RLS](https://learn.microsoft.com/power-bi/transform-model/service-edit-data-models#define-row-level-security-roles-and-rules)).

   ![Manage security roles with the role DACH, the table Customer and the rule sales_region equals DACH](../docs/images/ui/lab1-17-rls-role.png)

2. **Test the role (instructor demo):** on a new Direct Lake model, **Test as role** shows *Not supported – Test as role does not work with Single Sign-On (SSO)*. By default, Direct Lake reads OneLake with the identity of the person who runs the query (SSO).

   ![Not supported: Test as role does not work with Single Sign-On (SSO)](../docs/images/ui/lab1-18-test-as-role-sso.png)

   The instructor shows the production pattern on `REF_Sales_Model`. The model reads the lakehouse through a cloud connection with a fixed identity (the workspace identity), so report readers need no access to the lakehouse and can't bypass RLS there. **Test as role** works on this model, and a report reader in **DACH** sees only Germany, Austria and Switzerland. Steps: [governance/README.md – RLS that holds](../governance/README.md#rls-that-holds-fixed-identity) ([Integrate Direct Lake security](https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#data-access-rule-options), [Row-level security](https://learn.microsoft.com/fabric/security/service-admin-row-level-security#validate-the-role-within-the-power-bi-service)).
   > RLS restricts only users with the **Viewer** role or with access to the model or report alone. As a Contributor you always see all data.
3. **Sensitivity label:** open the workspace, select **…** next to `P07_Sales_Model` > **Settings**, then **<< Open settings page** at the bottom of the pane. Expand **Sensitivity label**, choose **Confidential**, then select **Apply**. Reports created from the model inherit the label ([Apply sensitivity labels](https://learn.microsoft.com/fabric/enterprise/powerbi/service-security-apply-data-sensitivity-labels), [Information protection](https://learn.microsoft.com/fabric/governance/information-protection)).

   ![Semantic model settings, Sensitivity label set to Confidential](../docs/images/ui/lab1-19-sensitivity-label.png)

4. **Endorse:** on the same settings page, expand **Endorsement and discovery**, select **Promoted**, then **Apply** ([Endorse content](https://learn.microsoft.com/power-bi/collaborate-share/service-endorse-content)). In the dry run, **Make discoverable** was turned on with it: people without access can then find the model and request access. Clear it if that isn't wanted ([Semantic model discoverability](https://learn.microsoft.com/power-bi/collaborate-share/service-discovery)).

   ![Endorsement and discovery with Promoted selected](../docs/images/ui/lab1-20-endorsement.png)

   > Use the full settings page. The side pane can show *These settings are turned off because you don't have the right permissions to change them* for these two settings, even for the model owner.
5. **Instructor demo:**
   - **Audit trail:** Microsoft Purview Audit shows `ApplyChangeToPowerBIModel`, `SensitivityLabelApplied` and `CopilotInteraction` records for this lab ([Operation list](https://learn.microsoft.com/fabric/admin/operation-list)).
   - **DLP policy tip** on the lakehouse `GOV/LH_Customer_Finance`, which holds synthetic bank account numbers: [governance/purview-demo.md](../governance/purview-demo.md) ([DLP for Fabric](https://learn.microsoft.com/purview/dlp-powerbi-get-started)).
   - The model setting **Copilot and Microsoft's MCP tools** (*Allow any person with only read permissions to use AI…*) under **Settings** > **Copilot** ([Use Copilot with semantic models](https://learn.microsoft.com/power-bi/create-reports/copilot-semantic-models)).

   More in [governance/README.md](../governance/README.md).

## Wrap-up

Go through the [best-practices checklist](best-practices-checklist.md). In Lab 2 you build a data agent on `P07_Sales_Model` and two lakehouse tables.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| No **Copilot** button | The workspace must be on a paid F2+ or P1+ capacity, with Copilot enabled by the admin. Use the manual fallback and continue ([Copilot overview](https://learn.microsoft.com/power-bi/create-reports/copilot-introduction)) |
| **LH_ContosoPharma** isn't listed in the OneLake catalog | Ask the instructor to check that you're a Contributor in **ContosoPharma_Workshop** |
| The model editor doesn't open after **Confirm** | Allow pop-ups for the Fabric portal, then open the model from the workspace with **…** > **Open semantic model** |
| The model opens read-only | Select **Viewing** > **Editing** at the top right |
| The **Year** slicer shows **(Blank)** | A relationship doesn't assume referential integrity, so Direct Lake keeps a blank member in the dimension. In the model, select **Manage relationships**, select the relationship, then **Edit**. Select **Assume referential integrity** and **Save**. Repeat for each relationship ([Assume referential integrity](https://learn.microsoft.com/power-bi/connect-data/desktop-assume-referential-integrity), [Model relationships](https://learn.microsoft.com/power-bi/transform-model/desktop-relationships-understand#relationship-evaluation)) |
| **Prep data for AI** tabs are disabled | Select **Turn on Q&A** |
| Copilot can't create a report page | Turn the model's Q&A switch on, and don't disable implicit measures |
| **Anomalies** is unavailable | Remove any legend or second measure. The X-axis must be a date |
| You broke the model | **File** > **Version history** > restore, or continue with `REF_Sales_Model` in the folder **REF** |
