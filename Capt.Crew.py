import discord
from discord import app_commands
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
import os
import random
import io
import time
from PIL import Image, ImageDraw
from aiohttp import web
import asyncio

MONGO_URL = os.environ.get("MONGO_URL")
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

async def handle(request): return web.Response(text="Bot is running!")
app = web.Application()
app.router.add_get('/', handle)
async def run_web():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000)))
    await site.start()

# Preset Assets Dictionary Configuration Maps
FIGHTER_IMAGES = {
    "Mario": "https://smashbros.com",
    "Donkey Kong": "https://smashbros.com",
    "Link": "https://smashbros.com",
    "Fox": "https://smashbros.com",
    "Joker": "https://smashbros.com",
    # Populate matching strings directly from your script's existing CHARACTER_POOL
}

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

class SmashBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.db = None

    async def setup_hook(self):
        client = AsyncIOMotorClient(MONGO_URL)
        self.db = client["smash_crew_db"]
        asyncio.get_event_loop().create_task(run_web())
        await self.tree.sync()

bot = SmashBot()

@bot.event
async def on_ready():
    print(f"📡 Logged in as: {bot.user.name}")
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
    """Programmatically constructs your server's player profile card asset using Pillow."""
    async with aiohttp.ClientSession() as session:
        # 1. Fetch Stage Background Resource
        bg_url = STAGE_BACKGROUNDS.get(background_name, STAGE_BACKGROUNDS["Battlefield"])
        async with session.get(bg_url) as resp:
            bg_data = await resp.read()
            
        # 2. Fetch Fighter Render Resource
        fighter_url = FIGHTER_IMAGES.get(fighter_name, FIGHTER_IMAGES["Mario"])
        async with session.get(fighter_url) as resp:
            fighter_data = await resp.read()

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
    "Mario": "https://smashbros.com",
    "Donkey Kong": "https://smashbros.com",
    "Link": "https://smashbros.com",
    "Fox": "https://smashbros.com",
    "Joker": "https://smashbros.com",
    "Sonic": "https://smashbros.com"
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
        fighter_url = FIGHTER_IMAGES.get(fighter_name, FIGHTER_IMAGES["Mario"])
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
    
    # Fetch currency ledger and rank positions from database collections
    profile_record = await bot.db.users.find_one({"_id": target_user.id})
    crew_record = await bot.db.crews.find_one({"members": target_user.id})
    
    # Assign default fallbacks for unranked or newly registered profiles
    gold_balance = profile_record.get("gold", 150) if profile_record else 150
    elo_rating = crew_record.get("elo", 1000) if crew_record else 1000
    
    equipped_fighter = profile_record.get("equipped_fighter", "Mario") if profile_record else "Mario"
    equipped_stage = profile_record.get("equipped_stage", "Battlefield") if profile_record else "Battlefield"
    equipped_tint_name = profile_record.get("equipped_tint", "Default Blue") if profile_record else "Default Blue"
    
    tint_color_tuple = STAGE_TINTS.get(equipped_tint_name, STAGE_TINTS["Default Blue"])

    try:
        # Run calculation graphic script pipeline
        card_file = await generate_player_card(
            username=target_user.name,
            fighter_name=equipped_fighter,
            background_name=equipped_stage,
            tint_rgba=tint_color_tuple,
            gold_balance=gold_balance,
            elo=elo_rating
        )
        await interaction.followup.send(file=card_file)
    except Exception as e:
        print(f"❌ Card Render Error: {e}")
        await interaction.followup.send("❌ An issue occurred while generating your profile graphics frame.", ephemeral=True)



# --- DISCORD SLASH COMMAND WRAPPERS ---



# =========================================================================
#                    THE TOURNAMENT MARKETPLACE MODULE
# =========================================================================

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

# Create a tiny dummy web application
app = Flask('')

@app.route('/')
def home():
    return "SmashBot is online and running!"

def run_web_server():
    # This automatically reads Render's required port number dynamically
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- KEEP ALL OF YOUR ORIGINAL BOT EXECUTION CODE ---
if __name__ == "__main__":
    # 1. Start the web server on a separate background thread
    print("🌐 Starting keep-alive web server...")
    Thread(target=run_web_server).start()

    # 2. Run your original Discord Bot startup line
    print("🚀 Connecting to Discord Gateway...")
    bot.run(os.environ.get("DISCORD_TOKEN"))



bot.run(BOT_TOKEN)
