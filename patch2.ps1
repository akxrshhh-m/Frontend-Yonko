$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding $false
$p = "static\index.html"
$h = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)

if ($h -notmatch 'id="voyager"') { throw "Run patch.ps1 first." }
if ($h -match 'id="sea"') { Write-Host "Already patched." -ForegroundColor Yellow; exit }

Copy-Item $p "static\index.backup2.html" -Force

function Swap($text, $a, $b, $new) {
  $s = $text.IndexOf($a, [StringComparison]::Ordinal)
  if ($s -lt 0) { throw "Marker not found: $a" }
  $e = $text.IndexOf($b, $s, [StringComparison]::Ordinal)
  if ($e -lt 0) { throw "Marker not found: $b" }
  return $text.Substring(0, $s) + $new + $text.Substring($e)
}

# ================= CSS =================
$css = @'
/* ---------- SAILING SHIP + SEA ---------- */
:root{--vr:clamp(4px,1.2vw,18px)}
#sea{
  position:fixed;top:0;right:calc(var(--vr) + 6px);width:96px;height:0;z-index:48;pointer-events:none;overflow:hidden;
  -webkit-mask:linear-gradient(180deg,transparent 0,#000 110px);mask:linear-gradient(180deg,transparent 0,#000 110px);
  background:
    repeating-linear-gradient(180deg,rgba(255,255,255,0) 0 20px,rgba(255,255,255,.30) 20px 23px,rgba(255,255,255,0) 23px 44px),
    linear-gradient(90deg,rgba(15,80,100,0) 0,rgba(20,110,130,.55) 28%,rgba(26,140,160,.75) 50%,rgba(20,110,130,.55) 72%,rgba(15,80,100,0) 100%);
  background-size:100% 44px,100% 100%;
  animation:flow 1.2s linear infinite;
}
#sea::before{
  content:'';position:absolute;inset:0;
  background:
    radial-gradient(circle,rgba(255,255,255,.6) 0 2px,transparent 3px) 0 0/34px 52px,
    radial-gradient(circle,rgba(255,255,255,.4) 0 1.5px,transparent 2.5px) 17px 26px/40px 60px;
  animation:bub .9s linear infinite;
}
#sea.fast{animation-duration:.45s}
#sea.fast::before{animation-duration:.35s}
@keyframes flow{to{background-position:0 -44px,0 0}}
@keyframes bub{to{background-position:0 -52px,17px -34px}}

