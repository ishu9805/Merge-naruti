from flask import Flask, jsonify
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

app = Flask(__name__)

# MongoDB connection URL
mongo_url = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(mongo_url)
db = client['Character_catcher']
collection = db['anime_characters_lol']

# Fetch waifus endpoint
@app.route('/waifus', methods=['GET'])
async def get_waifus():
    waifus = []
    async for document in collection.find():
        waifus.append({
            'character_name': document['character_name'],
            'anime_name': document['anime_name'],
            'img_url': document['img_url'],
            'id': document['id']
        })
    return jsonify(waifus)

# Run the Flask app
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run_task())
