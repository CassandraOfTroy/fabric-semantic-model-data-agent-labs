# Use Lab 3 on your own semantic model

How to explain the evaluation to a customer or a model owner, what you need, and what you change to run it on your own Power BI semantic model.

**In short:** the Python code is the grader and stays the same. Your model needs its own quiz: three files with your users' questions and correct answers, your business words, and a few rules. Then you run the same commands as in the lab.

## Explain it in two minutes

**What it is.** A quiz for your semantic model. You write business questions with their correct answers. An AI agent answers them by reading your model through the [Fabric IQ MCP server](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp), the read-only access point that Fabric IQ agents use. A script grades every answer, and the DAX behind it.

**Why.** Prep data for AI (the AI data schema and AI instructions) changes how Copilot and agents answer. Power BI doesn't have a batch test for it. Microsoft's guidance is to test a representative set of business questions against validated results ([Prepare the semantic model for Fabric IQ](https://learn.microsoft.com/power-bi/create-reports/copilot-ask-data-question#prepare-the-semantic-model-for-fabric-iq)). This does that in minutes, every time the model changes.

**What you get.** A report from two paths:

| Path | Answers the question | AI |
| --- | --- | --- |
| **A. Checks without AI** | Does the model give agents the right fields, descriptions and AI instructions? Do our business words hit the right columns? Do our measures return the validated numbers? | No |
| **B. The AI quiz** | Does an agent answer our users' questions correctly, with the right measure and filters? | Yes |

Every finding is mapped to where you fix it in Power BI. How it works: [Lab 3 README](README.md#how-it-works).

**What it isn't:**

- **Not a Copilot score.** Copilot in Power BI with Fabric IQ uses the same model context, but a different agent and LLM. Confirm important results in the Copilot pane.
- **Not a test of verified answers.** Fabric IQ doesn't return them ([what Fabric IQ gives an agent](README.md#what-fabric-iq-gives-an-agent)).
- **Not a security test.** It runs with your permissions, and RLS and OLS apply.
- **Not a production monitor.** Fabric IQ needs a person's sign-in, not a service principal.

**It doesn't change anything.** Fabric IQ is read-only, and the scripts never write to the model.

## 1. Check the prerequisites

### Fabric and Power BI

| Requirement | Why | Source |
| --- | --- | --- |
| The tenant's home region supports all Fabric workloads; not a Power BI-only region or a sovereign cloud | Fabric IQ MCP is available only there | [Fabric IQ MCP – limitations](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp#limitations-and-considerations) |
| An account that can open the model. For RLS, one test account per role | Fabric IQ runs as the signed-in user. You don't need a workspace role or Build permission | [Fabric IQ MCP – prerequisites](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp#prerequisites) |
| Consent for the delegated Power BI permissions `Item.Read.All` and `Item.Execute.All`, if your tenant restricts user consent | Fabric IQ sign-in | [Fabric IQ MCP – authenticate](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp#authenticate) |
| Optional: read and write permission on the model, for example the Contributor role | Only for the definition comparison in `inspect_model.py` | [Get Semantic Model Definition](https://learn.microsoft.com/rest/api/fabric/semanticmodel/items/get-semantic-model-definition) |
| Prep data for AI set up: Q&A on, AI data schema, AI instructions | That's what you evaluate | [Prepare your data for AI](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai) |

### GitHub

| Requirement | Why | Source |
| --- | --- | --- |
| A GitHub Copilot licence for each person who runs path B or the interactive review | Copilot CLI and Copilot Chat | [Installing GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/set-up/install-copilot-cli) |
| Organization or enterprise policies allow Copilot CLI and **MCP servers in Copilot**, and the LLMs you want to use | Administrators can turn off each of them | [Managing policies for Copilot in your organization](https://docs.github.com/copilot/how-tos/administer-copilot/manage-for-organization/manage-policies) |
| A usage budget. Each question in path B is one Copilot CLI prompt per run; `--judge` adds one more | Copilot usage is billed under your plan | [GitHub Copilot billing and usage](https://docs.github.com/copilot/concepts/billing-and-usage) |

### Your machine

| Tool | Why | Needed for |
| --- | --- | --- |
| [Python 3.10+](https://www.python.org/downloads/) | Runs the grader: `pip install -r eval/requirements.txt` | Paths A and B |
| [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) | Signs you in with `az login`. Fabric IQ accepts only a user's sign-in, not a service account | Paths A and B |
| GitHub Copilot CLI: `winget install GitHub.Copilot`, or `npm install -g @github/copilot` with Node.js 22+ | The AI agent that takes the quiz. A script can start it with one question, and it reports back every DAX query it ran. On Windows it needs [PowerShell 7](https://learn.microsoft.com/powershell/scripting/install/installing-powershell) | Path B |
| Skills for Fabric (recommended): in Copilot CLI, `/plugin marketplace add microsoft/skills-for-fabric`, then `/plugin install fabric-skills@fabric-collection` | The manual the agent follows for Fabric IQ: read the AI instructions, look up names before filtering, never invent numbers. Without it, each agent improvises, and a failure tells you less about your model ([Install Skills for Fabric](https://learn.microsoft.com/fabric/fundamentals/skills-for-fabric-install)) | Path B |
| [VS Code](https://code.visualstudio.com/) (optional) | Editor and terminal, and the optional interactive review with Copilot Chat | – |

### Data governance

- **What leaves Fabric.** In path B, `--judge` and the interactive review, model metadata and query results go to the AI model that GitHub Copilot uses. Agree on that with the data owner before you use production data. Path A and `inspect_model.py` don't use AI.
- **What stays on your machine.** The `results/` folder holds answers, DAX and query results. Keep it out of source control; it's in `.gitignore`.
- **The test set is business data.** It holds validated numbers, so keep it in a private repository.

## 2. Get the code

Either fork or clone this repository and work in `lab-03-ai-readiness-evals`, or copy the code into your own private repository. A layout that keeps one test set per model:

```text
your-repo/
  ai-readiness/
    eval/                    copy of lab-03-ai-readiness-evals/eval, unchanged
    testsets/
      sales/                 one folder per semantic model
        questions.csv
        value-probes.csv
        readiness-rules.json
        ai-instructions.md   optional: the AI instructions under source control
    results/                 add to .gitignore
```

Start each test set from a copy of [testset/](testset/): the workshop files show the format. Then run:

```powershell
python ai-readiness/eval/run_evals.py --model "<semantic model URL or ID>" `
    --testset ai-readiness/testsets/sales --out ai-readiness/results
```

## 3. What you change

| What | Where | Change it to | Required |
| --- | --- | --- | --- |
| The model | `--model`, or the `FABRIC_SEMANTIC_MODEL` environment variable | The model's browser URL or ID | Yes |
| Readiness rules | `readiness-rules.json` | Your technical fields, business terms, date table and AI instructions file. See [step 2](#step-2--readiness-rules-15-min) | Yes |
| Business terms | `value-probes.csv` | 10 to 30 terms your users type, with the column each must resolve to. See [step 3](#step-3--value-probes-15-min) | Yes |
| Test questions | `questions.csv` | 15 to 40 real questions, with validated answers and checks. See [step 4](#step-4--questions-1-to-2-hours) | Yes |
| AI instructions under source control | For example `ai-instructions.md` next to the rules | The text you paste into **Prep data for AI** > **Add AI instructions** | Recommended |
| The language of the answers | `CLARIFY_HINTS` and `DECLINE_HINTS` in [eval/scoring.py](eval/scoring.py), or use `--judge` | Phrases in your language | Only for answers that aren't in English |
| The endpoint | `FABRICIQ_ENDPOINT` | `https://api.fabric.microsoft.com/v1/mcp/fabriciq` | Only with private links |
| The token | `FABRICIQ_TOKEN` | A delegated Power BI token from your own app registration | Only if your tenant blocks Azure CLI tokens |

You don't change `run_evals.py`, `fabriciq_client.py`, `model_checks.py` or `agent_eval.py`. Other code changes, such as tolerances or the prompt, are listed in the [script reference](eval/README.md#change-the-code).

## 4. Build the test set, step by step

### Step 1 – See what agents see (15 min)

```powershell
python eval/inspect_model.py --model "<semantic model URL or ID>"
```

Then, optionally, run the interactive review in VS Code ([Lab 3, step 1](README.md#step-1--see-what-an-agent-sees-5-min)). Write down three things:

- the fields an agent sees that it shouldn't, such as IDs, raw amounts and sort columns
- the terms your users use: abbreviations, product names, regions, channels
- what the AI instructions say, and what they're missing

### Step 2 – Readiness rules (15 min)

Edit `readiness-rules.json`:

| Key | Meaning | Workshop example |
| --- | --- | --- |
| `must_not_expose` | Column and measure names agents must not see. Relationship columns don't count: Fabric IQ always returns them | `"Sales Line ID"`, `"Units"` |
| `ignore_description_columns_regex` | Columns that don't need a description (a regular expression) | `" Key$"` |
| `description_max_chars` | Longer descriptions get a warning: Copilot reads only the first 200 characters | `200` |
| `min_description_coverage` | Share of tables, columns and measures that need a description | `0.9` |
| `date_table` | The name of the date table | `"Date"` |
| `ai_instructions.max_chars` | The limit for AI instructions | `10000` |
| `ai_instructions.source_of_truth` | The file with your AI instructions under source control, relative to the rules file: its first `text` code block, or the whole file. Remove the key to skip the comparison | `"ai-instructions.md"` |
| `ai_instructions.must_mention` | Terms the AI instructions must cover | `["GTN", "DACH", "2025"]` |
| `ai_instructions.referenced_objects` | Tables, columns and measures the AI instructions name. Each must exist in what Fabric IQ returns, which catches renamed fields | `["Net Sales", "Brand"]` |
| `verified_answers` | Used only if Fabric IQ starts returning verified answers | – |

### Step 3 – Value probes (15 min)

Each row of `value-probes.csv` is a term a user types and where it must land:

| Column | Example |
| --- | --- |
| `term` | `DACH` |
| `expected_table` | `Customer` |
| `expected_column` | `Sales Region` |
| `expected_value` | `DACH` |
| `feature` | `AI instructions: terminology` |

A probe passes when Fabric IQ's best match is the expected value. It's a warning when another column also matches with a score of 0.5 or more: an agent could pick either. In the workshop, *UK & Ireland* also matches the country *Ireland*. Fix a warning with a line in the AI instructions, or by renaming values. Include:

- abbreviations and internal terms
- names that exist in more than one column, such as a country that's also part of a region name
- product names with and without a variant, such as a strength or size

### Step 4 – Questions (1 to 2 hours)

**Where the questions come from.** Ask three to five business users for the ten questions they ask most, plus questions that Copilot got wrong. Lab 2's [business test sheet](../lab-02-data-agent/testing/business-test-sheet.csv) is a template for collecting them.

**Cover every behaviour.** Plan at least one question for each:

| Behaviour | Example | `expect` |
| --- | --- | --- |
| A synonym or abbreviation from the AI instructions | *What was GTN in DACH last year?* | `answer` |
| No period, so the default period applies | *What is our revenue?* | `answer` |
| A name that matches several values | *Zentora sales in Germany in May 2026* | `answer` |
| A ranking | *Top 3 countries by net sales in 2026* | `answer` |
| A trend over time | *Monthly net sales of Oncology in 2025* | `answer` |
| An ambiguous question | *How are we doing?* | `clarify` |
| Data that isn't in the model | *How many quality complaints did we get?* | `decline` |

**Validate the expected values outside the model.** Take them from the source system or a report that finance has signed off, not from the model you're testing. Otherwise path A can't catch a wrong measure. The workshop values came from the source CSV files ([build_answer_key.py](../scripts/build_answer_key.py)).

**The columns of `questions.csv`:**

| Column | Required | Example | Meaning |
| --- | --- | --- | --- |
| `id` | Yes | `Q03` | Unique. Used with `--questions` and in trace file names |
| `feature` | Yes | `AI instructions: terminology` | Groups the result in the report. Start it with `AI instructions`, `AI data schema`, `Descriptions`, `Value grounding`, `Model design` or `Groundedness` to get a fix hint |
| `question` | Yes | `What was GTN in DACH last year?` | Exactly as a user would type it |
| `expect` | Yes | `answer`, `clarify` or `decline` | The behaviour you expect |
| `expected_answer` | Yes | `EUR 8.5 M, 9.6% of gross sales` | The answer in words. Shown in the report and used by `--judge` |
| `expected_values` | For `answer` | `8504817.16\|9.567%` | Numbers the answer must contain, separated by `\|`. Amounts as plain numbers; percentages with `%` |
| `match` | No | `all` or `any` | Whether all expected numbers or any one of them must appear. Default `all` |
| `must_mention` | No | `Oncology\|2025` | Words the answer must contain |
| `dax_must_contain` | No | `Discount Amount~Discount %\|DACH` | Tokens the agent's DAX must contain. `\|` separates tokens; `~` means *or* |
| `dax_must_not_contain` | No | `Order Date` | Tokens the DAX must not contain |
| `reference_dax` | For path A (L3) | `EVALUATE ROW ( "Value", CALCULATE ( [Net Sales], 'Date'[Year] = 2025 ) + 0 )` | Your own DAX that returns the expected numbers. Add `+ 0` and use an alias that isn't a measure name; otherwise Fabric IQ returns formatted text |

Tips:

- **Test one behaviour per question.** A question that fails for two reasons is hard to fix.
- **Prefer numbers and DAX checks over words.** Wording changes from run to run; the measure and the filters shouldn't.
- **Check the DAX, not only the number.** A right number from the wrong measure breaks on the next question.

### Step 5 – Validate the test set: run path A (10 min)

```powershell
python eval/run_evals.py --model "<semantic model URL or ID>" --testset <your test set> --layers lint,grounding,truth
```

The report shows path A as three layers:

- **L3 (correct numbers) fails:** the expected value or the measure is wrong. Find out which with the data owner before you go on.
- **L1 (readiness) fails on `must_not_expose`:** untick the field in **Prep data for AI** > **Simplify the data schema**. Hiding it in the model isn't enough.
- **L2 (word lookup) warns:** add a line to the AI instructions that says which column the term means.

### Step 6 – Baseline the AI quiz, path B (30 min)

```powershell
python eval/run_evals.py --model "<semantic model URL or ID>" --testset <your test set> --repeat 3 --llm <model>
```

Keep this results folder as your baseline. A question that passes 1 or 2 times out of 3 is unstable: the model context leaves room for interpretation. Pin the LLM with `--llm` so later runs are comparable.

### Step 7 – Improve and compare

Change one Prep data for AI setting at a time. Wait a few minutes, rerun the affected questions with `--questions`, then run everything and compare with the baseline.

### Step 8 – Make it routine

- Run path A after every model change, and path B before you mark the model **Approved for Copilot** and after every Prep data for AI change.
- Use `--fail-under 0.9` as a gate in your release checklist. It needs a person's sign-in, so run it on a developer machine or a pipeline agent that signs in as a user, not as a service principal.
- When a user reports a wrong answer, add the question to the test set.

## FAQ

| Question | Answer |
| --- | --- |
| Is this Copilot in Power BI? | No. It uses the same model context through Fabric IQ, but a different agent and LLM. Confirm important results in the Copilot pane |
| Does it change my model? | No. Fabric IQ is read-only, and so are the scripts |
| Do we still need verified answers? | They help Copilot in Power BI without Fabric IQ. Fabric IQ doesn't use them, so this evaluation doesn't test them |
| Can it run unattended with a service principal? | No. Fabric IQ supports only delegated user sign-in |
| Which data leaves Fabric? | Path A: nothing goes to an AI. Path B and the interactive review: model metadata and query results go to the AI model that GitHub Copilot uses |
| Can we test RLS roles? | Yes: run it as a test user in that role. Results are always what the signed-in user can see |
| How long does it take? | Path A: under a minute. Path B: about 30 seconds per question per run |
| What does it cost? | GitHub Copilot usage: one Copilot CLI prompt per question and run, plus one per `--judge` grade. The DAX queries run against your model like report queries |
| Can we use another agent than Copilot CLI? | Path A doesn't use an agent. For path B, the runner reads Copilot CLI's event stream; another MCP client needs its own runner in [agent_eval.py](eval/agent_eval.py) |

## Sources

- [Get started with the Fabric IQ MCP server](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp)
- [Ask data questions with Copilot and Fabric IQ](https://learn.microsoft.com/power-bi/create-reports/copilot-ask-data-question)
- [Prepare your data for AI to improve Copilot results](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai)
- [Prepare your data for AI: AI instructions](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-instructions)
- [Prepare your data for AI: Verified answers](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-verified-answers)
- [Install Skills for Fabric](https://learn.microsoft.com/fabric/fundamentals/skills-for-fabric-install)
- [Items – Get Semantic Model Definition](https://learn.microsoft.com/rest/api/fabric/semanticmodel/items/get-semantic-model-definition)
- [Installing GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/set-up/install-copilot-cli)
- [Managing policies and features for GitHub Copilot in your organization](https://docs.github.com/copilot/how-tos/administer-copilot/manage-for-organization/manage-policies)
- [GitHub Copilot billing and usage](https://docs.github.com/copilot/concepts/billing-and-usage)
