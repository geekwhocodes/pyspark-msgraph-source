import logging
from typing import Any, Dict, Union
from pyspark.sql.datasource import DataSource, DataSourceReader
from pyspark.sql.types import StructType
from source_msgraph.client import get_resource_schema, iter_records
from source_msgraph.models import ConnectorOptions

from source_msgraph.resources import get_resource
# Reference https://learn.microsoft.com/en-us/azure/databricks/pyspark/datasources

logger = logging.getLogger(__name__)

class MSGraphDataSource(DataSource):
    """

    """
    def __init__(self, options: Dict[str, Any]):

        tenant_id=options.pop("tenant_id")
        client_id=options.pop("client_id")
        client_secret=options.pop("client_secret")
        
        resource_name = options.pop("resource")
        if not resource_name:
            raise ValueError("resource is missing, please provide a valid resource name.")
        
        resource = get_resource(resource_name).map_options_to_params(options)

        self.connector_options: ConnectorOptions = ConnectorOptions(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            resource=resource
        )


    @classmethod
    def name(cls):
        return "msgraph"

    def schema(self):
        logger.info("Schema not provided, infering from the source.")
        _, schema = get_resource_schema(self.connector_options)
        logger.debug(f"Infered schema : {schema}")
        return schema

    def reader(self, schema: StructType):
        return MSGraphDataSourceReader(self.connector_options, schema)


class MSGraphDataSourceReader(DataSourceReader):

    def __init__(self, options: ConnectorOptions, schema: Union[StructType, str]):
        self.schema: StructType = schema
        self.options:ConnectorOptions = options
        
    def read(self, partition):
        from source_msgraph.utils import to_json
        from pyspark.sql import Row
        for row in iter_records(self.options):
            row = to_json(row)
            row_data = {f.name: row.get(f.name, None) for f in self.schema.fields}
            yield Row(**row_data)
