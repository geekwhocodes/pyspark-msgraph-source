# Define the resources to generate
from source_msgraph.models import BaseResource


RESOURCE_CONFIGS = [
    {"name": "sites", "resource_name": "sites", "request_builder_module": "sites.sites_request_builder"},
    {"name": "lists", "resource_name": "lists", "request_builder_module": "sites.item.lists.lists_request_builder"},
    {"name": "list_items", "resource_name": "items", "request_builder_module": "sites.item.lists.item.items.items_request_builder"},
]



def get_resource(name: str):
    """
    Generates a list of BaseResource instances for specified Microsoft Graph resources.
    """
    config = next((config for config in RESOURCE_CONFIGS if config["name"] == name), None)
    if not config:
        raise ValueError(f"Resource '{name}' is not supported yet. stay tuned!")
    
    # Create and store the BaseResource instance
    resource = BaseResource(
        name=config["name"],
        resource_name=config["resource_name"],
        request_builder_module=config["request_builder_module"]
    )
    return resource 



