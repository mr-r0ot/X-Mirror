"""
fetcher.py  —  دریافت داده از search.bertina.ir
FIX V2: اضافه کردن after: + tbs=sbd:1 برای جدیدترین پست‌ها
https://github.com/mr-r0ot/X-Mirror
"""

import re, base64, requests
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
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

# ── Date helpers ───────────────────────────────────────────

def _after_date(days_back: int = 60) -> str:
    return (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

def parse_date_ts(date_str: str) -> float:
    if not date_str:
        return 0.0
    now = datetime.now()
    s   = date_str.lower().strip()

    relative = [
        (r"(\d+)\s*s(?:ec)",    "seconds"),
        (r"(\d+)\s*m(?:in)",    "minutes"),
        (r"(\d+)\s*h(?:our)",   "hours"),
        (r"(\d+)\s*d(?:ay)",    "days"),
        (r"(\d+)\s*w(?:eek)",   "weeks"),
        (r"(\d+)\s*mo(?:nth)",  "months"),
        (r"(\d+)\s*y(?:ear)",   "years"),
    ]
    for pat, unit in relative:
        m = re.search(pat, s)
        if m:
            n = int(m.group(1))
            if unit == "months": return (now - timedelta(days=n*30)).timestamp()
            if unit == "years":  return (now - timedelta(days=n*365)).timestamp()
            return (now - timedelta(**{unit: n})).timestamp()

    fa = [
        ("ثانیه", "seconds"), ("دقیقه", "minutes"),
        ("ساعت",  "hours"),   ("روز",   "days"),
        ("هفته",  "weeks"),   ("ماه",   "months"),
    ]
    for fa_w, unit in fa:
        if fa_w in date_str:
            m = re.search(r"(\d+)", date_str)
            n = int(m.group(1)) if m else 1
            if unit == "months": return (now - timedelta(days=n*30)).timestamp()
            return (now - timedelta(**{unit: n})).timestamp()

    if any(w in s for w in ["just", "now", "الان", "همین", "لحظه"]):
        return now.timestamp()

    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%d %b %Y", "%b %d"):
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            # اگه سال نداشت، سال جاری
            if parsed.year == 1900:
                parsed = parsed.replace(year=now.year)
            return parsed.timestamp()
        except ValueError:
            continue

    return 0.0   

def _decode_url(href: str) -> str:
    if not href: return ""
    if href.startswith("http") and "x.com" in href: return href
    if "dest=" in href:
        try:
            full = (BERTINA + href) if href.startswith("/") else href
            qs   = parse_qs(urlparse(full).query)
            dest = qs.get("dest", [""])[0]
            if dest:
                pad = 4 - len(dest) % 4
                if pad != 4: dest += "=" * pad
                return base64.urlsafe_b64decode(dest).decode("utf-8")
        except Exception:
            pass
    if "x.com" in href: return href
    return ""


def fetch_raw(query: str, page: int = 1, sort_date: bool = True) -> str | None:
    params = {"q": query}
    if page > 1:
        params["page"] = str(page)
    if sort_date:
        params["tbs"] = "sbd:1"   # Sort By Date — جدیدترین اول
    try:
        r = requests.get(SEARCH_EP, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[fetcher] {e}")
        return None


def _parse_profile(snippet: str, title: str, username: str) -> dict:
    def num(pat):
        m = re.search(pat, snippet + " " + title, re.I)
        return int(m.group(1).replace(",","")) if m else 0

    joined_m  = re.search(r"Joined[:\s]+([^\n.·]+)", snippet + " " + title, re.I)
    website_m = re.search(r"Website[:\s]+(https?://\S+)", snippet, re.I)
    name_m    = re.match(r"^([^\n.✓✔@·]+?)[\s·✓✔]", snippet.strip())

    return {
        "username":     username,
        "display_name": name_m.group(1).strip() if name_m else username,
        "bio":          "",
        "posts":        num(r"([\d,]+)\s*Posts?"),
        "following":    num(r"([\d,]+)\s*Following"),
        "followers":    num(r"([\d,]+)\s*Followers?"),
        "joined":       joined_m.group(1).strip() if joined_m else "",
        "website":      website_m.group(1).strip() if website_m else "",
        "verified":     "✓" in snippet or "✔" in snippet,
    }


def _is_profile(url: str, username: str) -> bool:
    if "/status/" in url or "/i/" in url.lower():
        return False
    return bool(re.search(rf"x\.com/{re.escape(username)}/?$", url, re.I))


def _clean(snippet: str, username: str) -> str:
    t = re.sub(
        rf"^.{{0,80}}\(@{re.escape(username)}\)\.\s*[\d,]*\s*"
        r"(?:likes?|replies?)?[\s\d,]*[.،]?\s*",
        "", snippet, flags=re.I
    )
    t = re.sub(r"^[^\n]{1,50}\s*profile\.\s*[^\n]{1,50}\.\s*[✓✔]?\s*\w+\s*\.\s*", "", t, flags=re.I)
    return t.strip() or snippet.strip()


def parse_html(html: str, username: str) -> tuple[list, dict | None]:
    soup    = BeautifulSoup(html, "html.parser")
    posts   = []
    profile = None
    seen    = set()

    for article in soup.select("article.group, article"):
        link_el = article.select_one("h3 a[href]")
        if not link_el: continue

        url = _decode_url(link_el.get("href",""))
        if not url or "x.com" not in url or url in seen: continue
        seen.add(url)

        title   = link_el.get_text(strip=True)
        snip_el = article.select_one("p.text-sm")
        snippet = snip_el.get_text(strip=True) if snip_el else ""
        time_el = article.select_one("div.mt-1 span")
        date    = time_el.get_text(strip=True) if time_el else ""
        date_ts = parse_date_ts(date)   # ← timestamp واقعی برای sort

        if _is_profile(url, username):
            if not profile:
                profile = _parse_profile(snippet, title, username)
            continue

        tid_m    = re.search(r"/status/(\d+)", url)
        tweet_id = tid_m.group(1) if tid_m else None

        # tweet_id خودش timestamp encode داره
        # ID بالاتر = جدیدتر  (Twitter Snowflake)
        if tweet_id and not date_ts:
            tid_int  = int(tweet_id)
            # آفست Twitter epoch: 1288834974657
            ts_ms    = (tid_int >> 22) + 1288834974657
            date_ts  = ts_ms / 1000.0

        text = _clean(snippet, username)

        ptype = "reply" if re.search(r"replying to|در پاسخ", title + snippet, re.I) else "tweet"

        def to_int(pat):
            m = re.search(pat, snippet, re.I)
            return int(m.group(1).replace(",","")) if m else 0

        url_l = url.lower()
        is_target = (
            f"/{username.lower()}/" in url_l
            or url_l.rstrip("/").endswith(f"/{username.lower()}")
            or f"@{username.lower()}" in snippet.lower()
        )

        # username از URL
        url_user_m = re.search(r"x\.com/([^/]+)/status", url)
        actual_user = url_user_m.group(1) if url_user_m else username

        posts.append({
            "tweet_id":   tweet_id,
            "url":        url,
            "username":   actual_user,
            "is_target":  is_target,
            "text":       text,
            "date":       date,
            "date_ts":    date_ts,      # ← کلید اصلی برای مرتب‌سازی
            "type":       ptype,
            "likes":      to_int(r"([\d,]+)\s*likes?"),
            "replies":    to_int(r"([\d,]+)\s*replies?"),
            "has_media":  bool(re.search(r"\bimage\b|\bphoto\b|\bvideo\b", snippet, re.I)),
            "hashtags":   re.findall(r"#[\w\u0600-\u06FF]+", text),
            "mentions":   [m for m in re.findall(r"@\w+", text)
                          if m.lower() != f"@{actual_user.lower()}"],
            "raw_snippet": snippet,
            "seen":       False,
        })

    # مرتب‌سازی اولیه: جدیدترین اول
    posts.sort(key=lambda p: p.get("date_ts", 0), reverse=True)
    return posts, profile


def fetch_user(username: str, max_pages: int = 3) -> tuple[list, dict | None]:
    after    = _after_date(60)
    # query اصلی با فیلتر تاریخ
    query    = f"site:x.com/{username} after:{after}"

    all_posts = []
    profile   = None

    for page in range(1, max_pages + 1):
        html = fetch_raw(query, page, sort_date=True)
        if not html: break
        posts, pdata = parse_html(html, username)
        if not posts and page == 1:
            html2 = fetch_raw(f"site:x.com/{username}", page, sort_date=True)
            if html2:
                posts, pdata = parse_html(html2, username)
        if not posts and page > 1: break
        all_posts.extend(posts)
        if pdata and not profile: profile = pdata

    # dedup + sort نهایی
    seen_ids = set()
    unique   = []
    for p in all_posts:
        k = p.get("tweet_id") or p.get("url")
        if k and k not in seen_ids:
            seen_ids.add(k); unique.append(p)

    unique.sort(key=lambda p: p.get("date_ts", 0), reverse=True)
    return unique, profile


def fetch_search(query: str, max_pages: int = 2) -> tuple[list, dict | None]:
    q = query.strip()

    if q.startswith("@"):
        username = q.lstrip("@").split()[0]
        return fetch_user(username, max_pages)

    if q.startswith("#"):
        bertina_q = f'site:x.com "{q}" after:{_after_date(30)}'
    else:
        bertina_q = f"site:x.com {q} after:{_after_date(45)}"

    all_posts = []
    for page in range(1, max_pages + 1):
        html = fetch_raw(bertina_q, page, sort_date=True)
        if not html: break
        posts, _ = parse_html(html, "unknown")
        if not posts and page > 1: break
        all_posts.extend(posts)

    all_posts.sort(key=lambda p: p.get("date_ts", 0), reverse=True)
    return all_posts, None
