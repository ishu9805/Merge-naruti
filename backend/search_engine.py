import math
from backend.utils.media import resolve_media


def build_search_pipeline(query, page, limit):
    skip = (page - 1) * limit

    match_stage = {}
    if query:
        match_stage = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"anime": {"$regex": query, "$options": "i"}},
                {"rarity": {"$regex": query, "$options": "i"}}
            ]
        }

    return [
        {"$match": match_stage},
        {
            "$facet": {
                "data": [
                    {"$sort": {"_id": -1}},
                    {"$skip": skip},
                    {"$limit": limit}
                ],
                "count": [{"$count": "total"}]
            }
        }
    ]


def run_search(collection, query, page=1, limit=20):
    pipeline = build_search_pipeline(query, page, limit)
    result = list(collection.aggregate(pipeline))[0]

    docs = result.get("data", [])
    total = result.get("count", [])
    total_count = total[0]["total"] if total else 0

    items = []
    for doc in docs:
        media = resolve_media(doc)
        items.append({
            "id": str(doc["_id"]),
            "name": doc.get("name"),
            "anime": doc.get("anime"),
            "rarity": doc.get("rarity"),
            "media_type": media["media_type"],
            "media_url": media["media_url"]
        })

    return {
        "results": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": math.ceil(total_count / limit)
        }
    }
