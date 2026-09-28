$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding $false
$htmlPath = "static\index.html"
$routesPath = "api\routes.py"

# ---------- 0. Backups ----------
Copy-Item $htmlPath "static\index.backup.html" -Force
Copy-Item $routesPath "api\routes.backup.py" -Force

# ---------- 1. Background image (rotate the sideways photo) ----------
if (-not (Test-Path "static\bg.jpg")) {
    $ready = "$HOME\Downloads\bg.jpg"
    $orig  = "$HOME\Downloads\download (3).jpeg"   # change if your file name differs
    if (Test-Path $ready) {
        Copy-Item $ready "static\bg.jpg"
    } elseif (Test-Path $orig) {
        Add-Type -AssemblyName System.Drawing
        $img = [System.Drawing.Image]::FromFile($orig)
        $img.RotateFlip([System.Drawing.RotateFlipType]::Rotate270FlipNone)
        $img.Save("$PWD\static\bg.jpg", [System.Drawing.Imaging.ImageFormat]::Jpeg)
        $img.Dispose()
    } else {
        Write-Host "No image found. Put bg.jpg in static\ yourself." -ForegroundColor Yellow
    }
}

# ---------- 2. Flask: /media route ----------
$py = [IO.File]::ReadAllText($routesPath)
if ($py -notmatch '/media/') {
    $marker = 'return send_from_directory(STATIC_DIR, "index.html")'
    $add = @'

    @app.route("/media/<path:name>")
    def media(name):
        return send_from_directory(STATIC_DIR, name)
'@
    $py = $py.Replace($marker, $marker + "`n" + $add)
    [IO.File]::WriteAllText($routesPath, $py, $utf8)
}

# ---------- 3. Frontend ----------
$html = [IO.File]::ReadAllText($htmlPath)

if ($html -notmatch 'id="scene"') {

$css = @'
/* ---------- PHOTO BACKGROUND ---------- */
#scene{
  position:fixed;inset:0;z-index:0;pointer-events:none;will-change:transform;
  background:
    linear-gradient(180deg,rgba(20,8,10,.35) 0%,rgba(20,8,10,.62) 45%,rgba(12,8,14,.88) 100%),
    url('/media/bg.jpg') center 30%/cover no-repeat;
  transform:scale(1.08);
}
/* ---------- SAILING SHIP ---------- */
#route{
  position:fixed;top:0;right:calc(clamp(6px,2vw,26px) + 30px);height:0;
  border-left:2px dashed rgba(243,217,139,.6);z-index:49;pointer-events:none;
  filter:drop-shadow(0 0 4px rgba(224,179,74,.6));
}
#voyager{position:fixed;top:0;right:clamp(6px,2vw,26px);width:62px;z-index:50;pointer-events:none;will-change:transform}
#voyager svg{display:block;width:100%;height:auto;overflow:visible;transform-origin:50% 40%;
  animation:sway 5s ease-in-out infinite;filter:drop-shadow(0 8px 10px rgba(0,0,0,.6))}
@keyframes sway{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(5deg)}}
#isle{position:absolute;right:calc(100% + 8px);top:38%;white-space:nowrap;padding:5px 12px;border-radius:8px;
  background:linear-gradient(170deg,#e8d5a9,#cdb27b);color:#3a2a12;border:1px solid #8e6f3c;
  box-shadow:0 8px 20px -8px rgba(0,0,0,.8);font-family:var(--f-pirate);font-size:.95rem;letter-spacing:.03em}