#voyager{position:fixed;top:0;right:var(--vr);width:108px;z-index:50;pointer-events:none;will-change:transform}
#voyager .hull{
  display:block;width:100%;height:auto;overflow:visible;transform-origin:45% 78%;
  animation:rock 4.8s ease-in-out infinite;filter:drop-shadow(0 8px 10px rgba(0,0,0,.55));
}
@keyframes rock{0%,100%{transform:rotate(7deg)}50%{transform:rotate(14deg)}}
#voyager .wv{position:absolute;left:-15%;width:130%;top:66%;height:auto;display:block}
.w1{animation:wv 1.6s linear infinite}
.w2{animation:wv 2.6s linear infinite reverse}
@keyframes wv{to{transform:translateX(-40px)}}
#isle{
  position:absolute;right:calc(100% + 6px);top:26%;white-space:nowrap;padding:5px 12px;border-radius:8px;
  background:linear-gradient(170deg,#e8d5a9,#cdb27b);color:#3a2a12;border:1px solid #8e6f3c;
  box-shadow:0 8px 20px -8px rgba(0,0,0,.8);font-family:var(--f-pirate);font-size:.95rem;letter-spacing:.03em;
}
#isle.pop{animation:isle .5s cubic-bezier(.2,1.4,.4,1)}
@keyframes isle{from{opacity:.2;transform:translateX(14px) scale(.9)}to{opacity:1;transform:none}}
@media(max-width:900px){#voyager{width:74px}#sea{width:66px;right:calc(var(--vr) + 4px)}}
@media(max-width:640px){#isle{display:none}}

/* ---------- NEWS COO ---------- */
#coo{position:fixed;top:22vh;left:-120px;width:84px;z-index:47;pointer-events:none;animation:coo 28s linear infinite;animation-delay:7s}
#coo .wing{transform-origin:36px 30px;animation:flap .35s ease-in-out infinite alternate}
@keyframes flap{from{transform:rotate(-25deg)}to{transform:rotate(30deg)}}
@keyframes coo{
  0%{transform:translate(0,0)}25%{transform:translate(30vw,-34px)}50%{transform:translate(60vw,12px)}
  75%{transform:translate(90vw,-22px)}100%{transform:translate(calc(100vw + 240px),0)}
}

/* ---------- CREW ROSTER ---------- */
.crew{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}
.member{padding:16px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:6px}
.badge{
  width:64px;height:64px;border-radius:50%;display:grid;place-items:center;font-size:30px;
  background:radial-gradient(circle at 32% 28%,var(--gold-3),var(--gold-1) 55%,var(--gold-deep));
  border:2px solid #fff1cd;box-shadow:0 10px 22px -10px rgba(0,0,0,.8);
}
.member h3{font-family:var(--f-pirate);font-size:1.25rem;margin:4px 0 0;color:var(--gold-2);letter-spacing:.03em}
.member .role{font-size:.66rem;letter-spacing:.18em;text-transform:uppercase;color:var(--gold-1);font-weight:700}
.member p{margin:0 0 6px;font-family:var(--f-serif);font-style:italic;color:#cbb894;font-size:.95rem;line-height:1.4}
'@
$h = Swap $h '/* ---------- SAILING SHIP ---------- */' '/* ---------- GRAND LINE RANKS ---------- */' ($css + "`n")

# ================= HTML: sea + ship + coo =================
$scene = @'
<div id="sea" aria-hidden="true"></div>
<div id="voyager" aria-hidden="true">
  <div id="isle"><b>Foosha Village</b></div>
  <svg class="hull" viewBox="0 0 170 150">
    <path d="M74 12 L158 92 M74 12 L18 72" stroke="#f4ead6" stroke-opacity=".45" stroke-width="1"/>
    <rect x="72" y="12" width="4" height="82" fill="#3a2510"/>
    <rect x="118" y="34" width="4" height="60" fill="#3a2510"/>
    <path d="M74 6 L98 12 L74 18Z" fill="#b2332c"/>
    <rect x="50" y="22" width="52" height="3.4" rx="1.5" fill="#5b3410"/>
    <path d="M52 25 Q76 34 100 25 V64 Q76 74 52 64Z" fill="#f4ead6" stroke="#cdb27b"/>
    <use href="#i-roger" x="63" y="32" width="26" height="26" style="color:#2a1508"/>
    <rect x="100" y="40" width="40" height="3" rx="1.5" fill="#5b3410"/>
    <path d="M102 43 Q120 50 138 43 V68 Q120 75 102 68Z" fill="#f4ead6" stroke="#cdb27b"/>
    <path d="M102 55 Q120 62 138 55" stroke="url(#gGold)" stroke-width="3" fill="none"/>
    <path d="M12 92 H156 C150 116 132 128 108 130 H58 C36 128 18 116 12 92Z" fill="#2a1508" stroke="url(#gGold)" stroke-width="2.4"/>
    <path d="M14 98 H154" stroke="url(#gGold)" stroke-width="3"/>
    <path d="M10 92 V72 H44 V92Z" fill="#3a2510" stroke="url(#gGold)" stroke-width="1.6"/>
    <g fill="#ffe9ad"><rect x="16" y="78" width="5" height="6" rx="1"/><rect x="26" y="78" width="5" height="6" rx="1"/><rect x="36" y="78" width="5" height="6" rx="1"/></g>
    <g fill="#ffe9ad"><circle cx="56" cy="108" r="3.2"/><circle cx="76" cy="108" r="3.2"/><circle cx="96" cy="108" r="3.2"/><circle cx="116" cy="108" r="3.2"/></g>
    <path d="M154 90 L166 80" stroke="#5b3410" stroke-width="3" stroke-linecap="round"/>
    <circle cx="157" cy="98" r="9" fill="url(#gGoldV)" stroke="#fff1cd"/>
    <path d="M157 84v4M157 108v4M143 98h4M167 98h4M147 88l3 3M167 108l-3-3" stroke="#f3d98b" stroke-width="2" stroke-linecap="round"/>
  </svg>
  <svg class="wv" viewBox="0 0 170 40">
    <path class="w2" d="M-20 12 q10 -9 20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 V40 H-20Z" fill="rgba(14,90,110,.92)"/>
    <path class="w1" d="M-20 18 q10 -9 20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 V40 H-20Z" fill="rgba(28,140,160,.94)" stroke="#eafcff" stroke-width="1.6"/>
  </svg>
</div>
<div id="coo" aria-hidden="true">
  <svg viewBox="0 0 90 56">
    <ellipse cx="42" cy="32" rx="20" ry="11" fill="#f4ead6"/>
    <circle cx="64" cy="24" r="9" fill="#f4ead6"/>
    <path d="M71 24l14 3-14 4z" fill="#e0a13a"/>
    <circle cx="66" cy="22" r="1.8" fill="#222"/>
    <path class="wing" d="M36 30C30 8 14 6 8 8c6 6 10 14 14 24z" fill="#e6dcc3"/>
    <rect x="34" y="42" width="18" height="6" rx="3" fill="#cdb27b"/>
  </svg>
</div>
'@
$h = Swap $h '<div id="route"' '<a class="skip"' ($scene)

# ================= HTML: crew roster =================
$crew = @'
<section>
  <div class="wrap">
    <div class="sec-head">
      <div>
        <p class="eyebrow">The Guest List</p>
        <h2 class="h-sec goldtext">The Straw Hat Crew</h2>
        <p class="sub">Ten seats, ten dreams. Open a voyage, then invite them aboard.</p>
      </div>
    </div>
    <div class="crew">
      <div class="card member"><div class="badge">&#128082;</div><h3>Monkey D. Luffy</h3><span class="role">Captain</span><p>Dream: King of the Pirates.</p><button class="btn sm" data-invite="Monkey D. Luffy" data-tier="Captain">Invite</button></div>
      <div class="card member"><div class="badge">&#9876;&#65039;</div><h3>Roronoa Zoro</h3><span class="role">Swordsman</span><p>Dream: the world's greatest swordsman.</p><button class="btn sm" data-invite="Roronoa Zoro">Invite</button></div>
      <div class="card member"><div class="badge">&#127818;</div><h3>Nami</h3><span class="role">Navigator</span><p>Dream: to draw a map of the whole world.</p><button class="btn sm" data-invite="Nami">Invite</button></div>
      <div class="card member"><div class="badge">&#127919;</div><h3>Usopp</h3><span class="role">Sniper</span><p>Dream: to become a brave warrior of the sea.</p><button class="btn sm" data-invite="Usopp">Invite</button></div>
      <div class="card member"><div class="badge">&#127859;</div><h3>Sanji</h3><span class="role">Cook</span><p>Dream: to find the All Blue.</p><button class="btn sm" data-invite="Sanji">Invite</button></div>
      <div class="card member"><div class="badge">&#129658;</div><h3>Tony Tony Chopper</h3><span class="role">Doctor</span><p>Dream: a cure for every illness.</p><button class="btn sm" data-invite="Tony Tony Chopper">Invite</button></div>
      <div class="card member"><div class="badge">&#128218;</div><h3>Nico Robin</h3><span class="role">Archaeologist</span><p>Dream: to uncover the true history.</p><button class="btn sm" data-invite="Nico Robin">Invite</button></div>
      <div class="card member"><div class="badge">&#128295;</div><h3>Franky</h3><span class="role">Shipwright</span><p>Dream: to build a ship that sails the whole world.</p><button class="btn sm" data-invite="Franky">Invite</button></div>
      <div class="card member"><div class="badge">&#127931;</div><h3>Brook</h3><span class="role">Musician</span><p>Dream: to reunite with Laboon.</p><button class="btn sm" data-invite="Brook">Invite</button></div>
      <div class="card member"><div class="badge">&#127754;</div><h3>Jinbe</h3><span class="role">Helmsman</span><p>Dream: a sea where all can live as equals.</p><button class="btn sm" data-invite="Jinbe" data-tier="Warlord">Invite</button></div>
    </div>
  </div>
</section>

'@
$mark = '<!-- ============ MARIJOA / COUNCIL PANEL ============ -->'
if (-not $h.Contains($mark)) { throw "Marijoa marker not found" }
$h = $h.Replace($mark, $crew + $mark)

# ================= JS =================
$js = @'
/* ---------- SHIP SAILS DOWN AS YOU SCROLL ---------- */
(function voyage(){
  const ship=$('#voyager'), sea=$('#sea'), isle=$('#isle'), label=$('#isle b'), scene=$('#scene');
  const stops=[[0,'Foosha Village'],[.10,'Loguetown'],[.20,'Reverse Mountain'],[.32,'Water 7'],
    [.44,'Sabaody Archipelago'],[.56,'Marineford'],[.68,'Fish-Man Island'],[.80,'Wano Country'],
    [.93,'Laugh Tale \u2715']];
  let queued=false, last='', fastT=null;
  function update(){
    queued=false;
    const max=document.documentElement.scrollHeight-innerHeight;
    const p=max>0 ? Math.min(1,Math.max(0,scrollY/max)) : 0;
    const h=ship.offsetHeight||90, top=66, bottom=innerHeight-h-16;
    const y=top+p*Math.max(0,bottom-top);
    ship.style.transform='translateY('+y+'px)';
    sea.style.height=(y+h*0.86)+'px';
    if(!RM) scene.style.transform='translate3d(0,'+(-p*46)+'px,0) scale(1.08)';
    let name=stops[0][1]; stops.forEach(s=>{ if(p>=s[0]) name=s[1]; });
    if(name!==last){ last=name; label.textContent=name; isle.classList.remove('pop'); void isle.offsetWidth; isle.classList.add('pop'); }
  }
  const req=()=>{
    sea.classList.add('fast'); clearTimeout(fastT); fastT=setTimeout(()=>sea.classList.remove('fast'),220);
    if(!queued){ queued=true; requestAnimationFrame(update); }
  };
  addEventListener('scroll',req,{passive:true});
  addEventListener('resize',req);
  update();
})();

/* ---------- CREW INVITE BUTTONS ---------- */
document.addEventListener('click', e=>{
  const b=e.target.closest('[data-invite]'); if(!b) return;
  const name=b.dataset.invite;
  if(!S.active){
    toast('Pick a voyage first','Open a voyage ticket, then invite '+name+'.','');
    $('#deck').scrollIntoView({behavior:RM?'auto':'smooth'});
    return;
  }
  $('#g_name').value=name;
  $('#g_mail').value=name.toLowerCase().replace(/[^a-z]/g,'')+'@strawhat.sea';
  $('#g_aff').value='Straw Hat Pirates';
  $('#g_tier').value=b.dataset.tier||'Crew';
  $('#gSub').textContent='Inviting '+name+' to the Gold Room.';
  openModal('#vGuest');
});

'@
$h = Swap $h '/* ---------- SHIP SAILS DOWN AS YOU SCROLL ---------- */' '/* ---------- go ---------- */' $js

[IO.File]::WriteAllText($p, $h, $utf8)
Write-Host "Done. Ship, sea, News Coo and crew roster added." -ForegroundColor Green