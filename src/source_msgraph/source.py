from typing import Union
from pyspark.sql.datasource import DataSource, DataSourceReader
from pyspark.sql.types import StructType
from source_msgraph.async_interator import AsyncToSyncIterator
from source_msgraph.msgraph_spark.client import iter_records
from source_msgraph.msgraph_spark.options import MicrosoftGraphOptions

# Reference https://learn.microsoft.com/en-us/azure/databricks/pyspark/datasources


class MSGraphDataSource(DataSource):
    """

    """
    def __init__(self, options):
        
        # Extract query options
        query_option_keys = {"top", "filter", "orderby", "expand", "select"}
        query_options = {k: v for k, v in options.items() if k in query_option_keys}

        # Filter out credentials and query options
        resource_options = {
            k: v for k, v in options.items()
            if k not in {"tenant_id", "client_id", "client_secret", "resource_path"} and k not in query_option_keys
        }

        # Initialize MicrosoftGraphOptions
        self.options = MicrosoftGraphOptions(
            tenant_id=options["tenant_id"],
            client_id=options["client_id"],
            client_secret=options["client_secret"],
            resource_path=options["resource_path"],
            query_params=query_options,
            resource_options=resource_options
        )

    @classmethod
    def name(cls):
        return "msgraph"

    def schema(self):
        return "id string"

    def reader(self, schema: StructType):
        return MSGraphDataSourceReader(self.options, schema)


class MSGraphDataSourceReader(DataSourceReader):

    def __init__(self, options:MicrosoftGraphOptions, schema: Union[StructType, str]):
        self.schema: StructType = schema
        self.options:MicrosoftGraphOptions = options
        
    def read(self, partition):
        from source_msgraph.msgraph_spark.utils import to_json
        from pyspark.sql import Row
        for row in iter_records(self.schema, self.options):
            j = to_json(row)
            yield Row(**{
                "id": j.get("id", None)
            })
