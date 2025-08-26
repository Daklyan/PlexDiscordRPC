import json
import os
import time

CACHE_DIR = "cache"
CACHE_DURATION = 3600  # 1 hour

def get_cache_path(key: str) -> str:
    """Get the cache file path for a given key."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{key}.json")

def is_cache_valid(cache_path: str) -> bool:
    """Check if the cache is still valid."""
    if not os.path.exists(cache_path):
        return False

    with open(cache_path, "r") as f:
        cache_data = json.load(f)

    return time.time() - cache_data["timestamp"] < CACHE_DURATION

def get_cached_data(key: str) -> dict | None:
    """Get cached data for a given key."""
    cache_path = get_cache_path(key)
    if not is_cache_valid(cache_path):
        return None

    with open(cache_path, "r") as f:
        return json.load(f)["data"]

def set_cached_data(key: str, data: dict) -> None:
    """Set cached data for a given key."""
    cache_path = get_cache_path(key)
    with open(cache_path, "w") as f:
        json.dump({"timestamp": time.time(), "data": data}, f)
