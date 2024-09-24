from flask_cors import CORS
from pymongo import MongoClient
import requests
from flask import Flask, jsonify, send_from_directory, request, Response


from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client
import os

# Initialize Flask app
app = Flask(__name__, static_folder='frontend/static')
CORS(app)

# Initialize Pyrogram bot with your token, API ID, and API hash
BOT_TOKEN = "7540585353:AAHhU11Hpi_JtVHoaqLvlaAVMR0CWXKm9vs"
API_ID = 22792918  # Your API ID
API_HASH = "ff10095d2bb96d43d6eb7a7d9fc85f81"  # Your API Hash

# Initialize bot instance
bot = Client("my_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Chat ID where the message will be sent (replace with your chat/group ID)
CHAT_ID = "-1002434689265"

# APScheduler to schedule jobs
scheduler = BackgroundScheduler()

# Function to send a message every minute
def send_periodic_message():
    with bot:
        bot.send_message(CHAT_ID, "This is a periodic message sent every minute.")

# Route to start the scheduler (triggers message sending every minute)
@app.route('/start', methods=['POST'])
def start_schedule():
    scheduler.add_job(send_periodic_message, 'interval', minutes=1)  # Schedules the task every minute
    scheduler.start()
    return jsonify({"status": "Started sending messages every minute."})

# Route to stop the scheduler
@app.route('/stop', methods=['POST'])
def stop_schedule():
    scheduler.remove_all_jobs()  # Removes all scheduled jobs
    return jsonify({"status": "Stopped sending messages."})







# MongoDB connection URL
mongo_url = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_url)
db = client['Character_catcher']
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
