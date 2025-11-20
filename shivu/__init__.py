import logging  #

import os

from pyrogram import Client as PyrogramClient
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from resolve_peer import ResolvePeer

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
logging.getLogger("apscheduler").setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrate_limiter").setLevel(logging.ERROR)
LOGGER = logging.getLogger(__name__)



from moto.Config import *

class Client(PyrogramClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def resolve_peer(self, id):
        obj = ResolvePeer(self)
        return await obj.resolve_peer(id)


applicationps = Application.builder().token(TOKENsingings).concurrent_updates(True).build()
shivuups = Client("Shivu", api_id, api_hash, bot_token=TOKENsingings)
#app = TelegramClient('bot', api_id, api_hash).start(bot_token=TOKEN)

lol = AsyncIOMotorClient(mongo_urlings)
dbps = lol['NARUTOGAMEBOT']
#dbps = lol['AR']
dm_collection = dbps["started_users"]

collectionps = dbps['anime_characters_lol']
user_totals_collectionps = dbps['user_totals_lmaoooo']
user_collectionps = dbps["user_collection_lmaoooo"]
giveaway_collectionps = dbps["giveaway_collection"]
puzzle_collectionps = dbps["puzzle_collection"]
group_user_totals_collectionps = dbps['group_user_totalsssssss']
top_global_groups_collectionps = dbps['top_global_groups']
pm_usersps = dbps['total_pm_users']
pmusersps = dbps['total_pm_users']
users_collectionps = dbps['users']
chat_dataps = dbps['chat_data']
daily_shopps = dbps['sship']
shops_collectionps = dbps['shoping']
ban_collectionps = dbps['bans']
main_countps = dbps['counts']
user_countps = dbps['ucount']
banned_collectionps = dbps['banned']
anime_collection = dbps['anime']


    

guild = dbps["guild_team"]
gban = dbps["gban"]
clan_collection = dbps['clans']
join_requests_collection = dbps['join_requests']
global_ban_users_collection = dbps['global_ban_users']
users_collection = dbps['user']
videos_collection = dbps['videos']
sales_collection = dbps['sales']
blocked_users_collection = dbps["blocked_users"]

safari_cooldown_collection = dbps['safari_cooldown_collection']
safari_users_collection = dbps['safari_users_collection']
