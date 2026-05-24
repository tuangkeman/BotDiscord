"""
cogs/soal.py — Command /soal, /profil, SoalView, dan SubmitModal
Inti dari bot: menampilkan soal, menerima kode, dan menilai hasilnya.
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import random

import config
from utils.db import ensure_user, get_solved_ids, record_submission
from utils.judge import judge


# ─────────────────────────────────────────────
# Load semua soal dari JSON
# ─────────────────────────────────────────────
with open(config.SOAL_PATH, encoding="utf-8") as f:
    ALL_SOAL: list[dict] = json.load(f)

KATEGORI_LIST = list(config.EMOJI_KATEGORI.keys())


def get_soal_embed(soal: dict) -> discord.Embed:
    """Buat embed Discord untuk menampilkan sebuah soal."""
    emoji_kat  = config.EMOJI_KATEGORI.get(soal["kategori"], "📝")
    emoji_diff = config.EMOJI_DIFFICULTY.get(soal["difficulty"], "⬜")

    embed = discord.Embed(
        title=f"#{soal['id']} · {soal['judul']}",
        description=soal["cerita"],
        color=config.COLOR_INFO,
    )

    # Badge kategori & difficulty
    embed.add_field(
        name="Kategori & Kesulitan",
        value=f"{emoji_kat} **{soal['kategori']}** · {emoji_diff} **{soal['difficulty']}**",
        inline=False,
    )

    # Format input & output
    embed.add_field(name="📥 Format Input",  value=soal["input_format"],  inline=False)
    embed.add_field(name="📤 Format Output", value=soal["output_format"], inline=False)
    embed.add_field(name="📏 Batasan",       value=soal["batasan"],       inline=False)

    # Contoh
    embed.add_field(
        name="💡 Contoh Input",
        value=f"```\n{soal['contoh_input']}\n```",
        inline=True,
    )
    embed.add_field(
        name="✅ Contoh Output",
        value=f"```\n{soal['contoh_output']}\n```",
        inline=True,
    )

    tc_count = len(soal["test_cases"])
    embed.set_footer(text=f"🧪 {tc_count} test case tersembunyi  |  ⏱️ Timeout: {config.SANDBOX_TIMEOUT}s  |  🐍 Python")
    return embed


def get_verdict_embed(soal: dict, result: dict, username: str) -> discord.Embed:
    """Buat embed hasil submission."""
    verdict = result["verdict"]

    # Warna & emoji per verdict
    VERDICT_STYLE = {
        "Accepted":            (config.COLOR_SUCCESS, "✅"),
        "Wrong Answer":        (config.COLOR_ERROR,   "❌"),
        "Time Limit Exceeded": (config.COLOR_WARNING, "⏰"),
        "Runtime Error":       (config.COLOR_ERROR,   "💥"),
        "Forbidden Code":      (config.COLOR_ERROR,   "🚫"),
    }
    color, emoji = VERDICT_STYLE.get(verdict, (config.COLOR_DARK, "❓"))

    embed = discord.Embed(
        title=f"{emoji} {verdict}",
        color=color,
    )
    embed.set_author(name=f"Submission oleh {username}")
    embed.add_field(
        name="Soal",
        value=f"**#{soal['id']} · {soal['judul']}**",
        inline=False,
    )
    embed.add_field(
        name="Test Case",
        value=f"`{result['passed']}/{result['total']}` lulus",
        inline=True,
    )

    if verdict == "Accepted":
        embed.add_field(
            name="🏆 Poin",
            value="+10 poin" if True else "Sudah pernah solve",
            inline=True,
        )
        embed.description = "Mantap! Semua test case berhasil! 🎉"

    elif verdict == "Wrong Answer":
        embed.add_field(name="Gagal di Test Case", value=f"#{result['failed_tc']}", inline=True)
        embed.add_field(
            name="📥 Input",
            value=f"```\n{result['failed_input'][:200]}\n```",
            inline=False,
        )
        embed.add_field(
            name="📤 Output Kamu",
            value=f"```\n{result['got'] or '(kosong)'}\n```",
            inline=True,
        )
        embed.add_field(
            name="✅ Yang Diharapkan",
            value=f"```\n{result['expected']}\n```",
            inline=True,
        )

    elif verdict == "Time Limit Exceeded":
        embed.description = (
            f"Kode kamu melebihi batas waktu **{config.SANDBOX_TIMEOUT} detik** "
            f"pada test case #{result['failed_tc']}.\n"
            "Coba optimalkan algoritmamu! 🚀"
        )

    elif verdict == "Runtime Error":
        err = result.get("error_msg", "")[:400]
        embed.add_field(name="💬 Pesan Error", value=f"```\n{err}\n```", inline=False)

    elif verdict == "Forbidden Code":
        embed.description = result.get("error_msg", "Kode mengandung operasi yang dilarang.")

    embed.set_footer(text="KodeKuy Bot 🐍 | Python Coding Challenge")
    return embed


# ─────────────────────────────────────────────
# Modal: form input kode
# ─────────────────────────────────────────────
class SubmitModal(discord.ui.Modal, title="Submit Kode Python"):
    kode = discord.ui.TextInput(
        label="Kode Python kamu",
        style=discord.TextStyle.paragraph,
        placeholder="# Tulis kode Python kamu di sini...\nn = int(input())\n...",
        required=True,
        max_length=config.MAX_CODE_LENGTH,
    )

    def __init__(self, soal: dict):
        super().__init__()
        self.soal = soal

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        user = interaction.user
        await ensure_user(user.id, user.display_name)

        # Judge kode
        result = await judge(self.kode.value, self.soal["test_cases"])

        # Catat submission ke DB
        await record_submission(user.id, self.soal["id"], result["verdict"])

        embed = get_verdict_embed(self.soal, result, user.display_name)

        # Kirim hasil — ephemeral agar hanya submitter yang lihat
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Jika AC, umumkan ke channel
        if result["verdict"] == "Accepted" and interaction.channel:
            emoji_diff = config.EMOJI_DIFFICULTY.get(self.soal["difficulty"], "⬜")
            announce = discord.Embed(
                title="🏆 Accepted!",
                description=(
                    f"**{user.display_name}** berhasil menyelesaikan soal "
                    f"**#{self.soal['id']} · {self.soal['judul']}** "
                    f"{emoji_diff} {self.soal['difficulty']}! +10 poin 🎉"
                ),
                color=config.COLOR_SUCCESS,
            )
            try:
                await interaction.channel.send(embed=announce)
            except discord.Forbidden:
                pass


# ─────────────────────────────────────────────
# View: tombol-tombol di bawah embed soal
# ─────────────────────────────────────────────
class SoalView(discord.ui.View):
    def __init__(self, soal: dict, solved_ids: set):
        super().__init__(timeout=300)  # View aktif 5 menit
        self.soal = soal
        self.solved_ids = solved_ids

    @discord.ui.button(label="🚀 Submit Kode", style=discord.ButtonStyle.primary)
    async def submit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SubmitModal(soal=self.soal)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📋 Lihat Test Case", style=discord.ButtonStyle.secondary)
    async def testcase_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        soal = self.soal
        # Tampilkan 2 test case pertama saja (sisanya tersembunyi)
        tc_preview = soal["test_cases"][:2]
        lines = []
        for i, tc in enumerate(tc_preview, 1):
            lines.append(
                f"**Test Case #{i}**\n"
                f"Input:\n```\n{tc['input']}\n```"
                f"Output:\n```\n{tc['output']}\n```"
            )
        hidden = len(soal["test_cases"]) - len(tc_preview)
        footer = f"\n*...dan {hidden} test case tersembunyi lainnya.*" if hidden > 0 else ""

        embed = discord.Embed(
            title=f"📋 Contoh Test Case — #{soal['id']} {soal['judul']}",
            description="\n".join(lines) + footer,
            color=config.COLOR_DARK,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🎲 Soal Lain", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ambil soal acak lain (preferensi yang belum solved)."""
        user = interaction.user
        solved = await get_solved_ids(user.id)

        new_soal = pick_random_soal(
            exclude_ids=solved | {self.soal["id"]},
            kategori=None,
        )
        if not new_soal:
            new_soal = pick_random_soal(exclude_ids={self.soal["id"]}, kategori=None)

        if not new_soal:
            await interaction.response.send_message(
                "Tidak ada soal lain yang tersedia!", ephemeral=True
            )
            return

        embed = get_soal_embed(new_soal)
        new_view = SoalView(soal=new_soal, solved_ids=solved)

        # Cek apakah sudah solved
        if new_soal["id"] in solved:
            embed.set_footer(text="✅ Kamu sudah pernah menyelesaikan soal ini! | KodeKuy 🐍")

        await interaction.response.edit_message(embed=embed, view=new_view)

    async def on_timeout(self):
        """Disable semua tombol saat view timeout."""
        for item in self.children:
            item.disabled = True


