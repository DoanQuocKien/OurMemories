import base64
import os
import sys
import traceback
from pathlib import Path
import requests
import webview
from dotenv import load_dotenv

# Resolve the directory that contains (or should contain) .env.
# When frozen by PyInstaller, sys.executable is the .exe path — look there.
# When running as a plain script, look next to app.py.
if getattr(sys, "frozen", False):
    _BASE = Path(sys.executable).parent   # dist/ folder, next to the .exe
else:
    _BASE = Path(__file__).parent         # project folder, next to app.py

_ENV_PATH = _BASE / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID   = os.getenv("CHAT_ID", "")

if not BOT_TOKEN or not CHAT_ID:
    print(f"[WARN] .env not found or empty at: {_ENV_PATH}")
else:
    print(f"[OK] Credentials loaded from: {_ENV_PATH}")


class Api:
    """Python bridge exposed to JavaScript inside the desktop app."""

    def send_opening_ping(self):
        """Notifies you silently when Tho opens the app."""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        # Safe ASCII-only text avoids any encoding issues on Windows
        payload = {"chat_id": CHAT_ID, "text": "She just opened Our Memories! <3"}
        try:
            r = requests.post(url, json=payload, timeout=5)
            print("[ping] status:", r.status_code, r.json().get("ok"))
        except Exception:
            traceback.print_exc()

    def get_gallery_photos(self):
        """Fetches all photos stored in the cloud."""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        # allowed_updates left out so ALL message types are returned
        params = {"limit": 100}
        try:
            resp = requests.get(url, params=params, timeout=10).json()
            image_urls = []
            for result in resp.get("result", []):
                msg = result.get("message", {})
                if "photo" in msg:
                    file_id = msg["photo"][-1]["file_id"]
                    file_info = requests.get(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                        params={"file_id": file_id},
                        timeout=10,
                    ).json()
                    file_path = file_info.get("result", {}).get("file_path")
                    if file_path:
                        image_urls.append(
                            f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                        )
            print(f"[gallery] found {len(image_urls)} photos")
            return image_urls[::-1]
        except Exception:
            traceback.print_exc()
            return []

    def upload_photo_b64(self, base64_str):
        """Receives a base64 image from the UI and saves it to the cloud."""
        try:
            header, encoded = base64_str.split(",", 1)
            image_data = base64.b64decode(encoded)
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files = {"photo": ("memory.jpg", image_data, "image/jpeg")}
            # Caption uses only plain ASCII/unicode — NO surrogate-pair emoji
            data = {"chat_id": CHAT_ID, "caption": "Tho shared a new memory! <3"}
            r = requests.post(url, data=data, files=files, timeout=15)
            print("[upload] status:", r.status_code, r.json().get("ok"))
            return r.json().get("ok", False)
        except Exception:
            traceback.print_exc()
            return False


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Tho &amp; Em</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,500&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:       #0c080a;
      --surface:  #170e12;
      --card:     #201318;
      --border:   #3d1f28;
      --rose:     #e8587a;
      --rose-dim: #b8395a;
      --blush:    #f5c2c7;
      --text:     #f2e0e4;
      --muted:    #7a6068;
      --radius:   16px;
      --glow:     0 0 32px rgba(232,88,122,.22);
      --shadow:   0 8px 28px rgba(0,0,0,.55);
    }

    html, body {
      height: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', system-ui, sans-serif;
      font-size: 14px;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }

    .shell {
      display: flex;
      flex-direction: column;
      height: 100vh;
      padding: 22px 18px 14px;
      gap: 14px;
    }

    /* Header */
    header { text-align: center; flex-shrink: 0; user-select: none; }

    .logo-ring {
      width: 54px; height: 54px;
      margin: 0 auto 10px;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, #3d1420, #1a0b10);
      border: 1.5px solid #5a2535;
      display: flex; align-items: center; justify-content: center;
      box-shadow: var(--glow);
      animation: floatRing 4s ease-in-out infinite;
    }
    .logo-ring svg { color: var(--rose); }
    @keyframes floatRing {
      0%,100% { transform: translateY(0); box-shadow: var(--glow); }
      50%      { transform: translateY(-5px); box-shadow: 0 0 52px rgba(232,88,122,.38); }
    }

    header h1 {
      font-family: 'Playfair Display', serif;
      font-size: 1.85rem;
      font-weight: 600;
      background: linear-gradient(135deg, #f5c2c7 0%, #e8587a 55%, #a8304f 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      line-height: 1.15;
      letter-spacing: -.01em;
    }
    .tagline {
      font-size: .72rem;
      color: var(--muted);
      letter-spacing: .12em;
      text-transform: uppercase;
      margin-top: 5px;
      font-style: italic;
    }

    .petals { display: flex; justify-content: center; gap: 14px; margin-top: 10px; }
    .petal  { font-size: 1rem; animation: petalPulse 2.4s ease-in-out infinite; }
    .petal:nth-child(1) { animation-delay: 0s; }
    .petal:nth-child(2) { animation-delay: .5s; }
    .petal:nth-child(3) { animation-delay: 1s; }
    @keyframes petalPulse {
      0%,100% { transform: scale(1) rotate(-4deg); opacity: .7; }
      50%      { transform: scale(1.35) rotate(4deg); opacity: 1; }
    }

    /* Upload zone */
    .upload-zone {
      flex-shrink: 0;
      border: 1.5px dashed var(--border);
      border-radius: var(--radius);
      background: var(--surface);
      padding: 16px 14px;
      text-align: center;
      cursor: pointer;
      transition: border-color .25s, background .25s, transform .18s, box-shadow .25s;
      position: relative;
      overflow: hidden;
    }
    .upload-zone::after {
      content: '';
      position: absolute; inset: 0;
      background: radial-gradient(ellipse at 50% -10%, rgba(232,88,122,.14) 0%, transparent 65%);
      pointer-events: none;
    }
    .upload-zone:hover {
      border-color: var(--rose);
      background: #1c1014;
      transform: translateY(-2px);
      box-shadow: var(--glow);
    }

    .upload-icon-wrap {
      width: 40px; height: 40px;
      border-radius: 50%;
      background: rgba(232,88,122,.12);
      display: flex; align-items: center; justify-content: center;
      margin: 0 auto 9px;
      transition: background .25s;
    }
    .upload-zone:hover .upload-icon-wrap { background: rgba(232,88,122,.24); }
    .upload-icon-wrap svg { color: var(--rose); }

    .upload-label { font-size: .83rem; color: var(--blush); font-weight: 500; letter-spacing: .02em; }
    .upload-hint  { font-size: .7rem;  color: var(--muted); margin-top: 3px; }

    .progress-bar {
      height: 2px;
      background: linear-gradient(90deg, var(--rose), var(--blush));
      border-radius: 2px;
      margin-top: 10px;
      width: 0%;
      transition: width .45s ease;
      display: none;
    }

    /* Gallery header */
    .gallery-header {
      display: flex; align-items: center; justify-content: space-between;
      flex-shrink: 0; padding: 0 2px;
    }
    .gallery-label {
      display: flex; align-items: center; gap: 6px;
      font-size: .68rem; letter-spacing: .14em;
      text-transform: uppercase; color: var(--muted);
    }
    .gallery-label svg { color: var(--rose); }

    .refresh-btn {
      display: flex; align-items: center; gap: 5px;
      background: none; border: 1px solid var(--border);
      color: var(--muted); font-size: .7rem; font-family: inherit;
      padding: 4px 12px; border-radius: 20px; cursor: pointer;
      transition: color .2s, border-color .2s, background .2s;
    }
    .refresh-btn:hover {
      color: var(--rose); border-color: var(--rose-dim);
      background: rgba(232,88,122,.07);
    }
    .refresh-btn svg { transition: transform .45s; }
    .refresh-btn:hover svg { transform: rotate(180deg); }

    /* Gallery grid */
    .gallery {
      flex: 1; overflow-y: auto;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(118px, 1fr));
      gap: 8px; padding-right: 4px; align-content: start;
    }
    .gallery::-webkit-scrollbar { width: 3px; }
    .gallery::-webkit-scrollbar-track { background: transparent; }
    .gallery::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
    .gallery::-webkit-scrollbar-thumb:hover { background: var(--rose-dim); }

    .thumb {
      aspect-ratio: 1; border-radius: 12px; overflow: hidden;
      position: relative; cursor: pointer; background: var(--card);
      box-shadow: var(--shadow); transition: transform .22s, box-shadow .22s;
    }
    .thumb::after {
      content: ''; position: absolute; inset: 0;
      background: linear-gradient(160deg, rgba(255,255,255,.04) 0%, transparent 60%);
      pointer-events: none;
    }
    .thumb:hover { transform: scale(1.045); box-shadow: var(--glow), var(--shadow); }
    .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; transition: opacity .35s; }
    .thumb img.loading { opacity: 0; }

    /* States */
    .state-msg {
      grid-column: 1 / -1;
      display: flex; flex-direction: column; align-items: center;
      gap: 10px; padding: 44px 24px; color: var(--muted); font-size: .8rem; line-height: 1.5;
    }
    .state-msg svg { opacity: .45; }

    /* Lightbox */
    .lightbox {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,.9); backdrop-filter: blur(8px);
      z-index: 100; align-items: center; justify-content: center;
    }
    .lightbox.open { display: flex; animation: fadeIn .22s ease; }
    .lightbox img { max-width: 90vw; max-height: 88vh; border-radius: 14px; box-shadow: 0 28px 80px rgba(0,0,0,.85); }
    .lb-close {
      position: absolute; top: 14px; right: 16px;
      width: 36px; height: 36px; border-radius: 50%;
      background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14);
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; color: #fff; opacity: .75;
      transition: opacity .2s, background .2s;
    }
    .lb-close:hover { opacity: 1; background: rgba(255,255,255,.18); }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    /* Toast */
    .toast {
      position: fixed; bottom: 18px; left: 50%;
      transform: translateX(-50%) translateY(60px);
      background: var(--card); border: 1px solid var(--border);
      color: var(--text); font-size: .79rem;
      padding: 9px 18px; border-radius: 24px; box-shadow: var(--glow);
      transition: transform .32s cubic-bezier(.34,1.56,.64,1), opacity .3s;
      opacity: 0; z-index: 200; white-space: nowrap;
      display: flex; align-items: center; gap: 7px;
    }
    .toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }
  </style>
