# Naming rules and workspace etiquette

Everyone works in the same workspace, **ContosoPharma_Workshop**, at the same time. These rules prevent two people from saving over the same item.

## The workspace

| Folder | Contains | You |
| --- | --- | --- |
| `00_Shared` | The shared lakehouse `LH_ContosoPharma` | Read it, never change it |
| `REF` | The instructor's finished items (`REF_Sales_Model`, `REF_Sales_Report`, `REF_Sales_Agent`) | Use them as a fallback, never change them |
| `P01` … `P25` | One folder per participant | Build everything in **your** folder |

## Your participant ID

Your ID is a short number the instructor gives you: `P01`, `P02`, … `P25` ("P" for participant). You put it at the start of every item you create, so 25 people can work in one workspace without overwriting each other's items. The guides use **P07** as the example: wherever you see `P07`, type your own ID instead.

## Names to use

| What | Name | Example, if your ID is P07 |
| --- | --- | --- |
| Your folder | `<ID>` | `P07` |
| Semantic model (Lab 1) | `<ID>_Sales_Model` | `P07_Sales_Model` |
| Report (Lab 1) | `<ID>_Sales_Report` | `P07_Sales_Report` |
| Data agent (Lab 2) | `<ID>_Sales_Agent` | `P07_Sales_Agent` |
| Evaluation notebook (Lab 2, optional) | `<ID>_Agent_Eval` | `P07_Agent_Eval` |

Use letters, digits and underscores only. Start the name with a letter.

## Rules

1. **Create everything inside your own folder.** Open your folder first, then select **+ New item**. If an item lands in the workspace root, move it with **…** > **Move to**.
2. **Open and edit only items that start with your ID.**
3. **Never rename, move or delete someone else's item or folder.**
4. **Don't change anything in `00_Shared` or `REF`.** Everyone depends on the shared lakehouse.
5. **Don't change workspace settings or access.**

## Why these rules matter

- In the web model editor, changes are **saved automatically and can't be undone**. Several people can edit the same model at the same time ([Edit semantic models in the Power BI service](https://learn.microsoft.com/power-bi/transform-model/service-edit-data-models)). Version history keeps the last five versions of a model ([Semantic model version history](https://learn.microsoft.com/power-bi/transform-model/service-semantic-model-version-history)).
- **Contributors can create, change and delete any item in the workspace**, not only their own, and that includes the shared lakehouse ([Roles in workspaces](https://learn.microsoft.com/fabric/fundamentals/roles-workspaces)).
- Folders inherit the workspace permissions. Folder names can't contain `~"#.&*:<>?/{|}` ([Create folders in workspaces](https://learn.microsoft.com/fabric/fundamentals/workspaces-folders)).
- Lakehouse names must start with a letter and contain only letters, digits and underscores ([Create a lakehouse](https://learn.microsoft.com/fabric/data-engineering/create-lakehouse)). Using the same pattern for every item keeps names valid for any item type, and also for APIs and MCP tools.
