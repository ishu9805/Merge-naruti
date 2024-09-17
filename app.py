from flask import Flask, jsonify, request
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

app = Flask(__name__)

# MongoDB connection URL
mongo_url = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(mongo_url)
db = client['Character_catcher']
collection = db['anime_characters_lol']

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

@app.route('/waifus', methods=['POST'])
async def add_waifu():
    data = request.json
    result = await collection.insert_one(data)
    return jsonify({'inserted_id': str(result.inserted_id)}), 201

@app.route('/waifus/<string:character_name>', methods=['DELETE'])
async def delete_waifu(character_name):
    result = await collection.delete_one({'character_name': character_name})
    if result.deleted_count > 0:
        return jsonify({'message': 'Waifu deleted successfully'})
    else:
        return jsonify({'error': 'Waifu not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
