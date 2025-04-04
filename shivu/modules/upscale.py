import os
import base64
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageEnhance
from shivu import shivuups as app

async def upscale_image(image_path: str) -> str:
    """Upscale image using external API"""
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://lexica.qewertyy.dev/upscale",
                data={"image_data": encoded},
                timeout=30
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
                
                upscaled_path = "upscaled_" + os.path.basename(image_path)
                with open(upscaled_path, "wb") as out:
                    out.write(await response.read())
                
                # Verify the upscaled image is valid
                try:
                    Image.open(upscaled_path).verify()
                    return upscaled_path
                except:
                    raise Exception("Upscaled image is corrupted")
                
    except Exception as e:
        raise Exception(f"Upscaling failed: {str(e)}")

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
        
        # Save the enhanced image with optimized quality
        enhanced_path = "enhanced_" + os.path.basename(image_path)
        image.save(enhanced_path, quality=95, optimize=True)
        
        return enhanced_path
    except Exception as e:
        raise Exception(f"Enhancement failed: {str(e)}")

@app.on_message(filters.command("upenhance") & filters.reply)
async def upscale_and_enhance(client: Client, message: Message):
    replied = message.reply_to_message
    
    if not replied.photo:
        await message.reply_text("⚠️ Please reply to an image!")
        return
    
    # Initialize variables
    photo_path = upscaled_path = enhanced_path = None
    progress = None
    
    try:
        # Send initial progress message
        progress = await message.reply("🔄 Starting image processing...")
        
        # 1. Download the original image
        await progress.edit_text("⬇️ Downloading image...")
        photo_path = await replied.download()
        
        try:
            # 2. Upscale the image first
            await progress.edit_text("🖼️ Upscaling image...")
            upscaled_path = await upscale_image(photo_path)
            
            try:
                # 3. Enhance the upscaled image
                await progress.edit_text("🎨 Enhancing image...")
                enhanced_path = await enhance_image(upscaled_path)
                
                # 4. Send final result
                await progress.edit_text("📤 Sending result...")
                await message.reply_photo(
                    photo=enhanced_path,
                    caption=f"✨ **Upscaled & Enhanced Image**\nBy @{client.me.username}"
                )
                await progress.delete()
                
            except Exception as enhance_error:
                # If enhancement fails, send the upscaled version
                await progress.edit_text("⚠️ Enhancement failed. Sending upscaled version...")
                await message.reply_photo(
                    photo=upscaled_path,
                    caption=f"✨ **Upscaled Image** (Enhancement failed)\nBy @{client.me.username}"
                )
                await progress.delete()
                
        except Exception as upscale_error:
            # If upscaling fails, try to enhance the original
            await progress.edit_text("⚠️ Upscaling failed. Trying to enhance original...")
            try:
                enhanced_path = await enhance_image(photo_path)
                await message.reply_photo(
                    photo=enhanced_path,
                    caption=f"✨ **Enhanced Original** (Upscale failed)\nBy @{client.me.username}"
                )
                await progress.delete()
            except Exception as enhance_error:
                # If both fail, send the original
                await progress.edit_text("⚠️ Both upscaling and enhancement failed. Sending original...")
                await message.reply_photo(
                    photo=photo_path,
                    caption=f"⚠️ **Original Image** (Processing failed)\nBy @{client.me.username}"
                )
                await progress.delete()
            
    except Exception as main_error:
        error_msg = f"❌ Processing failed: {str(main_error)}"
        
        # Try to send error message in the most reliable way
        try:
            if progress:
                await progress.edit_text(error_msg)
            else:
                await message.reply_text(error_msg)
        except:
            try:
                await message.reply_text(error_msg)
            except:
                pass  # Final fallback if everything fails
            
    finally:
        # Cleanup files in a safe way
        for path in [photo_path, upscaled_path, enhanced_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
