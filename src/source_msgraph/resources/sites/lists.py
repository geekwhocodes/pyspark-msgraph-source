from dataclasses import dataclass
from typing import Optional
from msgraph import GraphServiceClient
from msgraph.generated.sites.item.lists.item.items.items_request_builder import ItemsRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from source_msgraph.async_interator import AsyncToSyncIterator
from source_msgraph.resources.base_options import MicrosoftGraphResourceOptions

@dataclass
class SharePointListOptions(MicrosoftGraphResourceOptions):
    site_id: str
    list_id: Optional[str] = None

    def validate(self):
        super().validate()
        if not self.site_id:
            raise ValueError("site_id is required for SharePoint lists.")
        if self.sub_resource == "lists" and not self.list_id:
            raise ValueError("list_id is required when accessing lists.")


class ResourceHandler:
    def __init__(self, client: GraphServiceClient, params: dict):
        self.client = client
        self.params = SharePointListOptions(**params)

    async def fetch_items_async(self, site_id, list_id, **params):
        query_parameters = ItemsRequestBuilder.ItemsRequestBuilderGetQueryParameters(**params,
            expand=["fields"])
        request_configuration = RequestConfiguration(
            query_parameters=query_parameters,
        )

        items = await self.client.sites.by_site_id(site_id).lists.by_list_id(list_id).items.get(request_configuration=request_configuration)

        while True:
            print("Page fetched....")
            for item in items.value:
                yield item
            if not items.odata_next_link:
                break    
            items = await self.client.sites.by_site_id(site_id).lists.by_list_id(list_id).items.with_url(items.odata_next_link).get()


    def fetch_items_sync(self, site_id, list_id, params):
        async_gen = self.fetch_items_async(self.client, site_id, list_id, **params)
        return AsyncToSyncIterator(async_gen)

