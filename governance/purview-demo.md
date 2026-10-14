# Purview demo: DLP and DSPM for Fabric, click by click

A 15-minute instructor demo that shows how Microsoft Purview protects the data behind the labs and watches the AI on top of it. Every screenshot comes from the workshop tenant.

| Part | What the audience sees | Minutes |
| --- | --- | ---: |
| [1. DLP finds bank data in a lakehouse](#1-dlp-finds-bank-data-in-a-lakehouse) | A policy tip on a Fabric lakehouse, the policy behind it, the alert | 5 |
| [2. DSPM shows what people ask the AI](#2-dspm-shows-what-people-ask-the-ai) | Copilot and data agent prompts and responses, including one with an IBAN | 5 |
| [3. DSPM data risk assessment for Fabric](#3-dspm-data-risk-assessment-for-fabric) | Oversharing of sensitive Fabric items | 3 |
| [4. Audit](#4-audit) | The same interactions as audit records | 2 |

## What you need

| Item | Where it comes from | Ready how long before the demo |
| --- | --- | --- |
| Folder `GOV` with lakehouse `LH_Customer_Finance` and table `customer_bank_accounts` | [Seed the demo data](#seed-the-demo-data) | 1 hour (DLP evaluation) |
| DLP policy *Workshop - Fabric customer bank data* | [scripts/create-dlp-policy.ps1](scripts/create-dlp-policy.ps1) | 1 hour |
| DSPM setup tasks done, pay-as-you-go billing on | [Prerequisites for DSPM](#prerequisites-for-dspm) | Once per tenant |
| A few Copilot and data agent conversations | Run Lab 1 and Lab 2 once (dry run) | 1 hour (audit pipeline) |
| Fabric connection for data risk assessments | [Connect DSPM to Fabric](#connect-dspm-to-fabric-for-data-risk-assessments) | 4 days for the first default assessment, up to 48 hours for a custom one |

All data is synthetic. The IBANs in `customer_bank_accounts` have valid check digits, so Purview recognizes them, but they don't belong to real accounts ([generate_governance_demo_data.py](../scripts/generate_governance_demo_data.py)).

## Seed the demo data

1. Generate the table: `python scripts/generate_governance_demo_data.py`. It writes `data/governance/customer_bank_accounts.parquet` (103 rows, one per customer).
2. In the workshop workspace, create the folder `GOV`. In it, create the lakehouse `LH_Customer_Finance`. Clear **Lakehouse schemas**.
3. Upload `customer_bank_accounts.parquet` to **Files**, then **…** > **Load to tables** > **New table** ([Load to tables](https://learn.microsoft.com/fabric/data-engineering/load-to-tables)).

The lakehouse is in its own folder and isn't used by the labs. Participants never need to open it.

## Create the DLP policy

Run the script once, as a Compliance Administrator. It needs PowerShell 7 and the ExchangeOnlineManagement module.

```powershell
Install-Module ExchangeOnlineManagement -Scope CurrentUser
./governance/scripts/create-dlp-policy.ps1 -WorkspaceId <workspace-guid> -UserPrincipalName admin@contoso.onmicrosoft.com
```

The policy covers only the workshop workspace. Its rule matches the sensitive information type **International Banking Account Number (IBAN)**, shows a policy tip to the item owner, and sends a high-severity alert ([New-DlpCompliancePolicy](https://learn.microsoft.com/powershell/module/exchangepowershell/new-dlpcompliancepolicy), [New-DlpComplianceRule](https://learn.microsoft.com/powershell/module/exchangepowershell/new-dlpcompliancerule)).

**The same in the portal:** **Data loss prevention** > **Policies** > **Create policy** > **Enterprise applications & devices** > **Custom** > **Custom policy**. Choose only the location **Fabric and Power BI workspaces** and include the workshop workspace. Create a rule with **Content contains** > **Sensitive info types** > *International Banking Account Number (IBAN)*. Turn on **User notifications** and **Incident reports**. DLP policy templates aren't supported for Fabric, so always start from **Custom** ([Create a DLP policy for Fabric](https://learn.microsoft.com/purview/dlp-create-policy-powerbi-cc-numbers), [DLP for Fabric](https://learn.microsoft.com/purview/dlp-powerbi-get-started)).

**When DLP evaluates:** a lakehouse is evaluated when its data changes, for example when you load or overwrite a table. A semantic model is evaluated when it's published or refreshed. DLP doesn't evaluate DirectQuery or live-connection models ([DLP for Fabric](https://learn.microsoft.com/purview/dlp-powerbi-get-started)). After you create the policy, reload the table once so that DLP evaluates it.

## Prerequisites for DSPM

All four are tenant-wide and are done once ([Data agent audit](https://learn.microsoft.com/fabric/data-science/data-agent-purview-governance), [Purview for Copilot in Fabric](https://learn.microsoft.com/purview/ai-copilot-fabric)):

1. Purview portal > **DSPM** > **Tasks and actions** > **Setup tasks**: complete **Activate Microsoft Purview Audit** and **Secure interactions in Microsoft Copilot experiences**.
2. Same page: **Set up pay-as-you-go billing for data storage**. Managing Copilot in Fabric and data agent interactions requires pay-as-you-go billing.
3. Fabric admin portal > **Tenant settings**: **Allow Microsoft Purview to secure AI interactions** is on (the default).

![DSPM setup tasks: Secure interactions in Microsoft Copilot experiences completed](../docs/images/ui/gov-01-dspm-setup-tasks.png)

## Connect DSPM to Fabric for data risk assessments

This one-time setup lets DSPM scan Fabric workspaces for oversharing ([Prerequisites for Fabric data risk assessments](https://learn.microsoft.com/purview/dspm-for-ai-considerations#prerequisites-for-fabric-data-risk-assessments), [Enable service principal authentication for admin APIs](https://learn.microsoft.com/fabric/admin/enable-service-principal-admin-apis)):

1. Purview portal > **DSPM** > **Discover** > **Data risk assessments** > **Fabric** tab > **Set config**. Keep **Federated Credentials** selected and copy the **OIDC Issuer URL**, **Namespace** and **Service Account Name**.

   ![Configure Fabric Settings dialog with the federated credential values](../docs/images/ui/gov-02-dspm-fabric-set-config.png)

2. In the Microsoft Entra admin center (Application Administrator):
   - create an app registration;
   - under **Certificates & secrets** > **Federated credentials**, add a credential of the scenario *Kubernetes accessing Azure resources*. Use the three values from step 1;
   - create a security group and add the app's service principal to it.
3. In Fabric (Fabric administrator): **Tenant settings** > **Admin API settings**. Turn on **Service principals can access read-only admin APIs** and **Service principals can access admin APIs used for updates**, each for that security group.
4. Back in **Set config**: paste the app's **Application (client) ID** into **Fabric ID (app ID)** > **Test connection** > **Save**.

The page then shows *You have set up connection for Fabric*. The default assessment covers the top 100 workspaces and runs weekly; its first results take up to 4 days.

![Data risk assessments, Fabric tab: connection set up, default assessment pending](../docs/images/ui/gov-03-dspm-fabric-connected.png)

---

## 1. DLP finds bank data in a lakehouse

1. Open the workshop workspace > folder **GOV** > **LH_Customer_Finance**. The header shows **Sensitive info detected**. Select it.

   ![Lakehouse header with the DLP policy tip Sensitive info detected](../docs/images/ui/gov-06-dlp-policy-tip.png)

2. Select **View details**. The panel shows the custom policy tip and the detected type, *International Banking Account Number (IBAN)* ([Respond to a DLP policy match](https://learn.microsoft.com/fabric/governance/data-loss-prevention-respond)).

   ![Sensitive info found panel with the policy tip text and the IBAN type](../docs/images/ui/gov-07-dlp-tip-details.png)

3. Switch to the Purview portal > **Data loss prevention** > **Policies**. Show *Workshop - Fabric customer bank data*: mode **On**, sync **completed**. Select it to show the rule and the location **Fabric and Power BI workspaces**.

   ![DLP policies list with the workshop policy On and Sync completed](../docs/images/ui/gov-04-dlp-policies.png)

   ![DLP policy details: rule IBAN in Fabric items, location Fabric and Power BI workspaces, mode On](../docs/images/ui/gov-05-dlp-policy-detail.png)

4. **Data loss prevention** > **Alerts**: open the high-severity alert for the lakehouse ([Monitor DLP policy matches in Fabric](https://learn.microsoft.com/fabric/governance/data-loss-prevention-monitor)).

**Say:** the same policy can **restrict access** (preview), so only the owner or people in the organization keep access. A data agent that uses this lakehouse respects the restriction ([DLP for Fabric](https://learn.microsoft.com/purview/dlp-powerbi-get-started), [Data agent concepts](https://learn.microsoft.com/fabric/data-science/concept-data-agent)).

## 2. DSPM shows what people ask the AI

1. Purview portal > **DSPM** > **Discover** > **Activity explorer** > **AI activities** tab.

   ![Activity explorer, AI activities: AI Interaction and Sensitive info types events by day](../docs/images/ui/gov-08-dspm-ai-activities.png)

2. Filter **App** = *Copilot in Fabric*. Open an **AI Interaction** row to show the prompt and the response. Open a **Sensitive info types** row: it was raised by the prompt *"Berlin Teaching Hospital pays from IBAN DE19… What were its net sales in 2025?"* sent to `REF_Sales_Agent` during the dry run.

   ![Activity details: Sensitive info types, app Copilot in Fabric, accessed in Power BI](../docs/images/ui/gov-09-dspm-ai-activity-detail.png)

**Say:**
- Prompts and responses of Copilot for Power BI are captured (generally available). Data agents and other Copilot experiences in Fabric are in preview ([Purview for Copilot in Fabric](https://learn.microsoft.com/purview/ai-copilot-fabric)).
- Only what the user sees is captured. The agent's internal steps and backend queries aren't ([Data agent audit](https://learn.microsoft.com/fabric/data-science/data-agent-purview-governance)).
- DLP doesn't act on the AI conversation itself in Copilot in Fabric. It protects the data sources, as in part 1 ([Purview for Copilot in Fabric](https://learn.microsoft.com/purview/ai-copilot-fabric)).

## 3. DSPM data risk assessment for Fabric

1. **DSPM** > **Discover** > **Data risk assessments** > **Fabric** tab.
2. Show the **Fabric default assessment**: sensitive information types found, items with and without sensitivity labels, and who can access them.
3. Show the custom assessment *Workshop - ContosoPharma_Workshop* and its **Overshared items**. Open the **Protect** tab: the recommended fixes are a DLP policy (part 1) and a default sensitivity label for new items ([Prevent oversharing with data risk assessments](https://learn.microsoft.com/purview/data-security-posture-management-oversharing)).

Scanned item types include lakehouses, warehouses, SQL analytics endpoints, reports and notebooks ([DSPM for AI](https://learn.microsoft.com/purview/dspm-for-ai)).

**If no results are shown yet:** the first default assessment takes up to 4 days, a custom assessment up to 48 hours. Show the connected Fabric tab and explain the scope instead.

## 4. Audit

Purview portal > **Audit** > search the last 24 hours. Use these **Activities - operation names** ([Operation list](https://learn.microsoft.com/fabric/admin/operation-list)):

| Operation | Created by |
| --- | --- |
| `CopilotInteraction` | Every Copilot and data agent prompt and response |
| `ApplyChangeToPowerBIModel` | Lab 1 model edits in the browser |
| `SensitivityLabelApplied` | Lab 1 step 9 |

Audit records can take up to an hour to appear. Use the records from your dry run.

## Clean up after the workshop

```powershell
Connect-IPPSSession -UserPrincipalName admin@contoso.onmicrosoft.com
Remove-DlpCompliancePolicy -Identity "Workshop - Fabric customer bank data"
```

Then delete the folder `GOV` with the lakehouse. If you created the app registration and security group only for this demo, delete them and remove the group from the two Fabric admin API settings.
