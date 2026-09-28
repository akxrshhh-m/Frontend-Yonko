$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding $false
$p = "static\index.html"; $r = "api\routes.py"
$h = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)
if ($h -match 'id="vAuth"') { Write-Host "Already patched." -ForegroundColor Yellow; exit }
Copy-Item $p "static\index.backup4.html" -Force
Copy-Item $r "api\routes.backup4.py" -Force

# ================= BACKEND: api/auth.py =================
$auth = @'
"""Member accounts, login and role checks (in-memory, demo grade)."""
import re
import secrets
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from storage.database import db
from config import RegistrationStatus

ORGANIZER = {"name": "Gild Tesoro", "email": "gild@tesoro.sea", "password": "Gold1234"}
MEMBERS = {}
TOKENS = {}

MEMBERS[ORGANIZER["email"]] = {
    "name": ORGANIZER["name"], "email": ORGANIZER["email"],
    "pw": generate_password_hash(ORGANIZER["password"]),
    "role": "organizer", "affiliation": "Tesoro Corporation",
}

EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ORG_RULES = [
    ("POST", re.compile(r"^/api/events$")),
    ("PUT", re.compile(r"^/api/events/[^/]+(/capacity)?$")),
    ("POST", re.compile(r"^/api/events/[^/]+/(close|cancel)$")),
    ("POST", re.compile(r"^/api/events/[^/]+/waitlist/remove$")),
]
REG_RX = re.compile(r"^/api/events/[^/]+/(register|cancel-registration)$")
OFFER_RX = re.compile(r"^/api/offers/([^/]+)/(accept|decline)$")


def _public(m):
    return {k: m[k] for k in ("name", "email", "role", "affiliation")}


def _me():
    h = request.headers.get("Authorization", "")
    if h.startswith("Bearer "):
        email = TOKENS.get(h[7:])
        return MEMBERS.get(email) if email else None
    return None


def _err(msg, code):
    return jsonify({"success": False, "error": msg}), code


def _mine(pid, email):
    p = db.get_participant(pid)
    return bool(p) and (getattr(p, "email", "") or "").lower() == email


def _offer_owner(offer_id):
    for ev in db.get_all_events():
        for o in db.get_pending_offers_for_event(ev.id):
            if getattr(o, "id", None) == offer_id:
                p = db.get_participant(o.participant_id)
                return (p.email or "").lower() if p else None
    return None


