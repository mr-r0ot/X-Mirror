"""
offline.py  —  https://github.com/mr-r0ot/X-Mirror
"""

import json, os, re, html as html_lib
from datetime import datetime

try:
    import customtkinter as ctk
    from tkinter import filedialog
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def _load():
    def rd(f, d):
        p = os.path.join(DATA_DIR, f)
        try:
            with open(p, encoding="utf-8") as fp: return json.load(fp)
        except: return d
    return rd("posts.json",[]), rd("profiles.json",{})

def _e(s): return html_lib.escape(str(s or ""))
def _av(u): return (str(u)[0] if u else "X").upper()


def build_html(posts: list, profiles: dict) -> str:
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M")
    real = [p for p in posts if p.get("type","tweet") != "profile"]
    pj   = json.dumps(real,   ensure_ascii=False)
    prj  = json.dumps(profiles, ensure_ascii=False)
    cnt  = len(real)

    cards = "\n".join(_card(p) for p in real)

    return f"""<!DOCTYPE html>
<html lang="fa">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>X Mirror — آفلاین ({cnt} پست)</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#000;--bgh:#080808;--surf:#16181c;--brd:#2f3336;
      --tx:#e7e9ea;--tx2:#71767b;--ac:#1d9bf0;
      --lk:#f91880;--rd:#f4212e;--rt:#00ba7c}}
body{{background:var(--bg);color:var(--tx);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;min-height:100vh}}
a{{color:inherit;text-decoration:none}}button{{cursor:pointer;border:none;background:none;font-family:inherit;color:inherit}}
.wrap{{display:flex;max-width:1000px;margin:0 auto}}
.nav{{width:240px;padding:12px;position:sticky;top:0;height:100vh;overflow-y:auto;flex-shrink:0;display:flex;flex-direction:column}}
.nav::-webkit-scrollbar{{display:none}}
.nav-logo{{font-size:28px;font-weight:900;padding:12px;margin-bottom:8px}}
.ni{{display:flex;align-items:center;gap:16px;padding:12px;border-radius:9999px;font-size:18px;cursor:pointer;transition:background .2s}}
.ni:hover{{background:rgba(239,243,244,.1)}}
.ni.active{{font-weight:700}}
.ni svg{{width:24px;height:24px;fill:var(--tx);flex-shrink:0}}
.nav-info{{font-size:11px;color:var(--tx2);padding:8px 12px;margin-top:auto;direction:rtl;line-height:1.9}}
.main{{flex:1;max-width:600px;border-right:1px solid var(--brd);border-left:1px solid var(--brd)}}
.ph{{position:sticky;top:0;z-index:10;background:rgba(0,0,0,.85);backdrop-filter:blur(12px);border-bottom:1px solid var(--brd)}}
.ph-row{{display:flex;align-items:center;gap:8px;padding:0 16px;height:53px}}
.ph-title{{font-size:20px;font-weight:700}}
.offline-badge{{background:rgba(255,165,0,.12);border:1px solid rgba(255,165,0,.3);color:orange;border-radius:9999px;padding:3px 10px;font-size:11px;font-weight:600;margin-right:auto}}
.tabs{{display:flex;border-bottom:1px solid var(--brd)}}
.tab{{flex:1;padding:14px 4px;text-align:center;font-size:15px;font-weight:500;color:var(--tx2);border-bottom:2px solid transparent;cursor:pointer;transition:all .2s}}
.tab:hover{{background:rgba(239,243,244,.07)}}
.tab.on{{color:var(--tx);border-bottom-color:var(--ac);font-weight:700}}
.av{{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;color:#fff;text-transform:uppercase;flex-shrink:0}}
.g0{{background:linear-gradient(135deg,#1d9bf0,#7856ff)}}
.g1{{background:linear-gradient(135deg,#7856ff,#ff6b9d)}}
.g2{{background:linear-gradient(135deg,#00ba7c,#1d9bf0)}}
.g3{{background:linear-gradient(135deg,#f4212e,#ff8c00)}}
.g4{{background:linear-gradient(135deg,#ff8c00,#f91880)}}
.g5{{background:linear-gradient(135deg,#f91880,#7856ff)}}
.tweet{{padding:12px 16px;border-bottom:1px solid var(--brd);display:flex;gap:12px;cursor:pointer;transition:background .15s}}
.tweet:hover{{background:var(--bgh)}}
.tw-left{{flex-shrink:0}}
.tw-right{{flex:1;min-width:0}}
.tw-head{{display:flex;align-items:center;gap:4px;overflow:hidden;flex-wrap:nowrap}}
.tw-name{{font-weight:700;font-size:15px;max-width:130px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0}}
.tw-name:hover{{text-decoration:underline}}
.vi{{width:18px;height:18px;flex-shrink:0}}
.tw-handle{{color:var(--tx2);font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tw-dot{{color:var(--tx2);font-size:13px;flex-shrink:0}}
.tw-time{{color:var(--tx2);font-size:15px;white-space:nowrap;flex-shrink:0}}
.tw-more{{margin-right:auto;width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--tx2);transition:all .2s;flex-shrink:0}}
.tw-more:hover{{background:rgba(29,155,240,.1);color:var(--ac)}}
.tw-text{{font-size:15px;line-height:1.5;margin-top:4px;word-break:break-word;direction:rtl;text-align:right}}
.tw-actions{{display:flex;margin-top:12px;gap:0}}
.ab{{display:flex;align-items:center;gap:4px;color:var(--tx2);font-size:13px;padding:6px 10px 6px 0;border-radius:9999px;transition:color .2s;min-width:56px}}
.ab svg{{width:18px;height:18px}}
.ab-r:hover{{color:var(--ac)}} .ab-rt:hover{{color:var(--rt)}}
.ab-l:hover,.ab-l.on{{color:var(--lk)}} .ab-d:hover,.ab-d.on{{color:var(--rd)}}
.ab-s:hover{{color:var(--ac)}}
.s-wrap{{padding:8px 16px;border-bottom:1px solid var(--brd)}}
.s-box{{background:var(--surf);border-radius:9999px;display:flex;align-items:center;gap:12px;padding:0 16px;height:44px;border:2px solid transparent;transition:border .2s}}
.s-box:focus-within{{background:var(--bg);border-color:var(--ac)}}
.s-box svg{{fill:var(--tx2);width:20px;height:20px;flex-shrink:0}}
.s-box input{{background:none;border:none;outline:none;color:var(--tx);font-size:15px;flex:1;direction:rtl;text-align:right}}
.s-box input::placeholder{{color:var(--tx2)}}
.empty{{padding:56px 32px;text-align:center;color:var(--tx2)}}
.empty h2{{font-size:28px;font-weight:800;color:var(--tx);margin-bottom:8px}}
.toast{{position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#333639;color:var(--tx);padding:12px 20px;border-radius:4px;font-size:15px;z-index:9999;opacity:0;transition:opacity .25s;pointer-events:none;white-space:nowrap}}
.toast.on{{opacity:1}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@media(max-width:700px){{.nav{{width:60px}}.nav .ni span,.nav-info{{display:none}}.ni{{justify-content:center}}}}
</style>
</head>
<body>
<div class="wrap">
<nav class="nav">
  <div class="nav-logo">𝕏</div>
  <div class="ni active" onclick="showPage('home')">
    <svg viewBox="0 0 24 24"><path d="M21.591 7.146L12.52 1.157c-.316-.21-.724-.21-1.04 0l-9.071 5.99c-.26.173-.409.456-.409.757v13.183c0 .502.418.913.929.913H9.14c.51 0 .929-.41.929-.913v-7.075h3.909v7.075c0 .502.417.913.928.913h6.212c.511 0 .929-.41.929-.913V7.904c0-.302-.158-.584-.408-.758z"/></svg>
    <span>خانه</span>
  </div>
  <div class="ni" onclick="showPage('search')">
    <svg viewBox="0 0 24 24"><path d="M10.25 3.75c-3.59 0-6.5 2.91-6.5 6.5s2.91 6.5 6.5 6.5c1.795 0 3.419-.726 4.596-1.904 1.178-1.177 1.904-2.801 1.904-4.596 0-3.59-2.91-6.5-6.5-6.5zm-8.5 6.5c0-4.694 3.806-8.5 8.5-8.5s8.5 3.806 8.5 8.5c0 1.986-.682 3.815-1.814 5.262l4.776 4.777-1.414 1.414-4.777-4.776c-1.447 1.132-3.276 1.814-5.261 1.814-4.694 0-8.5-3.806-8.5-8.5z"/></svg>
    <span>جستجو</span>
  </div>
  <div class="nav-info">
    📦 حالت آفلاین<br>
    {cnt} پست ذخیره‌شده<br>
    ساخته‌شده: {ts}
  </div>
</nav>
<main class="main">
  <!-- HOME -->
  <div id="pg-home">
    <div class="ph">
      <div class="ph-row">
        <div class="ph-title">خانه</div>
        <span class="offline-badge">📦 آفلاین</span>
      </div>
      <div class="tabs">
        <div class="tab on" onclick="switchTab(this,'all')">همه</div>
        <div class="tab" onclick="switchTab(this,'unseen')">دیده‌نشده</div>
        <div class="tab" onclick="switchTab(this,'liked')">لایک‌شده</div>
      </div>
    </div>
    <div id="feed">{cards}</div>
  </div>
  <!-- SEARCH -->
  <div id="pg-search" style="display:none">
    <div class="ph">
      <div class="ph-row">
        <div class="ph-title">جستجو</div>
        <span class="offline-badge">📦 آفلاین</span>
      </div>
    </div>
    <div class="s-wrap">
      <div class="s-box">
        <svg viewBox="0 0 24 24"><path d="M10.25 3.75c-3.59 0-6.5 2.91-6.5 6.5s2.91 6.5 6.5 6.5c1.795 0 3.419-.726 4.596-1.904 1.178-1.177 1.904-2.801 1.904-4.596 0-3.59-2.91-6.5-6.5-6.5zm-8.5 6.5c0-4.694 3.806-8.5 8.5-8.5s8.5 3.806 8.5 8.5c0 1.986-.682 3.815-1.814 5.262l4.776 4.777-1.414 1.414-4.777-4.776c-1.447 1.132-3.276 1.814-5.261 1.814-4.694 0-8.5-3.806-8.5-8.5z"/></svg>
        <input id="s-input" type="text" placeholder="جستجو در پست‌های ذخیره‌شده..." oninput="doSearch(this.value)">
      </div>
    </div>
    <div id="sr-results"></div>
  </div>
</main>
</div>
<div class="toast" id="toast"></div>
<script>
const POSTS    = {pj};
const PROFILES = {prj};

// ── State (localStorage) ──
const ST_KEY = 'xm_offline';
let st = {{}};
try{{ st = JSON.parse(localStorage.getItem(ST_KEY)||'{{}}'); }}catch{{}}
if(!st.likes)    st.likes    = {{}};
if(!st.dislikes) st.dislikes = {{}};
if(!st.weights)  st.weights  = {{}};
if(!st.seen)     st.seen     = {{}};
const save = () => {{ try{{localStorage.setItem(ST_KEY,JSON.stringify(st));}}catch{{}} }};

// ── Algorithm ──
function score(p) {{
  const u = (p.username||'').toLowerCase();
  let s = st.weights[u]||1.0;
  if(!st.seen[p.tweet_id]) s += 1.5;
  s += Math.min((p.likes||0)/500,1.0);
  if(p.has_media) s += 0.3;
  if(st.likes[p.tweet_id]) s += 0.4;
  if(st.dislikes[p.tweet_id]) s -= 0.8;
  // date bonus: جدیدتر = بیشتر
  if(p.date_ts) {{
    const age = (Date.now()/1000 - p.date_ts)/3600;
    s += Math.max(0, 2.0 - age/48);
  }}
  s += Math.random()*0.5;
  return Math.max(s,0.01);
}}

function wShuffle(posts) {{
  const pool=[...posts.map(p=>[score(p),p])];
  const res=[];
  while(pool.length) {{
    const tot=pool.reduce((a,[s])=>a+s,0);
    let r=Math.random()*tot,cum=0,idx=0;
    for(let i=0;i<pool.length;i++){{ cum+=pool[i][0]; if(r<=cum){{idx=i;break;}} }}
    res.push(pool[idx][1]); pool.splice(idx,1);
  }}
  return res;
}}

// ── Render ──
const VI = `<svg class="vi" viewBox="0 0 24 24"><path fill="#1d9bf0" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></svg>`;

const GRADS = ['g0','g1','g2','g3','g4','g5'];
let _gi = 0;
const gmap = {{}};
function grad(u) {{ if(!gmap[u]) gmap[u]=GRADS[_gi++%6]; return gmap[u]; }}

function renderCard(p) {{
  const tid = p.tweet_id||'';
  const u   = p.username||'?';
  const lOn = st.likes[tid]    ? ' on':'';
  const dOn = st.dislikes[tid] ? ' on':'';
  return `<article class="tweet" onclick="openP('${{p.url||''}}','${{tid}}')">
  <div class="tw-left"><div class="av ${{grad(u)}}">${{u[0]||'?'}}</div></div>
  <div class="tw-right">
    <div class="tw-head">
      <span class="tw-name">${{u}}</span>${{VI}}
      <span class="tw-handle">@${{u}}</span>
      ${{p.date?`<span class="tw-dot">·</span><span class="tw-time">${{p.date}}</span>`:''}}
      <button class="tw-more" onclick="event.stopPropagation()"><svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M3 12c0-1.1.9-2 2-2s2 .9 2 2-.9 2-2 2-2-.9-2-2zm9 2c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm7 0c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z"/></svg></button>
    </div>
    <div class="tw-text">${{p.text||''}}</div>
    <div class="tw-actions">
      <button class="ab ab-r" onclick="event.stopPropagation();showToast('ریپلای — آنلاین نیست')">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 8.129 3.64 8.129 8.13 0 2.96-1.607 5.68-4.196 7.11l-8.054 4.46v-3.69h-.067c-4.49.1-8.183-3.51-8.183-8.01zm8.005-6c-3.317 0-6.005 2.69-6.005 6 0 3.37 2.77 6.08 6.138 6.01l.351-.01h1.761v2.3l5.087-2.81c1.951-1.08 3.163-3.13 3.163-5.36 0-3.39-2.744-6.13-6.129-6.13H9.756z"/></svg>
        <span>${{p.replies||''}}</span>
      </button>
      <button class="ab ab-rt" onclick="event.stopPropagation();showToast('ریتوییت — آنلاین نیست')">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 2H13v2H7.5c-2.209 0-4-1.79-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 6H11V4h5.5c2.209 0 4 1.79 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z"/></svg>
      </button>
      <button class="ab ab-l${{lOn}}" id="lb-${{tid}}" onclick="event.stopPropagation();tLike('${{tid}}','${{u}}',this)">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-1.243.07-2.349.78-2.91 1.91-.552 1.12-.633 2.78.479 4.82 1.074 1.97 3.257 4.27 7.129 6.61 3.87-2.34 6.052-4.64 7.126-6.61 1.111-2.04 1.03-3.7.477-4.82-.561-1.13-1.666-1.84-2.908-1.91zm4.187 7.69c-1.351 2.48-4.001 5.12-8.379 7.67l-.503.3-.504-.3c-4.379-2.55-7.029-5.19-8.382-7.67-1.36-2.5-1.41-4.86-.514-6.67.887-1.79 2.647-2.91 4.601-3.01 1.651-.09 3.368.56 4.798 2.01 1.429-1.45 3.146-2.1 4.796-2.01 1.954.1 3.714 1.22 4.601 3.01.896 1.81.846 4.17-.514 6.67z"/></svg>
        <span>${{p.likes||''}}</span>
      </button>
      <button class="ab ab-d${{dOn}}" id="db-${{tid}}" onclick="event.stopPropagation();tDis('${{tid}}','${{u}}',this)">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 21.638h-.014C9.403 21.59 1.95 14.856 1.95 8.478c0-3.064 2.525-5.754 5.403-5.754 2.29 0 3.83 1.58 4.646 2.73.813-1.148 2.353-2.73 4.644-2.73 2.88 0 5.404 2.69 5.404 5.755 0 6.375-7.454 13.11-10.037 13.157H12zM7.354 4.724c-2.08 0-3.903 1.988-3.903 4.255 0 5.74 7.035 11.596 8.55 11.658 1.52-.062 8.55-5.917 8.55-11.658 0-2.267-1.822-4.255-3.902-4.255-2.528 0-3.94 2.936-3.952 2.965-.23.562-1.156.562-1.387 0-.015-.03-1.426-2.965-3.956-2.965z"/></svg>
      </button>
      <button class="ab ab-s" onclick="event.stopPropagation();copyL('${{p.url||''}}')">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2.59l5.7 5.7-1.41 1.42L13 6.41V16h-2V6.41l-3.3 3.3-1.41-1.42L12 2.59zM21 15l-.02 3.51c0 1.38-1.12 2.49-2.5 2.49H5.5C4.11 21 3 19.88 3 18.5V15h2v3.5c0 .28.22.5.5.5h12.98c.28 0 .5-.22.5-.5L19 15h2z"/></svg>
      </button>
    </div>
  </div>
</article>`;
}}

// ── Interactions ──
function adj(u,d){{ const k=u.toLowerCase(); st.weights[k]=Math.max(0.1,Math.min(5,(st.weights[k]||1)+d)); save(); }}
function tLike(tid,u,btn){{
  if(!tid) return;
  const was=!!st.likes[tid];
  if(st.dislikes[tid]){{ delete st.dislikes[tid]; adj(u,0.3); }}
  if(!was){{ st.likes[tid]=u; adj(u,0.5); showToast('❤ لایک شد'); }}
  else{{ delete st.likes[tid]; adj(u,-0.2); showToast('لایک برداشته شد'); }}
  save();
  btn.classList.toggle('on',!was);
  const db=document.getElementById('db-'+tid); if(db) db.classList.remove('on');
}}
function tDis(tid,u,btn){{
  if(!tid) return;
  const was=!!st.dislikes[tid];
  if(st.likes[tid]){{ delete st.likes[tid]; adj(u,-0.3); }}
  if(!was){{ st.dislikes[tid]=u; adj(u,-0.5); showToast('👎 دیسلایک شد'); }}
  else{{ delete st.dislikes[tid]; adj(u,0.1); showToast('دیسلایک برداشته شد'); }}
  save();
  btn.classList.toggle('on',!was);
  const lb=document.getElementById('lb-'+tid); if(lb) lb.classList.remove('on');
}}
function openP(url,tid){{
  if(tid) st.seen[tid]=true; save();
  if(url) window.open(url,'_blank');
}}
function copyL(url){{
  navigator.clipboard?.writeText(url).then(()=>showToast('لینک کپی شد ✓'))||showToast(url);
}}

// ── Pages ──
function showPage(name){{
  ['home','search'].forEach(n=>{{
    document.getElementById('pg-'+n).style.display=n===name?'':'none';
  }});
  document.querySelectorAll('.ni').forEach((el,i)=>el.classList.toggle('active',i===(name==='home'?0:1)));
  if(name==='home') renderFeed();
  if(name==='search'){{ document.getElementById('s-input').focus(); }}
}}
function switchTab(el,f){{
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
  el.classList.add('on');
  renderFeed(f);
}}
function renderFeed(filter){{
  filter = filter||'all';
  let posts = POSTS.filter(p=>p.type!=='profile');
  if(filter==='unseen') posts=posts.filter(p=>!st.seen[p.tweet_id]);
  if(filter==='liked')  posts=posts.filter(p=>!!st.likes[p.tweet_id]);
  const sorted = wShuffle(posts);
  const feed = document.getElementById('feed');
  if(!feed) return;
  feed.innerHTML = sorted.length ? sorted.map(renderCard).join('') :
    '<div class="empty"><h2>پستی نیست</h2><p>فیلتر دیگری انتخاب کنید</p></div>';
}}
function doSearch(q){{
  q=q.trim().toLowerCase();
  const res=document.getElementById('sr-results');
  if(!q){{ res.innerHTML=''; return; }}
  const found=POSTS.filter(p=>p.type!=='profile'&&
    (p.text+' '+p.username+' '+(p.raw_snippet||'')).toLowerCase().includes(q));
  res.innerHTML=found.length?
    `<div style="padding:8px 16px;font-size:13px;color:var(--tx2)">${{found.length}} نتیجه</div>`+
    found.map(renderCard).join(''):
    '<div class="empty"><h2>نتیجه‌ای نبود</h2></div>';
}}
function showToast(msg){{
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('on');
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove('on'),2500);
}}

// init
renderFeed();
</script>
</body>
</html>"""

