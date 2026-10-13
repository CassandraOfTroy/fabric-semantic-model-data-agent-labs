# Microsoft Fabric hands-on labs

**Build a semantic model with Copilot, then put a Fabric data agent on top of it.**
Two beginner labs, 2 hours each, browser only. Built for a group that shares one workspace.

![Workshop setup: one Fabric capacity and one workshop workspace. The folder 00_Shared holds the shared lakehouse LH_ContosoPharma, REF holds the instructor's reference items, and every participant has a folder, for example P07, with P07_Sales_Model and P07_Sales_Report from Lab 1 and P07_Sales_Agent from Lab 2. Governance across all of it: row-level security, sensitivity labels, DLP, Purview Audit, DSPM for AI.](docs/images/workshop-setup.png)

## Start here

**Participants**

1. Get your participant ID from the instructor, for example `P07`.
2. Read the [naming rules](docs/naming-and-etiquette.md). It takes 2 minutes.
3. Open <https://app.fabric.microsoft.com> in Edge or Chrome and start [Lab 1](lab-01-semantic-model/README.md). You don't need Power BI Desktop.

**Instructors**

Follow the [instructor setup](setup/README.md) at least one day before the session.

## The two labs

| | Lab 1 · Semantic model | Lab 2 · Data agent |
| --- | --- | --- |
| **You build** | A semantic model on the shared lakehouse (Direct Lake) and a report with AI visuals | A data agent on your model plus 2 lakehouse tables |
| **AI used** | Copilot in DAX query view, web modeling and reports | Build agent with AI, answers as charts |
| **Roles** | Model and report author | Developer and business user |
| **Time** | 120 minutes | 120 minutes |
| **Guide** | **[Open Lab 1 →](lab-01-semantic-model/README.md)** | **[Open Lab 2 →](lab-02-data-agent/README.md)** |

![Use case 1: the semantic model P07_Sales_Model reads the shared lakehouse tables directly (Direct Lake) and feeds the report P07_Sales_Report. Lab steps 1 to 9 are shown under each stage. Copilot helps at step 4 (DAX query view), step 5 (web modeling, preview), step 7 (report pages) and step 8 (narrative).](docs/images/use-case-1-semantic-model.png)

![Use case 2: the developer configures and publishes the data agent P07_Sales_Agent, the business user asks it questions and sends feedback. The agent queries P07_Sales_Model with DAX and two lakehouse tables with SQL. People use it in Fabric, Microsoft 365 Copilot and Teams (preview), Copilot Studio and VS Code through MCP.](docs/images/use-case-2-data-agent.png)

## The data

![The data: a sales star schema for Lab 1 (Sales with Customer, Product and Date) and two extra lakehouse tables for Lab 2 (inventory_weekly and quality_complaints). Story: 43 packaging complaints in April 2026, a stock-out in May and June, net sales of Zentora 100 mg tablets in Germany drop from EUR 660 k to 167 k, and recover to EUR 1,142 k in July.](docs/images/data-and-storyline.png)

All data is synthetic and all names are fictional. Column descriptions are in the [data dictionary](data/README.md).

<details>
<summary><b>What's in this repository</b></summary>

| Folder | Contents |
| --- | --- |
| [lab-01-semantic-model](lab-01-semantic-model/) | Lab 1 guide, DAX files, Copilot prompts, AI instructions, best-practice checklist |
| [lab-02-data-agent](lab-02-data-agent/) | Lab 2 guides (developer, business user), agent configuration, test sheets, MCP setup, evaluation notebook, gap matrix |
| [governance](governance/) | Row-level security, sensitivity labels, DLP, audit, DSPM for AI, and a 10-minute demo script |
| [setup](setup/) | Instructor setup guide, plus an optional notebook that loads the lakehouse from CSV |
| [data](data/) | The data as CSV (readable) and Parquet (typed, for upload to the lakehouse), plus the data dictionary |
| [docs](docs/) | Naming rules, and the diagrams with their editable PowerPoint source |
| [scripts](scripts/) | Data generator, answer-key builder and folder script (Python standard library), Parquet export (needs `pyarrow`) |

</details>

<details>
<summary><b>Feature status</b></summary>

The labs follow Microsoft Learn as of October 2026. These features are in **preview**, and each guide marks them where they're used:

- Copilot in web modeling and Prep data for AI (Lab 1)
- Build agent with AI, the preview runtime and the evaluation SDK (Lab 2)
- Data agents in Microsoft 365 Copilot, and Purview audit and DSPM for data agents (Lab 2)

Preview features can change and reach tenants at different times. If the portal looks different from a guide, follow the linked Microsoft Learn page. The full status table is in the [instructor setup](setup/README.md#features-used-and-their-status).

</details>

## License

[MIT](LICENSE). The data is synthetic; company, product and customer names are fictional.
