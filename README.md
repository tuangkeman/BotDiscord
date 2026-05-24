# 🐍 KodeKuy — Discord Python Coding Challenge Bot

Bot Discord bergaya **Pak Dengklek** untuk latihan soal coding Python!
Submit kode, uji terhadap test case, dan bersaing di leaderboard.

---

## ✨ Fitur

| Fitur | Keterangan |
|---|---|
| 📖 **25 Soal** | 5 kategori: Matematika, String, Array, Logika, Sorting |
| 🎲 **Soal Acak** | Selalu dapat soal berbeda, prioritas yang belum dikerjakan |
| 🚀 **Submit Kode** | Input kode via popup modal langsung di Discord |
| ✅ **Auto Judge** | Kode dijalankan vs hidden test cases secara real-time |
| 🏆 **Leaderboard** | Papan skor antar pemain dengan poin system |
| 📊 **Profil** | Progress per kategori & statistik pribadi |
| 🔒 **Sandbox** | Kode dijalankan aman dengan timeout & pemblokiran modul berbahaya |

---

## 🚀 Cara Setup (Windows)

### 1. Buat Bot Discord

1. Buka [Discord Developer Portal](https://discord.com/developers/applications)
2. Klik **New Application** → beri nama (misal: KodeKuy)
3. Masuk ke tab **Bot** → klik **Add Bot**
4. Di bagian **Privileged Gateway Intents**, aktifkan:
   - ✅ `MESSAGE CONTENT INTENT`
5. Klik **Reset Token** → copy token kamu
6. Masuk ke tab **OAuth2 → URL Generator**:
   - Centang `bot` dan `applications.commands`
   - Di Bot Permissions centang: `Send Messages`, `Embed Links`, `Use Slash Commands`
   - Copy URL yang muncul → buka di browser → invite bot ke servermu

### 2. Setup Project

```bat
# Jalankan setup otomatis:
setup.bat
```

Atau manual:
```bat
pip install -r requirements.txt
copy .env.example .env
```

### 3. Isi Token

Buka file `.env` dengan Notepad dan isi:
```
DISCORD_TOKEN=token_bot_discord_kamu_di_sini
```

### 4. Jalankan Bot

```bat
run_bot.bat
```

Atau via Python langsung:
```bat
python bot.py
```

---

## 📋 Slash Commands

| Command | Keterangan |
|---|---|
| `/soal` | Dapatkan soal acak (bisa filter kategori) |
| `/soal [kategori]` | Soal dari kategori tertentu |
| `/submit [id]` | Submit kode untuk soal dengan ID tertentu |
| `/profil` | Lihat statistik & progress kamu |
| `/leaderboard` | Top 10 papan peringkat |
| `/info` | Informasi lengkap tentang bot |

---

## 🎮 Cara Bermain

1. Ketik `/soal` di channel Discord
2. Baca soal yang muncul (embed dengan cerita, format input/output, batasan)
3. Klik tombol **📋 Lihat Test Case** untuk melihat contoh
4. Klik tombol **🚀 Submit Kode** — form popup akan muncul
5. Tulis kode Python kamu di form tersebut
6. Klik Submit → tunggu hasil judge!
7. Klik **🎲 Soal Lain** untuk soal berbeda

---

## 🏅 Sistem Poin & Verdict

| Verdict | Artinya | Poin |
|---|---|---|
| ✅ Accepted | Semua test case lulus | +10 (pertama kali) |
| ❌ Wrong Answer | Output tidak sesuai | 0 |
| ⏰ TLE | Melebihi 5 detik | 0 |
| 💥 Runtime Error | Kode crash/error | 0 |
| 🚫 Forbidden Code | Pakai modul terlarang | 0 |

---

## 📁 Kategori Soal

| Kategori | Jumlah | Contoh Soal |
|---|---|---|
| 🔢 Matematika | 5 | Rata-rata, FPB, Prima, Faktorial, Fibonacci |
| 🔤 String | 5 | Balik string, Palindrome, Caesar Cipher, Anagram |
| 📋 Array | 5 | Max/Min, Rotasi, Hapus duplikat, Two Sum |
| 🧠 Logika | 5 | FizzBuzz, Konversi suhu, Bilangan sempurna |
| 🔃 Sorting | 5 | Urutkan nilai, Median, K-terbesar, Inversions |

---

## 💡 Tips Coding

- Gunakan `input()` untuk membaca input dari stdin
- Gunakan `print()` untuk output
- Modul `sys` tersedia (`sys.stdin.readline` boleh)
- Modul `os`, `subprocess`, `socket` dll **diblokir**
- Setiap test case dibatasi **5 detik**

---

## 📂 Struktur Project

```
Antigra/
├── bot.py              # Entry point
├── config.py           # Konfigurasi
├── .env                # Token (jangan di-share!)
├── requirements.txt
├── setup.bat           # Setup otomatis
├── run_bot.bat         # Jalankan bot
│
├── cogs/
│   ├── soal.py         # /soal, /submit, /profil + UI
│   └── leaderboard.py  # /leaderboard, /info
│
├── data/
│   ├── soal.json       # 25 soal + test cases
│   └── kodekuy.db      # Database SQLite (auto-dibuat)
│
└── utils/
    ├── db.py           # Database handler
    ├── sandbox.py      # Code executor
    └── judge.py        # Verdict system
```