</head>
<body>

<div class="shell">

  <header>
    <div class="logo-ring">
      <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="currentColor" stroke="none">
        <path d="M12 21.593c-.525-.445-4.52-3.89-6.71-6.02C3.19 13.49 2 11.7 2 9.5 2 6.462 4.462 4 7.5 4c1.74 0 3.41.81 4.5 2.088C13.09 4.81 14.76 4 16.5 4 19.538 4 22 6.462 22 9.5c0 2.2-1.19 3.99-3.29 6.073-2.19 2.13-6.185 5.575-6.71 6.02z"/>
      </svg>
    </div>
    <h1>Th\u01a1 &amp; Em &#x1f495;</h1>
    <p class="tagline">Every moment with you is a treasure</p>
    <div class="petals">
      <span class="petal">&#x1f338;</span>
      <span class="petal">&#x2764;&#xfe0f;</span>
      <span class="petal">&#x1f338;</span>
    </div>
  </header>

  <div class="upload-zone" id="uploadZone"
       onclick="document.getElementById('fileInput').click()"
       ondragover="onDragOver(event)" ondrop="onDrop(event)">
    <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="handleFile(this.files[0])">
    <div class="upload-icon-wrap">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
    </div>
    <div class="upload-label">Drop a memory here, or click to choose &#x1f338;</div>
    <div class="upload-hint">Every photo you share is a little love letter &#x1f48c;</div>
    <div class="progress-bar" id="progressBar"></div>
  </div>

  <div class="gallery-header">
    <div class="gallery-label">
      <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <polyline points="21 15 16 10 5 21"/>
      </svg>
      Our little world
    </div>
    <button class="refresh-btn" onclick="loadGallery()">
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 4 23 10 17 10"/>
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
      </svg>
      Refresh
    </button>
  </div>

  <div class="gallery" id="gallery">
    <div class="state-msg">
      <svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <polyline points="21 15 16 10 5 21"/>
      </svg>
      <span>Gathering your beautiful moments&#8230;</span>
    </div>
  </div>