def _card(p: dict) -> str:
    tid = _e(p.get("tweet_id",""))
    u   = _e(p.get("username","unknown"))
    txt = _e(p.get("text",""))
    dt  = _e(p.get("date",""))
    lk  = p.get("likes",0) or ""
    rp  = p.get("replies",0) or ""
    url = _e(p.get("url",""))
    return f"""<article class="tweet" onclick="openP('{url}','{tid}')">
  <div class="tw-left"><div class="av g0">{_av(p.get("username"))}</div></div>
  <div class="tw-right">
    <div class="tw-head">
      <span class="tw-name">{u}</span>
      <svg class="vi" viewBox="0 0 24 24"><path fill="#1d9bf0" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></svg>
      <span class="tw-handle">@{u}</span>
      {'<span class="tw-dot">·</span><span class="tw-time">' + dt + '</span>' if dt else ''}
    </div>
    <div class="tw-text">{txt}</div>
    <div class="tw-actions">
      <button class="ab ab-r" onclick="event.stopPropagation()"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 8.129 3.64 8.129 8.13 0 2.96-1.607 5.68-4.196 7.11l-8.054 4.46v-3.69h-.067c-4.49.1-8.183-3.51-8.183-8.01z"/></svg><span>{rp}</span></button>
      <button class="ab ab-l" id="lb-{tid}" onclick="event.stopPropagation();tLike('{tid}','{u}',this)"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 5.44 7.304 5.5c-1.243.07-2.349.78-2.91 1.91-.552 1.12-.633 2.78.479 4.82 1.074 1.97 3.257 4.27 7.129 6.61 3.87-2.34 6.052-4.64 7.126-6.61 1.111-2.04 1.03-3.7.477-4.82-.561-1.13-1.666-1.84-2.908-1.91zm4.187 7.69c-1.351 2.48-4.001 5.12-8.379 7.67l-.503.3-.504-.3c-4.379-2.55-7.029-5.19-8.382-7.67-1.36-2.5-1.41-4.86-.514-6.67.887-1.79 2.647-2.91 4.601-3.01 1.651-.09 3.368.56 4.798 2.01 1.429-1.45 3.146-2.1 4.796-2.01 1.954.1 3.714 1.22 4.601 3.01.896 1.81.846 4.17-.514 6.67z"/></svg><span>{lk}</span></button>
      <button class="ab ab-d" id="db-{tid}" onclick="event.stopPropagation();tDis('{tid}','{u}',this)"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 21.638h-.014C9.403 21.59 1.95 14.856 1.95 8.478c0-3.064 2.525-5.754 5.403-5.754 2.29 0 3.83 1.58 4.646 2.73.813-1.148 2.353-2.73 4.644-2.73 2.88 0 5.404 2.69 5.404 5.755 0 6.375-7.454 13.11-10.037 13.157H12z"/></svg></button>
      <button class="ab ab-s" onclick="event.stopPropagation();copyL('{url}')"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2.59l5.7 5.7-1.41 1.42L13 6.41V16h-2V6.41l-3.3 3.3-1.41-1.42L12 2.59z"/></svg></button>
    </div>
  </div>
</article>"""



