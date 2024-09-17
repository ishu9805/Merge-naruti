from flask import Flask, jsonify, send_from_directory
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import re

app = Flask(__name__, static_folder='frontend/static')

# MongoDB connection URL
mongo_url = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(mongo_url)
db = client['Character_catcher']
collection = db['anime_characters_lol']

@app.route('/')
def home():
    return send_from_directory('frontend/static', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend/static', filename)

@app.route('/waifus/search', methods=['GET'])
async def search_waifus():
    query = request.args.get('query', '')
    regex_pattern = re.compile(query, re.IGNORECASE)
    cursor = collection.find({'character_name': regex_pattern})
    results = []
    async for document in cursor:
        results.append({
            'character_name': document['character_name'],
            'anime_name': document['anime_name'],
            'image_url': document['image_url'],
            'rarity': document.get('rarity', 'Unknown')  # Add rarity if present
        })
    return jsonify(results)

@app.route('/waifus/<string:character_name>', methods=['GET'])
async def get_waifu(character_name):
    regex_pattern = re.compile(character_name, re.IGNORECASE)
    waifu = await collection.find_one({'character_name': regex_pattern})
    if waifu:
        return jsonify({
            'character_name': waifu['character_name'],
            'anime_name': waifu['anime_name'],
            'image_url': waifu['image_url']
        })
    else:
        return jsonify({'error': 'Waifu not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
