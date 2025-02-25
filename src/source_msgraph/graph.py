# https://graph.microsoft.com/v1.0/sites/rapidcircle1com.sharepoint.com:/teams/msteams_49b7aa_734222/
# Get id by _api/site/id
# team sites are also available through https://graph.microsoft.com/v1.0/sites/9892ec2f-dd7b-4fbd-a896-2fa239f6b805/lists/
#
#

import asyncio
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.sites.item.lists.item.items.items_request_builder import ItemsRequestBuilder
import json
from kiota_serialization_json.json_serialization_writer_factory import JsonSerializationWriterFactory
from msgraph import GraphServiceClient
from azure.identity import ClientSecretCredential

from source_msgraph.async_interator import AsyncToSyncIterator

tenant_id = "7c78a7a0-8b3b-4d54-8c3c-ca6ab4da029f"
client_id = "59c8283d-4a90-44a9-9a58-579a0e511168"
client_secret = "gwz8Q~FJMTs_~yVNbYou3dU27UMBdKIrYg2s7bpg"


credentials = ClientSecretCredential(
    tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)

# from microsoft.kiota.serialization.json.json_serialization_writer_factory import JsonSerializationWriterFactory

# Convert to JSON using Kiota
writer_factory = JsonSerializationWriterFactory()
writer = writer_factory.get_serialization_writer("application/json")
graph_client = GraphServiceClient(credentials=credentials, scopes=[
                                  'https://graph.microsoft.com/.default'])


def to_json(value):
    value.serialize(writer)
    # Get JSON string
    return json.loads((writer.get_serialized_content().decode("utf-8")))


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