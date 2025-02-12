import logging  #
import os
from pyrogram import Client 
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from resolve_peer import ResolvePeer


from .config import *

class Client(PyrogramClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def resolve_peer(self, id):
        obj = ResolvePeer(self)
        return await obj.resolve_peer(id)


application = Application.builder().token(TOKEN).concurrent_updates(True).build()
shivuu = Client("Shivu", api_id, api_hash, bot_token=TOKEN)
#app = TelegramClient('bot', api_id, api_hash).start(bot_token=TOKEN)

lol = AsyncIOMotorClient(mongo_url)
db = lol['Character_catcher']
collection = db['anime_characters_lol']
user_totals_collection = db['user_totals_lmaoooo']
user_collection = db["user_collection_lmaoooo"]
group_user_totals_collection = db['group_user_totalsssssss']
top_global_groups_collection = db['top_global_groups']
pm_users = db['total_pm_users']
users_collection = db['users']
shops_collection = db['shoping']
ban_collection = db['bans']
main_count = db['counts']
user_count = db['ucount']
banned_collection = db['banned']

guild = db["guild_team"]
gban = db["gban"]
clan_collection = db['clans']
join_requests_collection = db['join_requests']
global_ban_users_collection = db['global_ban_users']
users_collection = db['user']
videos_collection = db['videos']
sales_collection = db['sales']
blocked_users_collection = db["blocked_users"]

safari_cooldown_collection = db['safari_cooldown_collection']
safari_users_collection = db['safari_users_collection']
