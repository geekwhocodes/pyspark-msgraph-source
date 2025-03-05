from functools import cached_property
import logging
from typing import Dict

from pyspark_msgraph_source.core.base_client import BaseResourceProvider
from pyspark_msgraph_source.core.models import BaseResource


class ListItemsResourceProvider(BaseResourceProvider):

    def __init__(self, options: Dict[str, str]):
        self.options = options
        super().__init__(options)
    
    @cached_property 
    def resource(self) -> BaseResource:
        return BaseResource(
        name="list_items",
        resource_name="items",
        request_builder_module="sites.item.lists.item.items.items_request_builder"
    ).map_options_to_params(self.options)


