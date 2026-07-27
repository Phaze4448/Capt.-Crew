import discord
from discord import app_commands
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
import os
import random
import io
from PIL import Image, ImageDraw, ImageFont

MONGO_URL = os.environ.get("MONGO_URL")
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

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
    description: str = "A competitive 3 Stock Strike Crew."

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
        await self.tree.sync()

bot = SmashBot()

@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user.name}!")

async def get_or_create_profile(user_id: int) -> dict:
    profile = await bot.db.players.find_one({"user_id": user_id})
    if not profile:
        new_p = PlayerProfile(user_id=user_id)
        await bot.db.players.insert_one(new_p.model_dump())
        return new_p.model_dump()
    return profile
@bot.tree.command(name="start_battle", description="Initialize a crew battle match session.")
async def start_battle(interaction: discord.Interaction, opponent_crew: str):
    user_id = interaction.user.id
    crew_a_data = await bot.db.crews.find_one({"leaders": user_id})
    crew_b_data = await bot.db.crews.find_one({"name": {"$regex": f"^{opponent_crew}$", "$options": "i"}})
    if not crew_a_data or not crew_b_data:
        await interaction.response.send_message("❌ Error: Invalid configuration.", ephemeral=True)
        return
    roster_a, roster_b = crew_a_data["members"], crew_b_data["members"]
    battle = ActiveBattle(
        channel_id=interaction.channel_id, crew_a=crew_a_data["name"], crew_b=crew_b_data["name"],
        roster_a=roster_a, roster_b=roster_b, current_player_a=roster_a, current_player_b=roster_b,
        total_stocks_a=len(roster_a)*3, total_stocks_b=len(roster_b)*3, current_striker=user_id
    )
    await bot.db.active_battles.insert_one(battle.model_dump())
    embed = discord.Embed(title="⚔️ 3 Stock Strike: Match Started!", color=discord.Color.red())
    embed.add_field(name=battle.crew_a, value=f"Active Fighter: <@{battle.current_player_a}>")
    embed.add_field(name=battle.crew_b, value=f"Active Fighter: <@{battle.current_player_b}>")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="report_match", description="Log the remaining stocks of the winner.")
async def report_match(interaction: discord.Interaction, winner_mention: discord.Member, stocks_left: int):
    battle_data = await bot.db.active_battles.find_one({"channel_id": interaction.channel_id})
    if not battle_data:
        await interaction.response.send_message("❌ Error: No active battle here.", ephemeral=True)
        return
    battle = ActiveBattle(**battle_data)
    winner_id = winner_mention.id
    if winner_id == battle.current_player_a:
        lost = battle.stocks_b
        battle.stocks_a = stocks_left
        battle.total_stocks_b -= lost
        await bot.db.players.update_one({"user_id": winner_id}, {"$inc": {"stocks_taken": lost}})
        await bot.db.players.update_one({"user_id": battle.current_player_b}, {"$inc": {"stocks_lost": lost}})
        idx = battle.roster_b.index(battle.current_player_b)
        if idx + 1 < len(battle.roster_b):
            battle.current_player_b = battle.roster_b[idx + 1]
            battle.stocks_b = 3
        else:
            await end_battle_session(interaction, battle, winner_crew=battle.crew_a, loser_crew=battle.crew_b)
            return
    elif winner_id == battle.current_player_b:
        lost = battle.stocks_a
        battle.stocks_b = stocks_left
        battle.total_stocks_a -= lost
        await bot.db.players.update_one({"user_id": winner_id}, {"$inc": {"stocks_taken": lost}})
        await bot.db.players.update_one({"user_id": battle.current_player_a}, {"$inc": {"stocks_lost": lost}})
        idx = battle.roster_a.index(battle.current_player_a)
        if idx + 1 < len(battle.roster_a):
            battle.current_player_a = battle.roster_a[idx + 1]
            battle.stocks_a = 3
        else:
            await end_battle_session(interaction, battle, winner_crew=battle.crew_b, loser_crew=battle.crew_a)
            return
    await bot.db.active_battles.replace_one({"channel_id": interaction.channel_id}, battle.model_dump())
    await interaction.response.send_message(f"Match Logged! Next up: <@{battle.current_player_a}> vs <@{battle.current_player_b}>")

async def end_battle_session(interaction, battle, winner_crew, loser_crew):
    w = await bot.db.crews.find_one({"name": winner_crew})
    l = await bot.db.crews.find_one({"name": loser_crew})
    exp = 1 / (1 + 10 ** ((l["elo"] - w["elo"]) / 400))
    diff = round(32 * (1 - exp))
    await bot.db.crews.update_one({"name": winner_crew}, {"$inc": {"elo": diff, "wins": 1}})
    await bot.db.crews.update_one({"name": loser_crew}, {"$inc": {"elo": -diff, "losses": 1}})
    await bot.db.active_battles.delete_one({"channel_id": battle.channel_id})
    await interaction.response.send_message(f"🏆 **{winner_crew}** wins! (+{diff} Elo Standings Mod)")

