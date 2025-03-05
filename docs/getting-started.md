## Installation

```bash
pip install pyspark-msgraph-source
```

---

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