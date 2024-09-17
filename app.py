from flask import Flask, jsonify, send_from_directory
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

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

@app.route('/waifus', methods=['GET'])
async def get_waifus():
    waifus = []
    async for document in collection.find():
        waifus.append({
            'character_name': document['character_name'],
            'anime_name': document['anime_name'],
            'image_url': document['image_url']
        })
    return jsonify(waifus)

@app.route('/waifus/<string:character_name>', methods=['GET'])
async def get_waifu(character_name):
    waifu = await collection.find_one({'character_name': character_name})
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
