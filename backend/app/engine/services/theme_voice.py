"""테마운 문장 규칙 v2 (2026-11-22) — 풀이 맨 위 해시태그 셋.

프로젝트 문서 decisions-2026-11-22-reading-voice-scope: 해시태그는 궁합·평생운세·신년운세·테마운 맨 위에 3개.
새 문장을 짓지 않고 풀이가 이미 말한 것에서 뽑는다: 일간 그림 · 기질 제목(첫 소제목) · 첫 습관/함정 이름.
"""
from __future__ import annotations

import re
from html import escape, unescape

from app.engine.services.now_me_copy import DAY_MASTER_ROWS

_H3 = re.compile(r"<h3>([^<]+)</h3>")
_STRONG = re.compile(r"<strong>([^<]{2,24})</strong>")


def hashtags(content: str, core) -> list[str]:
    day = (getattr(core.natal_facts, "pillars", None) or {}).get("day")
    label = (DAY_MASTER_ROWS.get(getattr(day, "stem", None)) or {}).get("label")
    head = next((m for m in _H3.findall(content) if not re.search(r"\d", m)), None)   # 나이·연도가 든 소제목은 건너뛴다
    trap = next((m for m in _STRONG.findall(content) if not re.search(r"\d", m)), None)
    out = []
    for t in (label, head, trap):
        tag = "#" + re.sub(r"[^0-9A-Za-z가-힣]", "", unescape(t)) if t else None
        if tag and len(tag) > 1 and tag not in out:
            out.append(tag)
    return out


def with_hashtags(content: str, core) -> str:
    """풀이 맨 위(감싸는 div 바로 안)에 해시태그 줄을 넣는다. 뽑을 것이 없으면 그대로 돌려준다."""
    tags = hashtags(content, core)
    cut = content.find(">") + 1
    if not tags or cut <= 0:
        return content
    return content[:cut] + f'<p class="theme-tags">{escape(" ".join(tags))}</p>' + content[cut:]
