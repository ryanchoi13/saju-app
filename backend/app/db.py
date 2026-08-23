from functools import lru_cache

from app.config import SUPABASE_SERVICE_KEY, SUPABASE_URL


@lru_cache
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    from supabase import create_client

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def save_profile(payload: dict) -> dict | None:
    client = get_supabase()
    if client is None:
        return None
    result = client.table("profiles").insert(payload).execute()
    return result.data[0] if result.data else None
