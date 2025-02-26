from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class MicrosoftGraphResourceOptions:
    """Base dataclass for Microsoft Graph resource options."""
    
    # resource: str  # e.g., "users", "sites", "groups"
    # sub_resource: Optional[str] = None  # e.g., for sites: "lists", "drive"
    # params: Dict[str, Any] = field(default_factory=dict)  # Additional query params
    
    # def validate(self):
    #     """Base validation for all resources."""
    #     if not self.resource:
    #         raise ValueError("Resource is required.")
    #     if self.sub_resource and not isinstance(self.sub_resource, str):
    #         raise ValueError("Sub-resource must be a string.")