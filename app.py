import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="frontend/static", static_url_path="")
CORS(app)

# MongoDB connection URL (restored old values)
mongo_url = "mongodb+srv://Ishu9805:narutohinatabf@ishu9805.bsxrhw9.mongodb.net/?appName=Ishu9805"
client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
db = client['NARUTOGAMEBOT']
collection = db['anime_characters_lol']
user_collection = db['user_collection_lmaoooo']

media_collection = db["anime_characters_lol"]
engagement_collection = db["media_engagement"]

RARITY_MAP = {
    1: "⚪️ Common",
    2: "🟣 Rare",
    3: "🟡 Legendary",
    4: "🟢 Medium",
    5: "💮 Special Edition",
    6: "🔮 Limited Edition",
    7: "💸 Premium Edition",
    8: "🌤 Summer",
    9: "🎐 Celestial",
    10: "❄️ Winter",
    11: "💝 Valentine",
    12: "🎃 Halloween",
    13: "🎄 Christmas Special",
    14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    15: "🎭 Cosplay Master 🎭",
    16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨",
    17: "🎖 Apex Lot ( AUCTION )",
    18: "🍑 Echhi",
    19: "☠️ 𝕯𝖎𝖛𝖎𝖓𝖊",
    20: "☔ Monsoon",
    21: "🪸 Aquatic",
    22: "🎨 Artistic",
    23: "💳 VIP SLOT",
    24: "👶 Chibi",
    25: "🏴‍☠️ Marauds",
    26: "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣",
}


def parse_media_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def normalize_media_doc(doc):
    media_id = doc.get("id")
    if "vid_url" in doc:
        media_type = "video"
        media_url = doc.get("vid_url")
    else:
        media_type = "image"
        media_url = doc.get("img_url")

    return {
        "media_id": str(media_id) if media_id is not None else "",
        "sort_id": parse_media_id(media_id),
        "type": media_type,
        "url": media_url,
        "name": doc.get("name"),
        "anime": doc.get("anime"),
        "rarity": doc.get("rarity", "Unknown"),
    }




def parse_rarity_value(rarity_value):
    try:
        rarity_int = int(rarity_value)
    except (TypeError, ValueError):
        return None
    return RARITY_MAP.get(rarity_int)




def build_user_lookup_queries(user_id):
    query_values = [str(user_id)]
    try:
        query_values.append(int(user_id))
    except (TypeError, ValueError):
        pass

    return [
        {"id": query_values[0]},
        {"id": {"$in": query_values}},
        {"user_id": query_values[0]},
        {"user_id": {"$in": query_values}},
    ]


def find_user_doc(user_id, projection):
    for query in build_user_lookup_queries(user_id):
        user = user_collection.find_one(query, projection)
        if user:
            return user
    return None




def collect_name_suggestions(items, query, limit=8):
    query_lower = query.lower()
    matched = []
    for item in items:
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        name_lower = name.lower()
        if query_lower in name_lower and name not in matched:
            matched.append(name)

    matched.sort(key=lambda value: (not value.lower().startswith(query_lower), value.lower()))
    return matched[:limit]

def normalize_user_character(character, user_id):
    media_id = character.get("id")
    vid_url = character.get("vid_url")
    img_url = character.get("img_url")

    return {
        "media_id": str(media_id) if media_id is not None else "",
        "sort_id": parse_media_id(media_id),
        "type": "video" if vid_url else "image",
        "url": vid_url or img_url,
        "name": character.get("name"),
        "anime": character.get("anime"),
        "rarity": character.get("rarity", "Unknown"),
        "owner_user_id": str(user_id),
    }


@app.route("/")
def home():
    return send_from_directory("frontend/static", "index.html")


@app.route("/media", methods=["GET"])
def get_media():
    page = max(int(request.args.get("page", 1)), 1)
    size = max(min(int(request.args.get("size", 12)), 40), 1)
    skip = (page - 1) * size

    try:
        docs = list(media_collection.find({}, {"_id": 0}).skip(skip).limit(size))
        results = [normalize_media_doc(doc) for doc in docs if doc.get("vid_url") or doc.get("img_url")]
        results.sort(key=lambda item: item["sort_id"], reverse=True)
        total = media_collection.count_documents({})
        has_next = total > page * size
    except Exception:
        results = []
        has_next = False

    for item in results:
        item.pop("sort_id", None)

    return jsonify({"results": results, "hasNextPage": has_next})


