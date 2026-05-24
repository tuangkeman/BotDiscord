"""
utils/sandbox.py — Sandboxed Python code execution
Menjalankan kode Python yang dikirim user secara aman menggunakan subprocess.
"""
import asyncio
import sys
import os
import tempfile
import re
import config


def check_code_safety(code: str) -> tuple[bool, str]:
    """
    Cek apakah kode mengandung import modul berbahaya.
    Returns (is_safe, pesan_error)
    """
    for module in config.FORBIDDEN_MODULES:
        # Cek pola 'import modul' atau 'from modul'
        patterns = [
            rf"^\s*import\s+{re.escape(module)}\b",
            rf"^\s*from\s+{re.escape(module)}\b",
            rf"\bimport\s+{re.escape(module)}\b",
        ]
        for pattern in patterns:
            if re.search(pattern, code, re.MULTILINE):
                return False, f"Import modul `{module}` tidak diizinkan!"

    # Cek penggunaan __import__ dan exec/eval untuk yang berbahaya
    dangerous_calls = [
        r"__import__\s*\(",
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"open\s*\([^)]*['\"]w['\"]"  # open file for writing
    ]
    for pattern in dangerous_calls:
        if re.search(pattern, code):
            return False, "Penggunaan fungsi/ekspresi ini tidak diizinkan!"

    return True, ""


async def run_code(code: str, stdin_data: str, timeout: float = None) -> dict:
    """
    Jalankan kode Python di subprocess terpisah.

    Returns dict:
        stdout     : str — output dari kode
        stderr     : str — pesan error (jika ada)
        returncode : int — exit code proses
        timed_out  : bool — True jika melebihi batas waktu
    """
    if timeout is None:
        timeout = config.SANDBOX_TIMEOUT

    # Tulis kode ke file sementara (menghindari masalah escape di -c)
    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_file = f.name

        process = await asyncio.create_subprocess_exec(
            sys.executable, tmp_file,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input=stdin_data.encode("utf-8")),
                timeout=timeout,
            )
            return {
                "stdout":     stdout_bytes.decode("utf-8", errors="replace").strip(),
                "stderr":     stderr_bytes.decode("utf-8", errors="replace").strip(),
                "returncode": process.returncode,
                "timed_out":  False,
            }
        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass
            return {
                "stdout":     "",
                "stderr":     "Time Limit Exceeded",
                "returncode": -1,
                "timed_out":  True,
            }

    finally:
        if tmp_file and os.path.exists(tmp_file):
            try:
                os.unlink(tmp_file)
            except Exception:
                pass