def register_auth(app):
    @app.before_request
    def guard():
        path, me = request.path, _me()
        for method, rx in ORG_RULES:
            if request.method == method and rx.match(path):
                if not me or me["role"] != "organizer":
                    return _err("Only the event organizer can do that. Sign in as an organizer.", 403)
                return None
        if request.method == "POST" and REG_RX.match(path):
            if not me:
                return _err("Sign in to reserve a seat.", 401)
            if me["role"] != "organizer":
                data = request.get_json(silent=True) or {}
                if (data.get("email") or "").strip().lower() != me["email"]:
                    return _err("Members can only manage their own seat.", 403)
        m = OFFER_RX.match(path)
        if request.method == "POST" and m:
            if not me:
                return _err("Sign in to answer this offer.", 401)
            if me["role"] != "organizer":
                owner = _offer_owner(m.group(1))
                if owner and owner != me["email"]:
                    return _err("This offer belongs to another guest.", 403)
        return None

    def _issue(m):
        tok = secrets.token_urlsafe(24)
        TOKENS[tok] = m["email"]
        return jsonify({"success": True, "token": tok, "member": _public(m)})

    @app.route("/api/auth/signup", methods=["POST"])
    def signup():
        d = request.get_json(silent=True) or {}
        name = (d.get("name") or "").strip()
        email = (d.get("email") or "").strip().lower()
        pw = d.get("password") or ""
        if len(name) < 2:
            return _err("Enter your name.", 400)
        if not EMAIL_RX.match(email):
            return _err("Enter a valid email address.", 400)
        if len(pw) < 6:
            return _err("Password needs at least 6 characters.", 400)
        if email in MEMBERS:
            return _err("That address is already on the crew list. Sign in instead.", 409)
        MEMBERS[email] = {"name": name, "email": email, "pw": generate_password_hash(pw),
                          "role": "member", "affiliation": d.get("affiliation") or "Independent"}
        return _issue(MEMBERS[email])

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        d = request.get_json(silent=True) or {}
        m = MEMBERS.get((d.get("email") or "").strip().lower())
        if not m or not check_password_hash(m["pw"], d.get("password") or ""):
            return _err("Wrong email or password.", 401)
        return _issue(m)

    @app.route("/api/auth/me", methods=["GET"])
    def me():
        m = _me()
        if not m:
            return _err("Not signed in.", 401)
        return jsonify({"success": True, "member": _public(m)})

    @app.route("/api/auth/logout", methods=["POST"])
    def logout():
        h = request.headers.get("Authorization", "")
        TOKENS.pop(h[7:], None)
        return jsonify({"success": True})

    @app.route("/api/me/passes", methods=["GET"])
    def my_passes():
        m = _me()
        if not m:
            return _err("Sign in first.", 401)
        email = m["email"]
        out = {"success": True, "seats": [], "waitlist": [], "offers": []}
        for ev in db.get_all_events():
            info = {"id": ev.id, "name": ev.name, "venue": ev.venue,
                    "date": ev.event_date, "status": ev.status}
            for reg in db.get_event_registrations(ev.id, status=RegistrationStatus.CONFIRMED):
                if _mine(reg.participant_id, email):
                    out["seats"].append({"event": info, "registration": reg.to_dict()})
            for w in db.get_event_waitlist(ev.id):
                if _mine(w.participant_id, email):
                    out["waitlist"].append({"event": info, "entry": w.to_dict()})
            for o in db.get_pending_offers_for_event(ev.id):
                if _mine(o.participant_id, email):
                    out["offers"].append({"event": info, "offer": o.to_dict()})
        return jsonify(out)
'@
[IO.File]::WriteAllText("api\auth.py", $auth, $utf8)

# ================= BACKEND: hook into routes.py =================
$py = [IO.File]::ReadAllText($r)
if ($py -notmatch 'register_auth') {
  $py = $py.Replace('from utils.validators import ValidationError', "from utils.validators import ValidationError`nfrom api.auth import register_auth")
  $i = $py.LastIndexOf('    return app')
  if ($i -lt 0) { throw "return app not found in routes.py" }
  $py = $py.Substring(0, $i) + "    register_auth(app)`n`n" + $py.Substring($i)
  [IO.File]::WriteAllText($r, $py, $utf8)
}

# ================= FRONTEND =================
function InsertAfterSection($text, $anchor, $new) {
  $a = $text.IndexOf($anchor, [StringComparison]::Ordinal)
  if ($a -lt 0) { throw "Anchor not found: $anchor" }
  $e = $text.IndexOf('</section>', $a, [StringComparison]::Ordinal)
  if ($e -lt 0) { throw "Section end not found" }
  $e += 10
  return $text.Substring(0, $e) + "`n" + $new + $text.Substring($e)
}

$css = @'
/* ---------- MEMBERS ---------- */
[hidden]{display:none!important}
body:not(.is-org) .org-only{display:none!important}
.acc{display:inline-flex;align-items:center;gap:8px}
.tabs{display:flex;gap:8px;margin:14px 0 4px}
.tabs button{flex:1;padding:9px;border-radius:10px;border:1px solid rgba(224,179,74,.35);background:transparent;color:var(--gold-2);font-weight:700;cursor:pointer}
.tabs button.on{background:var(--gold-1);color:var(--lacquer)}
#mine .roster{margin-bottom:16px}
.field[readonly]{opacity:.7;cursor:not-allowed}
'@
$h = $h.Replace('</style>', $css + "`n</style>")

