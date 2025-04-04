import os
import base64
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageEnhance
from shivu import shivuups as app

async def enhance_image(image_path: str) -> str:
    """Enhance image brightness and saturation"""
    image = Image.open(image_path)
    
    # Increase exposure (brightness)
    brightness_enhancer = ImageEnhance.Brightness(image)
    image = brightness_enhancer.enhance(1.1)  # +10% brightness
    
    # Increase saturation (color)
    color_enhancer = ImageEnhance.Color(image)
    image = color_enhancer.enhance(1.2)  # +10% saturation
    
    # Save the enhanced image
    enhanced_path = "enhanced_" + os.path.basename(image_path)
    image.save(enhanced_path)
    
    return enhanced_path

async def upscale_image(image_path: str) -> str:
    """Upscale image using external API"""
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    
    async with aiohttp.ClientSession() as s:
        async with s.post("https://lexica.qewertyy.dev/upscale", data={"image_data": encoded}) as r:
            upscaled_path = "upscaled_" + os.path.basename(image_path)
            with open(upscaled_path, "wb") as out:
                out.write(await r.read())
    
    return upscaled_path

@app.on_message(filters.command("upscale") & filters.reply)
async def enhance_and_upscale(client: Client, message: Message):
    replied = message.reply_to_message
    
    if not replied.photo:
        await message.reply_text("⚠️ Please reply to an image!")
        return
    
    # Download the image
    progress = await message.reply("⬇️ Downloading image...")
    photo_path = await replied.download()
    
    try:
        # Step 1: Enhance the image
        await progress.edit_text("🎨 Enhancing image...")
        enhanced_path = await enhance_image(photo_path)
        
        # Step 2: Upscale the enhanced image
        await progress.edit_text("🖼️ Upscaling image...")
        upscaled_path = await upscale_image(enhanced_path)
        
        # Send the final result
        await progress.delete()
        await message.reply_photo(
            photo=upscaled_path,
            caption=f"✅ **Image**\nBy @{client.me.username}"
        )
        
    except Exception as e:
        await progress.edit_text(f"❌ Error: {e}")
    
    # Clean up temporary files
    for path in [photo_path, enhanced_path, upscaled_path]:
        if path and os.path.exists(path):
            os.remove(path)
