from flask_cors import CORS
from pymongo import MongoClient
import requests
from flask import Flask, jsonify, send_from_directory, request, Response



# Other routes...


app = Flask(__name__, static_folder='static')
CORS(app)

# MongoDB connection URL
mongo_url = "mongodb+srv://abhi47903:sashtadev143@naruto.svojv.mongodb.net/"
client = MongoClient(mongo_url)
db = client['NARUTOGAMEBOT']
collection = db['anime_characters_lol']
user_collection = db['user_characters']  # Collection storing user collections with a 'characters' array

@app.route('/proxy-image/<path:url>')
def proxy_image(url):
    telegraph_url = f"https://telegra.ph/{url}"
    try:
        response = requests.get(telegraph_url, stream=True)
        response.raise_for_status()
        return Response(response.content, mimetype=response.headers['Content-Type'])
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Image not found or could not be retrieved'}), 404
    
# Serve homepage
@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

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
            'image_url': f"/proxy-image/{waifu['img_url'].replace('https://telegra.ph/', '')}",
            'rarity': waifu.get('rarity', 'Unknown'),
            'id': waifu.get('id', 'N/A')
        } for waifu in waifus]

        return jsonify({'results': results, 'hasNextPage': has_next_page})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Get specific waifu by character name
@app.route('/waifus/<string:character_name>', methods=['GET'])
def get_waifu(character_name):
    waifu = collection.find_one({'name': {'$regex': character_name, '$options': 'i'}})
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
