from flask_cors import CORS
from pymongo import MongoClient
import requests
from flask import Flask, jsonify, send_from_directory, request, Response

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from pymongo import MongoClient
import requests
import os
from dotenv import load_dotenv

# MongoDB connection URL
mongo_url = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_url)
db = client['NARUTOGAMEBOT']
collection = db['anime_characters_lol']
user_collection = db['user_collection_lmaoooo']  # Collection storing user collections with a 'characters' array


load_dotenv()

app = Flask(__name__, static_folder="frontend/static", static_url_path="")
CORS(app)

media_collection = db["anime_characters_lol"]   # images + videos
engagement_collection = db["media_engagement"]

# =======================
# HOME
# =======================
@app.route("/")
def home():
    return send_from_directory("frontend/static", "index.html")


#rariti3w
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
    25: "🏴‍☠️ Marauds"
}

# =======================
# MEDIA FEED (IMAGES + VIDEOS)
# =======================
@app.route("/media", methods=["GET"])
def get_media():
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 12))
    skip = (page - 1) * size

    total = media_collection.count_documents({})
    has_next = total > page * size

    docs = list(
        media_collection
        .find()
        .sort("_id", -1)   # NEWEST FIRST
        .skip(skip)
        .limit(size)
    )
    
    results = []
    for doc in docs:
        if "vid_url" in doc:
            results.append({
                "media_id": str(doc.get("id")),
                "type": "video",
                "url": doc["vid_url"],
                "name": doc.get("name"),
                "anime": doc.get("anime"),
                "rarity": doc.get("rarity", "Unknown")
            })
        elif "img_url" in doc:
            results.append({
                "media_id": str(doc.get("id")),
                "type": "image",
                "url": doc["img_url"],
                "name": doc.get("name"),
                "anime": doc.get("anime"),
                "rarity": doc.get("rarity", "Unknown")
            })

    return jsonify({
        "results": results,
        "hasNextPage": has_next
    })

# =======================
# SEARCH (IMAGE + VIDEO)
# =======================
@app.route("/media/search", methods=["GET"])
def search_media():
    name = request.args.get("name", "")
    anime = request.args.get("anime", "")
    rarity = request.args.get("rarity", "0")

    query = {}

    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    if anime:
        query["anime"] = {"$regex": anime, "$options": "i"}

    # RARITY FILTER
    if rarity != "0":
        query["rarity"] = RARITY_MAP.get(int(rarity))

    docs = list(media_collection.find(query))

    results = []
    for doc in docs:
        if "vid_url" in doc:
            results.append({
                "media_id": str(doc.get("id")),
                "type": "video",
                "url": doc["vid_url"],
                "name": doc.get("name"),
                "anime": doc.get("anime"),
                "rarity": doc.get("rarity")
            })
        elif "img_url" in doc:
            results.append({
                "media_id": str(doc.get("id")),
                "type": "image",
                "url": doc["img_url"],
                "name": doc.get("name"),
                "anime": doc.get("anime"),
                "rarity": doc.get("rarity")
            })

    return jsonify({"results": results})

# =======================
# LIKE MEDIA
# =======================
@app.route("/media/like", methods=["POST"])
def like_media():
    media_id = request.json.get("media_id")

    engagement_collection.update_one(
        {"media_id": media_id},
        {"$inc": {"likes": 1}},
        upsert=True
    )

    return jsonify({"success": True})

# =======================
# COMMENT MEDIA
# =======================
@app.route("/media/comment", methods=["POST"])
def comment_media():
    data = request.json

    engagement_collection.update_one(
        {"media_id": data["media_id"]},
        {"$push": {
            "comments": {
                "user": data.get("user", "anon"),
                "text": data["text"]
            }
        }},
        upsert=True
    )

    return jsonify({"success": True})

# =======================
# GET COMMENTS + LIKES
# =======================
@app.route("/media/<media_id>/engagement", methods=["GET"])
def get_engagement(media_id):
    doc = engagement_collection.find_one({"media_id": media_id}) or {}
    return jsonify({
        "likes": doc.get("likes", 0),
        "comments": doc.get("comments", [])
    })

# Search user by ID and get their characters array
@app.route('/user/search', methods=['GET'])
def search_user_collection():
    user_id = request.args.get('user_id', '')
    if user_id:
        user = user_collection.find_one({'user_id': user_id})
        if user:
            characters = user.get('characters', [])  # Assuming 'characters' is an array in user collection
            return jsonify({
                'user_id': user_id,
                'characters': characters
            })
        else:
            return jsonify({'error': 'User not found'}), 404
    else:
        return jsonify({'error': 'User ID is required'}), 400

# Serve user's collection via URL
@app.route('/user/<string:user_id>/collection', methods=['GET'])
def get_user_collection(user_id):
    user = user_collection.find_one({'user_id': user_id})
    if user:
        characters = user.get('characters', [])  # Assuming 'characters' is an array in user collection
        return jsonify({
            'user_id': user_id,
            'characters': characters
        })
    else:
        return jsonify({'error': 'User not found'}), 404
        

# =======================
# RUN
# =======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
