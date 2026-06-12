"""
main.py  —  launcher اصلی X Mirror
https://github.com/mr-r0ot/X-Mirror
"""

import os, sys, threading, webbrowser, time, socket
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PORT = 5000

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
        return ip
    except: return "127.0.0.1"

def run_headless():
    print("\n" + "="*50)
    print("  𝕏 Mirror — X Mirror Local Server")
    print("="*50)
    local_ip = get_local_ip()
    print(f"\n  محلی:   http://127.0.0.1:{PORT}")
    print(f"  شبکه:  http://{local_ip}:{PORT}")
    print("\n  Ctrl+C برای خروج\n")
    def _open():
        time.sleep(1.5)
        webbrowser.open(f"http://127.0.0.1:{PORT}")
    threading.Thread(target=_open, daemon=True).start()
    from app import start
    start(host="0.0.0.0", port=PORT)

# ── CTK GUI ────────────────────────────────────────────────
def run_gui():
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    LOCAL_IP = get_local_ip()
    LOCAL_URL = f"http://127.0.0.1:{PORT}"
    NET_URL   = f"http://{LOCAL_IP}:{PORT}"

    root = ctk.CTk()
    root.title("X Mirror")
    root.geometry("460x560")
    root.resizable(False, False)

    hf = ctk.CTkFrame(root, fg_color="#000000", corner_radius=0)
    hf.pack(fill="x")
    ctk.CTkLabel(hf, text="𝕏  Mirror",
                 font=ctk.CTkFont(size=34, weight="bold"),
                 text_color="#e7e9ea").pack(pady=(20,4))
    ctk.CTkLabel(hf, text="شبیه‌ساز X.com | اینترنت داخلی ایران",
                 font=ctk.CTkFont(size=13),
                 text_color="#71767b").pack(pady=(0,16))

    sf = ctk.CTkFrame(root, fg_color="#16181c", corner_radius=12)
    sf.pack(fill="x", padx=20, pady=8)
    status_lbl = ctk.CTkLabel(sf, text="⏳ در حال راه‌اندازی...",
                               font=ctk.CTkFont(size=13), text_color="#71767b")
    status_lbl.pack(pady=10)
    stats_lbl  = ctk.CTkLabel(sf, text="",
                               font=ctk.CTkFont(size=12), text_color="#536471")
    stats_lbl.pack(pady=(0,10))

    uf = ctk.CTkFrame(root, fg_color="#16181c", corner_radius=12)
    uf.pack(fill="x", padx=20, pady=4)
    ctk.CTkLabel(uf, text="آدرس‌های دسترسی:",
                 font=ctk.CTkFont(size=12), text_color="#71767b").pack(anchor="w", padx=16, pady=(10,4))

    def _url_row(parent, label, url):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=3)
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=13),
                     text_color="#71767b", width=60).pack(side="left")
        ctk.CTkButton(row, text=url, font=ctk.CTkFont(size=13),
                      fg_color="transparent", text_color="#1d9bf0",
                      hover_color="#0d1f2d", anchor="w",
                      command=lambda u=url: webbrowser.open(u)).pack(side="left", fill="x")

    _url_row(uf, "محلی:", LOCAL_URL)
    _url_row(uf, "شبکه:", NET_URL)
    ctk.CTkLabel(uf, text="هر کسی در همین مودم می‌تونه آدرس شبکه رو باز کنه",
                 font=ctk.CTkFont(size=11), text_color="#536471").pack(pady=(4,10))

    bf = ctk.CTkFrame(root, fg_color="transparent")
    bf.pack(fill="x", padx=20, pady=6)

    open_btn = ctk.CTkButton(bf,
        text="🌐  باز کردن در مرورگر",
        font=ctk.CTkFont(size=15, weight="bold"),
        height=50, corner_radius=9999,
        fg_color="#1d9bf0", hover_color="#1a8cd8",
        command=lambda: webbrowser.open(LOCAL_URL),
        state="disabled")
    open_btn.pack(fill="x", pady=4)

    def _refresh():
        refresh_btn.configure(text="در حال به‌روزرسانی...", state="disabled")
        def _run():
            try:
                import urllib.request
                urllib.request.urlopen(
                    urllib.request.Request(f"{LOCAL_URL}/api/fetch_all",
                                           method="POST", data=b""),
                    timeout=60)
            except: pass
            root.after(0, lambda: refresh_btn.configure(
                text="↻  به‌روزرسانی پست‌ها", state="normal"))
        threading.Thread(target=_run, daemon=True).start()

    refresh_btn = ctk.CTkButton(bf,
        text="↻  به‌روزرسانی پست‌ها",
        font=ctk.CTkFont(size=14), height=44, corner_radius=9999,
        fg_color="#16181c", hover_color="#1e2124",
        border_width=1, border_color="#2f3336",
        command=_refresh)
    refresh_btn.pack(fill="x", pady=3)

    def _offline():
        try:
            import offline
            threading.Thread(target=offline.run_gui, daemon=True).start()
        except Exception as e:
            status_lbl.configure(text=f"خطا: {e}", text_color="#f4212e")

    offline_btn = ctk.CTkButton(bf,
        text="📦  ساخت فایل آفلاین .html",
        font=ctk.CTkFont(size=14), height=44, corner_radius=9999,
        fg_color="#16181c", hover_color="#1e2124",
        border_width=1, border_color="#2f3336",
        command=_offline)
    offline_btn.pack(fill="x", pady=3)

    exit_btn = ctk.CTkButton(bf,
        text="✕  خروج",
        font=ctk.CTkFont(size=14), height=40, corner_radius=9999,
        fg_color="transparent", hover_color="#1a0000",
        border_width=1, border_color="#f4212e", text_color="#f4212e",
        command=lambda: (root.destroy(), os._exit(0)))
    exit_btn.pack(fill="x", pady=(8,0))

    def _start_server():
        from app import start as flask_start
        flask_start(host="0.0.0.0", port=PORT)

    threading.Thread(target=_start_server, daemon=True).start()

    def _check(n=0):
        if n > 30:
            status_lbl.configure(text="✗ سرور راه‌اندازی نشد", text_color="#f4212e")
            return
        try:
            import urllib.request
            urllib.request.urlopen(f"{LOCAL_URL}/api/status", timeout=1)
            status_lbl.configure(text="✓ سرور در حال اجراست", text_color="#00ba7c")
            open_btn.configure(state="normal")
            root.after(800, lambda: webbrowser.open(LOCAL_URL))
            _poll()
        except:
            root.after(400, lambda: _check(n+1))

    def _poll():
        try:
            import urllib.request, json
            d = json.loads(
                urllib.request.urlopen(f"{LOCAL_URL}/api/status", timeout=2).read())
            stats_lbl.configure(
                text=f"کل پست: {d.get('total',0)}   |   آخرین sync: {d.get('last','—')}")
        except: pass
        root.after(15000, _poll)

    root.after(600, _check)
    root.mainloop()


if __name__ == "__main__":
    try:
        import customtkinter
        run_gui()
    except ImportError:
        run_headless()
