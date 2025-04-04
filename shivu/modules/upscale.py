import os
import base64
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageEnhance
from shivu import shivuups as app

async def enhance_image(image_path: str) -> str:
    """Enhance image brightness and saturation"""
    try:
        image = Image.open(image_path)
        
        # Increase exposure (brightness)
        brightness_enhancer = ImageEnhance.Brightness(image)
        image = brightness_enhancer.enhance(1.1)  # +10% brightness
        
        # Increase saturation (color)
        color_enhancer = ImageEnhance.Color(image)
        image = color_enhancer.enhance(1.1)  # +10% saturation
        
        # Save the enhanced image
        enhanced_path = "enhanced_" + os.path.basename(image_path)
        image.save(enhanced_path, quality=95)  # Reduced quality to avoid processing errors
        
        return enhanced_path
    except Exception as e:
        raise Exception(f"Enhancement failed: {str(e)}")

async def upscale_image(image_path: str) -> str:
    """Upscale image using external API"""
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://lexica.qewertyy.dev/upscale", 
                data={"image_data": encoded},
                timeout=30
            ) as r:
                if r.status != 200:
                    raise Exception(f"Upscale API returned status {r.status}")
                
                upscaled_path = "upscaled_" + os.path.basename(image_path)
                with open(upscaled_path, "wb") as out:
                    out.write(await r.read())
        
        return upscaled_path
    except Exception as e:
        raise Exception(f"Upscaling failed: {str(e)}")

@app.on_message(filters.command("enhanceup") & filters.reply)
async def enhance_and_upscale(client: Client, message: Message):
    replied = message.reply_to_message
    
    if not replied.photo:
        await message.reply_text("⚠️ Please reply to an image!")
        return
    
    try:
        # Send initial progress message
        progress = await message.reply("🔄 Processing your image...")
        
        # Download the image
        photo_path = await replied.download()
        
        try:
            # Step 1: Enhance the image
            await progress.edit_text("🎨 Enhancing image...")
            enhanced_path = await enhance_image(photo_path)
            
            try:
                # Step 2: Upscale the enhanced image
                await progress.edit_text("🖼️ Upscaling image...")
                upscaled_path = await upscale_image(enhanced_path)
                
                # Send the final result
                try:
                    await message.reply_photo(
                        photo=upscaled_path,
                        caption=f"✅ **Enhanced & Upscaled Image**\nBy @{client.me.username}"
                    )
                    await progress.delete()
                except Exception as e:
                    await progress.edit_text(f"📤 Failed to send result: {str(e)}")
                    raise
                
            except Exception as upscale_error:
                await progress.edit_text(f"❌ Upscaling failed. Sending enhanced version...")
                try:
                    await message.reply_photo(
                        photo=enhanced_path,
                        caption=f"✅ **Enhanced Image (Upscale Failed)**\nBy @{client.me.username}"
                    )
                except Exception as e:
                    await progress.edit_text(f"❌ Completely failed: {str(e)}")
                    raise upscale_error
                
        except Exception as enhance_error:
            await progress.edit_text(f"❌ Enhancement failed. Sending original...")
            try:
                await message.reply_photo(
                    photo=photo_path,
                    caption=f"⚠️ **Original Image (Processing Failed)**\nBy @{client.me.username}"
                )
            except Exception as e:
                await progress.edit_text(f"❌ Complete failure: {str(e)}")
                raise enhance_error
            
    except Exception as e:
        # If we can't edit the progress message, send a new one
        try:
            await message.reply_text(f"❌ Processing failed: {str(e)}")
        except:
            pass  # If even this fails, there's nothing more we can do
            
    finally:
        # Clean up temporary files
        for path in [photo_path, enhanced_path, upscaled_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
