from elasticsearch import AsyncElasticsearch
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Elasticsearch Client
es = AsyncElasticsearch(
    ["http://localhost:9200"],  # In production, this should come from settings
    # api_key=("id", "api_key") # Add auth for production
)


async def index_order(order_id: int, client_name: str, phone: str, details: str):
    """
    Indexes an order into Elasticsearch for Full-Text Search.
    Task 25: Elasticsearch Integration
    """
    doc = {
        "order_id": order_id,
        "client_name": client_name,
        "phone": phone,
        "details": details,
    }
    try:
        response = await es.index(index="orders", id=str(order_id), document=doc)
        return response["result"]
    except Exception as e:
        logger.error(f"Failed to index order {order_id} in Elasticsearch: {e}")
        return None


async def search_orders(query: str):
    """
    Searches orders using Elasticsearch's multi_match query.
    """
    try:
        response = await es.search(
            index="orders",
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["client_name", "phone", "details"],
                    "fuzziness": "AUTO",  # Handles typos
                }
            },
        )
        return [hit["_source"] for hit in response["hits"]["hits"]]
    except Exception as e:
        logger.error(f"Search failed in Elasticsearch: {e}")
        return []
