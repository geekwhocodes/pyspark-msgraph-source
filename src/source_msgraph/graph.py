# https://graph.microsoft.com/v1.0/sites/rapidcircle1com.sharepoint.com:/teams/msteams_49b7aa_734222/
# Get id by _api/site/id
# team sites are also available through https://graph.microsoft.com/v1.0/sites/9892ec2f-dd7b-4fbd-a896-2fa239f6b805/lists/
#
#

import asyncio
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.sites.item.lists.item.items.items_request_builder import ItemsRequestBuilder
import json

from msgraph import GraphServiceClient
from azure.identity import ClientSecretCredential

from source_msgraph.async_interator import AsyncToSyncIterator
from source_msgraph.msgraph_spark.fetcher import MicrosoftGraphFetcher
from source_msgraph.msgraph_spark.options import MicrosoftGraphOptions

tenant_id = "7c78a7a0-8b3b-4d54-8c3c-ca6ab4da029f"
client_id = "59c8283d-4a90-44a9-9a58-579a0e511168"
client_secret = "gwz8Q~FJMTs_~yVNbYou3dU27UMBdKIrYg2s7bpg"


credentials = ClientSecretCredential(
    tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)

# from microsoft.kiota.serialization.json.json_serialization_writer_factory import JsonSerializationWriterFactory


graph_client = GraphServiceClient(credentials=credentials, scopes=[
                                  'https://graph.microsoft.com/.default'])




async def fetch_items_async(graph_client, site_id, list_id, **params):
    query_parameters = ItemsRequestBuilder.ItemsRequestBuilderGetQueryParameters(**params,
        expand=["fields"])
    request_configuration = RequestConfiguration(
        query_parameters=query_parameters,
    )

    items = await graph_client.sites.by_site_id(site_id).lists.by_list_id(list_id).items.get(request_configuration=request_configuration)

    while True:
        print("Page fetched....")
        for item in items.value:
            yield item
        if not items.odata_next_link:
            break    
        items = await graph_client.sites.by_site_id(site_id).lists.by_list_id(list_id).items.with_url(items.odata_next_link).get()


def fetch_items_sync(graph_client, site_id, list_id, params):
    async_gen = fetch_items_async(graph_client, site_id, list_id, **params)
    return AsyncToSyncIterator(async_gen)


def main():
    options = MicrosoftGraphOptions(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        resource="sites/by_site_id/lists/by_list_id/items",
        params={
            "top": 1,
            "expand": ["fields"]
        }
    )
    resource_path = "sites/by_site_id/lists/by_list_id/items"
    params = {
        "site_id": "37d7dde8-0b6b-4b7c-a2fd-2e217f54a263",  # Actual site ID
        "list_id": "5ecf26db-0161-4069-b763-856217415099",  # Actual list ID
        "top": 5,
        "expand": ["fields"]
    }
    fetcher = MicrosoftGraphFetcher(graph_client, resource_path, params)
    async_gen = fetcher.fetch_data()
    for row in AsyncToSyncIterator(async_gen):
        print(row)


if __name__ == "__main__":
    main()