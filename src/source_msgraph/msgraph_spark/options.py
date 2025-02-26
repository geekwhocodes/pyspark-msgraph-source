from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class MicrosoftGraphOptions:
    """Options for Microsoft Graph API requests with strict resource_path validation."""
    tenant_id: str
    client_id: str
    client_secret: str
    resource_path: str  # Unique identifier, e.g., "sites/{site_id}/lists/{list_id}"
    query_params: Dict[str, Any] = field(default_factory=dict)  # Query params like 'top', 'filter'
    resource_options: Dict[str, Any] = field(default_factory=dict)  # Other resource-specific options

    def __post_init__(self):
        """Validate query params and resource options based on full resource_path."""
        self.validate_query_params()
        self.validate_resource_options()
        

    def validate_query_params(self):
        """Validate query parameters against the allowed list for the full resource path."""
        valid_query_options = self.get_valid_query_options()
        invalid_keys = [key for key in self.query_params if key not in valid_query_options]
        if invalid_keys:
            raise ValueError(f"Invalid query parameters for {self.resource_path}: {invalid_keys}")

    def validate_resource_options(self):
        """Validate resource-specific options based on the full resource_path."""
        valid_options = self.get_valid_resource_options()
        invalid_keys = [key for key in self.resource_options if key not in valid_options]
        if invalid_keys:
            raise ValueError(f"Invalid resource options for {self.resource_path}: {invalid_keys}")

    def get_valid_query_options(self):
        """Returns allowed query parameters based on the full resource path."""
        valid_query_map = {
            "sites/by_site_id/lists/by_list_id/items": {"top", "filter", "orderby", "expand"},
        }
        return valid_query_map.get(self.resource_path, set())

    def get_valid_resource_options(self):
        """Returns allowed resource options based on the full resource path."""
        valid_resource_map = {
            "sites/by_site_id/lists/by_list_id/items": {"site_id", "list_id"},
           
        }
        return valid_resource_map.get(self.resource_path, set())

    def get_request_parameters(self):
        """Returns structured parameters for Microsoft Graph SDK."""
        return {
            "query_params": self.query_params,
            "resource_options": self.resource_options
        }
