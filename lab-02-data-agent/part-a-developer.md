# Part A – Developer: create, configure, test and publish

**Time:** 55 minutes. Replace `P07` with your ID.

| Step | What you do | Min |
| --- | --- | ---: |
| [A1](#a1-create-the-agent) | Create the agent | 5 |
| [A2](#a2-add-the-lakehouse-tables) | Add the lakehouse tables | 5 |
| [A3](#a3-generate-the-lakehouse-configuration-with-build-agent-with-ai) | Generate the lakehouse configuration with Build agent with AI | 10 |
| [A4](#a4-add-the-semantic-model) | Add the semantic model | 5 |
| [A5](#a5-add-the-agent-instructions) | Add the agent instructions | 5 |
| [A6](#a6-test-and-inspect) | Test and inspect | 15 |
| [A7](#a7-publish-and-share) | Publish and share | 5 |
| [A8](#a8-mcp-and-automation) | MCP and automation (demo, optional hands-on) | 5 |

> **Order matters.** You add the lakehouse first and the semantic model second. **Build agent with AI** works only while the agent has SQL or Eventhouse sources. Once a semantic model is attached, that mode is unavailable ([Build agent with AI](https://learn.microsoft.com/fabric/data-science/data-agent-creator-agent-overview)).

## A1. Create the agent

1. Open **ContosoPharma_Workshop** and your folder **P07**.
2. Select **+ New item**. On the **All items** tab, search for **Fabric data agent** and select it.
3. Enter the name `P07_Sales_Agent` and create it.

✅ The agent opens and the **OneLake catalog** appears so you can add a data source ([Create a data agent](https://learn.microsoft.com/fabric/data-science/how-to-create-data-agent)).

## A2. Add the lakehouse tables

1. In the OneLake catalog, select **LH_ContosoPharma**, the shared lakehouse from the folder **00_Shared**, then **Add**.
2. In the **Explorer**, expand the lakehouse. Select only `inventory_weekly` and `quality_complaints`, and clear everything else.

Select only the objects the agent needs. A focused schema means better routing and better queries ([Configure your data agent – schema selection](https://learn.microsoft.com/fabric/data-science/data-agent-configurations#data-agent-schema-selection)).

## A3. Generate the lakehouse configuration with Build agent with AI

*Preview.*

1. Select **Build agent with AI** on the ribbon.
2. Paste this prompt:

   ```text
   I'm building an agent that explains changes in sales with stock and quality data.
   Explore the schema of inventory_weekly and quality_complaints and summarize the key columns.
   Then propose a data source description, data source instructions, and 3 example queries for:
   complaints per batch in the last 90 days, products with the lowest days of supply last week,
   and average days to close a complaint by category in 2026.
   ```

3. Ask it to run one of the example queries to check the result. Review the proposal, then select **Accept**. Accepting replaces any existing configuration of the same type.
4. Select **Test data agent** to switch back to test mode.

**Fallback** (if the mode isn't available): copy the description, instructions and example queries from [config/lakehouse-datasource.md](config/lakehouse-datasource.md). Add example queries with **Example queries** > **Add or Edit Example Queries**. Only queries that pass validation are used ([Example queries](https://learn.microsoft.com/fabric/data-science/data-agent-example-queries)).

## A4. Add the semantic model

1. In the **Explorer**, select **+ Data source**. Select `P07_Sales_Model`, or `REF_Sales_Model` from the folder **REF** if you skipped Lab 1, then **Add**.
2. Select the tables **Sales**, **Customer**, **Product** and **Date**. Use the same fields you kept in the AI data schema in Lab 1.

For semantic models, the agent doesn't support data source instructions, descriptions or example queries. It uses the model's **Prep for AI** settings instead: the AI data schema, AI instructions and verified answers from Lab 1 ([Semantic model best practices](https://learn.microsoft.com/fabric/data-science/semantic-model-best-practices), [Add data sources](https://learn.microsoft.com/fabric/data-science/data-agent-add-datasources)).

## A5. Add the agent instructions

1. Select **Data agent instructions**.
2. Paste the text from [config/agent-instructions.md](config/agent-instructions.md). Replace `<SALES_MODEL>` with the model you attached (`P07_Sales_Model` or `REF_Sales_Model`). The limit is 15,000 characters.

These instructions control routing between the two sources, shared terminology and the answer format. They don't change the DAX that's generated for the model ([Configure your data agent](https://learn.microsoft.com/fabric/data-science/data-agent-configurations#data-agent-instructions)).

## A6. Test and inspect

1. Ask these five questions one at a time. Select **Clear chat** before each one, so an earlier answer doesn't influence the next:

   | # | Question | Expected source |
   | --- | --- | --- |
   | 1 | What were total net sales in 2025? | Semantic model |
   | 2 | How many quality complaints were received for Zentora 100 mg tablets in Germany in April 2026? | Lakehouse |
   | 3 | Show monthly net sales of Zentora 100 mg tablets in Germany in 2026 as a line chart. | Semantic model, chart |
   | 4 | Why did net sales of Zentora 100 mg tablets in Germany drop in May 2026? | Both |
   | 5 | How are we doing in DACH? | Should ask a clarifying question |

2. For each answer, open the **run steps**. Check which source the agent chose, the SQL or DAX it generated, and, for the lakehouse, which example queries it used ([Example queries – run steps](https://learn.microsoft.com/fabric/data-science/data-agent-example-queries)).
3. Fix one weak answer, test again, and note the change:
   - wrong source → improve the agent instructions or the lakehouse description
   - wrong SQL → add or fix an example query
   - wrong DAX → fix the AI instructions or add a verified answer in the model
4. Optional: switch the agent to the **preview runtime** and ask question 4 again. The preview runtime adds Advanced NL2SQL and Advanced DAX generation. A published agent keeps the runtime it had when you published it ([Data agent runtime](https://learn.microsoft.com/fabric/data-science/data-agent-runtime)).
5. Use **Diagnostics** to download the details of an answer, and **Clear chat** to start over. Conversation history is kept for up to 28 days unless it's cleared ([Data agent tenant settings](https://learn.microsoft.com/fabric/data-science/data-agent-tenant-settings)).

✅ Expected answers: 1 = EUR 293.8 M, 2 = 43 complaints. Question 4 should mention the stock-out from week ending 3 May to 14 June 2026, and the packaging complaints on batch ZT100-2603B.

## A7. Publish and share

1. Select **Publish**. Paste the description from [config/agent-instructions.md](config/agent-instructions.md#agent-description-used-when-you-publish).
2. You now have a **published** version (what users query) and a **draft** that you keep editing. You can switch between them to compare answers ([Publish and share data agents](https://learn.microsoft.com/fabric/data-science/data-agent-sharing)).
3. Share the agent with your partner and choose a permission:

   | Option | The user can |
   | --- | --- |
   | No extra permission | Query the **published** version only |
   | **View details** | Also see the configuration of the draft and published versions |
   | **Edit and view details** | Also change the configuration. Use this for power users who co-author it |

   For this exercise, choose **View details**.

   > In this workshop every participant is a Contributor in the workspace. That role already allows editing every item, so the share options don't restrict your partner. They apply to people **without a workspace role**, which is how real business users get access. The instructor shows this in the governance demo with a test account.

Users also need access to every source behind the agent: **Read** on the semantic model, and **Read** on the lakehouse item. Because the model is Direct Lake, they also need **ReadAll** on the lakehouse. RLS and CLS still apply. In this workshop, every participant already has this access as a Contributor ([Direct Lake security](https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#permission-requirements)).

## A8. MCP and automation

*The instructor demos this. You can try it later with [mcp/README.md](mcp/README.md).*

| Task | How | Status |
| --- | --- | --- |
| Use the agent from VS Code, GitHub Copilot or any MCP client | Agent **Settings** > **Model Context Protocol** > copy the **MCP server URL** or download `mcp.json` | Available ([Data agent MCP server](https://learn.microsoft.com/fabric/data-science/data-agent-mcp-server)) |
| Read the agent's configuration as code | Fabric Core MCP server: `search_catalog` and `get_item_definition` | Available ([Core MCP tools](https://learn.microsoft.com/rest/api/fabric/articles/mcp-servers/core-remote/tools-core-mcp-server)) |
| Create or update the agent from code | REST item definition, Fabric data agent Python SDK, or Git integration | Definition: available. SDK and Git: preview ([Definition](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/data-agent-definition), [SDK](https://learn.microsoft.com/fabric/data-science/fabric-data-agent-sdk), [Git](https://learn.microsoft.com/fabric/data-science/data-agent-source-control)) |
| Run the test set in batch | [notebooks/evaluate_data_agent.ipynb](notebooks/evaluate_data_agent.ipynb) | Preview ([Evaluate your data agent](https://learn.microsoft.com/fabric/data-science/evaluate-data-agent)) |

Continue with [Part B – Business user](part-b-business-user.md).
