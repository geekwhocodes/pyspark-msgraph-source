from abc import ABC, abstractmethod
from typing import Any, Dict
from msgraph import GraphServiceClient
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from source_msgraph.core.async_interator import AsyncToSyncIterator
from source_msgraph.core.models import BaseResource
from source_msgraph.core.utils import get_python_schema, to_json, to_pyspark_schema

from azure.identity import DefaultAzureCredential, EnvironmentCredential

class BaseResourceProvider(ABC):
    def __init__(self, options: Dict[str, Any]):
        """
        Initializes the fetcher with the Graph client, resource path, and query parameters.

        :param options: Connector options.
        """
        self.options = options
        credentials = DefaultAzureCredential()
        self.graph_client = GraphServiceClient(credentials=credentials)

    async def fetch_data(self):
        """
        Fetches data from Microsoft Graph using the dynamically built request.
        Handles pagination automatically.
        """
        query_parameters_cls = self.resource.get_query_parameters_cls()

        if query_parameters_cls:
            try:
                query_parameters_instance = query_parameters_cls()  # Ensure it can be instantiated without arguments
            except TypeError as e:
                raise ValueError(f"Failed to instantiate {query_parameters_cls.__name__}: {e}")

            if self.resource.query_params:
                for k, v in self.resource.query_params.items():
                    k = k.removeprefix("%24")
                    if hasattr(query_parameters_instance, k):
                        setattr(query_parameters_instance, k, v)  # Set attributes dynamically
                    else:
                        raise AttributeError(f"{query_parameters_cls.__name__} has no attribute '{k}'")
                
        request_configuration = RequestConfiguration(
            query_parameters=query_parameters_instance
        )
        
        try:
            builder = self.resource.get_request_builder_cls()(self.graph_client.request_adapter, self.resource.resource_params)
            items = await builder.get(request_configuration=request_configuration)
            while True:
                for item in items.value:
                    yield item
                if not items.odata_next_link:
                    break
                items = await builder.with_url(items.odata_next_link).get()

        except ODataError as e:
            raise Exception(f"Graph API Error: {e.error.message}")

    def iter_records(self):
        """
            Iterates over records from the Microsoft Graph API.

            :param options: Connector options containing authentication credentials and resource details.
            :return: A synchronous iterator over the fetched data.
            :raises ValueError: If any required credentials or resource parameters are missing.
            :raises GraphAPIError: If the API request fails.
        """
        async_gen = self.fetch_data()
        return AsyncToSyncIterator(async_gen)

    def get_resource_schema(self) -> Dict[str, Any]:
        """
        Retrieves the schema of a Microsoft Graph API resource by fetching a single record.

        :param options: Connector options containing authentication credentials and resource details.
        :return: A dictionary representing the schema of the resource.
        :raises ValueError: If no records are found or if required options are missing.
        :raises GraphAPIError: If the API request fails.
        """
        async_gen = self.fetch_data()

        try:
            record = next(AsyncToSyncIterator(async_gen), None)
            if not record:
                raise ValueError(f"No records found for resource: {self.resource.resource_name}")
            record = to_json(record)
            schema = to_pyspark_schema(get_python_schema(record))
            return record, schema
        
        except StopIteration:
            raise ValueError(f"No records available for {self.resource.resource_name}")
    
    @abstractmethod
    def resource(self) -> BaseResource:
        ...