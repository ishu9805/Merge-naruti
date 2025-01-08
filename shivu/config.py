class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "7378476666"
    sudo_users = "5578365728", "7378476666", "6759666329", "6965783469", "5316848198", "7228816990", "1118244185", "7469481988", "1744744841", "1017948073", "7036155390"
    PARTNER =  "7378476666", "1744744841"
    GROUP_ID = -1002198664660
    TOKEN = "7187229883:AAFO_cZf76s6dDupZc-PJ_6la9iFoLxY-tI"
    #TOKEN = "7107840748:AAHuqgu6Cc7eCGAHOemyyVtLiak50A-X73U"
    mongo_url = "mongodb+srv://babusona:hinatababy@cluster0.t0lfelh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    PHOTO_URL = ["https://telegra.ph/file/a75e0d1a655943665b662.jpg", "https://telegra.ph/file/bee112f781897c3447515.jpg", "https://telegra.ph/file/a0123f958a26695bd9e14.jpg"]
    SUPPORT_CHAT = "-1002338924488"
    UPDATE_CHAT = "Nᴀʀᴜᴛᴏ Uᴘᴅᴀᴛᴇs"
    BOT_USERNAME = "Fancy_Waifu_Husbando_Bot"
    CHARA_CHANNEL_ID = "-1002117539029"
    api_id = 22792918
    api_hash = "ff10095d2bb96d43d6eb7a7d9fc85f81"
    required_group_id = -1001999201034
    STRICT_GBAN = True
    ALLOW_CHATS = True
    ALLOW_EXCL = True
    DEL_CMDS = True
    INFOPIC = True

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
