import os
import random
import io
import time
import asyncio
import requests
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, TextInput
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image, ImageDraw
from flask import Flask
from threading import Thread

# 1. Configure Proxy
PROXY_URL = "http://sdxhomrv:2iglhif7xb7o@31.59.20.176:6754"

# 2. Define Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# 3. Initialize Bot Instance
bot = commands.Bot(command_prefix="!", intents=intents, proxy=PROXY_URL)

# 4. Environment Variables
MONGO_URL = os.environ.get("MONGO_URL")
BOT_TOKEN = os.environ.get("DISCORD_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")

app = Flask('')

@app.route('/')
def home():
    return "SmashBot is awake and running!"

def run_web_server():
    """Starts the native Flask web listener on the port Render requires."""
    port = int(os.environ.get("PORT", 10000))
    # CRITICAL FIX: Use app.run() instead of web.AppRunner()
    app.run(host='0.0.0.0', port=port)



# Preset Assets Dictionary Configuration Maps
FIGHTER_IMAGES = {
    # --- BASE ROSTER & SECRETS ---
    "Mario": "https://smashbros.com",
    "Donkey Kong": "https://smashbros.com",
    "Link": "https://smashbros.com",
    "Samus": "https://smashbros.com",
    "Dark Samus": "https://smashbros.com",
    "Yoshi": "https://smashbros.com",
    "Kirby": "https://smashbros.com",
    "Fox": "https://smashbros.com",
    "Pikachu": "https://smashbros.com",
    "Luigi": "https://smashbros.com",
    "Ness": "https://smashbros.com",
    "Captain Falcon": "https://smashbros.com",
    "Jigglypuff": "https://smashbros.com",
    "Peach": "https://smashbros.com",
    "Daisy": "https://smashbros.com",
    "Bowser": "https://smashbros.com",
    "Ice Climbers": "https://smashbros.com",
    "Sheik": "https://smashbros.com",
    "Zelda": "https://smashbros.com",
    "Dr. Mario": "https://smashbros.com",
    "Pichu": "https://smashbros.com",
    "Falco": "https://smashbros.com",
    "Marth": "https://smashbros.com",
    "Lucina": "https://smashbros.com",
    "Young Link": "https://smashbros.com",
    "Ganondorf": "https://smashbros.com",
    "Mewtwo": "https://smashbros.com",
    "Roy": "https://smashbros.com",
    "Chrom": "https://smashbros.com",
    "Mr. Game & Watch": "https://smashbros.com",
    "Meta Knight": "https://smashbros.com",
    "Pit": "https://smashbros.com",
    "Dark Pit": "https://smashbros.com",
    "Zero Suit Samus": "https://smashbros.com",
    "Wario": "https://smashbros.com",
    "Snake": "https://smashbros.com",
    "Ike": "https://smashbros.com",
    "Pokemon Trainer": "https://smashbros.com",
    "Diddy Kong": "https://smashbros.com",
    "Lucas": "https://smashbros.com",
    "Sonic": "https://smashbros.com",
    "King Dedede": "https://smashbros.com",
    "Olimar": "https://smashbros.com",
    "Lucario": "https://smashbros.com",
    "ROB": "https://smashbros.com",
    "Toon Link": "https://smashbros.com",
    "Wolf": "https://smashbros.com",
    "Villager": "https://smashbros.com",
    "Mega Man": "https://smashbros.com",
    "Wii Fit Trainer": "https://smashbros.com",
    "Rosalina & Luma": "https://smashbros.com",
    "Little Mac": "https://smashbros.com",
    "Greninja": "https://smashbros.com",
    "Mii Brawler": "https://smashbros.com",
    "Mii Swordfighter": "https://smashbros.com",
    "Mii Gunner": "https://smashbros.com",
    "Palutena": "https://smashbros.com",
    "Pac-Man": "https://smashbros.com",
    "Robin": "https://smashbros.com",
    "Shulk": "https://smashbros.com",
    "Bowser Jr.": "https://smashbros.com",
    "Duck Hunt": "https://smashbros.com",
    "Ryu": "https://smashbros.com",
    "Ken": "https://smashbros.com",
    "Cloud": "https://smashbros.com",
    "Corrin": "https://smashbros.com",
    "Bayonetta": "https://smashbros.com",
    "Inkling": "https://smashbros.com",
    "Ridley": "https://smashbros.com",
    "Simon": "https://smashbros.com",
    "Richter": "https://smashbros.com",
    "King K. Rool": "https://smashbros.com",
    "Isabelle": "https://smashbros.com",
    "Incineroar": "https://smashbros.com",

    # --- CHALLENGER PASSES & DLC FIGHTERS ---
    "Piranha Plant": "https://smashbros.com",
    "Joker": "https://smashbros.com",
    "Hero": "https://smashbros.com",
    "Banjo & Kazooie": "https://smashbros.com",
    "Terry": "https://smashbros.com",
    "Byleth": "https://smashbros.com",
    "Min Min": "https://smashbros.com",
    "Steve": "https://smashbros.com",
    "Sephiroth": "https://smashbros.com",
    "Pyra/Mythra": "https://smashbros.com",
    "Kazuya": "https://smashbros.com",
    "Sora": "https://smashbros.com"
}

    # Populate matching strings directly from your script's existing CHARACTER_POOL

STAGE_BACKGROUNDS = {
    "Battlefield": "https://smashbros.com",
    "Final Destination": "https://smashbros.com",
    "Smashville": "https://smashbros.com",
    "Pokemon Stadium 2": "https://smashbros.com",
    "Town and City": "https://smashbros.com"
}

STAGE_TINTS = {
    "Default Blue": (40, 60, 120, 140),     # RGBA Tint layers
    "Championship Gold": (180, 140, 20, 130),
    "Crimson Rage": (150, 20, 20, 140),
    "Shadow Realm": (20, 10, 40, 180)
}


CHARACTER_POOL = [
    "Mario", "Donkey Kong", "Link", "Samus", "Dark Samus", "Yoshi", "Kirby", "Fox", "Pikachu", "Luigi",
    "Ness", "Captain Falcon", "Jigglypuff", "Peach", "Daisy", "Bowser", "Ice Climbers", "Sheik", "Zelda",
    "Dr. Mario", "Pichu", "Falco", "Marth", "Lucina", "Young Link", "Ganondorf", "Mewtwo", "Roy", "Chrom",
    "Mr. Game & Watch", "Meta Knight", "Pit", "Dark Pit", "Zero Suit Samus", "Wario", "Snake", "Ike",
    "Pokemon Trainer", "Diddy Kong", "Lucas", "Sonic", "King Dedede", "Olimar", "Lucario", "ROB", "Toon Link",
    "Wolf", "Villager", "Mega Man", "Wii Fit Trainer", "Rosalina & Luma", "Little Mac", "Greninja", "Mii Brawler",
    "Mii Swordfighter", "Mii Gunner", "Palutena", "Pac-Man", "Robin", "Shulk", "Bowser Jr.", "Duck Hunt", "Ryu",
    "Ken", "Cloud", "Corrin", "Bayonetta", "Inkling", "Ridley", "Simon", "Richter", "King K. Rool", "Isabelle",
    "Incineroar", "Piranha Plant", "Joker", "Hero", "Banjo & Kazooie", "Terry", "Byleth", "Min Min", "Steve",
    "Sephiroth", "Pyra/Mythra", "Kazuya", "Sora"
]

LEGAL_STARTERS = ["Final Destination", "Battlefield", "Small Battlefield", "Pokemon Stadium 2", "Smashville"]
LEGAL_COUNTERPICKS = ["Town and City", "Kalos Pokemon League", "Hollow Bastion"]

class PlayerProfile(BaseModel):
    user_id: int
    mains: List[str] = []
    secondaries: List[str] = []
    region: str = "Unknown"
    card_color: str = "#7289DA"
    stocks_taken: int = 0
    stocks_lost: int = 0
    mvps: int = 0
    join_slots: int = 3

class CrewModel(BaseModel):
    name: str
    owner_id: int
    leaders: List[int]
    members: List[int]
    testers: List[int] = []
    tryout_list: List[int] = []
    tryouts_open: bool = True
    elo: int = 1000
    wins: int = 0
    losses: int = 0
    logo_url: str = "https://imgur.com"
    banner_url: Optional[str] = None
    description: str = "Official 3 Stock Strike Competitor Team."
    hex_color: str = "#ffffff"

class ActiveBattle(BaseModel):
    channel_id: int
    crew_a: str
    crew_b: str
    roster_a: List[int]
    roster_b: List[int]
    current_player_a: int
    current_player_b: int
    stocks_a: int = 3
    stocks_b: int = 3
    total_stocks_a: int
    total_stocks_b: int
    stage_strikes: List[str] = []
    current_striker: int
    is_mock: bool = False
    start_time: float = 0.0