</div>

<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <div class="lb-close" onclick="closeLightbox()">
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
         fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/>
      <line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  </div>
  <img id="lightboxImg" src="" alt="Memory" onclick="event.stopPropagation()">
</div>

<div class="toast" id="toast"></div>

<script>
  function showToast(icon, msg, dur) {
    dur = dur || 3000;
    var t = document.getElementById('toast');
    t.innerHTML = '<span>' + icon + '</span><span>' + msg + '</span>';
    t.classList.add('show');
    setTimeout(function(){ t.classList.remove('show'); }, dur);
  }

  function openLightbox(src) {
    document.getElementById('lightboxImg').src = src;
    document.getElementById('lightbox').classList.add('open');
  }
  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('open');
  }
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeLightbox(); });

  function galleryIcon(size) {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="'+size+'" height="'+size+'" viewBox="0 0 24 24"'
         + ' fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">'
         + '<rect x="3" y="3" width="18" height="18" rx="2"/>'
         + '<circle cx="8.5" cy="8.5" r="1.5"/>'
         + '<polyline points="21 15 16 10 5 21"/>'
         + '</svg>';
  }

  function loadGallery() {
    var g = document.getElementById('gallery');
    g.innerHTML = '<div class="state-msg">' + galleryIcon(28) + '<span>Gathering your beautiful moments&#8230;</span></div>';
    pywebview.api.get_gallery_photos().then(function(urls) {
      if (!urls || urls.length === 0) {
        g.innerHTML = '<div class="state-msg">' + galleryIcon(32) + '<span>No memories yet &#8212; be the first to share one &#x1f338;</span></div>';
        return;
      }
      g.innerHTML = urls.map(function(url){
        return '<div class="thumb" onclick="openLightbox(\\'' + url + '\\')">'
             + '<img src="' + url + '" class="loading" onload="this.classList.remove(\\'loading\\')" alt="Memory">'
             + '</div>';
      }).join('');
    }).catch(function(){
      g.innerHTML = '<div class="state-msg">' + galleryIcon(28) + '<span>Couldn&#x2019;t connect &#x2014; check your connection &#x1f4e1;</span></div>';
    });
  }

  function onDragOver(e){ e.preventDefault(); }
  function onDrop(e){
    e.preventDefault();
    var f = e.dataTransfer.files[0];
    if(f && f.type.startsWith('image/')) handleFile(f);
  }

  function handleFile(file){
    if(!file) return;
    var bar = document.getElementById('progressBar');
    bar.style.display = 'block'; bar.style.width = '25%';
    var reader = new FileReader();
    reader.onload = function(ev){
      bar.style.width = '65%';
      pywebview.api.upload_photo_b64(ev.target.result).then(function(ok){
        bar.style.width = '100%';
        setTimeout(function(){ bar.style.display='none'; bar.style.width='0%'; }, 700);
        if(ok){
          showToast('&#x2764;&#xfe0f;', 'Memory saved &#x2014; she\'ll love it!');
          setTimeout(loadGallery, 1400);
        } else {
          showToast('&#x26a0;&#xfe0f;', 'Couldn\'t save &#x2014; please try again.');
        }
        document.getElementById('fileInput').value = '';
      });
    };
    reader.readAsDataURL(file);
  }

  window.addEventListener('pywebviewready', function(){
    pywebview.api.send_opening_ping();
    loadGallery();
  });
</script>
</body>
</html>"""


if __name__ == "__main__":
    api = Api()
    webview.create_window(
        title="Tho & Em",
        html=HTML_CONTENT,
        width=520,
        height=690,
        resizable=True,
        js_api=api,
        background_color="#0c080a",
    )
    webview.start()