import base64
import os
import requests
import webview
from dotenv import load_dotenv

# Load credentials from .env file (never commit .env to git)
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID   = os.getenv("CHAT_ID", "")


class Api:
    """Python bridge exposed to JavaScript inside the desktop app."""

    def send_opening_ping(self):
        """Notifies your Telegram when the app is opened."""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": "❤️ She just opened Our Memories!"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass

    def get_gallery_photos(self):
        """Fetches all photos sent in the Telegram chat."""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"limit": 100, "allowed_updates": ["message"]}
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
            return image_urls[::-1]
        except Exception:
            return []

    def upload_photo_b64(self, base64_str):
        """Receives a base64-encoded image from the UI and uploads it to Telegram."""
        try:
            header, encoded = base64_str.split(",", 1)
            image_data = base64.b64decode(encoded)
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files = {"photo": ("memory.jpg", image_data, "image/jpeg")}
            data = {"chat_id": CHAT_ID, "caption": "📸 She shared a new memory with you!"}
            requests.post(url, data=data, files=files, timeout=15)
            return True
        except Exception:
            return False


HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Our Memories</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0f0a0c; --surface: #1a1015; --card: #22151a;
      --rose: #e8587a; --rose-dim: #c0426a; --gold: #f5c2c7;
      --text: #f0dde3; --muted: #8a6f76; --radius: 14px;
      --shadow: 0 8px 32px rgba(232,88,122,.18);
    }
    html, body { height: 100%; background: var(--bg); color: var(--text);
      font-family: 'Inter', system-ui, sans-serif; overflow: hidden; }

    .shell { display: flex; flex-direction: column; height: 100vh;
      padding: 24px 20px 16px; gap: 16px; }

    header { text-align: center; flex-shrink: 0; }
    header h1 { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 600;
      background: linear-gradient(135deg, #f5c2c7 0%, #e8587a 60%, #b5435e 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text; line-height: 1.1; }
    header p { font-size: .78rem; color: var(--muted); letter-spacing: .08em;
      margin-top: 4px; font-style: italic; }
    .hearts { display: flex; justify-content: center; gap: 10px; margin-top: 8px; }
    .hearts span { font-size: .9rem; animation: pulse 2s ease-in-out infinite; }
    .hearts span:nth-child(2) { animation-delay: .4s; }
    .hearts span:nth-child(3) { animation-delay: .8s; }
    @keyframes pulse { 0%,100% { transform: scale(1); opacity: .7; } 50% { transform: scale(1.35); opacity: 1; } }

    .upload-zone { flex-shrink: 0; border: 2px dashed #5a2d3a; border-radius: var(--radius);
      background: var(--surface); padding: 18px 12px; text-align: center; cursor: pointer;
      transition: border-color .25s, background .25s, transform .15s; position: relative; overflow: hidden; }
    .upload-zone::before { content: ''; position: absolute; inset: 0;
      background: radial-gradient(circle at 50% 0%, rgba(232,88,122,.12) 0%, transparent 70%);
      pointer-events: none; }
    .upload-zone:hover { border-color: var(--rose); background: #211219; transform: translateY(-1px); }
    .upload-icon { font-size: 1.6rem; margin-bottom: 4px; }
    .upload-label { font-size: .82rem; color: var(--gold); font-weight: 500; letter-spacing: .03em; }
    .upload-hint { font-size: .72rem; color: var(--muted); margin-top: 3px; }
    .progress-bar { height: 3px; background: linear-gradient(90deg, var(--rose), var(--gold));
      border-radius: 2px; margin-top: 10px; width: 0%; transition: width .4s ease; display: none; }

    .gallery-header { display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
    .gallery-title { font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
    .refresh-btn { background: none; border: 1px solid #3a2028; color: var(--muted); font-size: .72rem;
      padding: 4px 10px; border-radius: 20px; cursor: pointer; transition: color .2s, border-color .2s; }
    .refresh-btn:hover { color: var(--rose); border-color: var(--rose); }

    .gallery { flex: 1; overflow-y: auto; display: grid;
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
      gap: 8px; padding-right: 4px; align-content: start; }
    .gallery::-webkit-scrollbar { width: 4px; }
    .gallery::-webkit-scrollbar-track { background: transparent; }
    .gallery::-webkit-scrollbar-thumb { background: #3a2028; border-radius: 2px; }
    .gallery::-webkit-scrollbar-thumb:hover { background: var(--rose-dim); }

    .thumb { aspect-ratio: 1; border-radius: 10px; overflow: hidden; position: relative;
      cursor: pointer; background: var(--card); box-shadow: 0 4px 12px rgba(0,0,0,.4);
      transition: transform .2s, box-shadow .2s; }
    .thumb:hover { transform: scale(1.04); box-shadow: var(--shadow); }
    .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; transition: opacity .3s; }
    .thumb img.loading { opacity: 0; }

    .state-msg { grid-column: 1 / -1; text-align: center; padding: 40px 20px;
      color: var(--muted); font-size: .82rem; }
    .state-msg .icon { font-size: 2rem; display: block; margin-bottom: 8px; }

    .lightbox { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.88);
      backdrop-filter: blur(6px); z-index: 100; align-items: center; justify-content: center; }
    .lightbox.open { display: flex; animation: fadeIn .2s ease; }
    .lightbox img { max-width: 90vw; max-height: 90vh; border-radius: 12px;
      box-shadow: 0 24px 64px rgba(0,0,0,.8); }
    .lightbox-close { position: absolute; top: 16px; right: 20px; font-size: 1.6rem;
      cursor: pointer; color: #fff; opacity: .7; transition: opacity .2s; }
    .lightbox-close:hover { opacity: 1; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    .toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%) translateY(80px);
      background: var(--card); border: 1px solid #3a2028; color: var(--text); font-size: .8rem;
      padding: 10px 20px; border-radius: 24px; box-shadow: var(--shadow);
      transition: transform .3s ease, opacity .3s ease; opacity: 0; z-index: 200; white-space: nowrap; }
    .toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }
  </style>
</head>
<body>
<div class="shell">
  <header>
    <h1>Our Memories 💕</h1>
    <p>Thinking of you, always</p>
    <div class="hearts"><span>🌸</span><span>❤️</span><span>🌸</span></div>
  </header>

  <div class="upload-zone" id="uploadZone"
       onclick="document.getElementById('fileInput').click()"
       ondragover="onDragOver(event)" ondrop="onDrop(event)">
    <input type="file" id="fileInput" accept="image/*" style="display:none"
           onchange="handleFile(this.files[0])">
    <div class="upload-icon">📷</div>
    <div class="upload-label">Click or drag a photo here</div>
    <div class="upload-hint">Sends directly to your Telegram</div>
    <div class="progress-bar" id="progressBar"></div>
  </div>

  <div class="gallery-header">
    <span class="gallery-title">Our photo wall</span>
    <button class="refresh-btn" onclick="loadGallery()">↻ Refresh</button>
  </div>

  <div class="gallery" id="gallery">
    <div class="state-msg"><span class="icon">🌷</span>Loading memories…</div>
  </div>
</div>

<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <span class="lightbox-close" onclick="closeLightbox()">✕</span>
  <img id="lightboxImg" src="" alt="Memory">
</div>
<div class="toast" id="toast"></div>

<script>
  function showToast(msg, duration) {
    duration = duration || 2800;
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(function(){ t.classList.remove('show'); }, duration);
  }
  function openLightbox(src) {
    document.getElementById('lightboxImg').src = src;
    document.getElementById('lightbox').classList.add('open');
  }
  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('open');
  }
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeLightbox(); });

  function loadGallery() {
    var gallery = document.getElementById('gallery');
    gallery.innerHTML = '<div class="state-msg"><span class="icon">⏳</span>Fetching memories…</div>';
    pywebview.api.get_gallery_photos().then(function(urls) {
      if (!urls || urls.length === 0) {
        gallery.innerHTML = '<div class="state-msg"><span class="icon">🌷</span>No photos yet — share the first one!</div>';
        return;
      }
      gallery.innerHTML = urls.map(function(url) {
        return '<div class="thumb" onclick="openLightbox(\'' + url + '\')">' +
               '<img src="' + url + '" class="loading" onload="this.classList.remove(\'loading\')" alt="Memory">' +
               '</div>';
      }).join('');
    }).catch(function() {
      gallery.innerHTML = '<div class="state-msg"><span class="icon">📡</span>Could not load — check your connection.</div>';
    });
  }

  function onDragOver(e) { e.preventDefault(); }
  function onDrop(e) {
    e.preventDefault();
    var file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) handleFile(file);
  }

  function handleFile(file) {
    if (!file) return;
    var bar = document.getElementById('progressBar');
    bar.style.display = 'block';
    bar.style.width = '30%';
    var reader = new FileReader();
    reader.onload = function(e) {
      bar.style.width = '60%';
      pywebview.api.upload_photo_b64(e.target.result).then(function(success) {
        bar.style.width = '100%';
        setTimeout(function(){ bar.style.display = 'none'; bar.style.width = '0%'; }, 600);
        if (success) {
          showToast('📸 Memory sent! ❤️');
          setTimeout(loadGallery, 1200);
        } else {
          showToast('❌ Upload failed — try again.');
        }
        document.getElementById('fileInput').value = '';
      });
    };
    reader.readAsDataURL(file);
  }

  window.addEventListener('pywebviewready', function() {
    pywebview.api.send_opening_ping();
    loadGallery();
  });
</script>
</body>
</html>"""


if __name__ == "__main__":
    api = Api()
    webview.create_window(
        title="Our Memories 💕",
        html=HTML_CONTENT,
        width=520,
        height=680,
        resizable=True,
        js_api=api,
        background_color="#0f0a0c",
    )
    webview.start()
