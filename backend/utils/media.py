def resolve_media(doc):
    if doc.get("vid_url"):
        return {
            "media_type": "video",
            "media_url": doc["vid_url"]
        }

    return {
        "media_type": "image",
        "media_url": doc.get("img_url")
    }
