$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding $false
$p = "static\index.html"
$h = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)

if ($h -match 'id="relic"') { Write-Host "Already patched." -ForegroundColor Yellow; exit }
Copy-Item $p "static\index.backup3.html" -Force

# ---------- CSS ----------
$css = @'
/* ---------- HERO: WANTED POSTERS + LOG POSE ---------- */
.relic{position:relative;min-height:400px}
.wp{
  position:absolute;width:min(190px,44%);padding:12px 12px 14px;text-align:center;color:#2e2110;
  border:1px solid #8e6f3c;border-radius:4px;
  background:radial-gradient(circle at 20% 10%,rgba(120,88,40,.35),transparent 40%),linear-gradient(170deg,#e8d5a9,#d7bf8e 45%,#c9ad77);
  box-shadow:0 26px 46px -18px rgba(0,0,0,.9);
  transition:transform .4s cubic-bezier(.2,.9,.3,1.25);
}
.wp .w{display:block;font-family:var(--f-pirate);font-size:1.9rem;line-height:.9;letter-spacing:.07em;color:#3a2a12}
.wp .d{display:block;font-family:var(--f-serif);font-weight:600;font-size:.55rem;letter-spacing:.34em;text-transform:uppercase;margin:3px 0 6px}
.wp .fr{border:2px solid #3a2a12;background:linear-gradient(180deg,#f0e2c0,#dcc79a);height:92px;display:grid;place-items:center;font-size:40px;line-height:1}
.wp .fr svg{width:64px;height:42px}
.wp .n{display:block;font-family:var(--f-display);font-weight:900;font-size:.72rem;text-transform:uppercase;margin-top:7px}
.wp .bt{display:block;font-family:var(--f-display);font-weight:900;font-size:.98rem;margin-top:2px}
.wp.a{left:0;top:6%;transform:rotate(-9deg)}
.wp.b{right:0;top:0;transform:rotate(8deg)}
.wp.c{left:24%;bottom:2%;transform:rotate(-2deg);z-index:2}
.relic:hover .wp.a{transform:rotate(-13deg) translate(-8px,-8px)}
.relic:hover .wp.b{transform:rotate(12deg) translate(8px,-8px)}
.relic:hover .wp.c{transform:rotate(0) translateY(-10px)}
.lp{position:absolute;right:3%;bottom:0;width:132px;height:132px;z-index:3;filter:drop-shadow(0 14px 18px rgba(0,0,0,.7))}
#needle{transform-box:fill-box;transform-origin:50% 50%;animation:need 7s ease-in-out infinite}
@keyframes need{0%,100%{transform:rotate(-28deg)}50%{transform:rotate(40deg)}}
@media(max-width:940px){.relic{min-height:360px}}
@media(max-width:520px){.wp{width:46%}.wp .fr{height:70px;font-size:30px}.lp{width:96px;height:96px}}
'@
$h = $h.Replace('</style>', $css + "`n</style>")

# ---------- HTML: replace the flat ship illustration ----------
$art = @'
<!-- One Piece hero: wanted posters + Log Pose -->
    <div class="relic" id="relic" aria-hidden="true">
      <div class="wp a" data-n="Roronoa Zoro"><span class="w">WANTED</span><span class="d">Dead or Alive</span><div class="fr">&#9876;&#65039;</div><span class="n">Roronoa Zoro</span><span class="bt"></span></div>
      <div class="wp b" data-n="Nami"><span class="w">WANTED</span><span class="d">Dead or Alive</span><div class="fr">&#127818;</div><span class="n">Nami</span><span class="bt"></span></div>
      <div class="wp c" data-n="Monkey D. Luffy"><span class="w">WANTED</span><span class="d">Dead or Alive</span><div class="fr"><svg viewBox="0 0 40 26"><use href="#i-hat"/></svg></div><span class="n">Monkey D. Luffy</span><span class="bt"></span></div>
      <svg class="lp" viewBox="0 0 48 48">
        <use href="#i-pose"/>
        <g id="needle"><path d="M24 8l4 15-4 4-4-4z" fill="#c3453f"/><path d="M24 40l-4-15 4-4 4 4z" fill="#f3d98b"/></g>
        <circle cx="24" cy="24" r="2.8" fill="#0c1820" stroke="#e0b34a"/>
        <ellipse cx="17" cy="14" rx="7" ry="3.2" fill="#fff" opacity=".10" transform="rotate(-30 17 14)"/>
      </svg>
    </div>
'@
$rx = '(?s)<!-- Original SVG: Gran Tesoro ship over waves -->.*?</svg>\s*</div>'
if (-not [regex]::IsMatch($h, $rx)) { throw "Hero ship block not found." }
$h = [regex]::Replace($h, $rx, { param($m) $art })

# ---------- JS ----------
$js = @'
/* ---------- HERO: bounties + log pose follows the pointer ---------- */
(function relic(){
  $$('.wp[data-n]').forEach(p=>{ $('.bt',p).textContent='\u0E3F '+fmt(bounty(p.dataset.n)); });
  const nd=$('#needle'); if(!nd||RM) return;
  const lp=nd.closest('svg');
  addEventListener('pointermove',e=>{
    const r=lp.getBoundingClientRect();
    const a=Math.atan2(e.clientY-(r.top+r.height/2), e.clientX-(r.left+r.width/2))*180/Math.PI+90;
    nd.style.animation='none'; nd.style.transform='rotate('+a+'deg)';
  },{passive:true});
})();

'@
$mark = '/* ---------- go ---------- */'
if (-not $h.Contains($mark)) { throw "JS marker not found." }
$h = $h.Replace($mark, $js + $mark)

[IO.File]::WriteAllText($p, $h, $utf8)
Write-Host "Done. Flat ship replaced with wanted posters and Log Pose." -ForegroundColor Green