# header: account controls + organizer-only Charter
$acc = @'
<button class="btn sm ghost" id="accBtn">Sign in</button>
      <span class="acc" id="accBox" hidden><a class="chip" href="#mineSec" id="accName">Member</a><button class="icon-btn" id="outBtn" title="Sign out" aria-label="Sign out">&#10162;</button></span>
      <button class="btn sm org-only" id="newBtn">
'@.Trim()
$h = $h.Replace('<button class="btn sm" id="newBtn">', $acc)

# organizer-only controls
$h = $h.Replace('<button class="btn" id="heroNew">', '<button class="btn ghost org-only" id="heroNew">').Replace('class="btn ghost" id="heroNew"', 'class="btn ghost org-only" id="heroNew"')
$h = $h.Replace('<button class="btn" id="councilBtn">', '<button class="btn org-only" id="councilBtn">')
$h = $h.Replace('<button class="btn sm ghost" id="dClose">', '<button class="btn sm ghost org-only" id="dClose">')
$h = $h.Replace('<button class="btn sm danger" data-abandon=', '<button class="btn sm danger org-only" data-abandon=')
$h = $h.Replace('<button class="btn sm" data-invite=', '<button class="btn sm org-only" data-invite=')

# My Passes section after the voyages section
$mine = @'
<section id="mineSec">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <p class="eyebrow">Your Ledger</p>
        <h2 class="h-sec goldtext">My Passes</h2>
        <p class="sub">Your seats, your place on deck, and any seat the Den Den Mushi offers you.</p>
      </div>
    </div>
    <div id="mine"></div>
  </div>
</section>
'@
$h = InsertAfterSection $h '<div id="detail"></div>' $mine

# auth modal
$modal = @'
<div class="veil" id="vAuth" role="dialog" aria-modal="true" aria-labelledby="aT">
  <div class="card modal" style="position:relative">
    <button class="icon-btn x" data-close aria-label="Close"><svg width="16" height="16"><use href="#i-x"/></svg></button>
    <p class="eyebrow">Members of the Gold Room</p>
    <h2 id="aT" class="goldtext">Board the ship</h2>
    <div class="tabs"><button type="button" class="on" data-tab="in">Sign in</button><button type="button" data-tab="up">Join the crew</button></div>
    <form id="fAuth" style="display:flex;flex-direction:column;gap:14px;margin-top:14px">
      <div id="aNameBox" hidden><label for="a_name">Name on the poster</label><input class="field" id="a_name" placeholder="Monkey D. Luffy"></div>
      <div><label for="a_mail">Den Den Mushi address</label><input class="field" id="a_mail" type="email" required placeholder="luffy@strawhat.sea"></div>
      <div><label for="a_pw">Password</label><input class="field" id="a_pw" type="password" minlength="6" required></div>
      <div id="aAffBox" hidden><label for="a_aff">Crew or allegiance</label>
        <select class="field" id="a_aff"><option>Straw Hat Pirates</option><option>Heart Pirates</option><option>Red Hair Pirates</option><option>Kuja Pirates</option><option>Revolutionary Army</option><option>Marine Headquarters</option><option>World Nobles</option><option>Independent</option></select></div>
      <button class="btn block" type="submit" id="aGo">Sign in</button>
      <p class="sub" style="font-size:.9rem;margin:0">Organizer demo: gild@tesoro.sea / Gold1234</p>
    </form>
  </div>
</div>

'@
$m = '<div id="toasts"'
if (-not $h.Contains($m)) { throw "toasts marker not found" }
$h = $h.Replace($m, $modal + $m)

# send the login token with every existing API call
$old = "const opt = { method, headers:{'Content-Type':'application/json'} };"
if (-not $h.Contains($old)) { throw "call() header line not found" }
$h = $h.Replace($old, "const opt = { method, headers:Object.assign({'Content-Type':'application/json'}, S.token?{Authorization:'Bearer '+S.token}:{}) };")

