from flask_cors import CORS
from pymongo import MongoClient
from flask import Flask, jsonify, send_from_directory, request, Response

app = Flask(__name__, static_folder='frontend/static')
CORS(app)

# MongoDB connection URL
mongo_url = "mongodb+srv://abhi47903:sashtadev143@naruto.svojv.mongodb.net/"
client = MongoClient(mongo_url)
db = client['NARUTOGAMEBOT']
collection = db['anime_characters_lol']
user_collection = db['user_collection_lmaoooo']  # Collection storing user collections with a 'characters' array

# Serve homepage
@app.route('/')
def home():
    return send_from_directory('frontend/static', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend/static', filename)

# Search waifus by name, anime, rarity, or ID
@app.route('/waifus/search', methods=['GET'])
def search_waifus():
    name_query = request.args.get('name', '')
    anime_query = request.args.get('anime', '')
    rarity_query = request.args.get('rarity', '')
    id_query = request.args.get('id', '')

    query_filters = {}
    if name_query:
        query_filters['name'] = {'$regex': name_query, '$options': 'i'}
    if anime_query:
        query_filters['anime'] = {'$regex': anime_query, '$options': 'i'}
    if rarity_query:
        query_filters['rarity'] = {'$regex': rarity_query, '$options': 'i'}
    if id_query:
        query_filters['id'] = {'$regex': id_query, '$options': 'i'}

    waifus = list(collection.find(query_filters))
    results = []
    for waifu in waifus:
        media_url = waifu.get('vid_url') or waifu.get('img_url')
        results.append({
            'character_name': waifu['name'],
            'anime_name': waifu['anime'],
            'media_url': media_url,
            'rarity': waifu.get('rarity', 'Unknown'),
            'id': waifu.get('id', 'N/A')
        })

    return jsonify({'results': results})

# Paginated characters
@app.route('/waifus', methods=['GET'])
def get_characters():
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 15))
        skip = (page - 1) * size

        total_count = collection.count_documents({})
        has_next_page = total_count > (page * size)

        waifus = list(collection.find().skip(skip).limit(size))
        results = []
        for waifu in waifus:
            media_url = waifu.get('vid_url') or waifu.get('img_url')
            results.append({
                'character_name': waifu['name'],
                'anime_name': waifu['anime'],
                'media_url': media_url,
                'rarity': waifu.get('rarity', 'Unknown'),
                'id': waifu.get('id', 'N/A')
            })

        return jsonify({'results': results, 'hasNextPage': has_next_page})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get specific waifu by character name
@app.route('/waifus/<string:character_name>', methods=['GET'])
def get_waifu(character_name):
    waifu = collection.find_one({'name': {'$regex': character_name, '$options': 'i'}})
    if waifu:
        media_url = waifu.get('vid_url') or waifu.get('img_url')
        return jsonify({
            'character_name': waifu['name'],
            'anime_name': waifu['anime'],
            'media_url': media_url,
            'rarity': waifu.get('rarity', 'Unknown'),
            'id': waifu.get('id', 'N/A')
        })
    else:
        return jsonify({'error': 'Waifu not found'}), 404

# Search user by ID and get their characters array
@app.route('/user/search', methods=['GET'])
def search_user_collection():
    user_id = request.args.get('user_id', '')
    if user_id:
        user = user_collection.find_one({'user_id': user_id})
        if user:
            characters = user.get('characters', [])
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
        characters = user.get('characters', [])
        return jsonify({
            'user_id': user_id,
            'characters': characters
        })
    else:
        return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
