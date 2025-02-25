import asyncio
from pyspark.sql.datasource import DataSource, DataSourceReader
from pyspark.sql.types import StructType, StringType

# Reference https://learn.microsoft.com/en-us/azure/databricks/pyspark/datasources


class MSGraphDataSource(DataSource):
    """

    """

    @classmethod
    def name(cls):
        return "msgraph"

    def schema(self):
        return "id string"

    def reader(self, schema: StructType):
        return MSGraphDataSourceReader(schema, self.options)


class MSGraphDataSourceReader(DataSourceReader):

    def __init__(self, schema, options):
        self.schema: StructType = schema
        self.options = options

    def read(self, partition):
        from source_msgraph.graph import fetch_items_sync, graph_client, to_json
        from pyspark.sql import Row
        for item in fetch_items_sync(graph_client, "37d7dde8-0b6b-4b7c-a2fd-2e217f54a263", "5ecf26db-0161-4069-b763-856217415099", {"top":10}):
            j = to_json(item)
            yield Row(**{
                "id": j.get("id", None)
            })
