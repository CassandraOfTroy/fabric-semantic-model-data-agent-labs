---
description: Review how AI-ready a Power BI semantic model is, using only the Fabric IQ MCP tools
---

You review a Power BI semantic model for AI readiness. Use only the FabricIQ MCP tools. Don't change anything.

Semantic model: ${input:model:Semantic model name, ID or browser URL}

1. Identify the model. For a URL or ID, call `ResolveFabricItem`. For a name, call `DiscoverArtifacts` and confirm that the result has exactly that name.
2. Call `GetSemanticModelSchema` without queries and read the full response.
3. Report what the model gives an AI agent, as a table with a status (✅ ⚠️ ❌) per row:
   - **AI data schema:** which tables, columns and measures are exposed. Flag technical fields (IDs, raw amounts, sort columns).
   - **Descriptions:** coverage of tables, columns and measures; descriptions over 200 characters.
   - **AI instructions:** present or not, length (limit 10,000), business terms, default period, rules for ambiguity. Check that every measure or column the instructions name exists.
   - **Verified answers:** how many, and their trigger questions.
   - **Model design:** date table, relationships, format strings, duplicate column names.
4. Call `ValueSearch` with 5 business terms from the AI instructions (for example a region, a channel, a brand). Report the column each resolves to and any close second match.
5. Answer these 5 test questions with the fabriciq workflow, and for each one show the measure, filters and period you used:
   - a question that uses a synonym from the AI instructions
   - a question without a period
   - a question that names a brand without the strength
   - a vague question, such as "How are we doing?"
   - a question about data that isn't in the model
6. Finish with the top 3 fixes, each mapped to where it's done: Prep data for AI > Simplify the data schema, Add AI instructions, verified answers on a report visual, or model descriptions.
