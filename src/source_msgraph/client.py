from msgraph import GraphServiceClient
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from azure.identity import ClientSecretCredential
from source_msgraph.async_interator import AsyncToSyncIterator, AsyncToSyncIteratorV2
from source_msgraph.models import ConnectorOptions
from source_msgraph.utils import get_python_schema, to_json, to_pyspark_schema

class GraphClient:
    def __init__(self, options: ConnectorOptions):
        """
        Initializes the fetcher with the Graph client, resource path, and query parameters.


        :param options: Connector options.
        """
        credentials = ClientSecretCredential(options.tenant_id, options.client_id, options.client_secret)
        self.graph_client = GraphServiceClient(credentials=credentials)
        self.options: ConnectorOptions = options


    async def fetch_data(self):
        """
        Fetches data from Microsoft Graph using the dynamically built request.
        Handles pagination automatically.
        """
        query_parameters_cls = self.options.resource.get_query_parameters_cls()

        if query_parameters_cls:
            try:
                query_parameters_instance = query_parameters_cls()  # Ensure it can be instantiated without arguments
            except TypeError as e:
                raise ValueError(f"Failed to instantiate {query_parameters_cls.__name__}: {e}")

            if self.options.resource.query_params:
                for k, v in self.options.resource.query_params.items():
                    k = k.removeprefix("%24")
                    if hasattr(query_parameters_instance, k):
                        setattr(query_parameters_instance, k, v)  # Set attributes dynamically
                    else:
                        raise AttributeError(f"{query_parameters_cls.__name__} has no attribute '{k}'")
                
        request_configuration = RequestConfiguration(
            query_parameters=query_parameters_instance
        )
        
        try:
            builder = self.options.resource.get_request_builder_cls()(self.graph_client.request_adapter, self.options.resource.resource_params)
            items = await builder.get(request_configuration=request_configuration)
            while True:
                print("Page fetched....")
                for item in items.value:
                    yield item
                if not items.odata_next_link:
                    break
                items = await builder.with_url(items.odata_next_link).get()

        except ODataError as e:
            raise Exception(f"Graph API Error: {e.error.message}")


def iter_records(options: ConnectorOptions):
    """
        Iterates over records from the Microsoft Graph API.

        :param options: Connector options containing authentication credentials and resource details.
        :return: A synchronous iterator over the fetched data.
        :raises ValueError: If any required credentials or resource parameters are missing.
        :raises GraphAPIError: If the API request fails.
    """
    fetcher = GraphClient(options)
    async_gen = fetcher.fetch_data()
    return AsyncToSyncIterator(async_gen)

import json
from typing import Dict, Any
from dataclasses import asdict

def get_resource_schema(options: ConnectorOptions) -> Dict[str, Any]:
    """
    Retrieves the schema of a Microsoft Graph API resource by fetching a single record.

    :param options: Connector options containing authentication credentials and resource details.
    :return: A dictionary representing the schema of the resource.
    :raises ValueError: If no records are found or if required options are missing.
    :raises GraphAPIError: If the API request fails.
    """
    fetcher = GraphClient(options)
    async_gen = fetcher.fetch_data()

    try:
        record = next(AsyncToSyncIteratorV2(async_gen), None)
        if not record:
            raise ValueError(f"No records found for resource: {options.resource.resource_name}")
        record = to_json(record)
        schema = to_pyspark_schema(get_python_schema(record))
        return record, schema
    
    except StopIteration:
        raise ValueError(f"No records available for {options.resource.resource_name}")

# Example usage
# options = ConnectorOptions(...)
# schema = get_resource_schema(options)
# print(json.dumps(schema, indent=2))
