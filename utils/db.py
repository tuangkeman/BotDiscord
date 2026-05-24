"""
utils/db.py — SQLite database handler menggunakan aiosqlite
Menyimpan data user, submission, dan soal yang sudah diselesaikan.
"""
import aiosqlite
import config


async def init_db():
    """Inisialisasi database dan buat tabel jika belum ada."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        # Tabel users
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id   INTEGER PRIMARY KEY,
                username  TEXT    NOT NULL,
                total_solved      INTEGER DEFAULT 0,
                total_submissions INTEGER DEFAULT 0,
                points            INTEGER DEFAULT 0
            )
        """)
        # Tabel solved (soal yang sudah di-AC)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS solved (
                user_id  INTEGER,
                soal_id  INTEGER,
                solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, soal_id)
            )
        """)
        # Tabel submissions (riwayat semua submission)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                soal_id     INTEGER,
                verdict     TEXT,
                language    TEXT DEFAULT 'Python',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def ensure_user(user_id: int, username: str):
    """Pastikan user ada di database, insert jika belum."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username)
            VALUES (?, ?)
        """, (user_id, username))
        # Update username jika berubah
        await db.execute("""
            UPDATE users SET username = ? WHERE user_id = ?
        """, (username, user_id))
        await db.commit()


async def record_submission(user_id: int, soal_id: int, verdict: str):
    """Catat sebuah submission ke database."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        # Tambah ke tabel submissions
        await db.execute("""
            INSERT INTO submissions (user_id, soal_id, verdict)
            VALUES (?, ?, ?)
        """, (user_id, soal_id, verdict))
        # Tambah total_submissions
        await db.execute("""
            UPDATE users SET total_submissions = total_submissions + 1
            WHERE user_id = ?
        """, (user_id,))

        if verdict == "Accepted":
            # Cek apakah sudah pernah solve soal ini
            async with db.execute("""
                SELECT 1 FROM solved WHERE user_id = ? AND soal_id = ?
            """, (user_id, soal_id)) as cursor:
                already_solved = await cursor.fetchone()

            if not already_solved:
                # Tambah ke tabel solved
                await db.execute("""
                    INSERT INTO solved (user_id, soal_id) VALUES (?, ?)
                """, (user_id, soal_id))
                # Tambah poin dan total_solved
                await db.execute("""
                    UPDATE users SET total_solved = total_solved + 1,
                                    points = points + 10
                    WHERE user_id = ?
                """, (user_id,))

        await db.commit()


async def get_solved_ids(user_id: int) -> set:
    """Ambil set soal_id yang sudah di-solve oleh user."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("""
            SELECT soal_id FROM solved WHERE user_id = ?
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
    return {row[0] for row in rows}


async def get_leaderboard(limit: int = 10) -> list:
    """Ambil leaderboard top-N user."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("""
            SELECT username, total_solved, total_submissions, points
            FROM users
            ORDER BY points DESC, total_solved DESC, total_submissions ASC
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
    return rows


async def get_user_stats(user_id: int) -> dict | None:
    """Ambil statistik seorang user."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("""
            SELECT username, total_solved, total_submissions, points
            FROM users WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        return None
    return {
        "username":          row[0],
        "total_solved":      row[1],
        "total_submissions": row[2],
        "points":            row[3],
    }
