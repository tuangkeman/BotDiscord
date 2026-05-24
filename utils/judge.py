"""
utils/judge.py — Verdict system
Membandingkan output kode user dengan expected output dari test cases.
"""
from utils.sandbox import run_code, check_code_safety
import config


def normalize_output(text: str) -> list[str]:
    """Normalisasi output: strip tiap baris, hapus baris kosong di akhir."""
    lines = text.strip().split("\n")
    return [line.strip() for line in lines]


async def judge(code: str, test_cases: list[dict]) -> dict:
    """
    Jalankan kode terhadap semua test case dan kembalikan hasil judge.

    Returns dict:
        verdict      : str  — "Accepted" / "Wrong Answer" / "Time Limit Exceeded" /
                              "Runtime Error" / "Forbidden Code"
        passed       : int  — jumlah test case yang lulus
        total        : int  — total test case
        failed_tc    : int | None — nomor test case yang gagal (1-based)
        failed_input : str | None — input test case yang gagal
        got          : str | None — output aktual yang didapat
        expected     : str | None — output yang diharapkan
        error_msg    : str | None — pesan error jika Runtime Error
    """
    total = len(test_cases)

    # --- Cek keamanan kode ---
    is_safe, safety_msg = check_code_safety(code)
    if not is_safe:
        return {
            "verdict":      "Forbidden Code",
            "passed":       0,
            "total":        total,
            "failed_tc":    None,
            "failed_input": None,
            "got":          None,
            "expected":     None,
            "error_msg":    safety_msg,
        }

    # --- Jalankan tiap test case ---
    for i, tc in enumerate(test_cases, start=1):
        result = await run_code(
            code=code,
            stdin_data=tc["input"],
            timeout=config.SANDBOX_TIMEOUT,
        )

        if result["timed_out"]:
            return {
                "verdict":      "Time Limit Exceeded",
                "passed":       i - 1,
                "total":        total,
                "failed_tc":    i,
                "failed_input": tc["input"],
                "got":          None,
                "expected":     tc["output"],
                "error_msg":    f"Melewati batas waktu {config.SANDBOX_TIMEOUT} detik.",
            }

        if result["returncode"] != 0:
            # Potong stderr agar tidak terlalu panjang
            err = result["stderr"][:500] if result["stderr"] else "Unknown error"
            return {
                "verdict":      "Runtime Error",
                "passed":       i - 1,
                "total":        total,
                "failed_tc":    i,
                "failed_input": tc["input"],
                "got":          None,
                "expected":     tc["output"],
                "error_msg":    err,
            }

        actual   = normalize_output(result["stdout"])
        expected = normalize_output(tc["output"])

        if actual != expected:
            got_str = "\n".join(actual)
            return {
                "verdict":      "Wrong Answer",
                "passed":       i - 1,
                "total":        total,
                "failed_tc":    i,
                "failed_input": tc["input"],
                "got":          got_str[:300],
                "expected":     tc["output"][:300],
                "error_msg":    None,
            }

    # Semua test case lulus
    return {
        "verdict":      "Accepted",
        "passed":       total,
        "total":        total,
        "failed_tc":    None,
        "failed_input": None,
        "got":          None,
        "expected":     None,
        "error_msg":    None,
    }