#isle.pop{animation:isle .5s cubic-bezier(.2,1.4,.4,1)}
@keyframes isle{from{opacity:.2;transform:translateX(14px) scale(.9)}to{opacity:1;transform:none}}
@media(max-width:640px){#voyager{width:44px}#route{right:calc(clamp(6px,2vw,26px) + 21px)}#isle{display:none}}
/* ---------- GRAND LINE RANKS ---------- */
.ranks{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:16px}
.rank{padding:18px}
.rank h3{font-family:var(--f-pirate);font-size:1.35rem;margin:10px 0 6px;color:var(--gold-2);letter-spacing:.03em}
.rank p{margin:0;font-family:var(--f-serif);font-size:1rem;line-height:1.5;color:#cbb894}
'@

$scene = @'
<div id="scene" aria-hidden="true"></div>
<div id="route" aria-hidden="true"></div>
<div id="voyager" aria-hidden="true">
  <div id="isle"><b>Foosha Village</b></div>
  <svg viewBox="0 0 64 120">
    <path d="M20 10 4 -34M44 10 60 -34" stroke="#fff" stroke-opacity=".45" stroke-width="2.4" stroke-linecap="round" fill="none"/>
    <path d="M32 118C10 96 6 44 12 14Q32 4 52 14C58 44 54 96 32 118Z" fill="#2a1508" stroke="url(#gGold)" stroke-width="2.4"/>
    <path d="M32 108C16 90 13 46 18 20Q32 12 46 20C51 46 48 90 32 108Z" fill="#8a5a2b"/>
    <path d="M32 24v78" stroke="#5b3410" stroke-width="1.4"/>
    <path d="M6 36Q32 50 58 36V44Q32 58 6 44Z" fill="#f4ead6"/>
    <path d="M10 68Q32 80 54 68V75Q32 87 10 75Z" fill="#f4ead6"/>
    <circle cx="32" cy="41" r="3" fill="#b2332c"/>
    <circle cx="32" cy="72" r="3" fill="#5b3410"/>
    <use href="#i-roger" x="33" y="0" width="16" height="16" style="color:#f4ead6"/>
    <circle cx="32" cy="112" r="5" fill="url(#gGoldV)"/>
  </svg>
</div>
'@

$ranks = @'
<section>
  <div class="wrap">
    <div class="sec-head">
      <div>
        <p class="eyebrow">Who Sits Where</p>
        <h2 class="h-sec goldtext">Ranks of the Grand Line</h2>
        <p class="sub">Every guest sails under a standing. Each one gets a different table.</p>
      </div>
    </div>
    <div class="ranks">
      <div class="card rank"><span class="tier t-yonko">Yonko</span><h3>Emperors of the Sea</h3><p>One of the four rulers of the New World. Their table is always reserved.</p></div>
      <div class="card rank"><span class="tier t-warlord">Warlord</span><h3>Shichibukai</h3><p>Pirates licensed by the World Government. Their seat comes with a treaty.</p></div>
      <div class="card rank"><span class="tier t-captain">Supernova</span><h3>The Worst Generation</h3><p>Rookie captains with bounties over &#3647;100,000,000. Loud, fast, and hungry.</p></div>
      <div class="card rank"><span class="tier t-crew">Marine</span><h3>Justice, Guest List Edition</h3><p>Admirals and vice admirals of Marine HQ. They check every name twice.</p></div>
      <div class="card rank"><span class="tier t-warlord">Revolutionary</span><h3>Dragon's Army</h3><p>They arrive quietly and leave quietly. Nobody sees the seat move.</p></div>
      <div class="card rank"><span class="tier t-noble">World Noble</span><h3>Celestial Dragons</h3><p>Always seated first. Never sent to the waitlist.</p></div>
    </div>
  </div>
</section>

'@

$js = @'
/* ---------- SHIP SAILS DOWN AS YOU SCROLL ---------- */
(function voyage(){
  const ship=$('#voyager'), route=$('#route'), isle=$('#isle'), label=$('#isle b'), scene=$('#scene');
  const stops=[[0,'Foosha Village'],[.10,'Loguetown'],[.20,'Reverse Mountain'],[.32,'Water 7'],
    [.44,'Sabaody Archipelago'],[.56,'Marineford'],[.68,'Fish-Man Island'],[.80,'Wano Country'],
    [.93,'Laugh Tale \u2715']];
  let queued=false, last='';
  function update(){
    queued=false;
    const max=document.documentElement.scrollHeight-innerHeight;
    const p=max>0 ? Math.min(1,Math.max(0,scrollY/max)) : 0;
    const top=68, bottom=innerHeight-ship.offsetHeight-16;
    const y=top+p*Math.max(0,bottom-top);
    ship.style.transform='translateY('+y+'px)';
    route.style.height=(y+8)+'px';
    if(!RM) scene.style.transform='translate3d(0,'+(-p*46)+'px,0) scale(1.08)';
    let name=stops[0][1]; stops.forEach(s=>{ if(p>=s[0]) name=s[1]; });
    if(name!==last){ last=name; label.textContent=name; isle.classList.remove('pop'); void isle.offsetWidth; isle.classList.add('pop'); }
  }
  const req=()=>{ if(!queued){ queued=true; requestAnimationFrame(update); } };
  addEventListener('scroll',req,{passive:true});
  addEventListener('resize',req);
  update();
})();

'@

    # body background -> plain colour (the photo layer replaces it)
    $html = [regex]::Replace($html, '(?s)background:\s*radial-gradient\(1200px.*?background-attachment:fixed;', 'background:#0b0608;')
    # CSS
    $html = $html.Replace('</style>', $css + "`n</style>")
    # scene + ship right after <body>
    $html = $html.Replace('<body>', "<body>`n" + $scene)
    # hero copy
    $html = $html.Replace('<p class="eyebrow">Entertainment City &middot; Registry of the Chosen</p>', '<p class="eyebrow">Grand Line &middot; Entertainment City</p>')
    $html = $html.Replace('Entertainment City · Registry of the Chosen', 'Grand Line · Entertainment City')
    $html = [regex]::Replace($html, '(?s)<p class="tagline">.*?</p>', '<p class="tagline">Somewhere between Sabaody and the New World floats a city of pure gold. Gild Tesoro keeps the guest list. Fill your seat before the Den Den Mushi rings for the next name on deck.</p>')
    # ranks section before the Marijoa section
    $html = $html.Replace('<!-- ============ MARIJOA / COUNCIL PANEL ============ -->', $ranks + '<!-- ============ MARIJOA / COUNCIL PANEL ============ -->')
    # scroll-ship JS
    $html = $html.Replace('/* ---------- go ---------- */', $js + '/* ---------- go ---------- */')
    # real backend errors instead of fake demo events
    $html = $html.Replace('MOCK_WHEN_OFFLINE: true,', 'MOCK_WHEN_OFFLINE: false,')

    [IO.File]::WriteAllText($htmlPath, $html, $utf8)
    Write-Host "Done. Frontend patched." -ForegroundColor Green
} else {
    Write-Host "Already patched. Nothing to do." -ForegroundColor Yellow
}