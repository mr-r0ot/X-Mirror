"""
storage.py  —  https://github.com/mr-r0ot/X-Mirror
فایل‌ها:  data/posts.json  |  data/profiles.json
          data/followers.json  |  data/interactions.json
"""

import json, os, threading
from datetime import datetime

BASE        = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE, "data")
POSTS_F     = os.path.join(DATA_DIR, "posts.json")
PROFILES_F  = os.path.join(DATA_DIR, "profiles.json")
FOLLOWERS_F = os.path.join(DATA_DIR, "followers.json")
INTER_F     = os.path.join(DATA_DIR, "interactions.json")

_lock = threading.Lock()

# ── helpers ────────────────────────────────────────────────

def _mkdir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _read(path, default):
    _mkdir()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def _write(path, data):
    _mkdir()
    with _lock:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

# ══════════════════════════════════════════════════════════
#  POSTS
# ══════════════════════════════════════════════════════════

def load_posts() -> list:
    return _read(POSTS_F, [])

def save_posts(posts: list):
    _write(POSTS_F, posts)

def upsert_posts(new_posts: list) -> int:
    """اضافه کردن پست‌های جدید بدون تکرار — برمی‌گرداند تعداد اضافه‌شده"""
    existing = load_posts()
    exist_keys = {p.get("tweet_id") or p.get("url") for p in existing}
    added = 0
    now   = datetime.now().isoformat()
    for p in new_posts:
        key = p.get("tweet_id") or p.get("url")
        if key and key not in exist_keys:
            p.setdefault("seen",       False)
            p.setdefault("fetched_at", now)
            existing.append(p)
            exist_keys.add(key)
            added += 1
    # جدیدترین اول
    existing.sort(key=lambda x: x.get("fetched_at",""), reverse=True)
    save_posts(existing)
    return added

def get_posts_by_user(username: str) -> list:
    u = username.lower()
    return [p for p in load_posts() if p.get("username","").lower() == u
            and p.get("type","tweet") != "profile"]

def mark_seen(tweet_id: str):
    posts = load_posts()
    changed = False
    for p in posts:
        if (p.get("tweet_id") == tweet_id or
                p.get("url","").endswith(tweet_id)):
            if not p.get("seen"):
                p["seen"] = True
                changed   = True
    if changed:
        save_posts(posts)

def get_all_usernames() -> list:
    posts = load_posts()
    seen  = set()
    out   = []
    for p in posts:
        u = p.get("username","").lower()
        if u and u not in seen:
            seen.add(u); out.append(u)
    return out

# ══════════════════════════════════════════════════════════
#  PROFILES
# ══════════════════════════════════════════════════════════

def load_profiles() -> dict:
    return _read(PROFILES_F, {})

def save_profile(username: str, data: dict):
    profiles = load_profiles()
    profiles[username.lower()] = {
        **data,
        "updated_at": datetime.now().isoformat()
    }
    _write(PROFILES_F, profiles)

def get_profile(username: str) -> dict | None:
    return load_profiles().get(username.lower())

# ══════════════════════════════════════════════════════════
#  FOLLOWERS  (جدا برای هر کاربر شبکه بر اساس IP)
# ══════════════════════════════════════════════════════════

def _fl_data() -> dict:
    return _read(FOLLOWERS_F, {})

def load_followers(ip: str) -> dict:
    return _fl_data().get(ip, {})

def _save_followers(ip: str, d: dict):
    all_data      = _fl_data()
    all_data[ip]  = d
    _write(FOLLOWERS_F, all_data)

def follow(ip: str, username: str) -> bool:
    d = load_followers(ip)
    k = username.lower()
    if k not in d:
        d[k] = {"followed_at": datetime.now().isoformat()}
        _save_followers(ip, d)
        return True
    return False

def unfollow(ip: str, username: str) -> bool:
    d = load_followers(ip)
    k = username.lower()
    if k in d:
        del d[k]
        _save_followers(ip, d)
        return True
    return False

def is_following(ip: str, username: str) -> bool:
    return username.lower() in load_followers(ip)

def get_followed(ip: str) -> list:
    return list(load_followers(ip).keys())

# ══════════════════════════════════════════════════════════
#  INTERACTIONS  — like / dislike / weight
#  هر IP داده‌ی مستقل دارد
# ══════════════════════════════════════════════════════════

def _inter_data() -> dict:
    return _read(INTER_F, {})

def load_inter(ip: str) -> dict:
    base = {"likes": {}, "dislikes": {}, "weights": {}}
    return _inter_data().get(ip, base)

def _save_inter(ip: str, d: dict):
    all_data     = _inter_data()
    all_data[ip] = d
    _write(INTER_F, all_data)

def _adj_weight(d: dict, username: str, delta: float):
    k       = username.lower()
    current = d["weights"].get(k, 1.0)
    d["weights"][k] = round(max(0.1, min(5.0, current + delta)), 3)

def like_post(ip: str, tweet_id: str, username: str) -> dict:
    d  = load_inter(ip)
    u  = username.lower()
    # اگه قبلاً dislike داشت، برش دار
    if tweet_id in d["dislikes"]:
        del d["dislikes"][tweet_id]
        _adj_weight(d, u, +0.3)
    if tweet_id not in d["likes"]:
        d["likes"][tweet_id] = u
        _adj_weight(d, u, +0.5)
        action = "liked"
    else:
        del d["likes"][tweet_id]
        _adj_weight(d, u, -0.2)
        action = "unliked"
    _save_inter(ip, d)
    return {"action": action,
            "weight": d["weights"].get(u, 1.0)}

def dislike_post(ip: str, tweet_id: str, username: str) -> dict:
    d  = load_inter(ip)
    u  = username.lower()
    if tweet_id in d["likes"]:
        del d["likes"][tweet_id]
        _adj_weight(d, u, -0.3)
    if tweet_id not in d["dislikes"]:
        d["dislikes"][tweet_id] = u
        _adj_weight(d, u, -0.5)
        action = "disliked"
    else:
        del d["dislikes"][tweet_id]
        _adj_weight(d, u, +0.1)
        action = "undisliked"
    _save_inter(ip, d)
    return {"action": action,
            "weight": d["weights"].get(u, 1.0)}

def get_reaction(ip: str, tweet_id: str) -> str:
    d = load_inter(ip)
    if tweet_id in d["likes"]:    return "liked"
    if tweet_id in d["dislikes"]: return "disliked"
    return "none"

def get_weight(ip: str, username: str) -> float:
    return load_inter(ip)["weights"].get(username.lower(), 1.0)
