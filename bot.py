"""
bot.py — Entry point utama KodeKuy Bot
"""
import sys
import io

# Fix encoding Windows terminal agar emoji bisa ditampilkan
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import discord
from discord.ext import commands
import asyncio
import os

import config
from utils.db import init_db


class KodeKuyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        """Dipanggil sekali saat bot mulai — load cogs & sync slash commands."""
        # Pastikan folder data ada
        os.makedirs("data", exist_ok=True)

        # Inisialisasi database
        await init_db()
        print("✅ Database siap.")

        # Load semua cogs
        await self.load_extension("cogs.soal")
        await self.load_extension("cogs.leaderboard")
        print("✅ Semua cog dimuat.")

        # Sync slash commands ke Discord
        synced = await self.tree.sync()
        print(f"✅ {len(synced)} slash command berhasil di-sync.")

    async def on_ready(self):
        print(f"\n{'='*40}")
        print(f"  🐍 KodeKuy Bot Online!")
        print(f"  User : {self.user} (ID: {self.user.id})")
        print(f"  Guild: {len(self.guilds)} server")
        print(f"{'='*40}\n")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Python Coding Challenge 🐍 | /soal",
            )
        )

    async def on_command_error(self, ctx, error):
        pass  # Abaikan error prefix command (bot pakai slash commands)


bot = KodeKuyBot()


if __name__ == "__main__":
    token = config.DISCORD_TOKEN
    if not token:
        print("❌ DISCORD_TOKEN tidak ditemukan!")
        print("   Salin .env.example menjadi .env lalu isi token kamu.")
        exit(1)
    bot.run(token, log_handler=None)