@app.route("/media/search", methods=["GET"])
def search_media():
    source = request.args.get("source", "bot")
    name = request.args.get("name", "")
    anime = request.args.get("anime", "")
    rarity = request.args.get("rarity", "0")
    user_id = request.args.get("user_id", "")

    results = []

    if source == "user":
        if not user_id:
            return jsonify({"error": "user_id is required when source=user"}), 400

        try:
            user = find_user_doc(user_id, {"_id": 0, "characters": 1})
        except Exception:
            return jsonify({"results": []})
        if not user:
            return jsonify({"results": [], "profile": None})

        characters = user.get("characters", [])
        for char in characters:
            if name and name.lower() not in str(char.get("name", "")).lower():
                continue
            if anime and anime.lower() not in str(char.get("anime", "")).lower():
                continue
            rarity_label = parse_rarity_value(rarity)
            if rarity != "0" and char.get("rarity") != rarity_label:
                continue
            if not char.get("img_url") and not char.get("vid_url"):
                continue
            results.append(normalize_user_character(char, user_id))

    else:
        query = {}
        if name:
            query["name"] = {"$regex": name, "$options": "i"}
        if anime:
            query["anime"] = {"$regex": anime, "$options": "i"}
        if rarity != "0":
            query["rarity"] = parse_rarity_value(rarity)

        try:
            docs = list(media_collection.find(query, {"_id": 0}))
            results = [normalize_media_doc(doc) for doc in docs if doc.get("vid_url") or doc.get("img_url")]
        except Exception:
            results = []

    results.sort(key=lambda item: item["sort_id"], reverse=True)
    for item in results:
        item.pop("sort_id", None)

    return jsonify({"results": results})


@app.route("/media/suggestions", methods=["GET"])
def media_suggestions():
    source = request.args.get("source", "bot")
    query = request.args.get("query", "").strip()
    user_id = request.args.get("user_id", "").strip()

    if len(query) < 2:
        return jsonify({"suggestions": []})

    try:
        if source == "user":
            if not user_id:
                return jsonify({"suggestions": []})
            user = find_user_doc(user_id, {"_id": 0, "characters": 1})
            if not user:
                return jsonify({"suggestions": []})
            suggestions = collect_name_suggestions(user.get("characters", []), query)
            return jsonify({"suggestions": suggestions})

        docs = list(media_collection.find({"name": {"$regex": query, "$options": "i"}}, {"_id": 0, "name": 1}).limit(50))
        suggestions = collect_name_suggestions(docs, query)
        return jsonify({"suggestions": suggestions})
    except Exception:
        return jsonify({"suggestions": []})


@app.route("/profile", methods=["GET"])
def get_profile():
    user_id = request.args.get("user_id", "")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        user = find_user_doc(user_id, {"_id": 0})
    except Exception:
        return jsonify({"error": "Database unavailable"}), 503
    if not user:
        return jsonify({"error": "User not found"}), 404

    characters = user.get("characters", [])
    return jsonify(
        {
            "user_id": str(user.get("id", user.get("user_id", user_id))),
            "username": user.get("username") or "",
            "first_name": user.get("first_name") or "Telegram User",
            "photo_url": user.get("photo_url") or "",
            "total_characters": len(characters),
            "top_character_id": max((parse_media_id(c.get("id")) for c in characters), default=None),
        }
    )


@app.route("/media/like", methods=["POST"])
def like_media():
    media_id = request.json.get("media_id")
    engagement_collection.update_one({"media_id": media_id}, {"$inc": {"likes": 1}}, upsert=True)
    return jsonify({"success": True})


@app.route("/media/likes/<media_id>")
def get_likes(media_id):
    doc = engagement_collection.find_one({"media_id": media_id}) or {}
    return jsonify(likes=doc.get("likes", 0))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
