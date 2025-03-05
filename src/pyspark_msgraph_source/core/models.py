from dataclasses import dataclass
import importlib
import inspect
import logging
import re
from typing import Any, Dict
from pyspark_msgraph_source.core.constants import MSGRAPH_SDK_PACKAGE
from urllib.parse import unquote
from kiota_abstractions.base_request_builder import BaseRequestBuilder


@dataclass
class BaseResource:
    """
    Represents a resource from Microsoft Graph API, such as list_items, users, etc.

    Attributes:
        name (str): User-friendly name for the Spark reader.
        resource_name (str): Microsoft Graph leaf resource name (e.g., users, items).
        request_builder_module (str): Module path of the request builder class from the MSGraph Python SDK.
        query_params (Dict[str, Any], optional): Extracted query parameters from the URL template.
        resource_params (Dict[str, Any], optional): Extracted path parameters from the URL template.
        request_builder_cls_name (str, optional): PascalCase name of the request builder class.
        request_builder_query_cls_name (str, optional): PascalCase name of the request builder's query parameters class.
    """

    name: str
    resource_name: str
    request_builder_module: str
    query_params: Dict[str, Any] = None
    resource_params: Dict[str, Any] = None
    request_builder_cls_name: str = None
    request_builder_query_cls_name: str = None

    def __post_init__(self):
        """
        Initializes derived attributes and parses the URL template.

        Raises:
            ValueError: If the 'name' attribute is not provided.
        """
        if not self.name:
            raise ValueError("name is required")

        self.request_builder_cls_name = self._pascal_case(f"{self.resource_name}_request_builder")
        self.request_builder_query_cls_name = self._pascal_case(f"{self.resource_name}_request_builder_get_query_parameters")
        self.parse_url_template()

    @classmethod
    def _pascal_case(cls, snake_str: str) -> str:
        """
        Converts a snake_case string to PascalCase.

        Args:
            snake_str (str): The snake_case string to convert.

        Returns:
            str: PascalCase formatted string.
        """
        return "".join(word.title() for word in snake_str.split("_"))

    def get_query_parameters_cls(self):
        """
        Retrieves the query parameters class from the request builder module.

        Returns:
            Any: Query parameters class object.

        Raises:
            ImportError: If the request builder module is not found.
            AttributeError: If the required class is not found.
        """
        try:
            module = importlib.import_module(f"{MSGRAPH_SDK_PACKAGE}.{self.request_builder_module}")
            request_builder_cls = getattr(module, self.request_builder_cls_name, None)

            if not request_builder_cls or not issubclass(request_builder_cls, BaseRequestBuilder):
                raise AttributeError(f"{self.request_builder_cls_name} not found in {module.__name__}")

            for attr in dir(request_builder_cls):
                if attr == self.request_builder_query_cls_name:
                    return getattr(request_builder_cls, attr)
            raise AttributeError(f"{self.request_builder_query_cls_name} not found in {module.__name__}")

        except ModuleNotFoundError:
            raise ImportError(f"Module {self.request_builder_module} not found in {MSGRAPH_SDK_PACKAGE}")

    def get_request_builder_cls(self) -> BaseRequestBuilder:
        """
        Dynamically imports a module and retrieves the request builder class.

        Returns:
            BaseRequestBuilder: The request builder class.

        Raises:
            ImportError: If the module is not found.
            AttributeError: If the class is not valid.
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
        Extracts the URL template from the request builder class's __init__ method.

        Returns:
            str: URL template string.

        Raises:
            TypeError: If the URL template cannot be extracted.
        """
        try:
            cls = self.get_request_builder_cls()
            if inspect.isclass(cls) and hasattr(cls, "__init__"):
                init_source = inspect.getsource(cls.__init__)
                if "super().__init__(" in init_source:
                    for line in init_source.split("\n"):
                        if "super().__init__(" in line:
                            match = re.search(r'super\(\).__init__\s*\([^,]+,\s*"([^"]+)"', line)
                            if match:
                                return match.group(1).replace('"', "").replace("'", "")
        except TypeError:
            raise TypeError(f"Error extracting URL template from {cls.__name__}")

    def parse_url_template(self):
        """
        Parses the URL template to extract path and query parameters.

        Raises:
            ValueError: If the URL template is not found.
        """
        url_template = self.get_request_builder_url_template()
        if not url_template:
            raise ValueError("URL template not found in request builder class")

        path_parameters = [
            unquote(match.group(1)).replace("%2D", "_")
            for match in re.finditer(r"\{([^?}]+)\}", url_template)
            if match.group(1).lower() != "+baseurl"
        ]

        query_match = re.search(r"\{\?([^}]+)\}", url_template)
        query_parameters = (
            [unquote(q).replace("%24", "$") for q in query_match.group(1).split(",")]
            if query_match else []
        )

        self.resource_params = {k: None for k in path_parameters}
        self.query_params = {qp.strip().replace("$", ""): None for qp in query_parameters}

    def map_options_to_params(self, options: Dict[str, Any]) -> 'BaseResource':
        """
        Maps provided options to valid query and resource parameters.

        Args:
            options (Dict[str, Any]): User-provided options.

        Returns:
            BaseResource: Updated instance with mapped parameters.

        Raises:
            ValueError: If required resource parameters are missing or extra parameters are provided.
        """
        missing_params = [param for param in self.resource_params if param not in options]

        if missing_params:
            raise ValueError(f"Missing required resource parameters: {', '.join(missing_params)}")

        if int(options.get("top", 1)) <= 100:
            logging.warning("Setting a low `top` value in Microsoft Graph queries can cause high latency and increase throttling risk.")

        mapped_query_params = {"%24" + k: v for k, v in options.items() if k in self.query_params}
        mapped_resource_params = {k.replace("-", "%2D"): v for k, v in options.items() if k in self.resource_params}

        invalid_params = {k: v for k, v in options.items() if k not in self.query_params and k not in self.resource_params}

        if invalid_params:
            raise ValueError(f"Extra parameters {invalid_params} not allowed.")

        self.query_params = mapped_query_params
        self.resource_params = mapped_resource_params

        return self


GUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


@dataclass
class ConnectorOptions:
    """
    Options for Microsoft Graph API requests with strict credential validation.

    Attributes:
        tenant_id (str): Azure tenant ID (GUID).
        client_id (str): Azure client ID (GUID).
        client_secret (str): Azure client secret.
    """
    tenant_id: str
    client_id: str
    client_secret: str

    def __post_init__(self):
        ...

    def _validate_credentials(self):
        """
        Validates the format and presence of credentials.

        Raises:
            ValueError: If any credential is invalid or missing.
        """
        ...
