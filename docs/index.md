
# Welcome to **PySpark Microsoft Graph Connector**

Unlock seamless data access from **Microsoft Graph API** directly into **Apache Spark** using this connector designed for modern data pipelines.

---

## Why Use This Connector?

Working with Microsoft 365 data—such as SharePoint, Teams, Users, and Planner—has traditionally required intermediate services like Azure Data Factory, Logic Apps, or manual exports. With **`pyspark-msgraph-source`**, you can:

- Authenticate securely with **Entra ID** using `DefaultAzureCredential`  
- Query any supported Microsoft Graph resource directly in Spark  
- Automatically handle **pagination**, **dynamic schema inference**, and **large datasets**  
- Streamline analytics on Microsoft 365 data without extra infrastructure

---

## What is Microsoft Graph?

[Microsoft Graph](https://learn.microsoft.com/en-us/graph/overview) is the gateway to data and intelligence in Microsoft 365. It provides unified access to:

- **Users**
- **Groups**
- **Calendars**
- **SharePoint Lists**
- **Teams Channels**
- **Planner Tasks**
- And much more!

---

## What Can You Build?

- Reporting and analytics on SharePoint Lists
- Business intelligence dashboards with Microsoft Teams activity
- Enterprise insights from Entra ID (Azure AD)
- And much more!

---

## How Does It Work?

1. Configure your Microsoft Entra (Azure AD) application.
2. Authenticate with `DefaultAzureCredential`.
3. Load data into Spark using `.read.format("msgraph")`.
4. Query, process, and analyze at scale.

---

## Example

```python
df = spark.read.format("msgraph") \
    .option("resource", "list_items") \
    .option("site-id", "<your-site-id>") \
    .option("list-id", "<your-list-id>") \
    .load()

df.show()
```

---

## Ready to Get Started?

- Check out the [Getting Started Guide](getting-started.md)
- Explore available [Resources](api/resources)
- Learn how to [Contribute](contributing.md)  

---

## Need Help?

- Open an [issue](https://github.com/geekwhocodes/pyspark-msgraph-source/issues)
- Start a discussion with the community
- Submit feature requests and improvements

---

Welcome aboard and happy querying! 🚀