$js = @'
/* ---------- MEMBERS: login, roles, my passes ---------- */
S.me=null; S.token=null; S.seen=new Set();
try{ S.token=localStorage.getItem('gt_token'); }catch(_){}
async function jf(path, method, body){
  const r=await fetch(path,{method:method||'GET',headers:Object.assign({'Content-Type':'application/json'}, S.token?{Authorization:'Bearer '+S.token}:{}),body:body?JSON.stringify(body):undefined});
  let d={}; try{ d=await r.json(); }catch(_){}
  return {ok:r.ok&&d.success!==false, d};
}
function setMe(me){
  S.me=me;
  document.body.classList.toggle('is-org', !!me && me.role==='organizer');
  $('#accBtn').hidden=!!me; $('#accBox').hidden=!me;
  if(me) $('#accName').textContent=me.name+(me.role==='organizer'?' · Organizer':'');
  loadPasses();
}
const _open=openModal;
openModal=function(sel){
  if(sel==='#vGuest'){
    if(!S.me){ toast('Members only','Sign in to reserve a seat.',''); return _open('#vAuth'); }
    _open(sel);
    const lock=S.me.role!=='organizer';
    if(lock){ $('#g_name').value=S.me.name; $('#g_mail').value=S.me.email; }
    $('#g_name').readOnly=lock; $('#g_mail').readOnly=lock;
    return;
  }
  _open(sel);
};
const _rd=renderDetail;
renderDetail=function(){ _rd(); if(S.me) loadPasses(); };

async function loadPasses(){
  const box=$('#mine'); if(!box) return;
  if(!S.me){
    box.innerHTML='<div class="empty"><svg width="54" height="54" style="color:#7d6a45" aria-hidden="true"><use href="#i-hat"/></svg><p>Members hold the passes. Sign in to reserve a seat and watch your place on deck.</p><button class="btn sm" id="mineIn" style="margin-top:16px">Sign in</button></div>';
    $('#mineIn').onclick=()=>openModal('#vAuth'); return;
  }
  const r=await jf('/api/me/passes'); if(!r.ok) return;
  const d=r.d, meta=e=>esc(e.date)+' · '+esc(e.venue);
  let h='';
  d.offers.forEach(o=>{
    h+='<div class="offer"><div class="offer-in"><div class="offer-l"><svg class="snail" aria-hidden="true"><use href="#i-snail"/></svg><div><h3>Golden Den Den Mushi is calling…</h3><p>A chair opened at <b>'+esc(o.event.name)+'</b>. Answer before the timer ends.</p></div></div><div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap"><div class="ticker mt" data-exp="'+esc(o.offer.expires_at)+'">--</div><button class="btn sm ghost" data-odec="'+esc(o.offer.id)+'">Decline</button><button class="btn sm" data-oacc="'+esc(o.offer.id)+'">Accept the seat</button></div></div></div>';
    if(!S.seen.has(o.offer.id)){ S.seen.add(o.offer.id); toast('Den Den Mushi','A seat opened for you at '+o.event.name+'!','ok'); sfx.ring(); }
  });
  if(d.seats.length){
    h+='<p class="eyebrow" style="margin:6px 0 12px">Gold Room seats · '+d.seats.length+'</p><div class="roster">'+d.seats.map(s=>
      '<div class="guest"><div class="g-main"><div class="g-name">'+esc(s.event.name)+'</div><div class="g-sub"><span class="chip open">Seat '+esc(s.registration.registration_number||s.registration.seat_number||'held')+'</span><span>'+meta(s.event)+'</span></div></div><div class="g-act"><button class="btn sm danger" data-mycancel="'+esc(s.event.id)+'">Abandon ship</button></div></div>').join('')+'</div>';
  }
  if(d.waitlist.length){
    h+='<p class="eyebrow" style="margin:6px 0 12px">Waiting on deck · '+d.waitlist.length+'</p><div class="roster">'+d.waitlist.map(w=>
      '<div class="pose"><div class="g-main"><div class="g-name">'+esc(w.event.name)+'</div><div class="g-sub"><span class="chip">#'+esc(w.entry.position||'?')+' on deck</span><span>'+meta(w.event)+'</span></div></div></div>').join('')+'</div>';
  }
  if(!h) h='<div class="empty"><svg width="46" height="46" style="color:#7d6a45" aria-hidden="true"><use href="#i-hat"/></svg><p>No passes yet. Open a voyage and issue your invitation.</p></div>';
  box.innerHTML=h;
}

