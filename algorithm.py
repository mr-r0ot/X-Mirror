"""
algorithm.py  —  https://github.com/mr-r0ot/X-Mirror
"""

import random
from storage import load_posts, load_inter, get_followed, get_reaction, mark_seen

def _score(post: dict, inter: dict, followed: set) -> float:
    u      = post.get("username","").lower()
    weight = inter["weights"].get(u, 1.0)
    s      = weight

    if u in followed:                        s += 2.0
    if not post.get("seen", False):          s += 1.5
    tid = post.get("tweet_id","")
    if tid and tid in inter["likes"]:        s += 0.4

    s += min((post.get("likes",0) or 0) / 500.0, 1.0)
    if post.get("has_media"):                s += 0.3

    s += random.uniform(0.0, 0.5)
    return max(s, 0.01)

def _weighted_shuffle(scored: list) -> list:
    pool   = list(scored)
    result = []
    while pool:
        total = sum(s for s, _ in pool)
        r     = random.random() * total
        cum   = 0.0; idx = 0
        for i, (s, _) in enumerate(pool):
            cum += s
            if r <= cum: idx = i; break
        result.append(pool[idx][1])
        pool.pop(idx)
    return result

def _attach_reactions(posts: list, inter: dict) -> list:
    for p in posts:
        tid = p.get("tweet_id","")
        p["reaction"] = (
            "liked"    if tid in inter["likes"]    else
            "disliked" if tid in inter["dislikes"] else "none"
        )
    return posts


def get_home_feed(ip: str, page: int = 1, per_page: int = 20) -> list:
    posts    = [p for p in load_posts() if p.get("type","tweet") != "profile"]
    if not posts: return []
    inter    = load_inter(ip)
    followed = set(get_followed(ip))
    scored   = [(_score(p, inter, followed), p) for p in posts]
    feed     = _weighted_shuffle(scored)
    start    = (page-1)*per_page
    chunk    = feed[start:start+per_page]
    return _attach_reactions(chunk, inter)


def get_user_posts(ip: str, username: str, page: int = 1, per_page: int = 20) -> list:
    posts = [p for p in load_posts()
             if p.get("username","").lower() == username.lower()
             and p.get("type","tweet") != "profile"]

    # مرتب‌سازی: date_ts جدیدتر اول، سپس unseen، سپس fetched_at
    def sort_key(p):
        ts = p.get("date_ts", 0) or 0
        return (ts, 0 if p.get("seen") else 1, p.get("fetched_at",""))

    posts.sort(key=sort_key, reverse=True)

    start = (page-1)*per_page
    chunk = posts[start:start+per_page]
    inter = load_inter(ip)
    return _attach_reactions(chunk, inter)


def get_search_feed(ip: str, raw_posts: list) -> list:
    if not raw_posts: return []
    inter    = load_inter(ip)
    followed = set(get_followed(ip))

    def score(p):
        u  = p.get("username","").lower()
        w  = inter["weights"].get(u, 1.0)
        s  = w
        if u in followed:               s += 1.5
        s += min((p.get("likes",0) or 0) / 300.0, 1.0)
        if p.get("has_media"):          s += 0.2
        # جدیدتر = امتیاز بیشتر
        ts = p.get("date_ts", 0) or 0
        if ts > 0:
            import time
            age_hours = (time.time() - ts) / 3600
            s += max(0, 2.0 - age_hours/48)  # پست‌های زیر 48 ساعت بونوس
        return s

    sorted_posts = sorted(raw_posts, key=score, reverse=True)
    return _attach_reactions(sorted_posts, inter)
