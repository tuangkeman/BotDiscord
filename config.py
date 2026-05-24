import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Sandbox settings
SANDBOX_TIMEOUT = 5.0   # detik per test case
MAX_CODE_LENGTH = 3900  # batas karakter kode (Discord modal max 4000)

# Database
DB_PATH = "data/kodekuy.db"

# Soal
SOAL_PATH = "data/soal.json"

# Warna embed
COLOR_INFO    = 0x5865F2  # Biru Discord
COLOR_SUCCESS = 0x57F287  # Hijau
COLOR_ERROR   = 0xED4245  # Merah
COLOR_WARNING = 0xFEE75C  # Kuning
COLOR_DARK    = 0x2B2D31  # Abu gelap

# Emoji kategori
EMOJI_KATEGORI = {
    "Matematika": "🔢",
    "String":     "🔤",
    "Array":      "📋",
    "Logika":     "🧠",
    "Sorting":    "🔃",
}

# Emoji difficulty
EMOJI_DIFFICULTY = {
    "Easy":   "🟢",
    "Medium": "🟡",
    "Hard":   "🔴",
}

# Modul yang dilarang di sandbox
FORBIDDEN_MODULES = [
    "os", "subprocess", "socket", "requests", "urllib",
    "shutil", "pathlib", "ctypes", "multiprocessing",
    "pickle", "shelve", "importlib", "pty", "atexit",
]
