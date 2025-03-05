from abc import ABC, abstractmethod
from typing import Any, Dict
from msgraph import GraphServiceClient
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from pyspark_msgraph_source.core.async_iterator import AsyncToSyncIterator
from pyspark_msgraph_source.core.models import BaseResource
from pyspark_msgraph_source.core.utils import get_python_schema, to_json, to_pyspark_schema

from azure.identity import DefaultAzureCredential


class BaseResourceProvider(ABC):
    """
        Abstract base class to handle fetching data from Microsoft Graph API and 
        provide schema extraction for resources.
    """

    def __init__(self, options: Dict[str, Any]):
        """ 
            Initializes the resource provider with Graph client and options.

            This sets up the Microsoft Graph client using `DefaultAzureCredential`,
            which automatically handles Azure Active Directory (AAD) authentication
            by trying multiple credential types in a fixed order, such as:

                - Environment variables
                - Managed Identity (for Azure-hosted environments)
                - Azure CLI credentials
                - Visual Studio Code login
                - Interactive browser login (if applicable)
            
            This allows seamless local development and production deployments
            without code changes to the authentication mechanism.

            See Also:
                defaultazurecredential:
                https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential

            Args:
                options (Dict[str, Any]): Connector options including authentication 
                    details and resource configurations.

            Raises:
                CredentialUnavailableError: If no valid credentials are found during
                    authentication.
        """
        self.options = options
        credentials = DefaultAzureCredential()
        self.graph_client = GraphServiceClient(credentials=credentials)

    async def fetch_data(self):
        """
            Asynchronously fetches data from Microsoft Graph API with automatic 
            pagination handling.

            Yields:
                Any: Each record fetched from the API.

            Raises:
                ValueError: If the resource query parameters cannot be instantiated.
                AttributeError: If invalid query parameters are provided.
                Exception: If a Graph API error occurs.

            Example:
                async for record in provider.fetch_data():
                    print(record)
        """
        query_parameters_cls = self.resource.get_query_parameters_cls()

        if query_parameters_cls:
            try:
                query_parameters_instance = query_parameters_cls()
            except TypeError as e:
                raise ValueError(f"Failed to instantiate {query_parameters_cls.__name__}: {e}")

            if self.resource.query_params:
                for k, v in self.resource.query_params.items():
                    k = k.removeprefix("%24")
                    if hasattr(query_parameters_instance, k):
                        setattr(query_parameters_instance, k, v)
                    else:
                        raise AttributeError(f"{query_parameters_cls.__name__} has no attribute '{k}'")

        request_configuration = RequestConfiguration(
            query_parameters=query_parameters_instance
        )

        try:
            builder = self.resource.get_request_builder_cls()(
                self.graph_client.request_adapter, 
                self.resource.resource_params
            )
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
            Provides a synchronous iterator over records from the Microsoft Graph API.

            Returns:
                Iterator[Any]: Synchronous iterator over the fetched records.

            Raises:
                ValueError: If required credentials or resource parameters are missing.
                Exception: If the API request fails.

            Example:
                for record in provider.iter_records():
                    print(record)
        """
        async_gen = self.fetch_data()
        return AsyncToSyncIterator(async_gen)

    def get_resource_schema(self) -> Dict[str, Any]:
        """
            Retrieves the schema of a Microsoft Graph API resource by sampling a record.

            Returns:
                Tuple[Dict[str, Any], StructType]: A tuple containing the sample record 
                and its corresponding PySpark schema.

            Raises:
                ValueError: If no records are found or required options are missing.
                Exception: If the API request fails.

            Example:
                record, schema = provider.get_resource_schema()
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
        """
            Abstract property that must be implemented to provide the resource 
            configuration.

            Returns:
                BaseResource: The resource definition to use for fetching data.
        """
        ...
