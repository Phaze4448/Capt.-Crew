import discord
from discord import app_commands
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List
import os

MONGO_URL = os.environ.get("MONGO_URL")
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

class CrewModel(BaseModel):
    name: str
    owner_id: int
    leaders: List[int]
    members: List[int]
    elo: int = 1000
    wins: int = 0
    losses: int = 0

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

# ==========================================
# [EXISTING 4 CORE COMMANDS]
# ==========================================
@bot.tree.command(name="create_crew", description="Register a brand new crew.")
async def create_crew(interaction: discord.Interaction, name: str):
    user_id = interaction.user.id
    in_crew = await bot.db.crews.find_one({"members": user_id})
    if in_crew:
        await interaction.response.send_message("❌ Error: You are already in a crew!", ephemeral=True)
        return
    name_exists = await bot.db.crews.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
    if name_exists:
        await interaction.response.send_message("❌ Error: That crew name is already taken!", ephemeral=True)
        return
    new_crew = CrewModel(name=name, owner_id=user_id, leaders=[user_id], members=[user_id])
    await bot.db.crews.insert_one(new_crew.model_dump())
    await interaction.response.send_message(f"✅ Success! Crew **{name}** has been officially registered!")

@bot.tree.command(name="join_crew", description="Join an existing crew roster.")
async def join_crew(interaction: discord.Interaction, crew_name: str):
    user_id = interaction.user.id
    in_crew = await bot.db.crews.find_one({"members": user_id})
    if in_crew:
        await interaction.response.send_message("❌ Error: You must leave your current crew first!", ephemeral=True)
        return
    target = await bot.db.crews.find_one({"name": {"$regex": f"^{crew_name}$", "$options": "i"}})
    if not target:
        await interaction.response.send_message("❌ Error: That crew does not exist!", ephemeral=True)
        return
    await bot.db.crews.update_one({"name": target["name"]}, {"$push": {"members": user_id}})
    await interaction.response.send_message(f"🎉 Welcome! You have joined **{target['name']}**!")

@bot.tree.command(name="start_battle", description="Initialize a crew battle match session.")
async def start_battle(interaction: discord.Interaction, opponent_crew: str):
    user_id = interaction.user.id
    crew_a_data = await bot.db.crews.find_one({"leaders": user_id})
    crew_b_data = await bot.db.crews.find_one({"name": {"$regex": f"^{opponent_crew}$", "$options": "i"}})
    
    if not crew_a_data:
        await interaction.response.send_message("❌ Error: You must be a crew leader to start a battle!", ephemeral=True)
        return
    if not crew_b_data:
        await interaction.response.send_message("❌ Error: Opponent crew not found!", ephemeral=True)
        return

    roster_a = crew_a_data["members"]
    roster_b = crew_b_data["members"]

    battle = ActiveBattle(
        channel_id=interaction.channel_id,
        crew_a=crew_a_data["name"],
        crew_b=crew_b_data["name"],
        roster_a=roster_a,
        roster_b=roster_b,
        current_player_a=roster_a[0],
        current_player_b=roster_b[0],
        total_stocks_a=len(roster_a) * 3,
        total_stocks_b=len(roster_b) * 3
    )

    await bot.db.active_battles.insert_one(battle.model_dump())
    
    embed = discord.Embed(title="⚔️ 3 Stock Strike: Battle Started! ⚔️", color=discord.Color.red())
    embed.add_field(name=battle.crew_a, value=f"Active: <@{battle.current_player_a}> (3 Stocks)", inline=False)
    embed.add_field(name=battle.crew_b, value=f"Active: <@{battle.current_player_b}> (3 Stocks)", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="report_match", description="Log the remaining stocks of the winner.")