def run_gui():
    posts, profiles = _load()
    cnt = len([p for p in posts if p.get("type","tweet")!="profile"])
    if HAS_CTK:
        _ctk_gui(posts, profiles, cnt)
    elif HAS_TK:
        _tk_gui(posts, profiles, cnt)
    else:
        _cli(posts, profiles, cnt)

def _ctk_gui(posts, profiles, cnt):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    win = ctk.CTk()
    win.title("X Mirror — خروجی آفلاین")
    win.geometry("500x400")
    win.resizable(False, False)

    ctk.CTkLabel(win, text="📦 ساخت فایل HTML آفلاین",
                 font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20,4))
    ctk.CTkLabel(win, text=f"{cnt} پست در پایگاه‌داده",
                 text_color="gray").pack(pady=(0,16))

    ctk.CTkLabel(win, text="نام فایل:").pack(anchor="w", padx=20)
    name_v = ctk.StringVar(value=f"x-mirror-{datetime.now().strftime('%Y%m%d')}.html")
    ctk.CTkEntry(win, textvariable=name_v, width=460).pack(padx=20, pady=(4,12))

    ctk.CTkLabel(win, text="پوشه ذخیره:").pack(anchor="w", padx=20)
    path_v = ctk.StringVar(value=os.path.expanduser("~"))
    pf = ctk.CTkFrame(win, fg_color="transparent")
    pf.pack(fill="x", padx=20, pady=(4,16))
    ctk.CTkEntry(pf, textvariable=path_v, width=380).pack(side="left")
    ctk.CTkButton(pf, text="...", width=68,
                  command=lambda: path_v.set(
                      filedialog.askdirectory(initialdir=path_v.get()) or path_v.get())
                  ).pack(side="left", padx=6)

    prog = ctk.CTkProgressBar(win, width=460); prog.pack(padx=20); prog.set(0)
    msg_lbl = ctk.CTkLabel(win, text="آماده", text_color="gray")
    msg_lbl.pack(pady=6)

    def build():
        fname = name_v.get().strip()
        if not fname.endswith(".html"): fname += ".html"
        out = os.path.join(path_v.get(), fname)
        msg_lbl.configure(text="در حال ساخت...", text_color="orange")
        prog.set(0.4); win.update()
        try:
            content = build_html(posts, profiles)
            prog.set(0.85); win.update()
            with open(out, "w", encoding="utf-8") as f: f.write(content)
            prog.set(1.0)
            msg_lbl.configure(text=f"✓ ذخیره شد: {fname}", text_color="#00ba7c")
            import webbrowser; webbrowser.open(f"file://{os.path.abspath(out)}")
        except Exception as e:
            msg_lbl.configure(text=f"✗ خطا: {e}", text_color="#f4212e")

    ctk.CTkButton(win, text="ساخت و باز کردن فایل HTML",
                  command=build, height=46, width=460,
                  font=ctk.CTkFont(size=15, weight="bold"),
                  fg_color="#1d9bf0", hover_color="#1a8cd8").pack(padx=20, pady=10)
    win.mainloop()