@bot.tree.command(name="stagelist", description="Display full list of legal arenas.")
async def stagelist(interaction: discord.Interaction):
    embed = discord.Embed(title="🗺️ 3 Stock Strike Rulebook: Legal Arenas", color=discord.Color.dark_gray())
    embed.add_field(name="Starter Maps", value="\n".join([f"• {s}" for s in LEGAL_STARTERS]), inline=False)
    embed.add_field(name="Counterpick Maps", value="\n".join([f"• {c}" for c in LEGAL_COUNTERPICKS]), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="strike_stage", description="Ban a competitive stage.")
async def strike_stage(interaction: discord.Interaction, stage_name: str):
    battle_data = await bot.db.active_battles.find_one({"channel_id": interaction.channel_id})
    if not battle_data:
        await interaction.response.send_message("❌ Error: No active battle session.", ephemeral=True)
        return
    battle = ActiveBattle(**battle_data)
    battle.stage_strikes.append(stage_name)
    await bot.db.active_battles.replace_one({"channel_id": interaction.channel_id}, battle.model_dump())
    await interaction.response.send_message(f"⛔ **{stage_name}** has been banned.")

@bot.tree.command(name="setprofile", description="Set up your character mains and region data.")
async def setprofile(interaction: discord.Interaction, region: str, main_fighter: str):
    if main_fighter not in CHARACTER_POOL:
        await interaction.response.send_message("❌ Error: Invalid character name.", ephemeral=True)
        return
    await bot.db.players.update_one({"user_id": interaction.user.id}, {"$set": {"region": region, "mains": [main_fighter]}}, upsert=True)
    await interaction.response.send_message("✅ Personal profile metrics updated successfully!")

@bot.tree.command(name="tag", description="Render a graphical summary card profile banner.")
async def tag(interaction: discord.Interaction, target_user: Optional[discord.Member] = None):
    user = target_user or interaction.user
    p = await get_or_create_profile(user.id)
    img = Image.new("RGBA", (500, 200), color="#23272A")
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 490, 190], fill="#2C2F33", outline=p["card_color"], width=3)
    draw.text((30, 30), f"PLAYER PROFILE: {user.name}", fill="#FFFFFF")
    draw.text((30, 70), f"Region Standing: {p['region']}", fill="#B9BBBE")
    draw.text((30, 100), f"Character Mains: {', '.join(p['mains']) or 'None'}", fill="#B9BBBE")
    draw.text((30, 140), f"Stocks Taken: {p['stocks_taken']} | MVPs: {p['mvps']}", fill="#EF5350")
    byte_arr = io.BytesIO()
    img.save(byte_arr, format="PNG")
    byte_arr.seek(0)
    await interaction.response.send_message(file=discord.File(byte_arr, "profile_card.png"))

@bot.tree.command(name="create_crew", description="Register a brand new crew.")
async def create_crew(interaction: discord.Interaction, name: str):
    user_id = interaction.user.id
    in_crew = await bot.db.crews.find_one({"members": user_id})
    if in_crew:
        await interaction.response.send_message("❌ Error: Already registered on a team.", ephemeral=True)
        return
    new_crew = CrewModel(name=name, owner_id=user_id, leaders=[user_id], members=[user_id])
    await bot.db.crews.insert_one(new_crew.model_dump())
    await interaction.response.send_message(f"✅ Crew **{name}** has been successfully registered!")

@bot.tree.command(name="tryout", description="Apply for open recruitment on a crew.")
async def tryout(interaction: discord.Interaction, crew_name: str):
    crew = await bot.db.crews.find_one({"name": {"$regex": f"^{crew_name}$", "$options": "i"}})
    if not crew or not crew["tryouts_open"]:
        await interaction.response.send_message("❌ Error: Tryouts closed or crew doesn't exist.", ephemeral=True)
        return
    await bot.db.crews.update_one({"name": crew["name"]}, {"$push": {"tryout_list": interaction.user.id}})
    await interaction.response.send_message(f"📝 You joined the tryout queue for **{crew['name']}**!")

@bot.tree.command(name="leaderboard", description="Display top active crews sorted by Elo.")
async def leaderboard(interaction: discord.Interaction):
    cursor = bot.db.crews.find().sort("elo", -1).limit(10)
    crews = await cursor.to_list(length=10)
    embed = discord.Embed(title="🏆 3 Stock Strike Standings", color=discord.Color.gold())
    for i, c in enumerate(crews, 1):
        embed.add_field(name=f"#{i} {c['name']}", value=f"Elo: `{c['elo']}` | Record: {c['wins']}W - {c['losses']}L", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ironman", description="Generate 5 random fighters for challenge warmups.")
async def ironman(interaction: discord.Interaction):
    selected = random.sample(CHARACTER_POOL, 5)
    embed = discord.Embed(title="🎲 Random Ironman Roster Generator", color=discord.Color.purple())
    embed.description = "\n".join([f"{i}. {char}" for i, char in enumerate(selected, 1)])
    await interaction.response.send_message(embed=embed)

bot.run(BOT_TOKEN)
