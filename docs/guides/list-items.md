# Reading SharePoint List Items with PySpark

This guide explains how to read **List Items** from a **SharePoint List** using the `pyspark-msgraph-source` connector and Microsoft Graph API.

---

## Prerequisites
- Microsoft Entra (Azure AD) authentication set up with permissions to access SharePoint lists.
- Required Microsoft Graph API permissions:
  - `Sites.Read.All`
  - `Lists.Read`
- Installed `pyspark-msgraph-source` package.
- Initialized Spark session.

---

## 🔹 Supported Options for `list_items`

| Option       | Description                                               | Required |
|--------------|-----------------------------------------------------------|----------|
| `resource`  | Resource name (must be `"list_items"`)                    | ✅ Yes   |
| `site-id`   | The ID of the SharePoint site                              | ✅ Yes   |
| `list-id`   | The ID of the list within the SharePoint site              | ✅ Yes   |
| `top`       | (Optional) Number of records to fetch                      | ❌ No    |
| `expand`    | (Optional) Related entities to expand (e.g., `"fields"`)   | ❌ No    |

> **Note:** You can find `site-id` and `list-id` via Graph API explorer or SharePoint admin tools.

---

## Example Usage

```python
from pyspark_msgraph_source.core.source import MSGraphDataSource

# Register the data source (typically required once)
spark.dataSource.register(MSGraphDataSource)

# Read data from Microsoft Graph
df = spark.read.format("msgraph") \
    .option("resource", "list_items") \
        .option("site-id", "37d7dde8-0b6b-4b7c-a2fd-2e217f54a263") \
        .option("list-id", "5ecf26db-0161-4069-b763-856217415099")  \  
        .option("top", 111) \
        .option("expand", "fields") \
        .load()

# Show the results
df.show()
```

---

## Explanation of Example
- **`spark.read.format("msgraph")`**: Use the Microsoft Graph connector.
- **`.option("resource", "list_items")`**: Specify the resource to fetch SharePoint list items.
- **`.option("site-id", "...")` and `.option("list-id", "...")`**: Provide the SharePoint site and list IDs.
- **`.option("top", 111)`**: Limit the number of records (optional).
- **`.option("expand", "fields")`**: Retrieve additional field details (optional).
- **`.load()`**: Execute the read operation.

---

## Schema Inference
The connector automatically infers the schema by fetching a sample record from the API if you do not provide a schema.

---

## Error Handling
- Missing or invalid `site-id` or `list-id` will raise a `ValueError`.
- API permission errors will raise authentication exceptions.
- Network or Microsoft Graph issues will raise clear, descriptive exceptions.

---

## Notes
- Authentication is handled automatically via [**`DefaultAzureCredential`**](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python#defaultazurecredential), supporting:
  - Environment credentials
  - Managed Identity
  - Azure CLI login
  - Visual Studio Code authentication

- Use `.option("top", N)` to control the number of records retrieved for large datasets.
- To retrieve custom fields, include `.option("expand", "fields")`.

---

## Troubleshooting

| Issue                                  | Solution                                         |
|-----------------------------------------|-------------------------------------------------|
| `"resource is missing"` error          | Ensure `.option("resource", "list_items")`     |
| Empty dataframe                        | Check permissions and ensure valid IDs         |
| `"Unsupported resource name"` error    | Verify `"list_items"` is supported             |