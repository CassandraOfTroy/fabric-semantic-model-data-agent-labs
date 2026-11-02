# Lab 3 – Evaluate how AI-ready your semantic model is, with Fabric IQ MCP

**Time:** 60 minutes · **Level:** intermediate · **Tools:** terminal or VS Code, Python 3.10+, Azure CLI, GitHub Copilot CLI

In Lab 1 you prepared `P07_Sales_Model` for AI: descriptions, **Prep data for AI** (AI data schema, AI instructions, a verified answer). In Lab 2 you evaluated a data agent in batch with the evaluation SDK. This lab does the same for the **semantic model itself**: a repeatable, scripted test that tells you whether an AI agent gets the right answers from your model, and which Prep data for AI setting to fix when it doesn't.

## Why a separate lab

| | Lab 2 · data agent | Lab 3 · semantic model |
| --- | --- | --- |
| **What answers the question** | The published data agent | Any MCP agent, here GitHub Copilot CLI with the fabriciq skill |
| **How you reach the data** | Data agent SDK | [Fabric IQ MCP](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp), read-only, as the signed-in user |
| **What it evaluates** | Agent instructions, example queries, data sources | Descriptions, AI data schema, AI instructions, verified answers, values |
| **Scoring** | LLM critic | Deterministic checks first, optional LLM critic |
| **Output** | Lakehouse tables | `results/<run>/report.md`, CSV files and traces |

