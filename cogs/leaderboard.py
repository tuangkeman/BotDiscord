"""
cogs/leaderboard.py — Command /leaderboard dan /info
"""
import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.db import get_leaderboard, get_user_stats, ensure_user


MEDAL = ["🥇", "🥈", "🥉"]


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="leaderboard",
        description="Tampilkan papan peringkat top 10 pemain KodeKuy!"
    )
    async def leaderboard_command(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        rows = await get_leaderboard(limit=10)

        if not rows:
            await interaction.followup.send(
                "Belum ada data leaderboard. Mulai solve soal dengan `/soal`! 🐍",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🏆 Leaderboard — KodeKuy Python Challenge",
            color=config.COLOR_INFO,
        )

        lines = []
        for i, (username, total_solved, total_sub, points) in enumerate(rows, start=1):
            medal = MEDAL[i - 1] if i <= 3 else f"`#{i}`"
            acc   = round(total_solved / total_sub * 100, 1) if total_sub > 0 else 0.0
            lines.append(
                f"{medal} **{username}** — "
                f"🏆 {points} pts | ✅ {total_solved} solved | 🎯 {acc}%"
            )

        embed.description = "\n".join(lines)
        embed.set_footer(text="Setiap soal yang di-Accepted pertama kali = +10 poin | KodeKuy 🐍")

        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="info",
        description="Informasi tentang bot KodeKuy dan cara penggunaannya."
    )
    async def info_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🐍 KodeKuy — Python Coding Challenge Bot",
            description=(
                "Bot latihan soal coding Python bergaya **Pak Dengklek**!\n"
                "Solve soal cerita, uji kode kamu, dan bersaing di leaderboard!"
            ),
            color=config.COLOR_INFO,
        )

        embed.add_field(
            name="📋 Commands",
            value=(
                "`/soal` — Dapatkan soal acak (bisa filter kategori)\n"
                "`/submit [id]` — Submit kode untuk soal tertentu\n"
                "`/profil` — Lihat statistik & progress kamu\n"
                "`/leaderboard` — Papan peringkat top 10\n"
                "`/info` — Tampilkan info ini"
            ),
            inline=False,
        )

        embed.add_field(
            name="📁 Kategori Soal",
            value=(
                "🔢 Matematika · 🔤 String · 📋 Array\n"
                "🧠 Logika · 🔃 Sorting"
            ),
            inline=False,
        )

        embed.add_field(
            name="🏅 Verdict",
            value=(
                "✅ **Accepted** — +10 poin (pertama kali)\n"
                "❌ **Wrong Answer** — output tidak sesuai\n"
                "⏰ **TLE** — melebihi batas waktu 5 detik\n"
                "💥 **Runtime Error** — kode crash\n"
                "🚫 **Forbidden Code** — import modul berbahaya"
            ),
            inline=False,
        )

        embed.add_field(
            name="💡 Tips",
            value=(
                "• Gunakan `input()` untuk membaca input\n"
                "• Gunakan `print()` untuk output\n"
                "• `sys` tersedia, tapi `os`, `subprocess` diblokir\n"
                "• Setiap test case dibatasi **5 detik**"
            ),
            inline=False,
        )

        embed.set_footer(text="KodeKuy Bot 🐍 | Dibuat dengan discord.py")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
