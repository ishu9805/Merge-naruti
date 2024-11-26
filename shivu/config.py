class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "7378476666"
    sudo_users = "7378476666", "760680138", "1269025261", "6581286400"
    PARTNER =  "7378476666"
    GROUP_ID = -1002198664660
    TOKENs = "7229186679:AAFndhb6e5evZ8MTxTLOw27Dhjed1hbQ_tg"
    TOKEN = "7107840748:AAFxVNPZa3ob6DO1U7GuszLAeItFL9rX2j4"
    mongo_url = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    PHOTO_URL = ["https://telegra.ph/file/a75e0d1a655943665b662.jpg", "https://telegra.ph/file/bee112f781897c3447515.jpg", "https://telegra.ph/file/a0123f958a26695bd9e14.jpg"]
    SUPPORT_CHAT = "-1002338924488"
    UPDATE_CHAT = "Nᴀʀᴜᴛᴏ Uᴘᴅᴀᴛᴇs"
    BOT_USERNAME = "Fancy_Waifu_Husbando_Bot"
    CHARA_CHANNEL_ID = "-1002117539029"
    api_id = 22792918
    api_hash = "ff10095d2bb96d43d6eb7a7d9fc85f81"
    
    STRICT_GBAN = True
    ALLOW_CHATS = True
    ALLOW_EXCL = True
    DEL_CMDS = True
    INFOPIC = True

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
