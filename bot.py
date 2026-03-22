import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Music queue
queues = {}

# YTDL options
ytdl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'extract_flat': 'in_playlist'
}

ffmpeg_opts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_opts)

# ===== Bot Events =====
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# ===== Play Command =====
@bot.command()
async def play(ctx, *, url):
    voice_channel = ctx.author.voice.channel
    if not voice_channel:
        await ctx.send("Join a voice channel first!")
        return

    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = asyncio.Queue()

    # Add song to queue
    await queues[ctx.guild.id].put(url)
    await ctx.send(f"Added to queue: {url}")

    if not ctx.voice_client:
        await voice_channel.connect()
        await play_queue(ctx)

async def play_queue(ctx):
    guild_id = ctx.guild.id
    voice_client = ctx.voice_client

    while not queues[guild_id].empty():
        url = await queues[guild_id].get()

        info = ytdl.extract_info(url, download=False)
        audio_url = info['url']
        source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_opts)

        voice_client.play(source)
        await ctx.send(f"Now playing: {info.get('title', 'Unknown')}")

        while voice_client.is_playing():
            await asyncio.sleep(1)

    await voice_client.disconnect()

# ===== Skip Command =====
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped current song.")
    else:
        await ctx.send("Nothing is playing.")

# ===== Stop Command =====
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        queues[ctx.guild.id] = asyncio.Queue()  # Clear queue
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("Stopped playback and cleared queue.")
    else:
        await ctx.send("Bot is not in a voice channel.")

bot.run(TOKEN)
