"""Helper murni — tidak boleh import dari layer lain selain stdlib."""
import re


def is_strong_password(password: str) -> bool:
    """Minimal 8 char, ada huruf & angka."""
    return len(password) >= 8 and bool(re.search(r"[A-Za-z]", password)) and bool(re.search(r"\d", password))


def normalize_phone(number: str, country_code: str = "62") -> str:
    """Bersihkan nomor jadi format internasional tanpa '+': 08xx -> 628xx."""
    n = re.sub(r"[^0-9]", "", number or "")
    if n.startswith("0"):
        n = country_code + n[1:]
    elif n.startswith("620"):
        n = country_code + n[3:]
    return n
