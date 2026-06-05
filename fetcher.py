"""
https://github.com/mr-r0ot/X-Mirror
fetcher.py  —  دریافت داده از search.bertina.ir
منبع: موتور جستجوی برتینا (اینترنت داخلی ایران)
"""

import re, base64, requests
from urllib.parse import quote_plus, urlparse, parse_qs
from bs4 import BeautifulSoup

BERTINA   = "https://search.bertina.ir"
SEARCH_EP = f"{BERTINA}/search"

HEADERS = {
    "User-Agent":                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
    "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language":           "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest":            "document",
    "Sec-Fetch-Mode":            "navigate",
    "Sec-Fetch-Site":            "none",
    "Sec-Fetch-User":            "?1",
}

# ── URL decoder ────────────────────────────────────────────

def _decode_url(href: str) -> str:
    """لینک‌های redirect برتینا را به URL واقعی تبدیل می‌کند"""
    if not href:
        return ""
    # مستقیم x.com
    if href.startswith("http") and "x.com" in href:
        return href
    # /api/click?dest=BASE64
    if "dest=" in href:
        try:
            full = (BERTINA + href) if href.startswith("/") else href
            qs   = parse_qs(urlparse(full).query)
            dest = qs.get("dest", [""])[0]
            if dest:
                # padding
                pad = 4 - len(dest) % 4
                if pad != 4:
                    dest += "=" * pad
                return base64.urlsafe_b64decode(dest).decode("utf-8")
        except Exception:
            pass
    if "x.com" in href:
        return href
    return ""

# ── HTTP ───────────────────────────────────────────────────

