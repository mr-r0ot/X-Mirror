"""
algorithm.py  —  https://github.com/mr-r0ot/X-Mirror

منطق:
  ۱. جمع‌آوری همه پست‌ها
  ۲. امتیازدهی بر اساس:
       + وزن کاربر (از تاریخچه like/dislike)
       + فالوشده بودن (+2.0)
       + دیده‌نشده بودن (+1.5)
       + تعداد لایک (normalized)
       + رسانه (+0.3)
       + noise تصادفی (0–0.8) برای تنوع
  ۳. weighted-random shuffle
  ۴. صفحه‌بندی
"""

import random
from storage import (
    load_posts, load_inter, get_followed,
    get_weight, get_reaction, mark_seen
)

# ── helpers ────────────────────────────────────────────────

def _score(post: dict, ip: str, inter: dict, followed: set) -> float:
    u      = post.get("username", "").lower()
    weight = inter["weights"].get(u, 1.0)
    s      = weight

    if u in followed:
        s += 2.0

    if not post.get("seen", False):
        s += 1.5

    # لایک کاربر خودش
    tid = post.get("tweet_id", "")
    if tid and tid in inter["likes"]:
        s += 0.4

    # تعداد لایک‌های اجتماعی
    s += min((post.get("likes", 0) or 0) / 500.0, 1.0)

    if post.get("has_media"):
        s += 0.3

    # noise — تنوع
    s += random.uniform(0.0, 0.8)

    return max(s, 0.01)


def _weighted_shuffle(scored: list) -> list:
    """weighted sampling بدون جایگزینی"""
    pool   = list(scored)          # [(score, post), ...]
    result = []
    while pool:
        total = sum(s for s, _ in pool)
        r     = random.random() * total
        cum   = 0.0
        idx   = 0
        for i, (s, _) in enumerate(pool):
            cum += s
            if r <= cum:
                idx = i
                break
        result.append(pool[idx][1])
        pool.pop(idx)
    return result

# ══════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════

def get_home_feed(ip: str, page: int = 1, per_page: int = 20) -> list:
    """
    فید اصلی صفحه Home — weighted-random با اولویت unseen
    """
    posts    = [p for p in load_posts()
                if p.get("type","tweet") != "profile"]
    if not posts:
        return []

    inter    = load_inter(ip)
    followed = set(get_followed(ip))

    scored = [(_score(p, ip, inter, followed), p) for p in posts]
    feed   = _weighted_shuffle(scored)

    start = (page - 1) * per_page
    chunk = feed[start:start + per_page]

    # reaction وضعیت را به هر پست اضافه کن
    for p in chunk:
        tid         = p.get("tweet_id", "")
        p["reaction"] = get_reaction(ip, tid) if tid else "none"

    return chunk


def get_user_posts(ip: str, username: str,
                   page: int = 1, per_page: int = 20) -> list:
    """
    پست‌های یک کاربر خاص — ترتیب زمانی + reaction
    """
    posts = [p for p in load_posts()
             if p.get("username","").lower() == username.lower()
             and p.get("type","tweet") != "profile"]

    # unseen اول، بعد جدیدترین
    posts.sort(
        key=lambda x: (not x.get("seen", False), x.get("fetched_at","")),
        reverse=True
    )

    start = (page - 1) * per_page
    chunk = posts[start:start + per_page]

    inter = load_inter(ip)
    for p in chunk:
        tid         = p.get("tweet_id","")
        p["reaction"] = (
            "liked"    if tid in inter["likes"]    else
            "disliked" if tid in inter["dislikes"] else
            "none"
        )
    return chunk


def get_search_feed(ip: str, raw_posts: list) -> list:
    """
    نتایج جستجو را بر اساس وزن شخصی مرتب می‌کند
    """
    if not raw_posts:
        return []

    inter    = load_inter(ip)
    followed = set(get_followed(ip))

    def search_score(p):
        u  = p.get("username","").lower()
        w  = inter["weights"].get(u, 1.0)
        s  = w
        if u in followed:  s += 1.5
        s += min((p.get("likes",0) or 0) / 300.0, 1.0)
        if p.get("has_media"): s += 0.2
        return s

    sorted_posts = sorted(raw_posts, key=search_score, reverse=True)

    inter_d = inter
    for p in sorted_posts:
        tid         = p.get("tweet_id","")
        p["reaction"] = (
            "liked"    if tid in inter_d["likes"]    else
            "disliked" if tid in inter_d["dislikes"] else
            "none"
        )
    return sorted_posts