async def report_match(interaction: discord.Interaction, winner_mention: discord.Member, stocks_left: int):
    channel_id = interaction.channel_id
    battle_data = await bot.db.active_battles.find_one({"channel_id": channel_id})
    
    if not battle_data:
        await interaction.response.send_message("❌ Error: No active battle running in this channel.", ephemeral=True)
        return
    
    battle = ActiveBattle(**battle_data)
    winner_id = winner_mention.id

    if winner_id == battle.current_player_a:
        lost_stocks = battle.stocks_b
        battle.stocks_a = stocks_left
        battle.total_stocks_b -= lost_stocks
        
        curr_idx = battle.roster_b.index(battle.current_player_b)
        if curr_idx + 1 < len(battle.roster_b):
            battle.current_player_b = battle.roster_b[curr_idx + 1]
            battle.stocks_b = 3
        else:
            await end_battle_session(interaction, battle, winner_crew=battle.crew_a, loser_crew=battle.crew_b)
            return
            
    elif winner_id == battle.current_player_b:
        lost_stocks = battle.stocks_a
        battle.stocks_b = stocks_left
        battle.total_stocks_a -= lost_stocks
        
        curr_idx = battle.roster_a.index(battle.current_player_a)
        if curr_idx + 1 < len(battle.roster_a):
            battle.current_player_a = battle.roster_a[curr_idx + 1]
            battle.stocks_a = 3
        else:
            await end_battle_session(interaction, battle, winner_crew=battle.crew_b, loser_crew=battle.crew_a)
            return
    else:
        await interaction.response.send_message("❌ Error: Winner selection must be an active match player.", ephemeral=True)
        return

    await bot.db.active_battles.replace_one({"channel_id": channel_id}, battle.model_dump())
    
    embed = discord.Embed(title="Game Result Recorded", color=discord.Color.blue())
    embed.description = f"**Next Game:** <@{battle.current_player_a}> ({battle.stocks_a} Remaining) vs <@{battle.current_player_b}> ({battle.stocks_b} Remaining)"
    await interaction.response.send_message(embed=embed)

async def end_battle_session(interaction: discord.Interaction, battle: ActiveBattle, winner_crew: str, loser_crew: str):
    w_data = await bot.db.crews.find_one({"name": winner_crew})
    l_data = await bot.db.crews.find_one({"name": loser_crew})
    
    expected_win = 1 / (1 + 10 ** ((l_data["elo"] - w_data["elo"]) / 400))
    elo_change = round(32 * (1 - expected_win))
    
    await bot.db.crews.update_one({"name": winner_crew}, {"$inc": {"elo": elo_change, "wins": 1}})
    await bot.db.crews.update_one({"name": loser_crew}, {"$inc": {"elo": -elo_change, "losses": 1}})
    await bot.db.active_battles.delete_one({"channel_id": battle.channel_id})
    
    embed = discord.Embed(title="🏆 3 Stock Strike: Crew Battle Finished! 🏆", color=discord.Color.gold())
    embed.add_field(name="👑 Ultimate Winner", value=f"**{winner_crew}** (+{elo_change} Elo Increase)")
    embed.add_field(name="💀 Defeated Crew", value=f"**{loser_crew}** (-{elo_change} Elo)")
    await interaction.channel.send(embed=embed)

# ==========================================
# [NEW COMMAND 5: SEASONAL LEADERBOARD]
# ==========================================
@bot.tree.command(name="leaderboard", description="Display top active crews sorted by competitive Elo standing.")
async def leaderboard(interaction: discord.Interaction):
    cursor = bot.db.crews.find().sort("elo", -1).limit(10)
    crews = await cursor.to_list(length=10)
    
    if not crews:
        await interaction.response.send_message("The leaderboard is currently empty! No crews registered yet.", ephemeral=True)
        return

    embed = discord.Embed(title="🏆 3 Stock Strike Seasonal Leaderboard 🏆", color=discord.Color.gold())
    for i, crew in enumerate(crews, 1):
        embed.add_field(
            name=f"#{i} - {crew['name']}", 
            value=f"**Elo Standing:** `{crew['elo']}` | **Record:** {crew['wins']}W - {crew['losses']}L", 
            inline=False
        )
    await interaction.response.send_message(embed=embed)

# ==========================================
# [NEW COMMAND 6: DISPLAY ACTIVE ROSTER]
# ==========================================
@bot.tree.command(name="roster", description="View the complete player roster of a specific crew.")
async def roster(interaction: discord.Interaction, crew_name: str):
    crew = await bot.db.crews.find_one({"name": {"$regex": f"^{crew_name}$", "$options": "i"}})
    if not crew:
        await interaction.response.send_message("❌ Error: Crew not found.", ephemeral=True)
        return

    embed = discord.Embed(title=f"📋 {crew['name']} Roster Sheet", color=discord.Color.blue())
    embed.add_field(name="Owner / General Manager", value=f"<@{crew['owner_id']}>", inline=False)
    
    members_text = ""
    for member_id in crew["members"]:
        members_text += f"• <@{member_id}>\n"
        
    embed.add_field(name="Registered Competitors", value=members_text or "No members listed.", inline=False)
    embed.set_footer(text=f"Current Elo Rank: {crew['elo']}")
    await interaction.response.send_message(embed=embed)

# ==========================================
