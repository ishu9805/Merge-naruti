import os
import requests
import aiofiles
import httpx
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageEnhance
from shivu import shivuups as app

async def download_image(url: str, save_path: str) -> bool:
    """Download image from URL"""
    try:
        async with aiofiles.open(save_path, 'wb') as f:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                await f.write(response.content)
        return True
    except Exception:
        return False

async def enhance_image(image_path: str) -> str:
    """Enhance image brightness (+15%) and saturation (+15%)"""
    try:
        with Image.open(image_path) as img:
            # Enhance brightness
            brightness_enhancer = ImageEnhance.Brightness(img)
            img = brightness_enhancer.enhance(1.1)
            
            # Enhance color saturation
            color_enhancer = ImageEnhance.Color(img)
            img = color_enhancer.enhance(1.2)
            
            # Save optimized version
            enhanced_path = f"enhanced_{os.path.basename(image_path)}"
            img.save(enhanced_path, quality=95, optimize=True)
            return enhanced_path
    except Exception as e:
        raise Exception(f"Enhancement failed: {str(e)}")

async def upscale_image(image_path: str) -> str:
    """Upscale image 2x using DeepAI API"""
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(
                "https://api.deepai.org/api/torch-srgan",
                files={'image': f},
                headers={'api-key': 'bf9ee957-9fad-46f5-a403-3e96ca9004e4'},
                timeout=30
            )
        
        response.raise_for_status()
        data = response.json()
        
        if not data.get("output_url"):
            raise Exception("No output URL received from API")
            
        upscaled_path = f"upscaled_{os.path.basename(image_path)}"
        if not await download_image(data["output_url"], upscaled_path):
            raise Exception("Failed to download upscaled image")
            
        # Verify image is valid
        with Image.open(upscaled_path) as img:
            img.verify()
            
        return upscaled_path
    except Exception as e:
        raise Exception(f"Upscaling failed: {str(e)}")

@app.on_message(filters.command(["enhanceup", "upenhance"]) & filters.reply)
async def enhance_then_upscale(client: Client, message: Message):
    """First enhance then upscale the image"""
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("⚠️ Please reply to an image!")
    
    progress = await message.reply("🔄 Starting image processing...")
    original_path = enhanced_path = upscaled_path = None
    
    try:
        # Step 1: Download original
        original_path = await message.reply_to_message.download()
        
        # Step 2: Enhance first
        try:
            await progress.edit_text("🎨 upscaling image...")
            enhanced_path = await enhance_image(original_path)
            asyncio.sleep(2)
            
            # Step 3: Then upscale
            try:
                await progress.edit_text("🖼️ Upscaling 2 image...")
                upscaled_path = await upscale_image(enhanced_path)
                
                await progress.edit_text("📤 Sending result...")
                await message.reply_photo(
                    photo=upscaled_path,
                    caption="✨ **Upscaled** (+ 2X)"
                )
                
            except Exception as upscale_error:
                # If upscaling fails, send enhanced version
                await progress.edit_text("⚠️ U failed. Sending e version...")
                await message.reply_photo(
                    photo=enhanced_path,
                    caption="✨ **Enhanced Image** (U failed)"
                )
                
        except Exception as enhance_error:
            # If enhancement fails, try upscaling original
            try:
                await progress.edit_text("⚠️ e failed. Trying upscaling...")
                upscaled_path = await upscale_image(original_path)
                
                await message.reply_photo(
                    photo=upscaled_path,
                    caption="✨ **Upscaled Original** (2X, enhancement failed)"
                )
                
            except Exception as upscale_error:
                # If both fail, send original
                await progress.edit_text("⚠️ Both failed. Sending original...")
                await message.reply_photo(
                    photo=original_path,
                    caption="⚠️ **Original Image** (Processing failed)"
                )
                
    except Exception as e:
        await progress.edit_text(f"❌ Unexpected error: {str(e)}")
    finally:
        # Cleanup files
        await progress.delete()
        for path in [original_path, enhanced_path, upscaled_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

# Standalone commands
@app.on_message(filters.command("enhancing") & filters.reply)
async def enhance_only(client: Client, message: Message):
    """Only enhance the image"""
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("⚠️ Please reply to an image!")
    
    progress = await message.reply("🎨 Enhancing image...")
    original_path = enhanced_path = None
    
    try:
        original_path = await message.reply_to_message.download()
        enhanced_path = await enhance_image(original_path)
        
        await progress.edit_text("📤 Sending result...")
        await message.reply_photo(
            photo=enhanced_path,
            caption="✨ **Enhanced Image**"
        )
    except Exception as e:
        await progress.edit_text(f"❌ Enhancement failed: {str(e)}")
    finally:
        await progress.delete()
        for path in [original_path, enhanced_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

@app.on_message(filters.command("upscaling") & filters.reply)
async def upscale_only(client: Client, message: Message):
    """Only upscale the image"""
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("⚠️ Please reply to an image!")
    
    progress = await message.reply("🖼️ Upscaling image (2X)...")
    original_path = upscaled_path = None
    
    try:
        original_path = await message.reply_to_message.download()
        upscaled_path = await upscale_image(original_path)
        
        await progress.edit_text("📤 Sending result...")
        await message.reply_photo(
            photo=upscaled_path,
            caption="✨ **Upscaled Image** (2X)"
        )
    except Exception as e:
        await progress.edit_text(f"❌ Upscaling failed: {str(e)}")
    finally:
        await progress.delete()
        for path in [original_path, upscaled_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
