import importlib
from msgraph import GraphServiceClient
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from typing import Dict, Any
import asyncio

class MicrosoftGraphFetcher:
    def __init__(self, graph_client: GraphServiceClient, resource_path: str, query_params: Dict[str, Any], resource_params: Dict[str, str]):
        """
        Initializes the fetcher with the Graph client, resource path, and query parameters.

        :param graph_client: The authenticated GraphServiceClient instance.
        :param resource_path: The resource path (e.g., "sites/by_site_id/lists/by_list_id/items").
        :param params: Query parameters for the request.
        """
        self.graph_client = graph_client
        self.resource_path = resource_path
        self.query_params = query_params
        self.resource_params = resource_params

    def _get_request_builder_class(self):
        """
        Dynamically resolves the correct RequestBuilder class from `msgraph.generated`.

        Example: For "sites/by_site_id/lists/by_list_id/items", it will resolve:
            `msgraph.generated.sites.item.lists.item.items.items_request_builder.ItemsRequestBuilder`
        """
        path_parts = self.resource_path.split("/")
        base_module = "msgraph.generated"
        module_path = []
        class_name = "RequestBuilder"  # Default fallback

        i = 0
        while i < len(path_parts):
            part = path_parts[i]

            if part.startswith("by_"):  # Handling {site_id}, {list_id}, etc.
                module_path.append("item")  # `by_site_id` means `.item`
                
            else:
                module_path.append(part)

            i += 1

        # Construct the full module path
        module_name = f"{base_module}." + ".".join(module_path) + f".{module_path[-1]}_request_builder"

        try:
            module = importlib.import_module(module_name)
            pascal_case_class = self._pascal_case(f"{module_path[-1]}_request_builder")

            for attr in dir(module):
                if attr == pascal_case_class:
                    return getattr(module, attr)

            raise ValueError(f"Could not find {pascal_case_class} in {module_name}")

        except ModuleNotFoundError:
            raise ValueError(f"Could not resolve RequestBuilder for resource path: {self.resource_path}")

    def _pascal_case(self, snake_str: str) -> str:
        """
        Converts snake_case to PascalCase.
        Example: "items_request_builder" -> "ItemsRequestBuilder"
        """
        return "".join(word.title() for word in snake_str.split("_"))
    
    def _get_query_parameters_class(self, request_builder_class):
        """
        Fetches the corresponding `RequestBuilderGetQueryParameters` class dynamically.
        """
        for attr in dir(request_builder_class):
            if attr.endswith("RequestBuilderGetQueryParameters"):
                return getattr(request_builder_class, attr)
        raise ValueError(f"No QueryParameters class found for {request_builder_class.__name__}")

    async def fetch_data(self):
        """
        Fetches data from Microsoft Graph using the dynamically built request.
        Handles pagination automatically.
        """
        request_builder_class = self._get_request_builder_class()
        query_params_class = self._get_query_parameters_class(request_builder_class)

        
        # Create Query Parameters object
        valid_params = {p for p in query_params_class.__annotations__.keys()}
        filtered_params = {k: v for k, v in self.query_params.items() if k in valid_params}
        query_parameters = query_params_class(**filtered_params)
        request_configuration = RequestConfiguration(
            query_parameters=query_parameters,
        )
        
        # Get Request Builder Instance from Graph Client
        builder = self._get_request_builder_instance(request_builder_class)

        try:
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

    def _get_request_builder_instance(self, request_builder_class):
        """
        Uses the `graph_client` to resolve the correct instance of the request builder dynamically,
        passing actual `site_id`, `list_id`, etc., instead of placeholders.
        """
        parts = self.resource_path.split("/")
        builder = self.graph_client

        i = 0
        while i < len(parts):
            part = parts[i]

            if part.startswith("by_"):  # Handling "by_site_id", "by_list_id", etc.
                param_name = part[3:]  # Extract parameter name (e.g., "site_id", "list_id")
                actual_id = self.resource_params.get(param_name)  # Get actual ID from user input
                if not actual_id:
                    raise ValueError(f"Missing required parameter: {param_name}")
                method_name = part  # Keep "by_site_id" format

                if hasattr(builder, method_name):
                    builder = getattr(builder, method_name)(actual_id)  # Pass actual ID
            elif hasattr(builder, part):
                builder = getattr(builder, part)
            else:
                raise ValueError(f"Invalid resource path: '{part}' not found in {builder}")

            i += 1

        return builder
