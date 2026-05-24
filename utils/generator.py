"""
utils/generator.py — AI Soal Generator menggunakan Google Gemini API
Generate soal coding Python bergaya Pak Dengklek secara otomatis.
"""
import google.generativeai as genai
import json
import re
import random
import asyncio
import os

import config
from utils.sandbox import run_code


# ─────────────────────────────────────────────
# Konfigurasi Gemini
# ─────────────────────────────────────────────
_gemini_configured = False

def _ensure_configured():
    global _gemini_configured
    if not _gemini_configured:
        api_key = config.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY belum diisi di file .env!")
        genai.configure(api_key=api_key)
        _gemini_configured = True


KATEGORI_LIST  = list(config.EMOJI_KATEGORI.keys())
DIFFICULTY_LIST = ["Easy", "Medium", "Hard"]

PROMPT_TEMPLATE = """\
Buat soal coding Python bergaya "Pak Dengklek" — soal cerita kompetitif pemrograman Indonesia.

Kategori  : {kategori}
Kesulitan : {difficulty}

Keluarkan HANYA satu blok JSON valid tanpa markdown, tanpa penjelasan, tanpa komentar.
Format JSON harus PERSIS seperti berikut:

{{
  "judul": "Judul soal singkat dan menarik",
  "kategori": "{kategori}",
  "difficulty": "{difficulty}",
  "cerita": "2-3 kalimat cerita Pak Dengklek yang menarik, relevan dengan soal, dalam bahasa Indonesia",
  "input_format": "Penjelasan format input (markdown bold untuk variabel)",
  "output_format": "Penjelasan format output",
  "contoh_input": "contoh input (gunakan \\n untuk baris baru)",
  "contoh_output": "contoh output (gunakan \\n untuk baris baru)",
  "batasan": "Batasan nilai, misal: 1 ≤ N ≤ 1000",
  "test_cases": [
    {{"input": "...", "output": "..."}},
    {{"input": "...", "output": "..."}},
    {{"input": "...", "output": "..."}},
    {{"input": "...", "output": "..."}}
  ],
  "solusi": "kode Python lengkap yang benar untuk menyelesaikan soal (gunakan \\n untuk baris baru)"
}}

Aturan WAJIB:
1. Semua teks dalam Bahasa Indonesia
2. Soal harus bisa diselesaikan dengan Python standar menggunakan input() dan print()
3. Semua test_cases HARUS BENAR dan konsisten dengan soal & solusi
4. Solusi harus menghasilkan output yang tepat untuk SEMUA test case
5. Soal HARUS BERBEDA dari judul-judul ini: {existing_titles}
6. Output JSON saja, tidak ada teks lain sama sekali
"""


# ─────────────────────────────────────────────
# Helper: ekstrak JSON dari response Gemini
# ─────────────────────────────────────────────
def _extract_json(text: str) -> dict:
    """Coba parse JSON dari response model, handle berbagai format."""
    # Hapus markdown code block jika ada
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    text = text.strip()

    # Coba parse langsung
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Coba ekstrak objek JSON pertama dengan regex
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError("Response bukan JSON valid.")


# ─────────────────────────────────────────────
# Verifikasi: jalankan solusi vs test cases
# ─────────────────────────────────────────────
async def _verify_solution(solusi: str, test_cases: list[dict]) -> tuple[bool, str]:
    """
    Jalankan solusi referensi terhadap semua test case.
    Returns (semua_lulus, pesan_error)
    """
    for i, tc in enumerate(test_cases, 1):
        result = await run_code(
            code=solusi,
            stdin_data=tc["input"],
            timeout=10.0,  # lebih lama untuk solusi referensi
        )

        if result["timed_out"]:
            return False, f"Solusi TLE pada test case #{i}"

        if result["returncode"] != 0:
            return False, f"Solusi error pada test case #{i}: {result['stderr'][:200]}"

        actual   = result["stdout"].strip()
        expected = tc["output"].strip()

        if actual != expected:
            return False, (
                f"Solusi WA pada test case #{i}\n"
                f"  Input   : {tc['input'][:100]}\n"
                f"  Got     : {actual[:100]}\n"
                f"  Expected: {expected[:100]}"
            )

    return True, ""


# ─────────────────────────────────────────────
# Main: generate satu soal baru
# ─────────────────────────────────────────────
async def generate_soal(
    kategori: str = None,
    difficulty: str = None,
    existing_titles: list[str] = None,
    max_retries: int = 3,
) -> dict | None:
    """
    Generate soal baru menggunakan Gemini AI.

    Returns dict soal (tanpa field 'solusi') jika berhasil, None jika gagal.
    """
    _ensure_configured()

    if not kategori:
        kategori = random.choice(KATEGORI_LIST)
    if not difficulty:
        difficulty = random.choice(DIFFICULTY_LIST)
    if existing_titles is None:
        existing_titles = []

    titles_str = ", ".join(f'"{t}"' for t in existing_titles[:20]) or "tidak ada"

    prompt = PROMPT_TEMPLATE.format(
        kategori=kategori,
        difficulty=difficulty,
        existing_titles=titles_str,
    )

    model = genai.GenerativeModel("gemini-2.0-flash")

    for attempt in range(1, max_retries + 1):
        try:
            # Jalankan Gemini di thread agar tidak block event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(prompt)
            )

            raw_text = response.text
            data = _extract_json(raw_text)

            # Validasi field wajib
            required = [
                "judul", "kategori", "difficulty", "cerita",
                "input_format", "output_format", "contoh_input",
                "contoh_output", "batasan", "test_cases", "solusi",
            ]
            missing = [k for k in required if k not in data]
            if missing:
                raise ValueError(f"Field tidak lengkap: {missing}")

            if not isinstance(data["test_cases"], list) or len(data["test_cases"]) < 2:
                raise ValueError("test_cases minimal 2 item")

            # Verifikasi solusi referensi
            ok, err_msg = await _verify_solution(data["solusi"], data["test_cases"])
            if not ok:
                raise ValueError(f"Verifikasi gagal: {err_msg}")

            # Soal valid — hapus solusi sebelum disimpan
            soal = {k: v for k, v in data.items() if k != "solusi"}
            soal["ai_generated"] = True
            return soal

        except Exception as e:
            if attempt < max_retries:
                await asyncio.sleep(2)
                continue
            else:
                print(f"[Generator] Gagal setelah {max_retries} percobaan: {e}")
                return None

    return None


# ─────────────────────────────────────────────
# Simpan soal baru ke soal.json
# ─────────────────────────────────────────────
def save_soal(soal: dict, soal_path: str = None) -> int:
    """
    Tambahkan soal baru ke soal.json, beri ID baru.
    Returns ID soal yang baru disimpan.
    """
    if soal_path is None:
        soal_path = config.SOAL_PATH

    with open(soal_path, encoding="utf-8") as f:
        all_soal = json.load(f)

    new_id = max((s["id"] for s in all_soal), default=0) + 1
    soal["id"] = new_id
    all_soal.append(soal)

    with open(soal_path, "w", encoding="utf-8") as f:
        json.dump(all_soal, f, ensure_ascii=False, indent=2)

    return new_id
