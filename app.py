
from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = "32db2c898fbeb5d41a6bc341e0e68938dee3360b4e6a75250e1dda606ee880a7"
CORS(app)

# Configure logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

# Database connection
mongo_uri = "mongodb+srv://abhi47903:sashtadev143@naruto.svojv.mongodb.net/"
client = MongoClient(mongo_uri)
db = client['NARUTOGAMEBOT']

# Collections
characters_collection = db['anime_characters_lol']
users_collection = db['users']
collections_collection = db['user_collection_lmaoooo']

# Rate limiting setup (requires Redis)
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# limiter = Limiter(app, key_func=get_remote_address)

# JWT authentication decorator

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        try:
            data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = users_collection.find_one({'username': data['username']})
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400
        
    # Check if user exists
    if users_collection.find_one({'username': data['username']}):
        return jsonify({'message': 'User already exists'}), 400
        
    # Create new user
    hashed_password = generate_password_hash(data['password'], method='sha256')
    users_collection.insert_one({
        'username': data['username'],
        'password': hashed_password,
        'created_at': datetime.utcnow()
    })
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400
        
    # Find user
    user = users_collection.find_one({'username': data['username']})
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
        
    # Generate token
    token = jwt.encode({
        'username': user['username'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'])
    
    return jsonify({'token': token}), 200

# Enhanced character search with pagination and caching
@app.route('/waifus/search', methods=['GET'])
# @limiter.limit("60 per minute")  # Rate limiting
def search_waifus():
    try:
        # Get query parameters
        name = request.args.get('name', '').strip()
        anime = request.args.get('anime', '').strip()
        rarity = request.args.get('rarity', '').strip()
        character_id = request.args.get('id', '').strip()
        
        # Pagination
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 12))
        skip = (page - 1) * size
        
        # Build query
        query = {}
        if name:
            query['name'] = {'$regex': name, '$options': 'i'}
        if anime:
            query['anime'] = {'$regex': anime, '$options': 'i'}
        if rarity:
            query['rarity'] = {'$regex': rarity, '$options': 'i'}
        if character_id:
            query['id'] = {'$regex': character_id, '$options': 'i'}
        
        # Get total count for pagination
        total = characters_collection.count_documents(query)
        
        # Fetch paginated results
        characters = list(characters_collection.find(query)
                         .sort('id', -1)
                         .skip(skip)
                         .limit(size))
        
        # Prepare response
        results = [{
            'character_name': char['name'],
            'anime_name': char['anime'],
            'image_url': char['img_url'],
            'rarity': char.get('rarity', 'Unknown'),
            'id': str(char.get('id', ''))
        } for char in characters]
        
        return jsonify({
            'results': results,
            'total': total,
            'page': page,
            'size': size,
            'hasNextPage': (skip + size) < total
        })
        
    except Exception as e:
        app.logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Collection management
@app.route('/api/collection', methods=['GET'])
@token_required
def get_user_collection(current_user):
    try:
        collection = collections_collection.find_one({'user_id': current_user['_id']})
        if not collection:
            return jsonify({'characters': []})
            
        # Get character details
        character_ids = [ObjectId(char_id) for char_id in collection['characters']]
        characters = list(characters_collection.find({'_id': {'$in': character_ids}}))
        
        results = [{
            'character_name': char['name'],
            'anime_name': char['anime'],
            'image_url': char['img_url'],
            'rarity': char.get('rarity', 'Unknown'),
            'id': str(char.get('id', ''))
        } for char in characters]
        
        return jsonify({'characters': results})
        
    except Exception as e:
        app.logger.error(f"Collection error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/collection', methods=['POST'])
@token_required
def add_to_collection(current_user):
    try:
        data = request.get_json()
        character_id = data.get('character_id')
        
        if not character_id:
            return jsonify({'message': 'Character ID required'}), 400
            
        # Find or create user collection
        collections_collection.update_one(
            {'user_id': current_user['_id']},
            {'$addToSet': {'characters': character_id}},
            upsert=True
        )
        
        return jsonify({'message': 'Character added to collection'}), 200
        
    except Exception as e:
        app.logger.error(f"Add to collection error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
