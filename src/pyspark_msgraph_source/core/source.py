import logging
from typing import Any, Dict, Union
from pyspark.sql.datasource import DataSource, DataSourceReader
from pyspark.sql.types import StructType
from pyspark_msgraph_source.core.base_client import BaseResourceProvider

from pyspark_msgraph_source.core.resource_provider import get_resource_provider

# Reference https://learn.microsoft.com/en-us/azure/databricks/pyspark/datasources

logger = logging.getLogger(__name__)

class MSGraphDataSource(DataSource):
    """

    """
    def __init__(self, options: Dict[str, Any]):
        
        self.resource_name = options.pop("resource")
        if not self.resource_name:
            raise ValueError("resource is missing, please provide a valid resource name.")
        self.options = frozenset(options.items())
        
    @classmethod
    def name(cls):
        return "msgraph"
 
    def schema(self):
        logger.info("Schema not provided, infering from the source.")
        resource_provider:BaseResourceProvider = get_resource_provider(self.resource_name, self.options)
        _, schema = resource_provider.get_resource_schema()
        logger.debug(f"Infered schema : {schema}")
        return schema

    def reader(self, schema: StructType):
        return MSGraphDataSourceReader(self.resource_name, self.options, schema)


class MSGraphDataSourceReader(DataSourceReader):

    def __init__(self, resource_name :str, options: frozenset, schema: Union[StructType, str]):
        self.schema: StructType = schema
        self.options = options
        self.resource_name = resource_name
        
    def read(self, partition):
        from pyspark_msgraph_source.core.utils import to_json
        from pyspark.sql import Row
        resource_provider:BaseResourceProvider = get_resource_provider(self.resource_name, self.options)
        for row in resource_provider.iter_records():
            row = to_json(row)
            row_data = {f.name: row.get(f.name, None) for f in self.schema.fields}
            yield Row(**row_data)
