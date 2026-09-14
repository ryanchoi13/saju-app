"""Evidence gate for fashion boards labelled Trend.

Newness alone is not evidence. A candidate must repeat across independent core
editorial sources, show a Korean adoption signal, remain visibly distinct from
Daily, and pass owner review before it can be published.
"""

from collections import Counter


CORE_TREND_MEDIA = {
    "vogue_runway": {"label": "Vogue Runway", "gender": ("male", "female"), "role": "collection_origin"},
    "vogue_korea": {"label": "Vogue Korea", "gender": ("male", "female"), "role": "korean_editorial_translation"},
    "w_korea": {"label": "W Korea", "gender": ("female",), "role": "fashion_forward_styling"},
    "gq_korea": {"label": "GQ Korea", "gender": ("male",), "role": "menswear_styling"},
}

KOREAN_ADOPTION_SOURCES = {
    "musinsa": "search_sales_like_review",
    "29cm": "editorial_sales",
    "queenit": "forty_plus_search_sales",
}

VISUAL_AXES = {"silhouette", "material", "color_pattern", "shoe_styling"}


def evaluate_trend_candidate(gender, editorial_observations, adoption_sources,
                             visual_axes, owner_approved=False,
                             combination_supported=False):
    """Return a transparent Trend decision without treating newness as proof.

    ``editorial_observations`` maps a media id to repeated seasonal signal ids.
    The same signal must appear in two applicable core media.
    """
    if gender not in {"male", "female"}:
        raise ValueError("unknown gender")

    applicable = {
        source: tuple(dict.fromkeys(signals))
        for source, signals in editorial_observations.items()
        if source in CORE_TREND_MEDIA and gender in CORE_TREND_MEDIA[source]["gender"]
    }
    signal_counts = Counter(signal for signals in applicable.values() for signal in signals)
    repeated_signals = tuple(sorted(signal for signal, count in signal_counts.items() if count >= 2))
    verified_adoption = tuple(sorted(set(adoption_sources) & KOREAN_ADOPTION_SOURCES.keys()))
    verified_axes = tuple(sorted(set(visual_axes) & VISUAL_AXES))
    evidence_ready = (
        bool(repeated_signals)
        and bool(verified_adoption)
        and len(verified_axes) >= 2
        and bool(combination_supported)
    )

    return {
        "evidence_ready": evidence_ready,
        "publishable": evidence_ready and bool(owner_approved),
        "status": (
            "owner_approved" if evidence_ready and owner_approved
            else "owner_review_pending" if evidence_ready
            else "insufficient_evidence"
        ),
        "editorial_sources": tuple(sorted(applicable)),
        "repeated_signals": repeated_signals,
        "adoption_sources": verified_adoption,
        "visual_axes": verified_axes,
        "combination_supported": bool(combination_supported),
        "new_product_alone_qualifies": False,
    }