# ─────────────────────────────────────────────
# Helper: pilih soal acak
# ─────────────────────────────────────────────
def pick_random_soal(exclude_ids: set = None, kategori: str = None) -> dict | None:
    """
    Pilih soal secara acak.
    - exclude_ids : set soal_id yang dilewati (sudah solved / sudah tampil)
    - kategori    : filter kategori, None = semua kategori
    """
    pool = ALL_SOAL.copy()
    if kategori:
        pool = [s for s in pool if s["kategori"] == kategori]
    if exclude_ids:
        pool = [s for s in pool if s["id"] not in exclude_ids]
    if not pool:
        return None
    return random.choice(pool)


# ─────────────────────────────────────────────
# Cog
# ─────────────────────────────────────────────
class SoalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /soal ─────────────────────────────────
    @app_commands.command(name="soal", description="Dapatkan soal coding Python acak dari Pak Dengklek!")
    @app_commands.describe(kategori="Pilih kategori soal (opsional, default: acak)")
    @app_commands.choices(kategori=[
        app_commands.Choice(name="🔢 Matematika", value="Matematika"),
        app_commands.Choice(name="🔤 String",     value="String"),
        app_commands.Choice(name="📋 Array",      value="Array"),
        app_commands.Choice(name="🧠 Logika",     value="Logika"),
        app_commands.Choice(name="🔃 Sorting",    value="Sorting"),
    ])
    async def soal_command(
        self,
        interaction: discord.Interaction,
        kategori: str = None,
    ):
        await interaction.response.defer(thinking=True)

        user = interaction.user
        await ensure_user(user.id, user.display_name)
        solved = await get_solved_ids(user.id)

        # Prioritaskan soal yang belum pernah di-solve
        soal = pick_random_soal(exclude_ids=solved, kategori=kategori)

        # Jika semua sudah solved, boleh ulangi
        if not soal:
            soal = pick_random_soal(exclude_ids=None, kategori=kategori)

        if not soal:
            await interaction.followup.send(
                f"Tidak ada soal untuk kategori **{kategori}**.", ephemeral=True
            )
            return

        embed  = get_soal_embed(soal)
        view   = SoalView(soal=soal, solved_ids=solved)

        # Beri tanda jika sudah pernah solved
        if soal["id"] in solved:
            embed.set_footer(
                text="✅ Kamu sudah pernah solve soal ini! Coba lagi untuk latihan. | KodeKuy 🐍"
            )

        await interaction.followup.send(embed=embed, view=view)

    # ── /profil ───────────────────────────────
    @app_commands.command(name="profil", description="Lihat statistik coding kamu sendiri.")
    async def profil_command(self, interaction: discord.Interaction):
        from utils.db import get_user_stats
        await interaction.response.defer(thinking=True, ephemeral=True)

        user = interaction.user
        await ensure_user(user.id, user.display_name)
        stats = await get_user_stats(user.id)
        solved_ids = await get_solved_ids(user.id)

        acc = 0
        if stats["total_submissions"] > 0:
            acc = round(stats["total_solved"] / stats["total_submissions"] * 100, 1)

        # Hitung per kategori
        solved_per_kat = {}
        total_per_kat  = {}
        for kat in KATEGORI_LIST:
            kat_soal = [s for s in ALL_SOAL if s["kategori"] == kat]
            total_per_kat[kat]  = len(kat_soal)
            solved_per_kat[kat] = sum(1 for s in kat_soal if s["id"] in solved_ids)

        embed = discord.Embed(
            title=f"📊 Profil — {user.display_name}",
            color=config.COLOR_INFO,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="🏆 Poin",        value=f"**{stats['points']}**",            inline=True)
        embed.add_field(name="✅ Soal Solved",  value=f"**{stats['total_solved']}** / {len(ALL_SOAL)}", inline=True)
        embed.add_field(name="📬 Total Submit", value=f"**{stats['total_submissions']}**",  inline=True)
        embed.add_field(name="🎯 Akurasi",      value=f"**{acc}%**",                        inline=True)

        # Breakdown per kategori
        kat_lines = []
        for kat in KATEGORI_LIST:
            emoji = config.EMOJI_KATEGORI[kat]
            s = solved_per_kat[kat]
            t = total_per_kat[kat]
            bar_filled = int((s / t) * 10) if t else 0
            bar = "█" * bar_filled + "░" * (10 - bar_filled)
            kat_lines.append(f"{emoji} **{kat}** `{bar}` {s}/{t}")

        embed.add_field(name="📁 Progress Kategori", value="\n".join(kat_lines), inline=False)
        embed.set_footer(text="KodeKuy Bot 🐍 | Python Coding Challenge")

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /submit_id ────────────────────────────
    @app_commands.command(name="submit", description="Submit kode untuk soal tertentu berdasarkan ID.")
    @app_commands.describe(soal_id="ID soal yang ingin kamu submit (lihat /soal untuk ID)")
    async def submit_command(self, interaction: discord.Interaction, soal_id: int):
        soal = next((s for s in ALL_SOAL if s["id"] == soal_id), None)
        if not soal:
            await interaction.response.send_message(
                f"❌ Soal dengan ID **{soal_id}** tidak ditemukan. Gunakan `/soal` untuk melihat soal.",
                ephemeral=True,
            )
            return
        modal = SubmitModal(soal=soal)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot):
    await bot.add_cog(SoalCog(bot))
