# Data agent and MCP

Three developer tasks: **use** the agent from an MCP client, **read** its configuration as code, and **create or change** it from code.

## 1. Use the agent from VS Code (data agent MCP server)

A published data agent is also a remote MCP server with a single tool. Any client that supports MCP over Streamable HTTP with a Fabric token can call it ([Data agent MCP server](https://learn.microsoft.com/fabric/data-science/data-agent-mcp-server)).

1. **Publish** the agent (Lab 2, step A7).
2. Open the agent's **Settings** > **Model Context Protocol**. Copy the **MCP server URL**, or download **mcp.json**. The URL has this format:
   `https://api.fabric.microsoft.com/v1/mcp/workspaces/{WorkspaceId}/dataagents/{DataAgentId}/agent`
3. In VS Code, open a folder, create `.vscode/mcp.json`, select **Add Server** > **HTTP**, paste the URL and enter a name such as `p07-sales-agent`.
4. Select **Allow** and sign in with your work account.
5. Open GitHub Copilot Chat in **Agent** mode and ask:

   ```text
   Using the p07-sales-agent tool: which batch had the most quality complaints in 2026, and in which country?
   ```

The agent runs as you, so your RLS and source permissions apply. Long-running requests are supported through MCP tasks. Answers returned to a client outside Fabric may leave Fabric's compliance boundary ([Data agent tenant settings](https://learn.microsoft.com/fabric/data-science/data-agent-tenant-settings)).

## 2. Read the agent's configuration as code (Fabric Core MCP server)

The remote Fabric Core MCP server maps Fabric REST operations to MCP tools, including `search_catalog`, `get_item_definition` and `update_item_definition` ([Core MCP tools](https://learn.microsoft.com/rest/api/fabric/articles/mcp-servers/core-remote/tools-core-mcp-server)).

1. In VS Code: **Ctrl+Shift+P** > **MCP: Add Server** > **HTTP** > `https://api.fabric.microsoft.com/v1/mcp/core`, then name it `fabric` ([Get started with Core MCP](https://learn.microsoft.com/rest/api/fabric/articles/mcp-servers/core-remote/get-started-core)).
2. In Agent mode, ask:

   ```text
   Find the data agent P07_Sales_Agent in the workspace ContosoPharma_Workshop.
   Get its item definition, decode the parts, and show me:
   1) the agent instructions from the draft stage_config.json,
   2) the data sources and the tables selected in each,
   3) the example queries.
   Don't change anything.
   ```

The definition is a set of JSON parts:

- `Files/Config/data_agent.json`
- `Files/Config/draft/stage_config.json` (agent instructions)
- one folder per data source, with `datasource.json` and `fewshots.json`
- after publishing, a `published/` copy and `publish_info.json` (the description)

Source: [Data agent definition](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/data-agent-definition).

> Review every tool call before you approve it. Some Core MCP tools create items or change permissions ([Get started with Core MCP](https://learn.microsoft.com/rest/api/fabric/articles/mcp-servers/core-remote/get-started-core)).

## 3. Create or change the agent from code

| Option | When to use it | Notes |
| --- | --- | --- |
| **Fabric UI** | Building and testing interactively | What this lab uses |
| **REST API with an item definition** | Scripted creation, copying an agent | An update must include all required parts, not a partial patch ([Data agent definition](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/data-agent-definition)) |
| **Fabric data agent Python SDK** (preview) | Create, configure and publish from a notebook | `fabric-data-agent-sdk` ([SDK](https://learn.microsoft.com/fabric/data-science/fabric-data-agent-sdk)) |
| **Git integration and deployment pipelines** (preview) | Version control and dev → test → prod | Instructions, data source selection and example queries are stored as files ([Source control](https://learn.microsoft.com/fabric/data-science/data-agent-source-control)) |
| **Fabric Core MCP** `create_item` | Creating items by prompting an AI assistant | Check the item types the tool supports in your MCP client. At the time of writing, its list didn't include data agents. Use the options above to create an agent, and the MCP tools to inspect it |

## Files

- [mcp.json](mcp.json): VS Code template with both servers. Replace the placeholders with your IDs.
