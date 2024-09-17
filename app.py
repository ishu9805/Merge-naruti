from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from pymongo import MongoClient
import re

app = Flask(__name__, static_folder='frontend/static')
CORS(app)

# MongoDB connection URL
mongo_url = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_url)
db = client['Character_catcher']
collection = db['anime_characters_lol']

@app.route('/')
def home():
    return send_from_directory('frontend/static', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend/static', filename)

@app.route('/waifus/search', methods=['GET'])
def search_waifus():
    query = request.args.get('query', '')
    regex_pattern = re.compile(f".*{re.escape(query)}.*", re.IGNORECASE)
    waifus = list(collection.find({'name': regex_pattern}))
    results = [{
        'character_name': waifu['name'],
        'anime_name': waifu['anime'],
        'image_url': waifu['img_url'],
        'rarity': waifu.get('rarity', 'Unknown'),
        'id': waifu.get('id', 'N/A')
    } for waifu in waifus]
    return jsonify({'results': results})

@app.route('/waifus', methods=['GET'])
def get_characters():
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 15))
        skip = (page - 1) * size
        limit = size

        total_count = collection.count_documents({})
        has_next_page = (total_count > page * size)

        waifus = list(collection.find().skip(skip).limit(limit))
        results = [{
            'character_name': waifu['name'],
            'anime_name': waifu['anime'],
            'image_url': waifu['img_url'],
            'rarity': waifu.get('rarity', 'Unknown'),
            'id': waifu.get('id', 'N/A')
        } for waifu in waifus]

        return jsonify({'results': results, 'hasNextPage': has_next_page})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/waifus/<string:character_name>', methods=['GET'])
def get_waifu(character_name):
    regex_pattern = re.compile(f".*{re.escape(character_name)}.*", re.IGNORECASE)
    waifu = collection.find_one({'name': regex_pattern})
    if waifu:
        return jsonify({
            'character_name': waifu['name'],
            'anime_name': waifu['anime'],
            'image_url': waifu['img_url'],
            'rarity': waifu.get('rarity', 'Unknown'),
            'id': waifu.get('id', 'N/A')
        })
    else:
        return jsonify({'error': 'Waifu not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
