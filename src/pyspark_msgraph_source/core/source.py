import logging
from typing import Any, Dict, Iterator, Tuple, Union
from pyspark.sql.datasource import DataSource, DataSourceReader
from pyspark.sql.types import StructType
from pyspark_msgraph_source.core.base_client import BaseResourceProvider
from pyspark_msgraph_source.core.resource_provider import get_resource_provider

# Reference: https://learn.microsoft.com/en-us/azure/databricks/pyspark/datasources

logger = logging.getLogger(__name__)


class MSGraphDataSource(DataSource):
    """
    A custom PySpark DataSource implementation to read data from Microsoft Graph API.

    This datasource uses dynamic resource providers to connect to different
    Microsoft Graph resources based on the `resource` option.

    If schema inference is required, it fetches sample data to infer the schema.

    See Also:
        Databricks PySpark DataSource API: 
        https://learn.microsoft.com/en-us/azure/databricks/pyspark/datasources

    Args:
        options (Dict[str, Any]): Connector options, including the required 
            `resource` name and authentication parameters.

    Raises:
        ValueError: If the `resource` option is missing.

    Example:
        df = spark.read.format("msgraph") \
            .option("resource", "list_items") \
            .option("site-id", "<site-id>") \
            .option("list-id", "<list-id>") \
            .option("top", 999) \
            .option("expand", "fields") \
            .load()

        df.show()
    """

    def __init__(self, options: Dict[str, Any]):
        self.resource_name = options.pop("resource", None)
        if not self.resource_name:
            raise ValueError("resource is missing, please provide a valid resource name.")
        self.options = frozenset(options.items())

    @classmethod
    def name(cls) -> str:
        """
        Returns the registered name of the DataSource.

        Returns:
            str: The name of the DataSource, "msgraph".
        """
        return "msgraph"

    def schema(self):
        """
        Infers the schema of the Microsoft Graph resource.

        This will call the corresponding resource provider to fetch a sample
        record and determine its schema.

        Returns:
            StructType: The inferred schema of the resource.
        """
        logger.info("Schema not provided, inferring from the source.")
        resource_provider: BaseResourceProvider = get_resource_provider(self.resource_name, self.options)
        _, schema = resource_provider.get_resource_schema()
        logger.debug(f"Inferred schema: {schema}")
        return schema

    def reader(self, schema: StructType) -> "MSGraphDataSourceReader":
        """
        Provides the DataSourceReader to read data.

        Args:
            schema (StructType): The schema to apply to the records.

        Returns:
            MSGraphDataSourceReader: The configured reader for this resource.
        """
        return MSGraphDataSourceReader(self.resource_name, self.options, schema)


class MSGraphDataSourceReader(DataSourceReader):
    """
    A DataSourceReader to fetch records from a Microsoft Graph resource.

    This reader uses the resource provider to iterate over records and
    yields rows compatible with the provided schema.

    Args:
        resource_name (str): The name of the Microsoft Graph resource.
        options (frozenset): Connector options.
        schema (Union[StructType, str]): The schema to apply to the records.
    """

    def __init__(self, resource_name: str, options: frozenset, schema: Union[StructType, str]):
        self.schema: StructType = schema
        self.options = options
        self.resource_name = resource_name

    def read(self, partition) -> Union[Iterator[Tuple], Iterator["RecordBatch"]]: # type: ignore
        """
        Reads records from the Microsoft Graph API.

        For each record fetched from the resource provider, it transforms
        the record into a PySpark Row object matching the schema.

        Args:
            partition: Unused in this implementation (for future partitioning support).

        Yields:
            Row: A PySpark Row object for each record.
        """
        from pyspark_msgraph_source.core.utils import to_json
        from pyspark.sql import Row

        resource_provider: BaseResourceProvider = get_resource_provider(self.resource_name, self.options)
        for row in resource_provider.iter_records():
            row = to_json(row)
            row_data = {f.name: row.get(f.name, None) for f in self.schema.fields}
            yield Row(**row_data)
