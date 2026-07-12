
  function showToast(icon, msg, dur) {
    dur = dur || 3000;
    var t = document.getElementById('toast');
    t.innerHTML = '<span>' + icon + '</span><span>' + msg + '</span>';
    t.classList.add('show');
    setTimeout(function(){ t.classList.remove('show'); }, dur);
  }

  function openLightbox(src, type, name) {
    var lb = document.getElementById('lightbox');
    var content = document.getElementById('lightboxContent');
    if (type === 'video') {
      content.innerHTML = '<video controls autoplay src="' + src + '" style="max-width:90vw; max-height:80vh; border-radius:14px; box-shadow: 0 28px 80px rgba(0,0,0,.85);"></video>';
    } else {
      content.innerHTML = '<img src="' + src + '" alt="Memory" style="max-width:90vw; max-height:80vh; border-radius:14px; box-shadow: 0 28px 80px rgba(0,0,0,.85);">';
    }
    
    var delBtn = document.createElement('div');
    delBtn.className = 'lb-delete';
    delBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';
    delBtn.onclick = function(e) {
      e.stopPropagation();
      if (confirm("Are you sure you want to let this memory go? \ud83d\udc94")) {
        pywebview.api.delete_memory(name).then(function(ok) {
          if (ok) {
            closeLightbox();
            loadGallery();
            showToast('&#x2728;', "Memory cleared.");
          } else {
            showToast('&#x26a0;&#xfe0f;', "Couldn\'t clear memory.");
          }
        });
      }
    };
    content.appendChild(delBtn);
    lb.classList.add('open');
  }

  function closeLightbox() {
    var lb = document.getElementById('lightbox');
    lb.classList.remove('open');
    document.getElementById('lightboxContent').innerHTML = '';
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

  var quotes = [
    "Every moment with you is a treasure \ud83d\udc95",
    "I love you more today than yesterday, but not as much as tomorrow \u2764\ufe0f",
    "You are my favorite notification \ud83d\udcf1",
    "Thinking of you keeps me awake, dreaming of you keeps me asleep \ud83d\udca4",
    "I wish I could turn back the clock to find you sooner \u23f3",
    "You are the best part of my day \ud83c\udf1e",
    "My heart skips a beat when I see your name \ud83d\udc93"
  ];

  function loadGallery() {
    var g = document.getElementById('gallery');
    var randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
    
    g.innerHTML = '<div class="state-msg"><div class="heartbeat">&#x2764;&#xfe0f;</div><span>Gathering our beautiful moments&#8230;</span></div>';
    
    pywebview.api.get_gallery_photos().then(function(items) {
      if (!items || items.length === 0) {
        g.innerHTML = '<div class="state-msg">' + galleryIcon(32) + '<span>No memories yet &#8212; be the first to share one &#x1f338;</span><br><span style="color:var(--rose-dim);font-style:italic;">"' + randomQuote + '"</span></div>';
        return;
      }
      g.innerHTML = items.map(function(item){
        var el = '';
        if (item.type === 'video') {
            el = '<div class="thumb" onclick="openLightbox(\'' + item.url + '\', \'video\', \'' + item.name + '\')">'
               + '<video src="' + item.url + '" class="loading" oncanplay="this.classList.remove(\'loading\')" muted loop playsinline></video>'
               + '<div class="play-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg></div>'
               + '</div>';
        } else {
            el = '<div class="thumb" onclick="openLightbox(\'' + item.url + '\', \'image\', \'' + item.name + '\')">'
               + '<img src="' + item.url + '" class="loading" onload="this.classList.remove(\'loading\')" alt="Memory">'
               + '</div>';
        }
        return el;
      }).join('');
      
      var thumbs = g.querySelectorAll('.thumb video');
      thumbs.forEach(function(vid) {
        vid.parentElement.addEventListener('mouseenter', function() { vid.play().catch(function(){}); });
        vid.parentElement.addEventListener('mouseleave', function() { vid.pause(); });
      });

    }).catch(function(){
      g.innerHTML = '<div class="state-msg">' + galleryIcon(28) + '<span>Couldn&#x2019;t connect &#x2014; check your connection &#x1f4e1;</span></div>';
    });
  }

  function onDragOver(e){ e.preventDefault(); }
  function onDrop(e){
    e.preventDefault();
    var f = e.dataTransfer.files[0];
    if(f && (f.type.startsWith('image/') || f.type.startsWith('video/'))) handleFile(f);
  }

  function handleFile(file){
    if(!file) return;
    
    if (file.size > 50 * 1024 * 1024) {
      showToast('&#x26a0;&#xfe0f;', "File is too large! Please choose a video under 50MB.");
      document.getElementById('fileInput').value = '';
      return;
    }

    var bar = document.getElementById('progressBar');
    bar.style.display = 'block'; bar.style.width = '15%';
    
    var isVideo = file.type.startsWith('video/');
    var reader = new FileReader();

    if (isVideo) {
      reader.onload = function(ev) {
         bar.style.width = '50%';
         var b64 = ev.target.result;
         pywebview.api.upload_media_b64(b64, true).then(function(ok){
           bar.style.width = '100%';
           setTimeout(function(){ bar.style.display='none'; bar.style.width='0%'; }, 700);
           if(ok){
             showToast('&#x2764;&#xfe0f;', "Video saved &#x2014; she\'ll love it!");
             setTimeout(loadGallery, 1400);
           } else {
             showToast('&#x26a0;&#xfe0f;', "Couldn\'t save video &#x2014; please try again.");
           }
           document.getElementById('fileInput').value = '';
         });
      };
      reader.readAsDataURL(file);
    } else {
      reader.onload = function(ev){
        var img = new Image();
        img.onload = function() {
          var canvas = document.createElement('canvas');
          var ctx = canvas.getContext('2d');
          var maxW = 1600, maxH = 1600;
          var w = img.width, h = img.height;
          if (w > maxW || h > maxH) {
            if (w > h) { h = h * (maxW / w); w = maxW; }
            else       { w = w * (maxH / h); h = maxH; }
          }
          canvas.width = w; canvas.height = h;
          ctx.drawImage(img, 0, 0, w, h);
          
          var compressedB64 = canvas.toDataURL('image/jpeg', 0.85);
          bar.style.width = '50%';
          
          pywebview.api.upload_media_b64(compressedB64, false).then(function(ok){
            bar.style.width = '100%';
            setTimeout(function(){ bar.style.display='none'; bar.style.width='0%'; }, 700);
            if(ok){
              showToast('&#x2764;&#xfe0f;', "Memory saved &#x2014; she\'ll love it!");
              setTimeout(loadGallery, 1400);
            } else {
              showToast('&#x26a0;&#xfe0f;', "Couldn\'t save &#x2014; please try again.");
            }
            document.getElementById('fileInput').value = '';
          });
        };
        img.src = ev.target.result;
      };
      reader.readAsDataURL(file);
    }
  }

  window.addEventListener('pywebviewready', function(){
    loadGallery();
  });
