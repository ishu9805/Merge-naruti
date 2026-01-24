from pymongo import MongoClient

MONGO_URI = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "NARUTOGAMEBOT"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

global_collection = db["anime_characters_lol"]
user_collection = db["user_collection_lmaoooo"]
