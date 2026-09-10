"""Explicit particle selection for generated Korean templates, before HTML escaping.

This does not rewrite prose or infer pronunciations of arbitrary foreign names.
Hangul syllables and Korean readings of terminal digits are supported.
"""
import re
import unicodedata


def josa(word: str, pair: str) -> str:
    pairs = {"은/는", "이/가", "을/를", "과/와", "으로/로", "이며/며", "이/"}
    if pair not in pairs:
        raise ValueError(f"Unsupported particle pair: {pair}")
    if not word:
        return word
    spoken = re.sub(r'[\s\]\)\}〉》」』”’"\']+$', '', unicodedata.normalize('NFC', word))
    if not spoken:
        return word
    last = spoken[-1]
    if last.isascii() and last.isdigit():
        last = "영일이삼사오육칠팔구"[int(last)]
    final = (ord(last) - ord('가')) % 28 if '가' <= last <= '힣' else 0
    consonant, vowel = pair.split('/')
    return word + (vowel if not final or (pair == '으로/로' and final == 8) else consonant)
