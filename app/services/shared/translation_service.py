"""
Translation Service — MyMemory API (Gratis, Tanpa API Key)

MyMemory adalah layanan terjemahan gratis yang menggunakan mesin Google/Microsoft
di balik layar. Tidak perlu akun atau API key untuk penggunaan dasar.

Limit:
    - Tanpa API key : 5.000 kata/hari
    - Dengan email  : 10.000 kata/hari (opsional, tambahkan MYMEMORY_EMAIL di .env)

Cara pakai:
    from app.services.translation_service import translate, translate_article

    translated = await translate("Hutan tropis", target_lang="en")

Dokumentasi: https://mymemory.translated.net/doc/spec.php
"""

import asyncio
import hashlib

import httpx

from app.core.config import settings

# In-memory cache: { "md5(lang::text)": "hasil terjemahan" }
# Reset setiap kali server restart. Efektif untuk konten artikel yang jarang berubah.
_translation_cache: dict[str, str] = {}

MYMEMORY_URL = "https://api.mymemory.translated.net/get"


def _cache_key(text: str, target_lang: str) -> str:
    """Generate cache key unik berdasarkan konten & bahasa target."""
    raw = f"{target_lang}::{text}"
    return hashlib.md5(raw.encode()).hexdigest()


async def translate(text: str, target_lang: str = "en", source_lang: str = "id") -> str:
    """
    Menerjemahkan teks ke bahasa target menggunakan MyMemory API (gratis).

    Args:
        text       : Teks yang akan diterjemahkan.
        target_lang: Kode bahasa target (e.g., "en", "id"). Default "en".
        source_lang: Kode bahasa sumber. Default "id" (Indonesia).

    Returns:
        Teks terjemahan, atau teks asli jika terjadi error (graceful fallback).
    """
    # Tidak perlu translate jika bahasa sama
    if target_lang == source_lang or target_lang == settings.DEFAULT_LANGUAGE:
        return text

    # Teks kosong tidak perlu diterjemahkan
    if not text or not text.strip():
        return text

    # Cek cache
    key = _cache_key(text, target_lang)
    if key in _translation_cache:
        return _translation_cache[key]

    # Bangun language pair, contoh: "id|en"
    lang_pair = f"{source_lang}|{target_lang}"

    # Siapkan params — tambahkan email jika dikonfigurasi (untuk limit 10K kata/hari)
    params: dict = {"q": text, "langpair": lang_pair}
    if hasattr(settings, "MYMEMORY_EMAIL") and settings.MYMEMORY_EMAIL:
        params["de"] = settings.MYMEMORY_EMAIL

    # Panggil MyMemory API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(MYMEMORY_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # Cek response status dari MyMemory
            if data.get("responseStatus") == 200:
                translated_text = data["responseData"]["translatedText"]
                # Simpan ke cache
                _translation_cache[key] = translated_text
                return translated_text
            else:
                # Quota habis atau error — kembalikan teks asli
                return text

    except Exception:
        # Network error, timeout, dll → kembalikan teks asli (tidak crash)
        return text


async def translate_article(article_dict: dict, target_lang: str = "en") -> dict:
    """
    Menerjemahkan field teks dari sebuah artikel secara async paralel.
    Field yang diterjemahkan: title, content, tags.

    Args:
        article_dict: Dict representasi artikel.
        target_lang : Kode bahasa target.

    Returns:
        Dict artikel dengan field teks sudah diterjemahkan.
    """
    result = dict(article_dict)

    if target_lang == settings.DEFAULT_LANGUAGE:
        return result

    # Kumpulkan task terjemahan — jalankan paralel agar lebih cepat
    fields_to_translate = ["title", "content"]
    if result.get("tags"):
        fields_to_translate.append("tags")

    tasks = [
        translate(result.get(field, ""), target_lang=target_lang)
        for field in fields_to_translate
    ]

    translated_values = await asyncio.gather(*tasks)
    for field, value in zip(fields_to_translate, translated_values):
        result[field] = value

    return result
