# Security and governance for both labs

What protects the semantic model, the report and the data agent, and how to show it in 10 minutes.

## 1. Access model

| Layer | In this workshop | Key fact | Source |
| --- | --- | --- | --- |
| Workspace roles | One workspace. Participants are **Contributors** | Contributors can create, change and delete any item in the workspace, including the shared lakehouse. Viewers can only read | [Roles in workspaces](https://learn.microsoft.com/fabric/fundamentals/roles-workspaces) |
| Semantic model through an agent | Read on the model | **Read** is enough to query a model through a data agent. Build or Write is needed only to change the model or use Prep for AI | [Publish and share data agents](https://learn.microsoft.com/fabric/data-science/data-agent-sharing) |
| Lakehouse behind the Direct Lake model | Contributor role in the workspace | A Direct Lake model reads the lakehouse as the signed-in user, so everyone who queries it needs **Read** and **ReadAll** on the lakehouse. Contributors have both; others get them by sharing the lakehouse with **Read all with Apache Spark** | [Direct Lake security](https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#permission-requirements), [Lakehouse sharing](https://learn.microsoft.com/fabric/data-engineering/lakehouse-sharing) |
| Lakehouse through an agent | Contributor role in the workspace | **Read** on the lakehouse item (and table access, if it's enforced) | [Publish and share data agents](https://learn.microsoft.com/fabric/data-science/data-agent-sharing) |
| Data agent sharing | Share with **View details** | Default: query the published version only. **View details**: see the configuration. **Edit and view details**: change it. These options apply to people without a workspace role; Admins, Members and Contributors can already edit every item | [Publish and share data agents](https://learn.microsoft.com/fabric/data-science/data-agent-sharing), [Roles in workspaces](https://learn.microsoft.com/fabric/fundamentals/roles-workspaces) |
| Copilot on a model | Default setting | **Allow any person with only read permissions to use AI (for example, Copilot, Microsoft's MCP tools) on this model and its related reports** is on by default. It covers Copilot, data agents and the remote MCP tools | [Use Copilot with semantic models](https://learn.microsoft.com/power-bi/create-reports/copilot-semantic-models) |

## 2. Row-level security

- Lab 1 creates the role `DACH` (Customer > Sales Region = DACH).
- **RLS restricts only users with the Viewer role.** It doesn't apply to Admins, Members or Contributors, so participants check their role with **Test as role** ([Row-level security](https://learn.microsoft.com/fabric/security/service-admin-row-level-security)).
- A data agent runs every query as the signed-in user and honors RLS and CLS ([Publish and share data agents](https://learn.microsoft.com/fabric/data-science/data-agent-sharing)).
- Lakehouse tables can be secured with OneLake security roles, including row and column rules ([OneLake security](https://learn.microsoft.com/fabric/onelake/security/data-access-control-model)). This lab doesn't configure them.
- With Direct Lake, model RLS protects the model, not the files: a user with **ReadAll** on the lakehouse can read every row through Spark or OneLake. For production, enforce the rules with OneLake security, or bind the model to a fixed-identity connection so users need no lakehouse access ([Direct Lake security](https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration)).

## 3. Sensitivity labels

- Apply a label to a model or report: **…** > **Settings** > **Sensitivity label** ([Apply sensitivity labels](https://learn.microsoft.com/fabric/enterprise/powerbi/service-security-apply-data-sensitivity-labels)).
- Manual labelling works for all Fabric items. **Downstream inheritance** is on by default: a report created from a labelled model gets the model's label. Inheritance from data sources currently works for Power BI semantic models only ([Information protection](https://learn.microsoft.com/fabric/governance/information-protection)).
- Sensitivity labels aren't applied to the AI interactions themselves (prompts and responses) in Copilot in Fabric ([Purview for Copilot in Fabric](https://learn.microsoft.com/purview/ai-copilot-fabric)).

## 4. Data loss prevention (DLP)

- Purview DLP policies for Fabric evaluate **semantic models** and **lakehouses** (and other items). Conditions are sensitivity labels and sensitive information types. Actions are a policy tip, alerts, and **Restrict access** (preview) ([DLP for Fabric](https://learn.microsoft.com/purview/dlp-powerbi-get-started)).
- DLP isn't supported for semantic models that use DirectQuery or a live connection. DLP evaluates a lakehouse whenever its data changes, so the workshop demo shows the policy tip on `LH_ContosoPharma` ([DLP for Fabric – limitations](https://learn.microsoft.com/purview/dlp-powerbi-get-started)).
- Data agents respect Purview DLP and access-restriction policies on their sources ([Data agent concepts](https://learn.microsoft.com/fabric/data-science/concept-data-agent)). DLP for the AI interactions themselves isn't supported for Copilot in Fabric ([Purview for Copilot in Fabric](https://learn.microsoft.com/purview/ai-copilot-fabric)).

## 5. Audit

| Action in the labs | Audit operation | Source |
| --- | --- | --- |
| Edit the model in the web | `ApplyChangeToPowerBIModel`, `GetPowerBIDataModel`, `ApplyQueriesExecution` | [Edit semantic models – audit](https://learn.microsoft.com/power-bi/transform-model/service-edit-data-models#viewing-audit-logs-and-activity-events) |
| Apply or change a label | `SensitivityLabelApplied`, `SensitivityLabelChanged` | [Operation list](https://learn.microsoft.com/fabric/admin/operation-list) |
| Use Copilot or a data agent | `CopilotInteraction` (prompt and response) | [Operation list](https://learn.microsoft.com/fabric/admin/operation-list), [Data agent audit](https://learn.microsoft.com/fabric/data-science/data-agent-purview-governance) |

Search them in the Microsoft Purview portal under **Audit**, or in DSPM **Activity explorer**.

## 6. DSPM for AI (Data Security Posture Management)

- **Scope:** Copilot for Power BI is supported (all prompts and text responses). Other Copilot experiences in Fabric, and **Fabric data agents**, are in **preview** ([Purview for Copilot in Fabric](https://learn.microsoft.com/purview/ai-copilot-fabric)).
- **Setup:**
  - DSPM setup task **Activate Microsoft Purview Audit**
  - setup task **Secure interactions in Microsoft Copilot experiences**
  - Fabric tenant setting **Allow Microsoft Purview to secure AI interactions**
  - **pay-as-you-go billing** for Purview, which managing these AI interactions requires ([Purview for Copilot in Fabric](https://learn.microsoft.com/purview/ai-copilot-fabric))

  Source: [Data agent audit](https://learn.microsoft.com/fabric/data-science/data-agent-purview-governance).
- **What's captured:** the user prompt and the agent response, as `CopilotInteraction` records in the unified audit log. Internal steps and backend queries aren't captured ([Data agent audit](https://learn.microsoft.com/fabric/data-science/data-agent-purview-governance)).
- **Also supported** for AI interactions: Insider Risk Management, Communication Compliance, eDiscovery and retention policies ([Purview for Copilot in Fabric](https://learn.microsoft.com/purview/ai-copilot-fabric)).

## 7. Tenant, residency and capacity settings

- **Users can use Copilot and other features powered by Azure OpenAI** is required for Copilot and data agents ([Data agent tenant settings](https://learn.microsoft.com/fabric/data-science/data-agent-tenant-settings)).
- With a capacity in the EU Data Boundary, Copilot data is processed in the EU, and the cross-geo settings aren't needed ([Copilot in Fabric – regions](https://learn.microsoft.com/fabric/fundamentals/copilot-fabric-overview#available-regions)).
- Data agent conversation history is kept for up to 28 days unless the user clears the chat ([Data agent tenant settings](https://learn.microsoft.com/fabric/data-science/data-agent-tenant-settings)).
- If a data agent is used from outside Fabric (Microsoft 365 Copilot, Copilot Studio, Foundry, MCP), its responses may leave Fabric's compliance boundary ([Data agent tenant settings](https://learn.microsoft.com/fabric/data-science/data-agent-tenant-settings)).
- A data agent can't query a source whose capacity is in a different region from the agent's capacity ([Data agent concepts](https://learn.microsoft.com/fabric/data-science/concept-data-agent)).
- A **Fabric Copilot capacity** bills the Copilot and data agent usage of chosen users to one capacity ([Fabric Copilot capacity](https://learn.microsoft.com/fabric/enterprise/fabric-copilot-capacity)).

## 8. Instructor demo script (10 minutes)

Prepare this the day before ([setup, step 6](../setup/README.md#6-prepare-the-security-demos)).

1. **RLS through the agent (3 min):** in an InPrivate window, sign in as the test user (member of role `DACH`, not a workspace member). Open `REF_Sales_Agent` and ask *"What were net sales in France in 2025?"*, then *"Show net sales by country for 2025."* Only Germany, Austria and Switzerland appear.
2. **Labels (1 min):** show the **Sensitivity** column in the workspace. Show that `REF_Sales_Report` inherited the model's label.
3. **Audit (3 min):** in Purview **Audit**, search the last 24 hours for `ApplyChangeToPowerBIModel` and `CopilotInteraction`. Use records from the dry run, because audit data isn't instant.
4. **DSPM for AI (2 min):** in **Activity explorer**, open one data agent interaction and show the prompt and the response.
5. **DLP (1 min, if configured):** show the policy tip on the lakehouse `LH_ContosoPharma`.