def _tk_gui(posts, profiles, cnt):
    win = tk.Tk(); win.title("X Mirror — خروجی آفلاین")
    win.configure(bg="#000")
    tk.Label(win, text=f"📦 {cnt} پست", bg="#000", fg="#e7e9ea",
             font=("Arial",14,"bold")).pack(pady=10)
    path_v = tk.StringVar(value=os.path.expanduser("~"))
    name_v = tk.StringVar(value=f"x-mirror-{datetime.now().strftime('%Y%m%d')}.html")
    tk.Label(win,text="نام:",bg="#000",fg="gray").pack()
    tk.Entry(win,textvariable=name_v,width=40).pack()
    tk.Label(win,text="مسیر:",bg="#000",fg="gray").pack()
    fr=tk.Frame(win,bg="#000"); fr.pack()
    tk.Entry(fr,textvariable=path_v,width=32).pack(side="left")
    tk.Button(fr,text="...",command=lambda: path_v.set(filedialog.askdirectory() or path_v.get())).pack(side="left")
    msg=tk.Label(win,text="آماده",bg="#000",fg="gray"); msg.pack(pady=4)
    def build():
        fname=name_v.get(); out=os.path.join(path_v.get(),fname)
        msg.config(text="در حال ساخت...",fg="orange"); win.update()
        try:
            with open(out,"w",encoding="utf-8") as f: f.write(build_html(posts,profiles))
            msg.config(text=f"✓ {fname}",fg="#00ba7c")
            import webbrowser; webbrowser.open(f"file://{os.path.abspath(out)}")
        except Exception as e: msg.config(text=str(e),fg="red")
    tk.Button(win,text="ساخت HTML",command=build,
              bg="#1d9bf0",fg="white",font=("Arial",12,"bold"),padx=20,pady=8).pack(pady=10)
    win.mainloop()

def _cli(posts, profiles, cnt):
    print(f"\n📦 X Mirror — {cnt} پست")
    fname = input("نام فایل [x-mirror.html]: ").strip() or "x-mirror.html"
    path  = input(f"مسیر [{os.getcwd()}]: ").strip() or os.getcwd()
    out   = os.path.join(path, fname)
    with open(out,"w",encoding="utf-8") as f: f.write(build_html(posts,profiles))
    print(f"✓ ذخیره شد: {out}")

if __name__ == "__main__":
    run_gui()