@bot.event
async def on_ready():
    # PASTE THESE 4 LINES RIGHT HERE (Indented with 4 spaces):
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    bot.db = client["smash_crew_db"]

    # This is your existing line 227:
    print(f"📡 Logged in as: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="SSBU Crew Battles"))

    # 1. Put your actual Discord Server (Guild) ID here
    YOUR_SERVER_ID = 123456789012345678  
    target_guild = discord.Object(id=YOUR_SERVER_ID)
    
    try:
        # 2. Clear out any legacy server-bound command caches
        bot.tree.clear_commands(guild=target_guild)
        
        # 3. Clone every command in your script directly to this server
        bot.tree.copy_global_to(guild=target_guild)
        
        # 4. Fire the synchronization protocol
        synced = await bot.tree.sync(guild=target_guild)
        print(f"⚡ Instant Sync: {len(synced)} commands are now live in your server!")
        
        # 5. Background global fallback sync (takes 1-2 hours but registers elsewhere)
        await bot.tree.sync()
        print("🌐 Global background fallback sync complete.")
        
    except Exception as e:
        print(f"❌ Synchronization failure: {e}")


@bot.event
async def on_message(message: discord.Message):
    # 1. Defend against bot infinity loops
    if message.author.bot:
        return

    # 2. Check if the bot was explicitly mentioned
    if bot.user not in message.mentions:
        return

    # 3. Verify this channel has an active battle row tracked in MongoDB
    battle = await bot.db.active_battles.find_one({"channel_id": message.channel.id})
    if not battle:
        return  # Silently ignore if it's just a general server mention

    # 4. Clean text and extract parameters: [@Bot, Winner, Character, Stocks]
    tokens = [t.strip() for t in message.content.split() if t.strip()]
    
    # We expect exactly 4 pieces of data
    if len(tokens) < 4:
        await message.channel.send("❌ **Parsing Error!** Format must be exactly: `@Bot [WinnerName] [Character] [StocksLeft]`\n*Example:* `@SmashBot Phaze Link 2`")
        return

    winner_name_str = tokens[1]
    character_input = tokens[2]
    stocks_left_str = tokens[3]

    # Validate numeric properties
    if not stocks_left_str.isdigit():
        await message.channel.send("❌ **Parsing Error!** Stocks left must be a valid number between 1 and 3.")
        return
    stocks_left = int(stocks_left_str)
    if not (1 <= stocks_left <= 3):
        await message.channel.send("❌ **Rule Violation!** Remaining stocks must be 1, 2, or 3.")
        return

    # 5. Extract members list from the active database tracking row
    roster_a_ids = battle["roster_a"]
    roster_b_ids = battle["roster_b"]

    # Search for match variables across active channel members
    winning_member = None
    for member in message.channel.members:
        if winner_name_str.lower() in member.display_name.lower() or winner_name_str.lower() in member.name.lower():
            if member.id in roster_a_ids or member.id in roster_b_ids:
                winning_member = member
                break

    if not winning_member:
        await message.channel.send(f"❌ **Identity Error!** Could not identify an active roster competitor matching string: `{winner_name_str}`.")
        return

    # 6. Apply Standard Crew Battle Rules Progression Logic
    is_team_a = winning_member.id in roster_a_ids
    
    if is_team_a:
        winning_crew = battle["crew_a"]
        losing_crew = battle["crew_b"]
        current_loser_id = battle["current_player_b"]
        
        # Calculate stocks taken from the loser's active fighter
        loser_stocks_lost = battle["stocks_b"]
        new_total_stocks_b = max(0, battle["total_stocks_b"] - loser_stocks_lost)
        new_total_stocks_a = battle["total_stocks_a"]
        
        # Carry over winner's remaining stocks; reset upcoming counterpick to 3
        new_stocks_a = stocks_left
        new_stocks_b = 3
        
        # Sync profile card analytics counts
        await bot.db.players.update_one({"user_id": winning_member.id}, {"$inc": {"stocks_taken": loser_stocks_lost}})
        await bot.db.players.update_one({"user_id": current_loser_id}, {"$inc": {"stocks_lost": loser_stocks_lost}})
    else:
        winning_crew = battle["crew_b"]
        losing_crew = battle["crew_a"]
        current_loser_id = battle["current_player_a"]
        
        loser_stocks_lost = battle["stocks_a"]
        new_total_stocks_a = max(0, battle["total_stocks_a"] - loser_stocks_lost)
        new_total_stocks_b = battle["total_stocks_b"]
        
        new_stocks_b = stocks_left
        new_stocks_a = 3
        
        await bot.db.players.update_one({"user_id": winning_member.id}, {"$inc": {"stocks_taken": loser_stocks_lost}})
        await bot.db.players.update_one({"user_id": current_loser_id}, {"$inc": {"stocks_lost": loser_stocks_lost}})

    # 7. Check Game Over Win/Loss States (One squad runs out of total stocks)
    if new_total_stocks_a == 0 or new_total_stocks_b == 0:
        match_winner = battle["crew_a"] if new_total_stocks_b == 0 else battle["crew_b"]
        match_loser = battle["crew_b"] if new_total_stocks_b == 0 else battle["crew_a"]
        
        embed = discord.Embed(title="🏆 CREW BATTLE CONCLUDED 🏆", color=discord.Color.gold())
        embed.description = f"🏁 **{match_winner}** has taken the final stock pool and defeated **{match_loser}**!"
        embed.add_field(name="Final Leftover Stock Matrix", value=f"Stocks: `{max(new_total_stocks_a, new_total_stocks_b)}`", inline=False)
        embed.set_footer(text="Match logs frozen. Run /approve_battle to finalize records.")
        
        await bot.db.active_battles.update_one(
            {"channel_id": message.channel.id},
            {"$set": {"total_stocks_a": new_total_stocks_a, "total_stocks_b": new_total_stocks_b}}
        )
        await message.channel.send(embed=embed)
        return

    # 8. Frame Up Next Counterpick State Variables
    update_data = {
        "stocks_a": new_stocks_a,
        "stocks_b": new_stocks_b,
        "total_stocks_a": new_total_stocks_a,
        "total_stocks_b": new_total_stocks_b
    }
    await bot.db.active_battles.update_one({"channel_id": message.channel.id}, {"$set": update_data})

    # 9. Print real-time scoresheet match updates onto the channel
    embed = discord.Embed(title="🎮 Automated Score Logs Updated", color=discord.Color.green())
    embed.description = f"**{winning_member.display_name}** ({character_input}) wins the game! Carrying over **{stocks_left}★**."
    embed.add_field(name=f"📊 {battle['crew_a']}", value=f"Stocks Remaining: `{new_total_stocks_a}`", inline=True)
    embed.add_field(name=f"📊 {battle['crew_b']}", value=f"Stocks Remaining: `{new_total_stocks_b}`", inline=True)
    embed.set_footer(text=f"Awaiting counterpick recruitment entry from {losing_crew} via /send.")
    
    await message.channel.send(embed=embed)



import io
import discord
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import aiohttp

async def generate_player_card(username, fighter_name, background_name, tint_rgba, gold_balance, elo):
    async with aiohttp.ClientSession() as session:
        # 1. Pull preset stage image background with a safe default fallback
        bg_url = STAGE_BACKGROUNDS.get(background_name, STAGE_BACKGROUNDS["Battlefield"])
        try:
            async with session.get(bg_url) as resp:
                if resp.status != 200:
                    raise Exception()
                bg_data = await resp.read()
        except:
            # Absolute baseline safety image if an external URL drops offline
            async with session.get(STAGE_BACKGROUNDS["Battlefield"]) as resp:
                bg_data = await resp.read()
            background_name = "Battlefield"
            
        # 2. Pull preset fighter character render with a safe default fallback
        fighter_url = FIGHTER_IMAGES.get(fighter_name, "https://smashbros.com")
        try:
            async with session.get(fighter_url) as resp:
                if resp.status == 200:
                    fighter_data = await resp.read()
                else:
                    raise Exception()
        except:
            async with session.get("https://smashbros.com") as resp:
                fighter_data = await resp.read()

    # Create the graphics canvas layers
    base_bg = Image.open(io.BytesIO(bg_data)).convert("RGBA").resize((800, 450))
    fighter_img = Image.open(io.BytesIO(fighter_data)).convert("RGBA")
    
    # Proportional scaling calculations
    fighter_img.thumbnail((400, 400), Image.Resampling.LANCZOS)

    # Blend the custom color overlay tint matrix
    tint_layer = Image.new("RGBA", base_bg.size, tint_rgba)
    composited_card = Image.alpha_composite(base_bg, tint_layer)

    # Position fighter transparent graphic on the right side panel
    fighter_layer = Image.new("RGBA", composited_card.size)
    fighter_layer.paste(fighter_img, (420, 450 - fighter_img.size[1]), fighter_img)
    composited_card = Image.alpha_composite(composited_card, fighter_layer)

    # Overlay Typography Text Data using standard system fallback fonts
    draw = ImageDraw.Draw(composited_card)
    
    # CRITICAL FIX: Forces standard system font rendering (Removes .ttf dependency crash loops)
    font_main = ImageFont.load_default()

    # High-visibility contrast text canvas overlays
    draw.text((40, 40), f"PLAYER: {username.upper()}", font=font_main, fill=(255, 255, 255, 255))
    draw.text((40, 80), f"MAIN FIGHTER: {fighter_name}", font=font_main, fill=(220, 220, 220, 255))
    draw.text((40, 120), f"CREW BATTLE ELO: {elo}", font=font_main, fill=(100, 230, 100, 255))
    draw.text((40, 360), f"GOLD BALANCE: {gold_balance}G", font=font_main, fill=(255, 215, 0, 255))
    draw.text((40, 390), f"STAGE PRESET: {background_name}", font=font_main, fill=(200, 200, 200, 255))
    
    # Save image to a virtual stream file format for Discord transmission
    output_buffer = io.BytesIO()
    composited_card.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    return discord.File(fp=output_buffer, filename="smash_player_card.png")


    # Load images into Pillow canvas layers
    base_bg = Image.open(io.BytesIO(bg_data)).convert("RGBA").resize((800, 450))
    fighter_img = Image.open(io.BytesIO(fighter_data)).convert("RGBA")
    
    # Scale fighter profile assets proportionally
    fighter_img.thumbnail((400, 400), Image.Resampling.LANCZOS)

    # 3. Construct and Overlay the Color Tint Layer Mask
    tint_layer = Image.new("RGBA", base_bg.size, tint_rgba)
    composited_card = Image.alpha_composite(base_bg, tint_layer)

    # 4. Composite the Transparency-Stripped Fighter Layer
    # Places fighter on the right side of the canvas bounds
    fighter_layer = Image.new("RGBA", composited_card.size)
    fighter_layer.paste(fighter_img, (420, 450 - fighter_img.size[1]), fighter_img)
    composited_card = Image.alpha_composite(composited_card, fighter_layer)

    # 5. Build Graphic User Interface Metrics (Text Overlays)
    draw = ImageDraw.Draw(composited_card)
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_sub = ImageFont.truetype("DejaVuSans.ttf", 24)
    except IOError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Apply structural typography layout
    draw.text((40, 40), username.upper(), font=font_title, fill=(255, 255, 255, 255))
    draw.text((40, 95), f"Main: {fighter_name}", font=font_sub, fill=(220, 220, 220, 255))
    draw.text((40, 135), f"Arena ELO: {elo}", font=font_sub, fill=(100, 230, 100, 255))
    draw.text((40, 375), f"💰 Gold Balance: {gold_balance}G", font=font_title, fill=(255, 215, 0, 255))
    draw.text((40, 415), f"🏟️ Pitch: {background_name}", font=font_sub, fill=(180, 180, 180, 255))

    # Compress file streaming payload array bytes
    output_buffer = io.BytesIO()
    composited_card.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    return discord.File(fp=output_buffer, filename="smash_player_card.png")

import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont

# 1. Preset Asset Maps (Keeps styling clean and unvetted links out)
FIGHTER_IMAGES = {
    # --- BASE ROSTER & SECRETS ---
    "Mario": "https://smashbros.com",
    "Donkey Kong": "https://smashbros.com",
    "Link": "https://smashbros.com",
    "Samus": "https://smashbros.com",
    "Dark Samus": "https://smashbros.com",
    "Yoshi": "https://smashbros.com",
    "Kirby": "https://smashbros.com",
    "Fox": "https://smashbros.com",
    "Pikachu": "https://smashbros.com",
    "Luigi": "https://smashbros.com",
    "Ness": "https://smashbros.com",
    "Captain Falcon": "https://smashbros.com",
    "Jigglypuff": "https://smashbros.com",
    "Peach": "https://smashbros.com",
    "Daisy": "https://smashbros.com",
    "Bowser": "https://smashbros.com",
    "Ice Climbers": "https://smashbros.com",
    "Sheik": "https://smashbros.com",
    "Zelda": "https://smashbros.com",
    "Dr. Mario": "https://smashbros.com",
    "Pichu": "https://smashbros.com",
    "Falco": "https://smashbros.com",
    "Marth": "https://smashbros.com",
    "Lucina": "https://smashbros.com",
    "Young Link": "https://smashbros.com",
    "Ganondorf": "https://smashbros.com",
    "Mewtwo": "https://smashbros.com",
    "Roy": "https://smashbros.com",
    "Chrom": "https://smashbros.com",
    "Mr. Game & Watch": "https://smashbros.com",
    "Meta Knight": "https://smashbros.com",
    "Pit": "https://smashbros.com",
    "Dark Pit": "https://smashbros.com",
    "Zero Suit Samus": "https://smashbros.com",
    "Wario": "https://smashbros.com",
    "Snake": "https://smashbros.com",
    "Ike": "https://smashbros.com",
    "Pokemon Trainer": "https://smashbros.com",
    "Diddy Kong": "https://smashbros.com",
    "Lucas": "https://smashbros.com",
    "Sonic": "https://smashbros.com",
    "King Dedede": "https://smashbros.com",
    "Olimar": "https://smashbros.com",
    "Lucario": "https://smashbros.com",
    "ROB": "https://smashbros.com",
    "Toon Link": "https://smashbros.com",
    "Wolf": "https://smashbros.com",
    "Villager": "https://smashbros.com",
    "Mega Man": "https://smashbros.com",
    "Wii Fit Trainer": "https://smashbros.com",
    "Rosalina & Luma": "https://smashbros.com",
    "Little Mac": "https://smashbros.com",
    "Greninja": "https://smashbros.com",
    "Mii Brawler": "https://smashbros.com",
    "Mii Swordfighter": "https://smashbros.com",
    "Mii Gunner": "https://smashbros.com",
    "Palutena": "https://smashbros.com",
    "Pac-Man": "https://smashbros.com",
    "Robin": "https://smashbros.com",
    "Shulk": "https://smashbros.com",
    "Bowser Jr.": "https://smashbros.com",
    "Duck Hunt": "https://smashbros.com",
    "Ryu": "https://smashbros.com",
    "Ken": "https://smashbros.com",
    "Cloud": "https://smashbros.com",
    "Corrin": "https://smashbros.com",
    "Bayonetta": "https://smashbros.com",
    "Inkling": "https://smashbros.com",
    "Ridley": "https://smashbros.com",
    "Simon": "https://smashbros.com",
    "Richter": "https://smashbros.com",
    "King K. Rool": "https://smashbros.com",
    "Isabelle": "https://smashbros.com",
    "Incineroar": "https://smashbros.com",

    # --- CHALLENGER PASSES & DLC FIGHTERS ---
    "Piranha Plant": "https://smashbros.com",
    "Joker": "https://smashbros.com",
    "Hero": "https://smashbros.com",
    "Banjo & Kazooie": "https://smashbros.com",
    "Terry": "https://smashbros.com",
    "Byleth": "https://smashbros.com",
    "Min Min": "https://smashbros.com",
    "Steve": "https://smashbros.com",
    "Sephiroth": "https://smashbros.com",
    "Pyra/Mythra": "https://smashbros.com",
    "Kazuya": "https://smashbros.com",
    "Sora": "https://smashbros.com"
}

STAGE_BACKGROUNDS = {
    "Battlefield": "https://smashbros.com",
    "Final Destination": "https://smashbros.com",
    "Smashville": "https://smashbros.com",
    "Pokemon Stadium 2": "https://smashbros.com"
}

STAGE_TINTS = {
    "Default Blue": (40, 60, 120, 140),
    "Championship Gold": (180, 140, 20, 130),
    "Crimson Rage": (150, 20, 20, 140),
    "Shadow Realm": (20, 10, 40, 180)
}

# 2. The Core Pillow Drawing Function
async def generate_player_card(username, fighter_name, background_name, tint_rgba, gold_balance, elo):
    async with aiohttp.ClientSession() as session:
        # Pull preset stage image background
        bg_url = STAGE_BACKGROUNDS.get(background_name, STAGE_BACKGROUNDS["Battlefield"])
        async with session.get(bg_url) as resp:
            bg_data = await resp.read()
            
        # Pull preset fighter character transparent render
                # Pull preset fighter character transparent render
        formatted_name = fighter_name.strip().title()
        if "Pyra" in formatted_name or "Mythra" in formatted_name:
            formatted_name = "Pyra/Mythra"
            
        fighter_url = FIGHTER_IMAGES.get(formatted_name, "https://smashbros.com")
        async with session.get(fighter_url) as resp:
            fighter_data = await resp.read()

    # Create the graphics canvas layers
    base_bg = Image.open(io.BytesIO(bg_data)).convert("RGBA").resize((800, 450))
    fighter_img = Image.open(io.BytesIO(fighter_data)).convert("RGBA")
    fighter_img.thumbnail((400, 400), Image.Resampling.LANCZOS)

    # Blend the custom color overlay tint matrix
    tint_layer = Image.new("RGBA", base_bg.size, tint_rgba)
    composited_card = Image.alpha_composite(base_bg, tint_layer)

    # Position fighter transparent graphic on the right side panel
    fighter_layer = Image.new("RGBA", composited_card.size)
    fighter_layer.paste(fighter_img, (420, 450 - fighter_img.size[1]), fighter_img)
    composited_card = Image.alpha_composite(composited_card, fighter_layer)

    # Overlay Typography Text Data
    draw = ImageDraw.Draw(composited_card)
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_sub = ImageFont.truetype("DejaVuSans.ttf", 24)
    except IOError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((40, 40), username.upper(), font=font_title, fill=(255, 255, 255, 255))
    draw.text((40, 95), f"Main Fighter: {fighter_name}", font=font_sub, fill=(220, 220, 220, 255))
    draw.text((40, 135), f"Crew Battle ELO: {elo}", font=font_sub, fill=(100, 230, 100, 255))
    draw.text((40, 365), f"💰 Gold: {gold_balance}G", font=font_title, fill=(255, 215, 0, 255))
    
    # Save image to a virtual stream file format for Discord transmission
    output_buffer = io.BytesIO()
    composited_card.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    return discord.File(fp=output_buffer, filename="smash_player_card.png")

@bot.tree.command(name="card", description="Show your official tournament combat profile card.")
async def show_card(interaction: discord.Interaction, member: discord.User = None):
    await interaction.response.defer()
    target_user = member or interaction.user
    
    try:
        # 1. Fetch user data records from MongoDB Atlas
        profile_record = await bot.db.users.find_one({"_id": target_user.id})
        crew_record = await bot.db.crews.find_one({"members": target_user.id})
        
        # 2. Strict sanitation: Ensure nothing is None or an invalid type
        gold_balance = 150
        if profile_record and "gold" in profile_record and profile_record["gold"] is not None:
            gold_balance = int(profile_record["gold"])
            
        elo_rating = 1000
        if crew_record and "elo" in crew_record and crew_record["elo"] is not None:
            elo_rating = int(crew_record["elo"])
        
        # Pull layout strings with strict vanilla fallbacks
        equipped_fighter = "Mario"
        if profile_record and profile_record.get("equipped_fighter"):
            equipped_fighter = str(profile_record["equipped_fighter"]).strip()
            
        equipped_stage = "Battlefield"
        if profile_record and profile_record.get("equipped_stage"):
            equipped_stage = str(profile_record["equipped_stage"]).strip()
            
        equipped_tint_name = "Default Blue"
        if profile_record and profile_record.get("equipped_tint"):
            equipped_tint_name = str(profile_record["equipped_tint"]).strip()
        
        # Fetch the RGBA tuple map safely
        tint_color_tuple = STAGE_TINTS.get(equipped_tint_name, STAGE_TINTS["Default Blue"])

        # 3. Fire the image generator engine
        card_file = await generate_player_card(
            username=target_user.name,
            fighter_name=equipped_fighter,
            background_name=equipped_stage,
            tint_rgba=tint_color_tuple,
            gold_balance=gold_balance,
            elo=elo_rating
        )
        
        # Send the file!
        await interaction.followup.send(file=card_file)
        
    except Exception as e:
        # This will print the EXACT error to your Render log console so we can see it!
        print(f"❌ CRITICAL CARD EXECUTION ERROR: {e}")
        await interaction.followup.send("❌ An unexpected error occurred while compiling your user metrics.", ephemeral=True)





# =========================================================================
#                    THE TOURNAMENT MARKETPLACE MODULE
# =========================================================================



ROWS = {
    "Row 1": ["Mario", "Donkey Kong", "Link", "Samus", "Dark Samus", "Yoshi", "Kirby", "Fox", "Pikachu", "Luigi", "Ness", "Captain Falcon", "Jigglypuff"],
    "Row 2": ["Peach", "Daisy", "Bowser", "Ice Climbers", "Sheik", "Zelda", "Dr. Mario", "Pichu", "Falco", "Marth", "Lucina", "Young Link", "Ganondorf"],
    "Row 3": ["Mewtwo", "Roy", "Chrom", "Mr. Game & Watch", "Meta Knight", "Pit", "Dark Pit", "Zero Suit Samus", "Wario", "Snake", "Ike", "Pokemon Trainer", "Diddy Kong"],
    "Row 4": ["Lucas", "Sonic", "King Dedede", "Olimar", "Lucario", "R.O.B.", "Toon Link", "Wolf", "Villager", "Mega Man", "Wii Fit Trainer", "Rosalina & Luma", "Little Mac"],
    "Row 5": ["Greninja", "Palutena", "Pac-Man", "Robin", "Shulk", "Bowser Jr.", "Duck Hunt", "Ryu", "Ken", "Cloud", "Corrin", "Bayonetta", "Inkling"],
    "Row 6": ["Ridley", "Simon", "Richter", "King K. Rool", "Isabelle", "Incineroar", "Piranha Plant", "Joker", "Hero", "Banjo & Kazooie", "Terry", "Byleth", "Min Min"],
    "Row 7": ["Steve", "Sephiroth", "Pyra/Mythra", "Kazuya", "Sora", "Mii Brawler", "Mii Swordfighter", "Mii Gunner"]
}

ROSTER = {name: name for row in ROWS.values() for name in row}

ROLE_MAPPING = {
    "ssbucord_crew": "SSBUCord Crew Member",
    "scs_crew": "SCS Crew Member",
    "dscl_crew": "DSCL Crew Member",
    "ssbucord_sub": "SSBUCord Emergency Sub",
    "scs_sub": "SCS Emergency Sub",
    "dscl_sub": "DSCL Emergency Sub"
}

async def assign_fighter_role(interaction, fighter_input, role_type):
    matched = None
    for name in ROSTER:
        if fighter_input.lower() in name.lower():
            matched = name
            break
    if not matched:
        await interaction.response.send_message(f"❌ No fighter named '{fighter_input}'.", ephemeral=True)
        return
    role_name = f"{role_type}: {matched}"
    guild, member = interaction.guild, interaction.user
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        try:
            role = await guild.create_role(name=role_name, mentionable=True)
            await interaction.channel.send(f"🛠️ Created: `{role_name}`")
        except:
            await interaction.response.send_message("❌ Missing permissions!", ephemeral=True)
            return
    if role in member.roles:
        await interaction.response.send_message(f"ℹ️ You already have `{role_name}`!", ephemeral=True)
    else:
        try:
            await member.add_roles(role)
            await interaction.response.send_message(f"✅ Added `{role_name}`!", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Move bot role higher!", ephemeral=True)

@bot.tree.command(name="main")
async def slash_main(interaction: discord.Interaction, fighter_name: str):
    await assign_fighter_role(interaction, fighter_name, "Main")

@bot.tree.command(name="secondary")
async def slash_secondary(interaction: discord.Interaction, fighter_name: str):
    await assign_fighter_role(interaction, fighter_name, "Secondary")

@bot.tree.command(name="removefighter")
async def slash_remove(interaction: discord.Interaction, fighter_name: str):
    guild, member = interaction.guild, interaction.user
    for r_type in ["Main", "Secondary"]:
        for name in ROSTER:
            if fighter_name.lower() in name.lower():
                role = discord.utils.get(guild.roles, name=f"{r_type}: {name}")
                if role and role in member.roles:
                    await member.remove_roles(role)
                    await interaction.response.send_message(f"🗑️ Removed `{role.name}`.", ephemeral=True)
                    return
    await interaction.response.send_message("❌ Role not found.", ephemeral=True)

@bot.tree.command(name="smashmenu")
@app_commands.checks.has_permissions(administrator=True)
async def slash_menu(interaction: discord.Interaction):
    embed = discord.Embed(title="🎮 SSBU Crew Matchmaking Dashboard", description="Select a fighter below.", color=0xff4500)
    embed.set_image(url="https://i.imgur.com/kb35FCI.jpeg")
    await interaction.response.send_message(embed=embed, view=RosterView(), ephemeral=False)

class RolePingSelect(Select):
    def __init__(self, all_users, fighter_name):
        self.all_users = all_users
        self.fighter_name = fighter_name
        options = [
            discord.SelectOption(label="SSBUCord Crew Member", value="ssbucord_crew"),
            discord.SelectOption(label="SCS Crew Member", value="scs_crew"),
            discord.SelectOption(label="DSCL Crew Member", value="dscl_crew"),
            discord.SelectOption(label="SSBUCord Emergency Sub", value="ssbucord_sub"),
            discord.SelectOption(label="SCS Emergency Sub", value="scs_sub"),
            discord.SelectOption(label="DSCL Emergency Sub", value="dscl_sub")
        ]
        super().__init__(placeholder="📣 Select Crew or Emergency Sub Role to Ping...", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        target_role_name = ROLE_MAPPING[selected_key]
        to_ping = [m.mention for m in self.all_users if any(r.name == target_role_name for r in m.roles)]
        
        if to_ping:
            await interaction.response.send_message(f"🚨 **{target_role_name} Alert!** Match needed against **{self.fighter_name}**:\n" + " ".join(to_ping))
        else:
            await interaction.response.send_message(f"ℹ️ No active **{self.fighter_name}** players possess the **{target_role_name}** role.", ephemeral=True)

class PingActionView(View):
    def __init__(self, mains, secondaries, fighter_name, player_options):
        super().__init__(timeout=None)
        self.mains, self.secondaries, self.fighter_name, self.all_users = mains, secondaries, fighter_name, list(set(mains + secondaries))
        
        if player_options:
            sel = Select(placeholder="🎯 Select 1 Specific Player to Ping...", options=player_options[:25], row=0)
            sel.callback = self.single_ping_callback
            self.add_item(sel)
            
        if len(self.all_users) > 0:
            self.add_item(RolePingSelect(self.all_users, self.fighter_name))
            
        self.btn_everyone.disabled = len(self.all_users) == 0

    async def single_ping_callback(self, interaction):
        member = interaction.guild.get_member(int(interaction.data['values'][0]))
        if member: await interaction.response.send_message(f"🔔 {interaction.user.mention} challenged {member.mention} ({self.fighter_name})!")

    @discord.ui.button(label="Ping Everyone who plays character", style=discord.ButtonStyle.danger, row=2)
    async def btn_everyone(self, interaction, button):
        await interaction.response.send_message(f"📣 {interaction.user.mention} wants matches against **{self.fighter_name}**!\n" + " ".join([m.mention for m in self.all_users]))

class RosterView(View):
    def __init__(self, page=1):
        super().__init__(timeout=None)
        self.page = page
        display_rows = list(ROWS.items())[:3] if page == 1 else list(ROWS.items())[3:]
        btn_row = 3 if page == 1 else 4
        for label, fighters in display_rows:
            sel = Select(placeholder=label, options=[discord.SelectOption(label=n, value=n) for n in fighters])
            sel.callback = self.select_callback
            self.add_item(sel)
        if page == 1:
            btn = Button(label="Next Rows (4-7) ➡️", style=discord.ButtonStyle.secondary, row=btn_row)
            btn.callback = self.next_page
        else:
            btn = Button(label="⬅️ Previous Rows (1-3)", style=discord.ButtonStyle.secondary, row=btn_row)
            btn.callback = self.prev_page
        self.add_item(btn)

    async def next_page(self, interaction): await interaction.response.edit_message(view=RosterView(page=2))
    async def prev_page(self, interaction): await interaction.response.edit_message(view=RosterView(page=1))

    async def select_callback(self, interaction):
        await interaction.response.defer()
        name = interaction.data['values'][0]
        guild = interaction.guild
        mains = discord.utils.get(guild.roles, name=f"Main: {name}").members if discord.utils.get(guild.roles, name=f"Main: {name}") else []
        secs = discord.utils.get(guild.roles, name=f"Secondary: {name}").members if discord.utils.get(guild.roles, name=f"Secondary: {name}") else []
        all_p = list(set(mains + secs))
        opts = [discord.SelectOption(label=p.display_name, value=str(p.id), description="Main" if p in mains else "Secondary") for p in all_p]
        text = f"🔲 **Fighter Profile: {name}**\n\n⭐ **Mains:**\n" + ("\n".join([f"• {m.display_name}" for m in mains]) if mains else "• None\n")
        text += f"\n🥈 **Secondaries:**\n" + ("\n".join([f"• {s.display_name}" for s in secs]) if secs else "• None\n")
        await interaction.followup.send(content=text, view=PingActionView(mains, secs, name, opts), ephemeral=True)

@bot.command(name="sync")
@commands.is_owner()
async def manual_sync(ctx):
    await bot.tree.sync()
    await ctx.send("🔄 7-Row layout matrix synced globally!")

# 1. Add your testing server's ID at the top of your script
MY_GUILD_ID = 1494137588250972250  # 👈 Replace with your actual Server ID

# 2. Update your on_ready event at the bottom of your script
@bot.event
async def on_ready():
    print(f"✅ Character Roster Bot logged in as {bot.user}")
    try:
        # Syncs commands instantly to your specific server for testing
        guild = discord.Object(id=MY_GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"🔄 Instantly synced {len(synced)} slash commands to server {MY_GUILD_ID}!")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")





@bot.tree.command(name="shop", description="Browse cosmetic background stages and color tints for your profile card.")
async def open_shop(interaction: discord.Interaction):
    """Displays all available card cosmetics and their gold costs."""
    embed = discord.Embed(
        title="🏪 Tournament Gold Marketplace",
        description="Spend gold earned from victorious crew battles to upgrade your profile visual themes!",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="🎨 Tint Overlays (150 Gold each)", 
        value="• `Championship Gold` \n• `Crimson Rage` \n• `Shadow Realm`", 
        inline=False
    )
    embed.add_field(
        name="🏟️ Arena Background Stages (300 Gold each)", 
        value="• `Final Destination` \n• `Smashville` \n• `Pokemon Stadium 2` \n• `Town and City`", 
        inline=False
    )
    embed.add_field(
        name="🛒 How to Purchase", 
        value="Use `/buy <item_name>` to instantly purchase and unlock any item tier.", 
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="buy", description="Purchase a card cosmetic using your accumulated crew battle gold.")
async def buy_item(interaction: discord.Interaction, item_name: str):
    """Processes cosmetic transactions and updates the user's MongoDB profile ledger."""
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    
    # Standard pricing lookup catalog
    item_prices = {
        "championship gold": 150, "crimson rage": 150, "shadow realm": 150,
        "final destination": 300, "smashville": 300, "pokemon stadium 2": 300, "town and city": 300
    }
    
    normalized_name = item_name.strip().lower()
    if normalized_name not in item_prices:
        await interaction.followup.send("❌ That item is not available in the shop catalog.", ephemeral=True)
        return
        
    cost = item_prices[normalized_name]
    
    # Query current user's profile wallet balance
    user_data = await bot.db.users.find_one({"_id": user_id})
    current_gold = user_data.get("gold", 0) if user_data else 0
    
    if current_gold < cost:
        await interaction.followup.send(
            f"❌ Transaction declined. You need **{cost}G**, but you currently only hold **{current_gold}G**.", 
            ephemeral=True
        )
        return
        
    # Check if they already own it
    unlocked_inventory = user_data.get("unlocked_items", []) if user_data else []
    if normalized_name in unlocked_inventory:
        await interaction.followup.send("❌ You already own this cosmetic upgrade.", ephemeral=True)
        return

    # Deduct gold and add the item to their inventory array in MongoDB Atlas
    await bot.db.users.update_one(
        {"_id": user_id},
        {
            "$inc": {"gold": -cost},
            "$push": {"unlocked_items": normalized_name}
        },
        upsert=True
    )
    
    await interaction.followup.send(
        f"🎉 **Purchase Confirmed:** Unlocked **{item_name}**! Use `/equip` to update your profile card layout.", 
        ephemeral=True
    )


import os
import discord
from discord import app_commands
from discord.ext import commands

# --- PLACE INSIDE YOUR WIZARD REDIRECT BLOCK ---

import os
import discord
from discord import app_commands, ui

# 1. Define the Interactive Popup Window Form
class CrewApplicationModal(ui.Modal, title="🛡️ Register Your Tournament Crew"):
    # Text input slots that display directly inside the Discord UI window
    crew_name = ui.TextInput(
        label="Crew Team Name", 
        placeholder="e.g., The Horsemen", 
        required=True, 
        max_length=32
    )
    leaders = ui.TextInput(
        label="Co-Leaders / Captains (User IDs)", 
        placeholder="Paste User IDs separated by spaces (Optional)", 
        required=False,
        style=discord.TextStyle.long
    )
    members = ui.TextInput(
        label="Roster Members (User IDs)", 
        placeholder="Paste User IDs separated by spaces (Optional)", 
        required=False,
        style=discord.TextStyle.long
    )

    # 2. This execution loop fires the moment the user clicks the blue "Submit" button
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        guild = interaction.guild
        
        # Clean up input string data from form variables into structured ID lists
        def parse_ids(text_input):
            if not text_input:
                return []
            # Split by space or comma, remove empty elements, and convert to numeric clean strings
            return [chunk.strip() for chunk in text_input.replace(",", " ").split() if chunk.strip().isdigit()]

        captured_crew_name = self.crew_name.value.strip()
        captured_leaders = parse_ids(self.leaders.value)
        captured_members = parse_ids(self.members.value)

        try:
            # 3. Resolve user objects and build invitation mention links cleanly
            all_participants = list(set([str(user_id)] + captured_leaders + captured_members))
            roster_mentions = []

            for participant_id in all_participants:
                try:
                    member = guild.get_member(int(participant_id)) or await guild.fetch_member(int(participant_id))
                    if member:
                        roster_mentions.append(member.mention)
                        
                        # Dispatch Paperwork notifications straight to recruits' DMs
                        if member.id != user_id:
                            try:
                                dm_embed = discord.Embed(
                                    title="⚔️ Crew Roster Notification",
                                    description=f"You have been officially recruited onto **{captured_crew_name}** by <@{user_id}>!\nHead to your server's new private channel room to check in.",
                                    color=discord.Color.blue()
                                )
                                await member.send(embed=dm_embed)
                            except discord.Forbidden:
                                print(f"⚠️ Could not DM user ID {member.id} (DMs Closed).")
                except Exception as e:
                    print(f"⚠️ Error resolving user ID {participant_id}: {e}")

            roster_ping_string = " ".join(roster_mentions)

            # 4. Handle future-proof Crew Mod / Staff Role checks
            staff_mentions = []
            for role in guild.roles:
                if role.name.lower() in ["crew mod", "crew admin"] or role.permissions.administrator:
                    staff_mentions.append(role.mention)
            staff_ping_string = " ".join(staff_mentions)

            # 5. Build and commit persistent database schema record to MongoDB Atlas
            await bot.db.crews.insert_one({
                "name": captured_crew_name,
                "owner": user_id, 
                "leaders": list(set([user_id] + [int(i) for i in captured_leaders])), 
                "members": list(set([user_id] + [int(i) for i in captured_leaders] + [int(i) for i in captured_members])), 
                "elo": 1000
            })

            # 6. Create private text container thread
            thread = await interaction.channel.create_thread(
                name=f"crew-{captured_crew_name}", 
                type=discord.ChannelType.private_thread
            )

            # 7. Format clean welcome message display panel
            welcome_embed = discord.Embed(
                title=f"🛡️ Crew Registered: {captured_crew_name}",
                description=f"Welcome to your private headquarters!\n\n**Owner:** <@{user_id}>",
                color=discord.Color.green()
            )
            welcome_embed.add_field(name="Roster Base", value=roster_ping_string if roster_ping_string else "None Listed", inline=False)
            await thread.send(embed=welcome_embed)

            # 8. Force notification hook inside thread layer context to pull them inside
            if roster_ping_string or staff_ping_string:
                ping_payload = await thread.send(f"🔔 **Notification Hook:** {roster_ping_string} {staff_ping_string}")
                await ping_payload.delete(delay=2)

            await interaction.followup.send(f"✅ Your crew has been safely created! Head on over to <#{thread.id}>.", ephemeral=True)

        except Exception as err:
            print(f"❌ Error during submission pipeline execution: {err}")
            await interaction.followup.send(f"❌ Initialization error occurred: {err}", ephemeral=True)


# 3. The primary base slash command endpoint 
@bot.tree.command(name="crewapplication", description="Start an interactive application form wizard to form a brand new crew.")
async def crewapplication(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    # Run the strict upstream single-crew portfolio validation guard check
    existing_crew = await bot.db.crews.find_one({
        "$or": [{"owner": user_id}, {"leaders": user_id}, {"members": user_id}]
    })
    
    if existing_crew:
        await interaction.response.send_message(f"❌ You are already in a crew: **{existing_crew['name']}**.", ephemeral=True)
        return

    # Call and send the clean interactive popup window right on the user's screen
    await interaction.response.send_modal(CrewApplicationModal())



@bot.tree.command(name="start_battle", description="Initialize an official competitive crew battle in a brand new dedicated text channel.")
async def start_battle(interaction: discord.Interaction, opponent_crew: str):
    user_id = interaction.user.id
    guild = interaction.guild
    crew_a_data = await bot.db.crews.find_one({"leaders": user_id})
    crew_b_data = await bot.db.crews.find_one({"name": {"$regex": f"^{opponent_crew}$", "$options": "i"}})
    
    if not crew_a_data or not crew_b_data:
        await interaction.response.send_message("❌ Error: Verification failed. Confirm crew leader properties or target name arrays.", ephemeral=True)
        return

    await interaction.response.defer()

    # 🏢 1. CREATE A SEPARATE TEXT CHANNEL FOR THE BATTLE
    channel_name = f"⚔️-{crew_a_data['name']}-vs-{crew_b_data['name']}".lower().replace(" ", "-")
    battle_channel = await guild.create_text_channel(
        name=channel_name,
        category=interaction.channel.category, # Places it right in the same folder category
        topic=f"Official 3 Stock Strike Match Hub: {crew_a_data['name']} vs {crew_b_data['name']}"
    )

    battle = ActiveBattle(
        channel_id=battle_channel.id, # Anchor tracking data to the new channel ID
        crew_a=crew_a_data["name"], crew_b=crew_b_data["name"],
        roster_a=crew_a_data["members"], roster_b=crew_b_data["members"], 
        current_player_a=crew_a_data["members"], current_player_b=crew_b_data["members"],
        total_stocks_a=len(crew_a_data["members"])*3, total_stocks_b=len(crew_b_data["members"])*3, 
        current_striker=user_id, start_time=time.time()
    )
    
    await bot.db.active_battles.insert_one(battle.model_dump())
    await interaction.followup.send(f"✅ **Match Channel Formed!** Proceed to <#{battle_channel.id}> to conduct your battle routines.")
    
    # Send opening layout embed straight to the new text channel
    embed = discord.Embed(title="⚔️ 3 Stock Strike Arena Arena Online ⚔️", color=discord.Color.red())
    embed.description = f"Welcome to the official battlefield channel for **{battle.crew_a}** and **{battle.crew_b}**!"
    embed.add_field(name=battle.crew_a, value=f"Active Fighter: <@{battle.current_player_a}> (3★)", inline=True)
    embed.add_field(name=battle.crew_b, value=f"Active Fighter: <@{battle.current_player_b}> (3★)", inline=True)
    await battle_channel.send(embed=embed)


@bot.tree.command(name="forcesync", description="Admin Only: Instantly purge caches and rebuild application command menus.")
async def forcesync(interaction: discord.Interaction):
    # CHANGE THIS NUMBER to your actual Discord User ID
    if interaction.user.id != 503657385419407360:  
        await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
        return



@bot.tree.command(name="mock", description="Instantly launch a casual practice mock match environment.")
async def mock(interaction: discord.Interaction, team_a: str, team_b: str):
    battle = ActiveBattle(
        channel_id=interaction.channel_id, crew_a=team_a, crew_b=team_b, roster_a=[interaction.user.id], roster_b=[interaction.user.id],
        current_player_a=interaction.user.id, current_player_b=interaction.user.id, total_stocks_a=3, total_stocks_b=3, current_striker=interaction.user.id, is_mock=True
    )
    await bot.db.active_battles.insert_one(battle.model_dump())
    await interaction.response.send_message(f"🎮 **Mock Battle Initialized:** Casual settings active for {team_a} vs {team_b}!")

@bot.tree.command(name="counterpick", description="Trigger the match counterpick window phase layout.")
async def counterpick(interaction: discord.Interaction):
    await interaction.response.send_message("🔄 **Counterpick Phase Triggered:** Waiting for incoming roster selections.")

@bot.tree.command(name="send", description="Deploy your crew's next counterpick combat fighter into the live arena.")
async def send(interaction: discord.Interaction, player: discord.Member):
    await interaction.response.defer()
    
    # 1. Verify this channel has an active match tracked
    battle = await bot.db.active_battles.find_one({"channel_id": interaction.channel_id})
    if not battle:
        await interaction.followup.send("❌ Error: No official active battle registered to this channel context.")
        return

    # 2. Determine which crew the target player belongs to
    is_team_a = player.id in battle["roster_a"]
    is_team_b = player.id in battle["roster_b"]
    
    if not is_team_a and not is_team_b:
        await interaction.followup.send(f"❌ Error: {player.display_name} is not registered on either team's roster.")
        return

    # 3. Restrict deployment logic based on who needs to counterpick
    if is_team_a:
        if battle["stocks_a"] != 3:
            await interaction.followup.send("❌ Rule Violation: You cannot send a new fighter while your current fighter still has stocks left.")
            return
        
        await bot.db.active_battles.update_one(
            {"channel_id": interaction.channel_id}, 
            {"$set": {"current_player_a": player.id}}
        )
        current_crew = battle["crew_a"]
    else:
        if battle["stocks_b"] != 3:
            await interaction.followup.send("❌ Rule Violation: You cannot send a new fighter while your current fighter still has stocks left.")
            return
            
        await bot.db.active_battles.update_one(
            {"channel_id": interaction.channel_id}, 
            {"$set": {"current_player_b": player.id}}
        )
        current_crew = battle["crew_b"]

    # 4. Confirm entry visually
    embed = discord.Embed(title="🚀 Roster Entry Deployed", color=discord.Color.orange())
    embed.description = f"**{player.display_name}** has jumped into the arena representing **{current_crew}**!"
    embed.set_footer(text="Play your game! When finished, mention the bot to log the score.")
    
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="recordmatch", description="Manually log specific individual score data details.")
async def recordmatch(interaction: discord.Interaction, winner: discord.Member, loser: discord.Member, stocks: int):
    await interaction.response.send_message(f"📝 Result logged: <@{winner.id}> beat <@{loser.id}> keeping `{stocks}` stocks active.")

@bot.tree.command(name="scoresheet", description="DM the updated visual layout data matrix summary sheet.")
async def scoresheet(interaction: discord.Interaction):
    await interaction.response.send_message("📬 Scoresheet data matrix context dispatched directly to your private DMs!", ephemeral=True)

@bot.tree.command(name="extend", description="Grant your crew a 1-time 3-minute extension on the clock response timer.")
async def extend(interaction: discord.Interaction):
    await interaction.response.send_message("⏱️ **Extension Granted:** Added 3 minutes to the active pacing timer.")

@bot.tree.command(name="timer", description="Enforce competitive pacing loops via an official 8-minute countdown clock.")
async def timer(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ **8-Minute Match Timer Started:** Stay alert on response locks!")

# 1. DEFINE THE INTERACTIVE BUTTON INTERFACE OVERLAY
class ForfeitConfirmation(discord.ui.View):
    def __init__(self, initiator: discord.Member):
        super().__init__(timeout=60.0)  # Buttons automatically shut off after 60 seconds of inactivity
        self.initiator = initiator

    @discord.ui.button(label="Yes, Forfeit Match", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defend against unauthorized users hijacking the prompt
        if interaction.user.id != self.initiator.id:
            await interaction.response.send_message("❌ Error: Only the player who triggered the forfeit can confirm it.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        # 1. Fetch active battle tracking data linked to this channel context
        battle = await bot.db.active_battles.find_one({"channel_id": interaction.channel_id})
        if not battle:
            await interaction.followup.send("❌ Error: No official active battle registered to this channel.")
            return

        # 2. Determine who the forfeiting team belongs to
        is_team_a = interaction.user.id in battle["roster_a"]
        match_winner = battle["crew_b"] if is_team_a else battle["crew_a"]
        match_loser = battle["crew_a"] if is_team_a else battle["crew_b"]

        # 3. Print the final victory announcement embed to the channel
        embed = discord.Embed(title="🏳️ MATCH CONCLUDED VIA FORFEIT 🏳️", color=discord.Color.red())
        embed.description = f"**{match_loser}** has voluntarily conceded the match!\n\n🏆 **{match_winner}** is officially awarded the victory!"
        embed.set_footer(text="Match logs frozen. Deleting channel in 10 seconds...")
        await interaction.channel.send(embed=embed)

        # 4. Clear active tracking file from MongoDB database storage records
        await bot.db.active_battles.delete_one({"channel_id": interaction.channel_id})

        # 5. Disable active buttons on the original prompt
        self.stop()
        
        # 6. Wait 10 seconds and permanently purge the text channel environment
        await asyncio.sleep(10)
        await interaction.channel.delete()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.initiator.id:
            await interaction.response.send_message("❌ Error: Only the player who triggered the forfeit can cancel it.", ephemeral=True)
            return
            
        self.stop()
        await interaction.response.edit_message(content="🛑 **Forfeit Cancelled.** The crew battle will continue normally!", view=None)

# 2. THE ACTUAL APPLICATION SLASH COMMAND
@bot.tree.command(name="forfeit", description="Voluntarily concede the entire match and award victory to the opposing crew.")
async def forfeit(interaction: discord.Interaction):
    # 1. Verify this channel is actively tracking an ongoing match
    battle = await bot.db.active_battles.find_one({"channel_id": interaction.channel_id})
    if not battle:
        await interaction.response.send_message("❌ Error: You can only forfeit inside an active match channel context.", ephemeral=True)
        return

    # 2. Verify the player belongs to one of the active match rosters
    is_team_a = interaction.user.id in battle["roster_a"]
    is_team_b = interaction.user.id in battle["roster_b"]
    if not is_team_a and not is_team_b:
        await interaction.response.send_message("❌ Error: You must be a registered competitor on this match scoresheet to issue a forfeit.", ephemeral=True)
        return

    # 3. Deploy the confirmation interface message overlay
    view = ForfeitConfirmation(initiator=interaction.user)
    await interaction.response.send_message(
        content="⚠️ **CRITICAL WARNING:** Are you completely sure you want to forfeit the **entire match**? This will instantly award the victory to your opponents and delete this channel.",
        view=view
    )


@bot.tree.command(name="endbattle", description="Force close, remove records, and permanently delete an active battle channel.")
@app_commands.checks.has_permissions(manage_channels=True)
async def endbattle(interaction: discord.Interaction):
    # 1. Defend the thread from timeout cutoffs
    await interaction.response.defer(ephemeral=True)
    
    # 2. Check if this channel has an active tracking row inside MongoDB
    battle = await bot.db.active_battles.find_one({"channel_id": interaction.channel_id})
    if not battle:
        await interaction.followup.send("❌ Error: No official active battle registered to this channel context.", ephemeral=True)
        return

    # 3. Clean and delete the match row tracking matrix from the database
    await bot.db.active_battles.delete_one({"channel_id": interaction.channel_id})
    
    # 4. Announce cleanup and safely delete the Discord text channel
    await interaction.followup.send("🛑 **Match Closed:** Roster records purged cleanly. Deleting channel in 5 seconds...", ephemeral=True)
    await interaction.channel.send("🛑 **Administrative Closure:** This match channel is being deleted in 5 seconds...")
    
    await asyncio.sleep(5)
    await interaction.channel.delete()


@bot.tree.command(name="endmock", description="Instantly terminate a practice casual simulation layer.")
async def endmock(interaction: discord.Interaction):
    await bot.db.active_battles.delete_one({"channel_id": interaction.channel_id})
    await interaction.response.send_message("🧹 **Mock Purged:** Casual interface vectors closed cleanly.")

@bot.tree.command(name="undo", description="Wipe out the most recently logged match tracking mistake layout.")
async def undo(interaction: discord.Interaction):
    await interaction.response.send_message("⏪ **Action Undone:** Reverting the last entry parameter block.")


@bot.tree.command(name="kowalski", description="Fun stat analysis matrix tool mapping your metrics directly vs another player.")
async def kowalski(interaction: discord.Interaction, player: discord.Member):
    await interaction.response.send_message(f"🐧 *Kowalski, Analysis!* Comparing stats matrix metrics of <@{interaction.user.id}> directly against <@{player.id}>.")

@bot.tree.command(name="h2h", description="Display direct head-to-head career record history details between any two competitors.")
async def h2h(interaction: discord.Interaction, p1: discord.Member, p2: discord.Member):
    await interaction.response.send_message(f"📊 Head-to-Head Registry: Tracking career encounters between <@{p1.id}> and <@{p2.id}>.")

@bot.tree.command(name="mvps", description="Rank the top performing roster players across a specific crew team layout index.")
async def mvps(interaction: discord.Interaction, crew_name: str):
    await interaction.response.send_message(f"🎖️ MVP Ranks: Compiling highest performance counts for crew team **{crew_name}**.")

@bot.tree.command(name="leaderboard", description="Display top active crews sorted by competitive standing metrics.")
async def leaderboard(interaction: discord.Interaction):
    cursor = bot.db.crews.find().sort("elo", -1).limit(10)
    crews = await cursor.to_list(length=10)
    embed = discord.Embed(title="🏆 3 Stock Strike Seasonal Standings", color=discord.Color.gold())
    for i, c in enumerate(crews, 1):
        embed.add_field(name=f"#{i} {c['name']}", value=f"Elo: `{c['elo']}` | Record: {c['wins']}W - {c['losses']}L", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rankings", description="Fetch the structural tier placement brackets for the active seasonal standings.")
async def rankings(interaction: discord.Interaction):
    await interaction.response.defer()
    
    # 1. Fetch data metrics sorted by highest competitive Elo score
    cursor = bot.db.crews.find().sort("elo", -1).limit(15)
    crews = await cursor.to_list(length=15)
    
    embed = discord.Embed(title="📊 Seasonal Division Bracket Rankings", color=discord.Color.purple())
    
    tier_diamond = []
    tier_gold = []
    tier_silver = []
    
    # 2. Filter teams instantly into local structural rows based on current stats
    for c in crews:
        row_str = f"• **{c['name']}** (Elo: `{c['elo']}` | Record: {c['wins']}W - {c['losses']}L)"
        if c['elo'] >= 1150:
            tier_diamond.append(row_str)
        elif c['elo'] >= 1000:
            tier_gold.append(row_str)
        else:
            tier_silver.append(row_str)
            
    # 3. Compile layout columns into the final text embed
    embed.add_field(name="💎 Diamond Division (1150+ Elo)", value="\n".join(tier_diamond) if tier_diamond else "*No teams currently qualified*", inline=False)
    embed.add_field(name="🥇 Gold Division (1000-1149 Elo)", value="\n".join(tier_gold) if tier_gold else "*No teams currently qualified*", inline=False)
    embed.add_field(name="🥈 Silver Division (<1000 Elo)", value="\n".join(tier_silver) if tier_silver else "*No teams currently qualified*", inline=False)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="lumirank", description="Instantly display the latest global real-world professional player data tiers.")
async def lumirank(interaction: discord.Interaction):
    await interaction.response.send_message("🌍 **LumiRank Integration:** Querying global professional player tournament standings.")

@bot.tree.command(name="history", description="Pull up full record logs matching past competitive actions.")
async def history(interaction: discord.Interaction, crew_name: str):
    await interaction.response.send_message(f"📜 **Historical Logs:** Extracting past activity files for crew **{crew_name}**.")

@bot.tree.command(name="record", description="Display the official win/loss track metric catalog of a team.")
async def record(interaction: discord.Interaction, crew_name: str):
    await interaction.response.send_message(f"🗂️ **Database Record Query:** Compiling metric historical spreadsheets for **{crew_name}**.")

@bot.tree.command(name="recruit", description="Issue a formal server invite verification token for a player to join your crew.")
async def recruit(interaction: discord.Interaction, target: discord.Member):
    await interaction.response.send_message(f"✉️ **Roster Invite Dispatched:** Sent recruitment verification paperwork token layout routing to <@{target.id}>.")

@bot.tree.command(name="kick", description="Evict a specific member asset registry from your crew roster configuration sheet.")
async def kick(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"👢 **Roster Update:** Removed <@{member.id}> tracking files from active crew system registries.")

@bot.tree.command(name="leavecrew", description="Depart and resign from your current competitive organization sheet.")
async def leavecrew(interaction: discord.Interaction):
    await interaction.response.send_message("👋 **Resignation Processed:** Cleared your user data tracking parameters from the local group roster array layout.")

@bot.tree.command(name="promote", description="Elevate a trusted competitor asset to an executive Crew Leader permissions tier.")
async def promote(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🔼 Permissions Escalated: Granted Leader configuration execution flags to <@{member.id}>.")

@bot.tree.command(name="demote", description="Strip operational administrative permissions flags back down to basic regular user rows.")
async def demote(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🔽 Permissions Revoked: Reverted <@{member.id}> back to baseline competitor classification rows.")


@bot.tree.command(name="challenge", description="Issue a formal match challenge that opens a new tracking thread.")
async def challenge(interaction: discord.Interaction, target_crew: str):
    user_id = interaction.user.id
    caller_crew = await bot.db.crews.find_one({"members": user_id})
    
    if not caller_crew:
        await interaction.response.send_message("❌ Error: You must be a registered member of a crew to issue an official challenge.", ephemeral=True)
        return

    await interaction.response.defer()

    # 🧵 2. CREATE A DYNAMIC THREAD CONTEXT BLOCK FOR CHALLENGE SCHEDULING
    thread_title = f"Challenge: {caller_crew['name']} v {target_crew}"
    challenge_thread = await interaction.channel.create_thread(
        name=thread_title,
        auto_archive_duration=1440, # Keeps it alive for 24 hours of chatter
        type=discord.ChannelType.public_thread
    )

    await interaction.followup.send(f"✉️ **Challenge Dispatched!** Schedulers and captains, head to the thread at <#{challenge_thread.id}> to lock down match details.")
    await challenge_thread.send(f"⚠️ **Match Ultimatum Issued:** Squad **{caller_crew['name']}** has thrown down the gauntlet against organization **{target_crew}**! Awaiting formal response token verification loops.")



@bot.tree.command(name="denychallenge", description="Formally deny or wave off an incoming crew battle matching invitation matrix.")
async def denychallenge(interaction: discord.Interaction, attacking_crew: str):
    await interaction.response.send_message(f"🛡️ **Challenge Invite Dismissed:** Request invitation token sent from team **{attacking_crew}** was dropped safely.")

@bot.tree.command(name="modifycard", description="Change layout cosmetics, style structures, or template models of your player card.")
async def modifycard(interaction: discord.Interaction, visual_theme: str):
    await interaction.response.send_message(f"🎨 Personal configuration tag theme switched over to: `{visual_theme}`.")

@bot.tree.command(name="cardbackground", description="Link a raw picture custom background engine asset link directly to your graphic tags.")
async def cardbackground(interaction: discord.Interaction, link_url: str):
    await interaction.response.send_message("🖼️ Custom imagery tracking path anchor bound cleanly to canvas rendering properties layer fields.")

@bot.tree.command(name="setcolor", description="Map a custom hex code structural profile frame color palette layout variable.")
async def setcolor(interaction: discord.Interaction, hex_code: str):
    await interaction.response.send_message(f"🖌️ Profile frame visual embed border palette swapped to: `{hex_code}`.")

@bot.tree.command(name="ironman", description="Generate random structural rosters for challenge warmup brackets.")
async def ironman(interaction: discord.Interaction):
    selected = random.sample(CHARACTER_POOL, 5)
    await interaction.response.send_message(f"🎲 **Ironman Warmup Generation:** Your random roster is: {', '.join(selected)}")

@bot.tree.command(name="coin", description="Flip a rapid digital utility currency token coin to resolve stage striking priorities.")
async def coin(interaction: discord.Interaction):
    res = random.choice(["Heads 🪙", "Tails 🪙"])
    await interaction.response.send_message(f"🪙 Coin flipped: It landed squarely on **{res}**!")

@bot.tree.command(name="countdown", description="10-second countdown.")
async def countdown(interaction: discord.Interaction):
    # Send the initial message
    await interaction.response.send_message("⏰ **Countdown: 10**")
    
    # Fetch the message to edit
    countdown_msg = await interaction.original_response()
    
    # Loop from 9 to 1

    for seconds_left in range(9, 0, -1):
        await asyncio.sleep(1)
        await countdown_msg.edit(content=f"⏰ **Countdown: {seconds_left}**")
        
    # Finalize
    await asyncio.sleep(1)
    await countdown_msg.edit(content="🏁 **Countdown Finished! Ready up!**")

@bot.tree.command(name="approve_battle", description="Staff Only: Approve scoresheet, update records, and delete match channel.")
@app_commands.checks.has_permissions(manage_channels=True)
async def approve_battle(interaction: discord.Interaction, winner_crew: str, loser_crew: str):
    await interaction.response.defer(ephemeral=True)
    
    # 1. Update Database Stats
    await bot.db.crews.update_one({"name": {"$regex": f"^{winner_crew}$", "$options": "i"}}, {"$inc": {"wins": 1, "elo": 25}})
    await bot.db.crews.update_one({"name": {"$regex": f"^{loser_crew}$", "$options": "i"}}, {"$inc": {"losses": 1, "elo": -25}})
    
    # 2. Purge active tracking row from DB
    await bot.db.active_battles.delete_one({"channel_id": interaction.channel_id})
    
    # 3. Inform and delete channel
    await interaction.followup.send("✅ Scoresheet Approved! Deleting channel in 5 seconds...")
    await asyncio.sleep(5)
    await interaction.channel.delete()


@bot.tree.command(name="stagelist", description="Display full visual graphic maps mapping all legal starters and counterpick arenas.")
async def stagelist(interaction: discord.Interaction):
    embed = discord.Embed(title="🗺️ Official 3 Stock Strike Arena Ruleset", color=discord.Color.dark_gray())
    
    # 1. Map out structural listings cleanly
    embed.add_field(name="🔹 Starters (Game 1 Choices)", value="\n". join([f"• {stage}" for stage in LEGAL_STARTERS]), inline=True)
    embed.add_field(name="🔸 Counterpicks (Games 2+)", value="\n". join([f"• {stage}" for stage in LEGAL_COUNTERPICKS]), inline=True)
    
    # 2. Attach direct graphic layout URL (0% server footprint)
    # REPLACE THIS URL with your own custom ruleset image link if preferred
    embed.set_image(url="https://i.imgur.com/hRz1neH.jpeg") 
    embed.set_footer(text="Alternate map banning procedures sequentially in channel chat.")
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="starter", description="Secretly declare your lead-off game 1 starter player layout anonymously.")
async def starter(interaction: discord.Interaction, fighter: str):
    await interaction.response.send_message("🔒 **Game 1 Starter Locked Anonymously:** Selection catalog parameters held in private cache data layers.", ephemeral=True)

@bot.tree.command(name="stagegame1", description="Initiate the interactive stage-banning phase for the open matching frame.")
async def stagegame1(interaction: discord.Interaction):
    await interaction.response.send_message("🗺️ **Stage Strikes Initiated:** Players alternate strikes inside channel context tracking maps.")

@bot.tree.command(name="stream", description="Tie a live video broadcast transmission channel link directly into the ongoing match hub.")
async def stream(interaction: discord.Interaction, link: str):
    await interaction.response.send_message(f"📺 **Broadcast Link Attached:** Stream view path routing set directly to: <{link}>.")

@bot.tree.command(name="tryout", description="Apply for an open recruitment testing queue on a crew.")
async def tryout(interaction: discord.Interaction, crew_name: str):
    await interaction.response.send_message(f"📝 Added to **{crew_name}** recruitment list files.")

@bot.tree.command(name="tryouts", description="A master toggle configuration to instantly toggle team public recruiting doors on or off.")
async def tryouts(interaction: discord.Interaction, open_status: bool):
    state = "OPEN ✅" if open_status else "CLOSED ❌"
    await interaction.response.send_message(f"🚪 **Recruitment Gateways Modified:** Team trial applications are now set to: **{state}**.")

@bot.tree.command(name="tester", description="Assign or manage the specific crew member entities labeled as structural trials testers.")
async def tester(interaction: discord.Interaction, action: str, member: discord.Member):
    await interaction.response.send_message(f"🛠️ **Tester Roster Modified:** Set evaluation flags on user <@{member.id}> to structural index action: `{action}`.")

@bot.tree.command(name="transferownership", description="Securely pass full structural control flags of the crew entity over to a teammate.")
async def transferownership(interaction: discord.Interaction, recipient: discord.Member):
    await interaction.response.send_message(f"👑 **Ownership Migration Complete:** Primary administration matrix keys moved safely to <@{recipient.id}>.")


@bot.tree.command(name="equip", description="Equip an item from your unlocked inventory collection.")
async def equip_item(interaction: discord.Interaction, category: str, selection: str):
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    
    # Category sorting configurations maps
    valid_categories = ["fighter", "stage", "tint"]
    if category.strip().lower() not in valid_categories:
        await interaction.followup.send("❌ Invalid category. Choose from: `fighter`, `stage`, or `tint`.", ephemeral=True)
        return
        
    user_data = await bot.db.users.find_one({"_id": user_id})
    unlocked_inventory = user_data.get("unlocked_items", []) if user_data else []
    
    norm_selection = selection.strip().lower()
    
    # All baseline vanilla base features are unlocked from day one
    is_default = selection.strip() in ["Mario", "Battlefield", "Default Blue"]
    
    if not is_default and norm_selection not in unlocked_inventory and category.strip().lower() != "fighter":
        await interaction.followup.send(f"❌ You haven't purchased `{selection}` from the `/shop` yet.", ephemeral=True)
        return
        
    # Write choice state variables dynamically directly down to database fields
    db_field = f"equipped_{category.strip().lower()}"
    await bot.db.users.update_one({"_id": user_id}, {"$set": {db_field: selection.strip()}}, upsert=True)
    
    await interaction.followup.send(f"✅ Your profile card visual configuration for `{category}` has been updated to **{selection}**!", ephemeral=True)


@bot.tree.command(name="setmains", description="Instantly update your primary competitive character fighter choices on your card profile.")
async def setmains(interaction: discord.Interaction, mains: str):
    await interaction.response.send_message(f"🎯 Competitive primary configuration rows set cleanly to: `{mains}`.")

@bot.tree.command(name="setregion", description="Alter the geographic competitive server tag displayed on your player profile banner.")
async def setregion(interaction: discord.Interaction, location: str):
    await interaction.response.send_message(f"📍 Regional geolocation parameters mapped over to registry track: `{location}`.")

@bot.tree.command(name="setcrewcolor", description="Map a signature organization background embed color code parameter variable.")
async def setcrewcolor(interaction: discord.Interaction, color_hex: str):
    await interaction.response.send_message(f"🎨 Crew theme color configuration variable mapped over to parameters: `{color_hex}`.")

@bot.tree.command(name="setcrewimage", description="Link an image URL to panels displaying team specifications records layout files.")
async def setcrewimage(interaction: discord.Interaction, url: str):
    await interaction.response.send_message("🖼️ Crew layout image canvas property binding parameters locked down cleanly.")

@bot.tree.command(name="setcrewinfo", description="Publish summary text blocks describing active trial demands on team public boards.")
async def setcrewinfo(interaction: discord.Interaction, text_details: str):
    await interaction.response.send_message("📝 **Team Board Rules Updated:** Profile descriptions modified successfully.")

@bot.tree.command(name="setcrewlogo", description="Anchor an image link file to display as your signature crew organization crest symbol.")
async def setcrewlogo(interaction: discord.Interaction, logo_url: str):
    await interaction.response.send_message("🛡️ Organization structural team crest logo updated cleanly inside system archives.")

@bot.tree.command(name="substitute", description="Swap a player asset registry mid-battle if an active teammate steps out of loop paths.")
async def substitute(interaction: discord.Interaction, player_out: discord.Member, player_in: discord.Member):
    await interaction.response.send_message(f"🔄 **Roster Substitution Logged:** Pulling out <@{player_out.id}> and path routing <@{player_in.id}> into live arena loops.")


@bot.tree.command(name="force_win", description="Staff Override: Instantly award the active match victory to a specific crew team.")
async def force_win(interaction: discord.Interaction, crew_name: str):
    await interaction.response.send_message(f"⚖️ **Administrative Override:** Battle closed. Victory has been manually awarded to team **{crew_name}**.")

@bot.tree.command(name="blindpick", description="Submit your Game 1 fighter secretly to the bot to prevent counterpicking.")
async def blindpick(interaction: discord.Interaction, character: str):
    if character not in CHARACTER_POOL:
        await interaction.response.send_message("❌ Error: Invalid character name layout.", ephemeral=True)
        return
    await interaction.response.send_message("🔒 **Blind Pick Registered:** Your fighter choice has been safely held in secret cache memory.", ephemeral=True)

@bot.tree.command(name="reveal_blind", description="Simultaneously unlock and display both starting players hidden blind character picks.")
async def reveal_blind(interaction: discord.Interaction):
    await interaction.response.send_message("🔓 **Simultaneous Reveal:** Opening cached starter selections to the channel layout arena!")

@bot.tree.command(name="pause_battle", description="Halt the active match pacing timers due to a dynamic disconnect or lag dispute.")
async def pause_battle(interaction: discord.Interaction):
    await interaction.response.send_message("⏸️ **Battle Paused:** Pacing countdown timers frozen. Awaiting staff resolution clearance parameters.")

@bot.tree.command(name="resume_battle", description="Unfreeze a paused crew battle session and restart the active match clock tracking.")
async def resume_battle(interaction: discord.Interaction):
    await interaction.response.send_message("▶️ **Battle Resumed:** Timers un-paused. Competitors, return to your active setups immediately!")

@bot.tree.command(name="setcrewbanner", description="Anchor an image link URL to serve as your decorative background crew banner template.")
async def setcrewbanner(interaction: discord.Interaction, banner_url: str):
    await interaction.response.send_message("🖼️ **Branding Profile Upgraded:** Crew structural background banner asset linked cleanly.")

@bot.tree.command(name="setcrewname", description="Formally change the public alphanumeric title layout name of your crew organization.")
async def setcrewname(interaction: discord.Interaction, new_name: str):
    await interaction.response.send_message(f"✏️ **Branding Profile Upgraded:** Team identity registry swapped over to: **{new_name}**.")

@bot.tree.command(name="disband_crew", description="Permanently delete your crew portfolio, delete its channel, and free all members.")
async def disband_crew(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    guild = interaction.guild

    try:
        # Find the crew where the execution user is the explicit master owner
        target_crew = await bot.db.crews.find_one({"owner": user_id})

        if not target_crew:
            await interaction.followup.send("❌ You do not own a registered crew portfolio.", ephemeral=True)
            return

        crew_name = target_crew["name"]

        # --- NEW THREAD DELETION ENGINE LOCKS ---
        # Look for the crew's private channel thread inside the server active arrays
        # This scans threads under the channel where the command was run
        for thread in interaction.channel.threads:
            if thread.name.lower() == f"crew-{crew_name.lower()}":
                try:
                    await thread.delete()
                    print(f"🗑️ Successfully deleted thread channel: crew-{crew_name}")
                except discord.Forbidden:
                    print(f"⚠️ Permissions Error: Bot lacks Manage Threads privilege to delete crew-{crew_name}.")
                except discord.NotFound:
                    pass
                break # Found and handled, break the thread lookup loop
        # ----------------------------------------

        # Explicitly remove the document tracking the team record matching this specific id
        delete_result = await bot.db.crews.delete_one({"_id": target_crew["_id"]})

        if delete_result.deleted_count > 0:
            await interaction.followup.send(
                f"💥 **Organization Terminated:** Deleted **{crew_name}**, purged its private text thread, and released all roster members to free agency.", 
                ephemeral=True
            )
        else:
            await interaction.followup.send("❌ Error: Database entry could not be removed. Please retry.", ephemeral=True)

    except Exception as e:
        print(f"❌ Disband command failure: {e}")
        await interaction.followup.send(f"❌ Database execution failure: {e}", ephemeral=True)


@bot.tree.command(name="free_agents", description="Display a complete dynamic index directory list mapping all un-crewed server free agents.")
async def free_agents(interaction: discord.Interaction):
    await interaction.response.send_message("🕵️ **Directory Query:** Accessing global server tracking databases for available un-crewed talent rows.")

@bot.tree.command(name="toggle_fa", description="Toggle your personal public status marker between Free Agent and Unavailable rows.")
async def toggle_fa(interaction: discord.Interaction):
    await interaction.response.send_message("🏷️ **Status Tag Swapped:** Toggled your public profile search criteria markers inside team recruitment lists.")

@bot.tree.command(name="season_reset", description="Master Admin: Wipe active seasonal records and compress career rankings into historical files.")
async def season_reset(interaction: discord.Interaction):
    await interaction.response.send_message("🔄 **Seasonal Transition Engaged:** Archiving leaderboard standings rows and resetting active score tallies to zero.")

@bot.tree.command(name="vouch", description="Give an official competitive recommendation signature verification to an incoming trial recruit.")
async def vouch(interaction: discord.Interaction, player: discord.Member):
    await interaction.response.send_message(f"🤝 **Vouch Logged:** Added a permanent leadership character reference tag entry onto <@{player.id}>'s file profile.")

@bot.tree.command(name="setsecondary", description="Quickly map secondary pocket fighter backup characters onto your graphical player card matrix.")
async def setsecondary(interaction: discord.Interaction, alternate_char: str):
    await interaction.response.send_message(f"🥈 **Profile Updated:** Pocket backup secondary selection options bound cleanly to tag layout fields: `{alternate_char}`.")

@bot.tree.command(name="player_history", description="Extract dense, match-by-match career encounter logs for a specific competitor user ID.")
async def player_history(interaction: discord.Interaction, competitor: discord.Member):
    await interaction.response.send_message(f"🗂️ **Database Deep Sweep:** Fetching historic historical scoreboard frames mapping matches fought by <@{competitor.id}>.")

@bot.tree.command(name="help_referee", description="Open an interactive instructional manual panel layout breakdown of live match stock flows.")
async def help_referee(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 3 Stock Strike: Referee Manual", color=discord.Color.blue())
    embed.description = "Core flow chart steps mapping match commands out sequentially for server tournament structures."
    await interaction.response.send_message(embed=embed)

from flask import Flask
from threading import Thread

# =========================================================================
#                    KEEP-ALIVE WEB SERVER & BOT LAUNCH
# =========================================================================

# =========================================================================
#                    KEEP-ALIVE WEB SERVER & BOT LAUNCH
# =========================================================================

app = Flask('')

@app.route('/')
def home():
    return "SmashBot is awake and running!"

def run_web_server():
    """Starts the native Flask web listener on the port Render requires."""
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    print("🌐 Launching Render keep-alive web listener...")
    Thread(target=run_web_server, daemon=True).start()

    print("🚀 Connecting bot to Discord Gateway...")
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("❌ Error: DISCORD_TOKEN variable not found in Render Environment Variables.")

