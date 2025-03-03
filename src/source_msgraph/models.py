from dataclasses import dataclass
import importlib
import inspect
import re
from typing import Any, Dict
from source_msgraph.constants import MSGRAPH_SDK_PACKAGE
from urllib.parse import unquote, quote
from kiota_abstractions.base_request_builder import BaseRequestBuilder

@dataclass
class BaseResource:
    name: str # User friendly name for Spark reader
    resource_name: str # Microsoft Graph leaf resource name
    request_builder_module: str
    query_params: Dict[str, Any] = None
    resource_params: Dict[str, Any] = None
    request_builder_cls_name: str = None
    request_builder_query_cls_name: str = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("name is required")
        
        self.request_builder_cls_name = self._pascal_case(f"{self.resource_name}_request_builder")
        #self.request_builder_cls = self.get_request_builder_cls()
        self.request_builder_query_cls_name = self._pascal_case(f"{self.resource_name}_request_builder_get_query_parameters")
        #self.query_parameters_cls = self.get_query_parameters_cls()
        self.parse_url_template()

    
    @classmethod
    def _pascal_case(cls, snake_str: str) -> str:
        """
        Converts snake_case to PascalCase.
        Example: "items_request_builder" -> "ItemsRequestBuilder"
        """
        return "".join(word.title() for word in snake_str.split("_"))
    
    def get_query_parameters_cls(self):
        """
        Retrieves the query parameters class from the request builder module.
        """
        try:
            module = importlib.import_module(f"{MSGRAPH_SDK_PACKAGE}.{self.request_builder_module}")
            request_builder_cls = getattr(module, self.request_builder_cls_name, None)

            if not request_builder_cls or not issubclass(request_builder_cls, BaseRequestBuilder):
                raise AttributeError(f"{self.request_builder_cls_name} not found in {module.__name__}")

            # Inspect the attributes to find the query parameters class

            for attr in dir(request_builder_cls):
                if attr == self.request_builder_query_cls_name:
                    return getattr(request_builder_cls, attr)
            raise AttributeError(f"{self.request_builder_query_cls_name} not found in {module.__name__}")        
                    
        except ModuleNotFoundError:
            raise ImportError(f"Module {self.request_builder_module} not found in {MSGRAPH_SDK_PACKAGE}")

    def get_request_builder_cls(self) -> BaseRequestBuilder:
        """
        Dynamically imports a module and finds the RequestBuilder class.
        """
        try:
            module = importlib.import_module(f"{MSGRAPH_SDK_PACKAGE}.{self.request_builder_module}")
            for attr in dir(module):
                if attr == self.request_builder_cls_name:
                    cls = getattr(module, attr)
                    if not issubclass(cls, BaseRequestBuilder):
                        raise AttributeError(f"{attr} is not a subclass of BaseRequestBuilder")
                    return cls
        except ImportError:
            raise ImportError(f"Module {self.request_builder_module} not found in {MSGRAPH_SDK_PACKAGE}")
    
    def get_request_builder_url_template(self):
        """
        Extracts the `url_template` by analyzing the source code of the class.
        """
        try:
            cls = self.get_request_builder_cls()
            if inspect.isclass(cls) and hasattr(cls, "__init__"):
                # Extract the __init__ function source code
                init_source = inspect.getsource(cls.__init__)
                if "super().__init__(" in init_source:
                    lines = init_source.split("\n")
                    for line in lines:
                        if "super().__init__(" in line:
                            match = re.search(r'super\(\).__init__\s*\([^,]+,\s*"([^"]+)"', line)
                            if match:
                                url_template = match.group(1).replace('"', "").replace("'", "")
                            return url_template
                    
        except TypeError:
            raise TypeError(f"Error extracting URL template from {cls.__name__}")

    def parse_url_template(self):
        """
        Parses the `url_template` string to extract path parameters and query parameters.
        """
        url_template = self.get_request_builder_url_template()
        if not url_template:
            raise ValueError("URL template not found in request builder class")

        # Extract path parameters (decode %2Did → _id)
        path_parameters = [
            unquote(match.group(1)).replace("%2D", "_")
            for match in re.finditer(r"\{([^?}]+)\}", url_template)
            if match.group(1).lower() != "+baseurl"
        ]

        # Extract query parameters (decode %24expand → $expand)
        query_match = re.search(r"\{\?([^}]+)\}", url_template)
        query_parameters = (
            [unquote(q).replace("%24", "$") for q in query_match.group(1).split(",")]
            if query_match else []
        )

        self.resource_params = {k:None for k in path_parameters}
        self.query_params = {qp.strip().replace("$", ""): None for qp in query_parameters}

    
    def map_options_to_params(self, options: Dict[str, Any]) -> 'BaseResource':
        """
        Maps the provided options to either query parameters or resource parameters.

        :param options: Dictionary of options provided by the user.
        :param query_params: List of valid query parameter names.
        :param resource_params: List of valid resource parameter names.
        :return: A tuple (mapped_query_params, mapped_resource_params, invalid_params)
        """
        missing_params = [param for param in self.resource_params if param not in options]

        if missing_params:
            raise ValueError(f"Missing required resource parameters: {', '.join(missing_params)}")

        mapped_query_params = {"%24"+k: v for k, v in options.items() if k in self.query_params}
        
        mapped_resource_params = {k.replace("-", "%2D"): v for k, v in options.items() if k in self.resource_params}
        
        invalid_params = {k: v for k, v in options.items() if k not in self.query_params and k not in self.resource_params}
        
        if len(invalid_params) > 0:
            raise ValueError(f"Extra parameters {invalid_params} not allowed.")
        
        self.query_params = mapped_query_params
        self.resource_params = mapped_resource_params
        
        return self

GUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


@dataclass
class ConnectorOptions:
    """Options for Microsoft Graph API requests with strict resource_path validation."""
    tenant_id: str
    client_id: str
    client_secret: str
    resource: BaseResource
    def __post_init__(self):
        ...
        
    def _validate_credentials(self):
        """Validates the format and presence of credentials."""
        if not self.tenant_id or not GUID_PATTERN.match(self.tenant_id):
            raise ValueError("Invalid tenant_id: must be a valid GUID.")
        
        if not self.client_id or not GUID_PATTERN.match(self.client_id):
            raise ValueError("Invalid client_id: must be a valid GUID.")
        
        if not self.client_secret or not isinstance(self.client_secret, str):
            raise ValueError("Invalid client_secret: must be a non-empty string.")    