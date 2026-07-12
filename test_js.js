
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
        return '<div class="thumb" onclick="openLightbox(\'' + url + '\')">'
             + '<img src="' + url + '" class="loading" onload="this.classList.remove(\'loading\')" alt="Memory">'
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
    bar.style.display = 'block'; bar.style.width = '15%';
    
    var reader = new FileReader();
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
        
        pywebview.api.upload_photo_b64(compressedB64).then(function(ok){
          bar.style.width = '100%';
          setTimeout(function(){ bar.style.display='none'; bar.style.width='0%'; }, 700);
          if(ok){
            showToast('&#x2764;&#xfe0f;', "Memory saved &#x2014; she'll love it!");
            setTimeout(loadGallery, 1400);
          } else {
            showToast('&#x26a0;&#xfe0f;', "Couldn't save &#x2014; please try again.");
          }
          document.getElementById('fileInput').value = '';
        });
      };
      img.src = ev.target.result;
    };
    reader.readAsDataURL(file);
  }

  window.addEventListener('pywebviewready', function(){
    loadGallery();
  });