There's no batch evaluation API for Copilot in Power BI. Microsoft's guidance is to test Prep data for AI changes in the Copilot pane, and to use **How Copilot arrived at this** and **Download diagnostics** to troubleshoot ([Prepare your data for AI – test your changes](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai#test-your-copilot-tooling-changes)). Fabric IQ MCP makes a scripted test possible: it returns the same model context to any agent (schema, descriptions, AI instructions, verified answers) and runs DAX as the signed-in user. It doesn't answer questions itself; *the calling agent writes the DAX* ([Fabric IQ MCP](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp)). So a wrong answer points at either the agent or what the model told it, and the traces show which.

> **What this measures.** How well an agent that reads your model through Fabric IQ answers your business questions. It uses the same Prep data for AI inputs as Copilot in Power BI, but a different orchestrator and LLM, so treat it as a regression test for the model, not as a Copilot score. Confirm the result in the Copilot pane before you mark the model **Approved for Copilot** ([Approved for Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai#mark-your-model-as-approved-for-copilot)).

## The four layers

| Layer | What it checks | Fabric IQ tool | LLM |
| --- | --- | --- | --- |
| **L1 readiness lint** | Technical fields hidden from AI, description coverage and length, format strings, date table, relationships, AI instructions (present, under 10,000 characters, business terms covered, named objects exist, same as source control), verified answers, discoverability by name | `GetSemanticModelSchema`, `DiscoverArtifacts` | No |
| **L2 value grounding** | Business terms (Zentora, DACH, Tender, UK & Ireland) resolve to the right column and value, and aren't ambiguous | `ValueSearch` | No |
| **L3 ground truth** | Reference DAX returns the expected numbers, which come from the source CSV files and not from the model | `ExecuteQuery` | No |
| **L4 agent** | Copilot CLI answers 16 questions. Each answer is scored on numbers, mentions and the DAX the agent ran (measure, filters, columns it must avoid). Optional LLM critic | All six | Yes |

L1 to L3 are deterministic and take under a minute. Run them on every model change. L4 takes about 30 seconds per question.

The 16 questions in [testset/questions.csv](testset/questions.csv) each target one Prep data for AI feature:

| Feature | Questions | Example |
| --- | --- | --- |
| AI instructions: terminology | Q01, Q03, Q04, Q08, Q09, Q10 | *What was GTN in DACH last year?* must use Discount Amount or Discount %, Sales Region = DACH, 2025 |
| AI instructions: default period | Q02 | *What is our revenue?* must use 2025 and say so |
| AI instructions: brand rule | Q05 | *Zentora sales in Germany in May 2026* must filter on Brand (EUR 843 k), not on one product (EUR 167 k) |
| AI instructions: year over year, trend, data range | Q07, Q13, Q14 | Trends must not use Order Date |
| AI instructions: ambiguity | Q15 | *How are we doing?* must get a clarifying question |
| Verified answers | Q11 | *Show sales by TA* |
| Groundedness | Q16 | Quality complaints aren't in the model: the agent must say so |

## Before you start

- **Model:** `P07_Sales_Model` from Lab 1, or `REF_Sales_Model` in the folder **REF**. You need read access to it. Fabric IQ uses your existing permissions; RLS and OLS apply ([Fabric IQ MCP – authenticate](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp#authenticate)).
- **Python 3.10+**, then `pip install -r eval/requirements.txt`.
- **Azure CLI**, signed in with your work account: `az login`. The scripts use your delegated token. Fabric IQ doesn't support service principals or app-only tokens, and you don't need an app registration.
- **GitHub Copilot CLI** for L4: `npm install -g @github/copilot`, then `copilot` and sign in.
- **Skills for Fabric** (recommended for L4): Fabric IQ works best with the fabriciq skill. Install it in Copilot CLI through the plugin marketplace ([Install Skills for Fabric](https://learn.microsoft.com/fabric/fundamentals/skills-for-fabric-install)).

> Query results go to the LLM that Copilot CLI uses. Use the workshop data, or check your organization's policy before you point this at production data. The `results/` folder holds answers, DAX and traces; it's in `.gitignore`.

## Step 1 – Connect and look at what AI sees (10 min)

1. Add Fabric IQ to Copilot CLI: copy [copilot/mcp-config.json](copilot/mcp-config.json) into `%USERPROFILE%\.copilot\mcp-config.json` (Windows) or `~/.copilot/mcp-config.json`. If you installed Skills for Fabric, the server is already there.
2. Start `copilot`, run `/mcp show FabricIQ` and sign in ([Fabric IQ MCP – set up GitHub Copilot CLI](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp#set-up-github-copilot-cli)).
3. Paste the review prompt from [copilot/ai-readiness-review.prompt.md](copilot/ai-readiness-review.prompt.md) and replace the model placeholder with your model's browser URL. In VS Code you can run the same file as a prompt file in Copilot Chat agent mode.

You get a one-off review. The next steps make it repeatable.

## Step 2 – Run the deterministic checks (5 min)

```powershell
cd lab-03-ai-readiness-evals/eval
python run_evals.py --model "<semantic model URL or ID>" --layers lint,grounding,truth
```

You can also pass the model name, but only if Fabric IQ search finds it. If it doesn't, the L1 check **Discoverable by name** shows that, and you pass the URL or ID instead.

## Step 3 – Run the agent evaluation (10 min)

```powershell
python run_evals.py --model "<semantic model URL or ID>"
```

Options:

| Option | Use |
| --- | --- |
| `--questions Q02,Q05` | Run only some questions |
| `--repeat 3` | Run each question 3 times. Answers are nondeterministic, so a question that passes 1 of 3 times is a finding too |
| `--parallel 2` | Run 2 agents at the same time. Power BI throttles bursts; keep it at 1 or 2 |
| `--llm <model>` | Pin the Copilot CLI model, so runs are comparable |
| `--judge` | Also grade each answer with an LLM critic, like the data agent evaluation SDK in Lab 2 |
| `--fail-under 0.9` | Exit with code 1 if the L4 pass rate is below 90% or an L1–L3 check fails |
| `--rescore <results folder>` | Apply changed checks in `questions.csv` to a saved run, without calling Power BI or the agent again |

How it works: for each question the runner starts `copilot -p` in an empty folder with only the Fabric IQ tools and the skill allowed. It passes your token as an `Authorization` header, which replaces the interactive sign-in for that run ([Fabric IQ MCP – set up GitHub Copilot CLI](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp#set-up-github-copilot-cli)). The token file is deleted after the run. The runner reads the JSONL event stream, which contains the final answer, every tool call and every DAX query. Runs that Power BI throttles are paused, retried, and reported as throttled instead of failed.

## Step 4 – Read the report (10 min)

Open `results/<timestamp>/report.md`:

- **Scorecard:** pass, warn and fail per layer.
- **By Prep data for AI feature:** where the model is weakest, and where in Power BI you fix it.
- **Failed runs:** the question, the expected answer, the agent's answer, what failed and the DAX it ran.

Read every failed run in this order:

1. **L3 failed?** The model returns the wrong number. Fix the measure first: no AI setting can fix wrong DAX.
2. **The DAX uses the wrong measure or column?** Fix the AI instructions (terminology), the AI data schema (hide the competing field) or the descriptions.
3. **The DAX uses the wrong value?** Check L2. For example, *UK & Ireland* also matches the country *Ireland*.
4. **The DAX is right but the answer is wrong?** That's the agent. Rerun with `--repeat 3` before you change the model.

### Example: REF_Sales_Model, November 2026

One run with the Copilot CLI default model:

| Layer | Result |
| --- | --- |
| L1 readiness | 11 pass, 2 warn, 2 fail |
| L2 grounding | 7 pass, 3 warn |
| L3 ground truth | 12 of 12 |
| L4 agent | 15 of 16 |

What the run found, and what to do about it:

| Finding | Layer | Fix |
| --- | --- | --- |
| **No verified answers.** Lab 1, step 7b adds *Net Sales by Therapeutic Area*, but the model has none. Q11 (*Show sales by TA*) still passed, because the AI instructions and descriptions are good enough. So L4 alone wouldn't have caught it | L1 | Set up the verified answer on the report visual |
| **AI instructions differ from source control.** The model says GTN means *Discount Amount or Discount %* and adds *packs = Units Sold*. [ai-instructions.md](../lab-01-semantic-model/ai-instructions.md) says *Discount %* only and has a growth synonym and a full-year YoY rule that the model doesn't | L1 | Decide which text is right, then update the other |
| **Vague questions get an answer, not a question.** *How are we doing?* returned a full 2025 analysis. The rule *no period → use 2025* won over *ambiguous → ask one question* | L4 | Make the ambiguity rule explicit, for example: *If the user doesn't name a metric, ask which one before you answer. The default period applies only when the metric is clear* |
| **Search doesn't find the model by name.** Agents that start from a name, not a URL, won't reach it | L1 | Add a model description, endorse the model, mark it **Approved for Copilot** |
| **Ambiguous values.** *UK & Ireland* also matches the country *Ireland*; *Wholesale* (channel) is close to *Wholesaler* (customer type) | L2 | Add the region and the channel/customer-type difference to the AI instructions |
| **One technical column without a description.** `Sales[Order Date]` is exposed through the relationship | L1 | Describe it as *order date; use the Date table for time filters* |

L3 and the AI data schema checks passed: every measure returns the right number, and no technical field reaches AI.

## Step 5 – Fix, wait, rerun (15 min)

1. Make one change, for example add the verified answer from Lab 1, step 7b, or align the AI instructions with [ai-instructions.md](../lab-01-semantic-model/ai-instructions.md).
2. Wait a few minutes. Prep data for AI changes can take a few minutes to reach AI experiences ([Prepare your data for AI](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai#power-bi-service)). If you deploy the model through Git or a deployment pipeline, refresh it in the service so the AI settings sync.
3. Rerun only the questions you expect to change: `--questions Q11`. Then rerun everything to check nothing else broke.

## Step 6 – Make it yours

- **Add your business users' questions** to [testset/questions.csv](testset/questions.csv). For each question set `feature`, `expected_answer` and the checks:

  | Column | Example | Meaning |
  | --- | --- | --- |
  | `expect` | `answer`, `clarify`, `decline` | The behaviour you expect |
  | `expected_values` | `8504817.16\|9.567%` | Numbers the answer must contain (1% tolerance; percentages ±0.1 points) |
  | `match` | `all` or `any` | All or any of the numbers |
  | `must_mention` | `Oncology\|2025` | Words the answer must contain |
  | `dax_must_contain` | `Discount Amount~Discount %\|DACH` | Tokens the agent's DAX must contain; `~` means *or* |
  | `dax_must_not_contain` | `Order Date` | Tokens the DAX must not contain |
  | `reference_dax` | `EVALUATE ROW ( "Value", ... + 0 )` | For L3. Add `+ 0` and use an alias that isn't a measure name; otherwise Fabric IQ returns the measure's formatted text |

- **Compute expected values from the source**, not from the model. That's how L3 catches wrong measures. The workshop values came from the CSV files in [data](../data/).
- **Change the readiness rules** in [testset/readiness-rules.json](testset/readiness-rules.json): fields that must stay hidden from AI, terms the AI instructions must cover, verified answers you expect.
- **Add value probes** to [testset/value-probes.csv](testset/value-probes.csv) for every business term users type.

## Limits

- **A proxy for Copilot.** Same model context, different agent. A model that scores well here is well described. Copilot can still answer differently.
- **Delegated sign-in only.** Fabric IQ doesn't support service principals ([Fabric IQ MCP – limitations](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp#limitations-and-considerations)). Run it from a developer machine, or a pipeline agent that runs as a user, not from a service principal.
- **Throttling.** Fabric IQ calls count against Power BI limits. Several agents in parallel can block your account for a few minutes.
- **RLS.** Results are what *you* can see. Run as a test user to evaluate a role.
- **What the lint can't see.** Fabric IQ returns what AI can use: it doesn't say which fields you hid in the model, whether Q&A is on, or whether the model is approved for Copilot. Check those in the service.

## Files

| File | Use |
| --- | --- |
| [eval/run_evals.py](eval/run_evals.py) | Runs the layers and writes the report |
| [eval/fabriciq_client.py](eval/fabriciq_client.py) | Minimal Fabric IQ MCP client (Streamable HTTP, delegated token) |
| [eval/model_checks.py](eval/model_checks.py) | L1 lint, L2 value grounding, L3 ground truth |
| [eval/agent_eval.py](eval/agent_eval.py) | L4 runner for GitHub Copilot CLI, and the optional LLM critic |
| [eval/scoring.py](eval/scoring.py) | Number, mention and DAX checks |
| [testset/questions.csv](testset/questions.csv) | 16 questions with expected answers, checks and reference DAX |
| [testset/value-probes.csv](testset/value-probes.csv) | Business terms and the column each should resolve to |
| [testset/readiness-rules.json](testset/readiness-rules.json) | Rules for the L1 lint |
| [copilot/mcp-config.json](copilot/mcp-config.json) | Fabric IQ MCP server for Copilot CLI |
| [copilot/ai-readiness-review.prompt.md](copilot/ai-readiness-review.prompt.md) | Interactive review prompt |

## Sources

- [Get started with the Fabric IQ MCP server](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp)
- [Prepare your data for AI to improve Copilot results](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai)
- [Prepare your data for AI: AI instructions](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-instructions)
- [Prepare your data for AI: Verified answers](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-verified-answers)
- [Prepare your data for AI: AI data schemas](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-data-schema)
- [Optimize your semantic model for Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-evaluate-data)
- [Semantic model best practices for data agent](https://learn.microsoft.com/fabric/data-science/semantic-model-best-practices)
- [Evaluate your data agent](https://learn.microsoft.com/fabric/data-science/evaluate-data-agent)
- [Install Skills for Fabric](https://learn.microsoft.com/fabric/fundamentals/skills-for-fabric-install)