def fetch_raw(query: str, page: int = 1) -> str | None:
    params = {"q": query}
    if page > 1:
        params["page"] = str(page)
    try:
        r = requests.get(SEARCH_EP, params=params,
                         headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[fetcher] {e}")
        return None

# ── Profile snippet parser ─────────────────────────────────

def _parse_profile(snippet: str, username: str) -> dict:
    def num(pattern):
        m = re.search(pattern, snippet, re.I)
        if not m: return 0
        return int(m.group(1).replace(",", ""))

    posts_n    = num(r"([\d,]+)\s*Posts?")
    following_n= num(r"([\d,]+)\s*Following")
    followers_n= num(r"([\d,]+)\s*Followers?")
    joined_m   = re.search(r"Joined[:\s]+([^\n.]+)", snippet, re.I)
    website_m  = re.search(r"Website[:\s]+(https?://\S+)", snippet, re.I)

    name_m = re.match(r"^([^\n.✓]+?)[\s✓]", snippet.strip())
    display = name_m.group(1).strip() if name_m else username

    return {
        "username":     username,
        "display_name": display,
        "bio":          "",
        "posts":        posts_n,
        "following":    following_n,
        "followers":    followers_n,
        "joined":       joined_m.group(1).strip() if joined_m else "",
        "website":      website_m.group(1).strip() if website_m else "",
        "verified":     "✓" in snippet or "✔" in snippet,
    }

# ── Result classifier ──────────────────────────────────────

def _is_profile_url(url: str, username: str) -> bool:
    """
    تشخیص می‌دهد آیا URL یک پروفایل است یا یک پست.
    پروفایل:  x.com/{username}  یا  x.com/{username}/
    پست:      x.com/{username}/status/{id}
              x.com/i/...
    """
    if "/status/" in url:
        return False
    if "/i/" in url.lower():
        return False
    # الگوی پروفایل
    pattern = rf"x\.com/{re.escape(username)}/?$"
    return bool(re.search(pattern, url, re.I))

def _clean_text(snippet: str, username: str) -> str:
    """پاک‌سازی متن snippet از پیشوندهای برتینا"""
    # حذف "نام (@handle). N likes. N replies."
    t = re.sub(
        rf"^.{{1,60}}\(@{re.escape(username)}\)\.\s*[\d]*\s*"
        r"(?:likes?[\s\d,]*)?(?:replies?[\s\d,]*)?[.،]?\s*",
        "", snippet, flags=re.I
    )
    # حذف "username profile. username. ✓. handle."
    t = re.sub(r"^[^\n]{1,40}\s*profile\.\s*[^\n]{1,40}\.\s*[✓✔]?\s*\w+\s*\.\s*", "", t, flags=re.I)
    return t.strip() or snippet.strip()

# ── Main parser ────────────────────────────────────────────

def parse_html(html: str, username: str) -> tuple[list, dict | None]:
    soup    = BeautifulSoup(html, "html.parser")
    posts   = []
    profile = None
    seen    = set()

    for article in soup.select("article.group, article"):
        link_el = article.select_one("h3 a[href]")
        if not link_el:
            continue

        url = _decode_url(link_el.get("href", ""))
        if not url or "x.com" not in url:
            continue
        if url in seen:
            continue
        seen.add(url)

        title   = link_el.get_text(strip=True)
        snip_el = article.select_one("p.text-sm")
        snippet = snip_el.get_text(strip=True) if snip_el else ""
        time_el = article.select_one("div.mt-1 span, span.tweet-time")
        date    = time_el.get_text(strip=True) if time_el else ""

        # ── پروفایل؟
        if _is_profile_url(url, username):
            if not profile:
                profile = _parse_profile(snippet + " " + title, username)
            continue

        # ── پست معمولی
        tid_m    = re.search(r"/status/(\d+)", url)
        tweet_id = tid_m.group(1) if tid_m else None

        text = _clean_text(snippet, username)

        if re.search(r"replying to|در پاسخ به", title + " " + snippet, re.I):
            ptype = "reply"
        else:
            ptype = "tweet"

        likes_m   = re.search(r"([\d,]+)\s*likes?",   snippet, re.I)
        replies_m = re.search(r"([\d,]+)\s*replies?",  snippet, re.I)

        def to_int(m):
            return int(m.group(1).replace(",","")) if m else 0

        url_l = url.lower()
        is_target = (
            f"/{username.lower()}/" in url_l
            or url_l.rstrip("/").endswith(f"/{username.lower()}")
            or f"@{username.lower()}" in snippet.lower()
        )

        # هشتگ و منشن
        hashtags = re.findall(r"#[\w\u0600-\u06FF]+", text)
        mentions = [m for m in re.findall(r"@\w+", text)
                    if m.lower() != f"@{username.lower()}"]

        posts.append({
            "tweet_id":    tweet_id,
            "url":         url,
            "username":    username,
            "is_target":   is_target,
            "text":        text,
            "date":        date,
            "type":        ptype,
            "likes":       to_int(likes_m),
            "replies":     to_int(replies_m),
            "has_media":   bool(re.search(r"\bimage\b|\bphoto\b|\bvideo\b|\bpic\b", snippet, re.I)),
            "hashtags":    hashtags,
            "mentions":    mentions,
            "raw_snippet": snippet,
            "seen":        False,
        })

    return posts, profile

# ── High-level API ─────────────────────────────────────────

def fetch_user(username: str, max_pages: int = 3) -> tuple[list, dict | None]:
    all_posts = []
    profile   = None
    query     = f"site:x.com/{username}"

    for page in range(1, max_pages + 1):
        html = fetch_raw(query, page)
        if not html:
            break
        posts, pdata = parse_html(html, username)
        if not posts and page > 1:
            break
        all_posts.extend(posts)
        if pdata and not profile:
            profile = pdata

    return all_posts, profile


def fetch_search(query: str, max_pages: int = 2) -> tuple[list, dict | None]:
    q = query.strip()

    if q.startswith("@"):
        # جستجوی کاربر
        username = q.lstrip("@").split()[0]
        return fetch_user(username, max_pages)

    elif q.startswith("#"):
        bertina_q = f'site:x.com "{q}"'
        username  = "unknown"
    else:
        bertina_q = f"site:x.com {q}"
        username  = "unknown"

    all_posts = []
    for page in range(1, max_pages + 1):
        html = fetch_raw(bertina_q, page)
        if not html:
            break
        posts, _ = parse_html(html, username)
        for p in posts:
            url_m = re.search(r"x\.com/([^/]+)/status", p.get("url",""))
            if url_m:
                p["username"] = url_m.group(1)
        all_posts.extend(posts)

    return all_posts, None
