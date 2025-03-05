from functools import cached_property
import logging
from typing import Dict

from pyspark_msgraph_source.core.base_client import BaseResourceProvider
from pyspark_msgraph_source.core.models import BaseResource

logger = logging.getLogger(__name__)


class ListItemsResourceProvider(BaseResourceProvider):
    """
    Resource provider for fetching list items from Microsoft Graph API.
    
    See Also:
        https://learn.microsoft.com/en-us/graph/api/listitem-list?view=graph-rest-1.0:
        https://learn.microsoft.com/en-us/graph/api/listitem-list?view=graph-rest-1.0


    This provider handles the setup of the `list_items` resource,
    configuring the request builder and mapping options to the required parameters.

    Args:
        options (Dict[str, str]): Connector options, typically containing 
            site ID, list ID, and any query parameters.

    Example:
        provider = ListItemsResourceProvider(options)
        for record in provider.iter_records():
            print(record)
    """

    def __init__(self, options: Dict[str, str]):
        """
        Initializes the ListItemsResourceProvider.

        Args:
            options (Dict[str, str]): Connector options required to configure 
                the resource and authenticate requests.
        """
        self.options = options
        super().__init__(options)

    @cached_property
    def resource(self) -> BaseResource:
        """
        Returns the BaseResource configuration for list items.

        This sets up the request builder path and resource name
        required to make API calls to retrieve list items.

        Returns:
            BaseResource: Configured resource with mapped options.
        """
        return BaseResource(
            name="list_items",
            resource_name="items",
            request_builder_module="sites.item.lists.item.items.items_request_builder"
        ).map_options_to_params(self.options)