document.addEventListener('click', async e=>{
  const c=e.target.closest('[data-mycancel]'), a=e.target.closest('[data-oacc]'), n=e.target.closest('[data-odec]');
  if(c){
    if(!confirm('Abandon ship? This frees your chair for the next on deck.')) return;
    const r=await jf('/api/events/'+c.dataset.mycancel+'/cancel-registration','POST',{email:S.me.email});
    if(r.ok){ alarm(); toast('You left the ship','Your chair goes to the next on deck.',''); } else toast('Cannot release',r.d.error||'Try again.','err');
    loadEvents(); loadPasses();
  }
  if(a||n){
    const r=await jf('/api/offers/'+(a||n).dataset[a?'oacc':'odec']+'/'+(a?'accept':'decline'),'POST');
    if(r.ok){ if(a){ rain(80); sfx.coin(); toast('Seat claimed','Welcome to the Gold Room.','ok'); } else toast('Passed along','The invitation moves to the next on deck.',''); }
    else toast('Snail hung up',r.d.error||r.d.message||'That offer is no longer live.','err');
    loadEvents(); loadPasses();
  }
});

let authMode='in';
$$('#vAuth [data-tab]').forEach(b=>b.onclick=()=>{
  authMode=b.dataset.tab;
  $$('#vAuth [data-tab]').forEach(x=>x.classList.toggle('on',x===b));
  $('#aNameBox').hidden=$('#aAffBox').hidden=authMode!=='up';
  $('#a_name').required=authMode==='up';
  $('#aGo').textContent=authMode==='up'?'Join the crew':'Sign in';
});
$('#fAuth').onsubmit=async e=>{
  e.preventDefault();
  const body={email:$('#a_mail').value.trim().toLowerCase(),password:$('#a_pw').value};
  if(authMode==='up'){ body.name=$('#a_name').value.trim(); body.affiliation=$('#a_aff').value; }
  const r=await jf(authMode==='up'?'/api/auth/signup':'/api/auth/login','POST',body);
  if(!r.ok){ toast('Access denied',r.d.error||'Could not sign in.','err'); return; }
  S.token=r.d.token; try{ localStorage.setItem('gt_token',S.token); }catch(_){}
  closeModal(); $('#fAuth').reset(); setMe(r.d.member);
  toast('Welcome aboard',r.d.member.name+', the Gold Room is open.','ok'); rain(40); sfx.coin();
  loadEvents(); if(S.active) selectEvent(S.active);
};
$('#accBtn').onclick=()=>openModal('#vAuth');
$('#outBtn').onclick=async()=>{
  await jf('/api/auth/logout','POST'); S.token=null; try{ localStorage.removeItem('gt_token'); }catch(_){}
  setMe(null); toast('Signed out','Fair winds.',''); loadEvents(); if(S.active) selectEvent(S.active);
};

(async function restore(){
  if(S.token){ const r=await jf('/api/auth/me'); if(r.ok) return setMe(r.d.member); S.token=null; try{ localStorage.removeItem('gt_token'); }catch(_){} }
  setMe(null);
})();
setInterval(async()=>{ if(S.me && !document.hidden){ await jf('/api/offers/check-expired','POST'); loadPasses(); } },8000);
setInterval(()=>{ $$('.mt').forEach(el=>{
  const t=Math.round((new Date(el.dataset.exp)-Date.now())/1000);
  if(isNaN(t)){ el.textContent='--'; return; }
  const s=Math.max(0,t); el.textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0'); el.classList.toggle('warn',s<=15);
}); },1000);

'@
$mark = '/* ---------- go ---------- */'
if (-not $h.Contains($mark)) { throw "go marker not found" }
$h = $h.Replace($mark, $js + $mark)

[IO.File]::WriteAllText($p, $h, $utf8)
Write-Host "Done. Member login, roles and My Passes added." -ForegroundColor Green