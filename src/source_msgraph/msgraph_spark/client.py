from typing import Union
from pyspark.sql.types import StructType

from source_msgraph.async_interator import AsyncToSyncIterator
from source_msgraph.msgraph_spark.fetcher import MicrosoftGraphFetcher
from source_msgraph.msgraph_spark.options import MicrosoftGraphOptions
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient

def iter_records(schema: Union[StructType, str], options: MicrosoftGraphOptions):
    # Authenticate using ClientSecretCredential
    credentials = ClientSecretCredential(
        tenant_id=options.tenant_id,
        client_id=options.client_id,
        client_secret=options.client_secret
    )

    # Initialize Graph Client
    client = GraphServiceClient(credentials=credentials, scopes=["https://graph.microsoft.com/.default"])

    fetcher = MicrosoftGraphFetcher(client, options.resource_path, options.query_params, options.resource_options)
    async_gen = fetcher.fetch_data()
    return AsyncToSyncIterator(async_gen)