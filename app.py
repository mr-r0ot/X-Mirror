from flask import Flask, render_template, request, jsonify
import threading, time, socket
from fetcher import fetch_user, fetch_search
from storage import (upsert_posts, save_profile, get_profile, load_posts,
                     follow, unfollow, is_following, like_post, dislike_post,
                     get_reaction, get_followed, mark_seen, get_all_usernames, load_inter)
from algorithm import get_home_feed, get_user_posts, get_search_feed

app = Flask(__name__)

def _ip():
    xff = request.headers.get("X-Forwarded-For","")
    return xff.split(",")[0].strip() if xff else (request.remote_addr or "127.0.0.1")

_status = {"running":False,"last":"هنوز اجرا نشده","added":0}
_flock  = threading.Lock()

def _do_fetch_all():
    if _status["running"]: return 0
    with _flock:
        _status["running"] = True
        total = 0
        try:
            for u in get_all_usernames()[:10]:
                try:
                    posts,prof = fetch_user(u,max_pages=2)
                    if prof: save_profile(u,prof)
                    total += upsert_posts(posts)
                except Exception as e: print(f"[auto]{u}:{e}")
        finally:
            _status["running"] = False
            _status["last"]    = time.strftime("%H:%M:%S")
            _status["added"]  += total
    return total

def _bg(interval=300):
    while True:
        time.sleep(interval)
        _do_fetch_all()

def _total():
    return len([p for p in load_posts() if p.get("type","tweet")!="profile"])

@app.route("/")
def home():
    ip   = _ip()
    page = int(request.args.get("page",1))
    feed = get_home_feed(ip,page=page,per_page=20)
    for p in feed:
        if p.get("tweet_id"): mark_seen(p["tweet_id"])
    return render_template("index.html",
        view="home",feed=feed,page=page,
        followed=get_followed(ip),total_posts=_total(),status=_status)

@app.route("/<username>")
def profile_page(username):
    if "." in username or username.startswith("_") or username=="favicon.ico":
        return "Not found",404
    ip   = _ip()
    page = int(request.args.get("page",1))
    prof = get_profile(username)
    if not prof:
        posts,pdata = fetch_user(username,max_pages=3)
        if pdata: save_profile(username,pdata); prof=pdata
        upsert_posts(posts)
    posts     = get_user_posts(ip,username,page=page)
    following = is_following(ip,username)
    weight    = round(load_inter(ip)["weights"].get(username.lower(),1.0),2)
    return render_template("index.html",
        view="profile",
        profile=prof or {"username":username,"display_name":username,
                         "bio":"","posts":0,"following":0,"followers":0,
                         "joined":"","website":"","verified":False},
        posts=posts,username=username,following=following,
        weight=weight,page=page,followed=get_followed(ip),status=_status)

@app.route("/search")
def search_page():
    ip = _ip()
    q  = request.args.get("q","").strip()
    results,s_profile = [],None
    if q:
        raw,s_profile = fetch_search(q,max_pages=2)
        if s_profile: save_profile(q.lstrip("@").split()[0],s_profile)
        upsert_posts(raw)
        results = get_search_feed(ip,raw)
    return render_template("index.html",
        view="search",query=q,results=results,
        s_profile=s_profile,followed=get_followed(ip),
        status=_status,page=1,total_posts=_total())

@app.route("/api/follow",   methods=["POST"])
def api_follow():
    u=(request.json or {}).get("username","")
    if not u: return jsonify({"error":"no username"}),400
    follow(_ip(),u); return jsonify({"following":True,"username":u})

@app.route("/api/unfollow", methods=["POST"])
def api_unfollow():
    u=(request.json or {}).get("username","")
    unfollow(_ip(),u); return jsonify({"following":False,"username":u})

@app.route("/api/like",     methods=["POST"])
def api_like():
    d=request.json or {}
    return jsonify(like_post(_ip(),d.get("tweet_id",""),d.get("username","")))

@app.route("/api/dislike",  methods=["POST"])
def api_dislike():
    d=request.json or {}
    return jsonify(dislike_post(_ip(),d.get("tweet_id",""),d.get("username","")))

@app.route("/api/fetch",    methods=["POST"])
def api_fetch():
    u=(request.json or {}).get("username","")
    if not u: return jsonify({"error":"no username"}),400
    posts,prof = fetch_user(u,max_pages=3)
    if prof: save_profile(u,prof)
    return jsonify({"added":upsert_posts(posts),"profile":prof})

@app.route("/api/fetch_all",methods=["POST"])
def api_fetch_all():
    added=_do_fetch_all()
    return jsonify({"added":added,**_status})

@app.route("/api/status")
def api_status():
    return jsonify({**_status,"total":_total()})

def get_local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close(); return ip
    except: return "127.0.0.1"

def start(host="0.0.0.0",port=5000):
    threading.Thread(target=_bg,args=(300,),daemon=True).start()
    app.run(host=host,port=port,debug=False,use_reloader=False)

if __name__=="__main__": start()
