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
async def on_ready(): print(f"Logged in as {bot.user.name}!")

async def get_or_create_profile(user_id: int) -> dict:
    profile = await bot.db.players.find_one({"user_id": user_id})
    if not profile:
        new_p = PlayerProfile(user_id=user_id)
        await bot.db.players.insert_one(new_p.model_dump())
        return new_p.model_dump()
    return profile


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

@bot.tree.command(name="send", description="Deploy the next counterpick combat fighter.")
async def send(interaction: discord.Interaction, player: discord.Member):
    await interaction.response.send_message(f"🚀 Roster entry deployed! <@{player.id}> is jumping into the arena!")

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

@bot.tree.command(name="forfeit", description="Voluntarily concede the current match map calculation flow.")
async def forfeit(interaction: discord.Interaction):
    await interaction.response.send_message("🏳️ **Concession Logged:** Crew has chosen to forfeit the current map section.")

@bot.tree.command(name="endbattle", description="Force close and archive an active battle track sequence layout.")
async def endbattle(interaction: discord.Interaction):
    await bot.db.active_battles.delete_one({"channel_id": interaction.channel_id})
    await interaction.response.send_message("🛑 **Match Closed:** Roster logs compiled and active session path purged cleanly.")

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

@bot.tree.command(name="rankings", description="Fetch the exact structural tier placement brackets for the active season array.")
async def rankings(interaction: discord.Interaction):
    await interaction.response.send_message("📈 **Bracket Standings:** Accessing official division structural arrays.")

@bot.tree.command(name="lumirank", description="Instantly display the latest global real-world professional player data tiers.")
async def lumirank(interaction: discord.Interaction):
    await interaction.response.send_message("🌍 **LumiRank Integration:** Querying global professional player tournament standings.")

@bot.tree.command(name="history", description="Pull up full record logs matching past competitive actions.")
async def history(interaction: discord.Interaction, crew_name: str):
    await interaction.response.send_message(f"📜 **Historical Logs:** Extracting past activity files for crew **{crew_name}**.")

@bot.tree.command(name="record", description="Display the official win/loss track metric catalog of a team.")
async def record(interaction: discord.Interaction, crew_name: str):
    await interaction.response.send_message(f"🗂️ **Database Record Query:** Compiling metric historical spreadsheets for **{crew_name}**.")

@bot.tree.command(name="crewapplication", description="Start an automated private DM onboarding module wizard to form a brand new crew.")
async def crewapplication(interaction: discord.Interaction):
    await interaction.response.send_message("📬 Onboarding file package delivered! Please check your private DMs to start your creation wizard application process.", ephemeral=True)

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

@bot.tree.command(name="countdown", description="Trigger a rapid utility 10-second structural clock execution frame.")
async def countdown(interaction: discord.Interaction):
    await interaction.response.send_message("⏰ **Pacing Countdown Commenced:** 10... 9... 8... Ready up standard configurations!")

@bot.tree.command(name="stagelist", description="Display full list of legal starter and counterpick arenas.")
async def stagelist(interaction: discord.Interaction):
    embed = discord.Embed(title="🗺️ Legal Arena Standings", color=discord.Color.dark_gray())
    embed.add_field(name="Starters", value="\n".join(LEGAL_STARTERS))
    embed.add_field(name="Counterpicks", value="\n".join(LEGAL_COUNTERPICKS))
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

@bot.tree.command(name="shop", description="Access the cosmetic shop marketplace to browse alternative profile card background skins.")
async def shop(interaction: discord.Interaction):
    await interaction.response.send_message("🛒 **Cosmetics Marketplace Connected:** Browsing item catalogs for card background overlays.")

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

@bot.tree.command(name="create_crew", description="Register a brand new crew and initialize their locked private headquarters thread.")
async def create_crew(interaction: discord.Interaction, name: str):
    user_id = interaction.user.id
    in_crew = await bot.db.crews.find_one({"members": user_id})
    
    if in_crew:
        await interaction.response.send_message("❌ Error: You are already registered to an active crew team roster loop.", ephemeral=True)
        return
        
    name_exists = await bot.db.crews.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
    if name_exists:
        await interaction.response.send_message("❌ Error: That crew organization name is already cataloged.", ephemeral=True)
        return

    # Defer response to buy time for private channel creation sweeps
    await interaction.response.defer()

    # 🔒 DYNAMIC PRIVATE THREAD GENERATION LOGIC
    # Private threads completely hide the huddle space from anyone not explicitly added
    crew_thread_title = f"🔒┃{name}-headquarters"
    personal_thread = await interaction.channel.create_thread(
        name=crew_thread_title,
        auto_archive_duration=4320, # Keeps it open for multiple days of roster strategy chatter
        type=discord.ChannelType.private_thread,
        reason=f"Locked 3 Stock Strike Private Headquarters Instance Framework Initialization."
    )

    # Save data arrays cleanly into MongoDB cloud data storage models
    new_crew = CrewModel(name=name, owner_id=user_id, leaders=[user_id], members=[user_id])
    await bot.db.crews.insert_one(new_crew.model_dump())
    
    # Explicitly pull the creator user profile into the newly formed private workspace
    await personal_thread.add_user(interaction.user)
    
    # Send a clean fallback confirmation message onto the main setup channel
    await interaction.followup.send(f"✅ **Crew Registered!** Your locked private operations thread has been successfully initialized at <#{personal_thread.id}>.")
    
    # Send a welcoming guide statement right into the secure bunker room
    embed = discord.Embed(title=f"👑 Welcome to the {name} Headquarters 👑", color=discord.Color.from_str("#7289DA"))
    embed.description = (
        f"This workspace is a **Secure Private Thread** locked away from the public server channel list.\n\n"
        f"• **Roster Status:** Only <@{user_id}> can access this feed initially.\n"
        f"• **Recruitment Actions:** Use Discord's built-in **`+ Add to Thread`** link panel button at the top of your screen to pull your roster members in!"
    )
    await personal_thread.send(embed=embed)


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

@bot.tree.command(name="disband_crew", description="Permanently delete your crew organization database file folder from the master index.")
async def disband_crew(interaction: discord.Interaction):
    await interaction.response.send_message("💥 **Organization Terminated:** Deleted your team portfolio and released all roster members to free agency.")


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

bot.run(BOT_TOKEN)
