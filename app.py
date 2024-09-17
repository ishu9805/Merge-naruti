from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from pymongo import MongoClient

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
    # Get query parameters from the request
    name_query = request.args.get('name', None)
    anime_query = request.args.get('anime', None)
    rarity_query = request.args.get('rarity', None)
    id_query = request.args.get('id', None)

    # Build the query dictionary based on filters
    query = {}
    if name_query:
        query['name'] = {'$regex': f'^{name_query}', '$options': 'i'}  # Case-insensitive prefix match
    if anime_query:
        query['anime'] = {'$regex': f'^{anime_query}', '$options': 'i'}
    if rarity_query:
        query['rarity'] = {'$regex': f'^{rarity_query}', '$options': 'i'}
    if id_query:
        query['id'] = id_query  # Assuming ID is an exact match

    try:
        waifus = list(collection.find(query))
        results = [{
            'character_name': waifu.get('name', 'Unknown'),
            'anime_name': waifu.get('anime', 'Unknown'),
            'image_url': waifu.get('img_url', ''),
            'rarity': waifu.get('rarity', 'Unknown'),
            'id': waifu.get('id', 'N/A')
        } for waifu in waifus]
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            'character_name': waifu.get('name', 'Unknown'),
            'anime_name': waifu.get('anime', 'Unknown'),
            'image_url': waifu.get('img_url', ''),
            'rarity': waifu.get('rarity', 'Unknown'),
            'id': waifu.get('id', 'N/A')
        } for waifu in waifus]

        return jsonify({'results': results, 'hasNextPage': has_next_page})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/waifus/<string:character_name>', methods=['GET'])
def get_waifu(character_name):
    try:
        waifu = collection.find_one({'name': {'$regex': f'^{character_name}', '$options': 'i'}})
        if waifu:
            return jsonify({
                'character_name': waifu.get('name', 'Unknown'),
                'anime_name': waifu.get('anime', 'Unknown'),
                'image_url': waifu.get('img_url', ''),
                'rarity': waifu.get('rarity', 'Unknown'),
                'id': waifu.get('id', 'N/A')
            })
        else:
            return jsonify({'error': 'Waifu not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
