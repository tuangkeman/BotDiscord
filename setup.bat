@echo off
echo ============================================
echo   KodeKuy Bot - Setup Otomatis
echo ============================================
echo.

:: Cek Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan! Install Python 3.10+ dulu.
    pause
    exit /b 1
)
echo [OK] Python ditemukan.

:: Install dependencies
echo.
echo [INFO] Menginstall dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Gagal install dependencies!
    pause
    exit /b 1
)
echo [OK] Dependencies berhasil diinstall.

:: Cek .env
if not exist .env (
    echo.
    echo [INFO] File .env belum ada, membuat dari .env.example...
    copy .env.example .env
    echo.
    echo ============================================
    echo  PENTING: Edit file .env dan isi token bot!
    echo  Buka file .env lalu ganti:
    echo    DISCORD_TOKEN=your_discord_bot_token_here
    echo  dengan token bot Discord kamu.
    echo ============================================
    echo.
    pause
) else (
    echo [OK] File .env ditemukan.
)

echo.
echo [OK] Setup selesai! Jalankan bot dengan: run_bot.bat
pause
