
# PySpark Microsoft Graph Source




A **PySpark DataSource** to seamlessly integrate and read data from **Microsoft Graph API**, enabling easy access to resources like **SharePoint List Items**, and more.

---

## Features
- Entra ID Authentication
Securely authenticate with Microsoft Graph using DefaultAzureCredential, supporting local development and production seamlessly.

- Automatic Pagination Handling
Fetches all paginated data from Microsoft Graph without manual intervention.

- Dynamic Schema Inference
Automatically detects the schema of the resource by sampling data, so you don't need to define it manually.

- Simple Configuration with .option()
Easily configure resources and query parameters directly in your Spark read options, making it flexible and intuitive.

- Zero External Ingestion Services
No additional services like Azure Data Factory or Logic Apps are needed—directly ingest data into Spark from Microsoft Graph.

- Extensible Resource Providers
Add custom resource providers to support more Microsoft Graph endpoints as needed.

- Pluggable Architecture
Dynamically load resource providers without modifying core logic.

- Optimized for PySpark
Designed to work natively with Spark's DataFrame API for big data processing.

- Secure by Design
Credentials and secrets are handled using Azure Identity best practices, avoiding hardcoding sensitive data.

---

## Installation

```bash
pip install pyspark-msgraph-source
```

---

## ⚡ Quickstart

### 1. Authentication

This package uses [DefaultAzureCredential](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python#defaultazurecredential).  
Ensure you're authenticated:

```bash
az login
```

Or set environment variables:
```bash
export AZURE_CLIENT_ID=<your-client-id>
export AZURE_TENANT_ID=<your-tenant-id>
export AZURE_CLIENT_SECRET=<your-client-secret>
```

### 2. Example Usage

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \ 
.appName("MSGraphExample") \ 
.getOrCreate()

from pyspark_msgraph_source.core.source import MSGraphDataSource
spark.dataSource.register(MSGraphDataSource)

df = spark.read.format("msgraph") \ 
.option("resource", "list_items") \ 
.option("site-id", "<YOUR_SITE_ID>") \ 
.option("list-id", "<YOUR_LIST_ID>") \ 
.option("top", 100) \ 
.option("expand", "fields") \ 
.load()

df.show()

# with schema

df = spark.read.format("msgraph") \ 
.option("resource", "list_items") \ 
.option("site-id", "<YOUR_SITE_ID>") \ 
.option("list-id", "<YOUR_LIST_ID>") \ 
.option("top", 100) \ 
.option("expand", "fields") \ 
.schema("id string, Title string")
.load()

df.show()

```

---

## Supported Resources

| Resource     | Description                 |
|--------------|-----------------------------|
| `list_items`| SharePoint List Items       |
| *(more coming soon...)* |                 |

---

## Development

Coming soon...

---

## Troubleshooting

| Issue                          | Solution                                     |
|---------------------------------|----------------------------------------------|
| `ValueError: resource missing` | Add `.option("resource", "list_items")`     |
| Empty dataframe                | Verify IDs, permissions, and access         |
| Authentication failures        | Check Azure credentials and login status    |

---

## 📄 License

[MIT License](LICENSE)

---

## 📚 Resources

- [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/overview)
- [DefaultAzureCredential](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python#defaultazurecredential)
