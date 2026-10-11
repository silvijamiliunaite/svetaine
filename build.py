"""Statinės svetainės generatorius. Paleidžiamas automatiškai GitHub'e; keisti nereikia."""
import json, shutil, html, pathlib, os, datetime, unicodedata, re, zipfile
R = pathlib.Path(__file__).parent
S = json.load(open(R/"content/site.json", encoding="utf-8")); D = R/"dist"
shutil.rmtree(D, ignore_errors=True)
shutil.copytree(R/"assets", D/"assets", ignore=shutil.ignore_patterns("archive"))

# ---- Paveikslėlių paruošimas (automatiškai, kad nereikėtų nieko konvertuoti) ----
from PIL import Image, ImageOps
EXT = {".jpg", ".jpeg", ".png"}
def _save(src, dst, long_edge, q):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((long_edge, long_edge), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True); im.save(dst, "WEBP", quality=q, method=6)
    return im.size
# Naujienų nuotraukos: įkelk .jpg/.png į assets/news/, svetainė pati paverčia į .webp
for f in list((D/"assets/news").glob("*")):
    if f.suffix.lower() in EXT:
        _save(f, f.with_suffix(".webp"), 1600, 82); f.unlink()
# Galerijos nuotraukos: įmesk į aplanką naujos-nuotraukos/ (vardas: „Fotografo Vardas - bet kas.jpg“)
NEWPH = []
inbox = R/"naujos-nuotraukos"
if inbox.is_dir():
    for f in sorted(inbox.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.suffix.lower() not in EXT: continue
        stem = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", f.stem).encode("ascii", "ignore").decode().lower()).strip("-")[:40] or "foto"
        pid = f"nauja-{stem}"
        _save(f, D/"assets/img"/f"{pid}.webp", 2000, 82)
        tw, th = _save(f, D/"assets/thumbs"/f"{pid}.webp", 640, 80)
        credit = f.stem.split(" - ")[0].strip() if " - " in f.stem else ""
        NEWPH.append({"id": pid, "tw": tw, "th": th, "credit": credit, "cat": "stage", "hide": False})
KEY = os.environ.get("FORM_KEY") or S["form_access_key"]
if not KEY: print("DĖMESIO: content/site.json lauke form_access_key nėra rakto, forma nesiųs žinučių!")
e = html.escape
tr = lambda v, L: v[L] if isinstance(v, dict) else v
OTHER = {"lt": "en", "en": "lt"}

def href(L, pid, depth):
    slug = next(n["slug"][L] for n in S["nav"] if n["id"] == pid)
    return "../"*depth + f"{L}/" + (slug + "/" if slug else "")

def layout(L, pid, title, body, over=False):
    slug = next(n["slug"][L] for n in S["nav"] if n["id"] == pid)
    depth = 2 if slug else 1; P = "../"*depth
    url = lambda l: S["domain"] + "/" + l + "/" + (next(n["slug"][l] for n in S["nav"] if n["id"] == pid) + "/" if next(n["slug"][l] for n in S["nav"] if n["id"] == pid) else "")
    nav = "".join(f'<a href="{href(L,n["id"],depth)}"{" aria-current=page" if n["id"]==pid or (pid=="presskit" and n["id"]=="press") else ""}>{e(tr(n["title"],L))}</a>' for n in S["nav"] if not n.get("hidden"))
    desc = e(tr(S["description"], L))
    ld = ('<script type="application/ld+json">' + json.dumps({"@context":"https://schema.org","@type":"Person","name":S["name"],"jobTitle":tr(S["tagline"],L),"url":S["domain"]+"/"+L+"/","image":S["domain"]+"/assets/og.jpg","sameAs":[u for n,u in S["social"]]}, ensure_ascii=False) + '</script>') if pid == "home" else ""
    return f"""<!doctype html><html lang="{L}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{desc}">
<link rel="canonical" href="{url(L)}"><link rel="alternate" hreflang="lt" href="{url('lt')}"><link rel="alternate" hreflang="en" href="{url('en')}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{desc}"><meta property="og:type" content="website">
<meta property="og:image" content="{S['domain']}/assets/og.jpg">
{ld}<link rel="icon" href="{P}assets/favicon.png"><link rel="stylesheet" href="{P}assets/css/style.css"><script src="{P}assets/js/site.js" defer></script><script data-goatcounter="https://silvijamil.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script></head><body>
<header class="top{' on-photo' if over else ''}"><a class="logo" href="{href(L,'home',depth)}" aria-label="{e(S['name'])}"><img src="{P}assets/logo.png" alt="SM"></a>
<nav id="nav">{nav}</nav><a class="lang" href="{href(OTHER[L],pid,depth).replace(f'{OTHER[L]}/',OTHER[L]+'/',1)}" hreflang="{OTHER[L]}">{tr(S['ui']['lang'],L)}</a>
<button class="menu" aria-label="{tr(S['ui']['menu'],L)}" onclick="this.closest('header').querySelector('nav').classList.toggle('open')"><span></span><span></span></button></header>
<main>{body}</main>{dialog(L) if pid != "contact" else ""}
<footer><p>© 2026 {e(S['name'])} · <a href="{href(L,'presskit',depth)}">Press kit</a></p><p class="soc">{''.join(f'<a href="{u}" rel="noopener" target="_blank">{e(tr(n,L))}</a>' for n,u in S['social'][:5])}</p></footer></body></html>"""


def mform(L):
    u = S["ui"]; t = lambda k: e(tr(u[k], L))
    return (f'<form class="mform" action="https://api.web3forms.com/submit" method="POST" data-key="{e(KEY)}" data-sending="{t("sending")}" data-err="{t("err")}" data-ok="{t("thanks")}" data-mail="{S["email"]}">'
            f'<input type="hidden" name="access_key" value="{e(KEY)}"><input type="hidden" name="from_name" value="{e(S["name"])} (svetainė)"><input type="checkbox" name="botcheck" hidden tabindex="-1">'
            f'<input name="name" placeholder="{t("name")}" aria-label="{t("name")}" autocomplete="name"><input type="email" name="email" placeholder="{t("email")}" aria-label="{t("email")}" required autocomplete="email">'
            f'<input name="subject" placeholder="{t("subject")}" aria-label="{t("subject")}"><textarea name="message" rows="6" placeholder="{t("msg")}" aria-label="{t("msg")}" required></textarea>'
            f'<button class="btn">{t("send")}</button><p class="fnote" role="status"></p><p class="fpriv">{t("priv")}</p></form>')

def dialog(L):
    u = S["ui"]
    return (f'<dialog class="mdlg" aria-label="{e(tr(u["title"],L))}"><div class="box"><button class="x" type="button" data-close aria-label="{e(tr(u["close"],L))}">×</button>'
            f'<h2>{e(tr(u["title"],L))}</h2><p class="lead">{e(tr(u["lead"],L))}</p>{mform(L)}</div></dialog>')

MLT = ["sausio","vasario","kovo","balandžio","gegužės","birželio","liepos","rugpjūčio","rugsėjo","spalio","lapkričio","gruodžio"]
MEN = ["January","February","March","April","May","June","July","August","September","October","November","December"]
MS = {"lt": ["Sau","Vas","Kov","Bal","Geg","Bir","Lie","Rgp","Rgs","Spa","Lap","Gru"], "en": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]}
def fdate(d, L):
    y, m, dd = map(int, d.split("-"))
    return f"{y} m. {MLT[m-1]} {dd} d." if L == "lt" else f"{dd} {MEN[m-1]} {y}"
TODAY = datetime.date.today().isoformat()
def load(n):
    d = json.load(open(R/"content"/n, encoding="utf-8"))
    return d["items"] if isinstance(d, dict) and "items" in d else d

def news_page(L, P):
    u = S["ui"]; out = []
    for it in sorted(load("news.json"), key=lambda x: x["date"], reverse=True):
        img = f'<img src="{P}assets/news/{os.path.splitext(it["img"])[0]}.webp" alt="" loading="lazy">' if it.get("img") else ""
        cr = "".join(f'<div><dt>{e(tr(r,L))}</dt><dd>' + (f'<a href="{e(url)}" rel="noopener" target="_blank">{e(tr(nm,L))}</a>' if url else e(tr(nm,L))) + '</dd></div>' for r, nm, url in it.get("credits", []))
        w = tr(it["when"], L) if it.get("when") is not None else fdate(it["date"], L)
        tm = f'<time datetime="{it["date"]}">{w}</time>' if w else ""
        txt = f'<p>{e(tr(it["text"],L))}</p>' if it.get("text") else ""
        if it.get("dates"):
            tm = ""
            pl = '<ul class="when-list">' + "".join(f'<li><b>{fdate(d,L)}</b>{e(" · ".join(v for v in (t_, tr(p_,L) if p_ else "") if v))}</li>' for d, t_, p_ in it["dates"]) + '</ul>'
        else:
            pl = f'<p class="place">{e(tr(it["place"],L))}</p>' if it.get("place") else ""
        lab = tr(it["label"], L) if it.get("label") else tr(u["more"], L)
        out.append(f'<article class="card{"" if img else " noimg"}{" poster" if it.get("poster") else ""}">{img}<div class="cbody">{tm}<h2>{e(tr(it["title"],L))}</h2>{txt}<dl>{cr}</dl>{pl}{(f'<p class="cta"><a class="btn ghost" href="{e(it["url"])}" rel="noopener" target="_blank">{e(lab)}</a></p>') if it.get("url") else ""}</div></article>')
    return f'<section class="page"><h1>{e(tr(next(n for n in S["nav"] if n["id"]=="news")["title"],L))}</h1><div class="cards">{"".join(out)}</div></section>'

def calendar_page(L, P):
    u = S["ui"]; evs = sorted(load("events.json"), key=lambda x: (x["date"], x.get("time",""))); ld = []
    def row(x, past):
        y, m, d = map(int, x["date"].split("-")); a = tr(u["tickets"], L) if x.get("tickets") else tr(u["more"], L)
        btn = f'<a class="btn" href="{e(x["url"])}" rel="noopener" target="_blank">{a}</a>' if x.get("url") else ""
        more = f'<a class="btn ghost" href="{e(x["more"])}" rel="noopener" target="_blank">{tr(u["alldates"],L)}</a>' if x.get("more") else ""
        if not past: ld.append({"@type":"Event","name":tr(x["title"],L),"startDate":x["date"]+"T"+x.get("time","00:00"),**({"url":x["url"]} if x.get("url") else {}),**({"location":{"@type":"Place","name":tr(x["place"],L)}} if x.get("place") else {})})
        return f'<li class="ev{" past" if past else ""}"><div class="date"><b>{d}</b><span>{MS[L][m-1]} {y}</span></div><div class="info"><h2>{e(tr(x["title"],L))}</h2><p>{e(" · ".join(v for v in (x.get("time",""), tr(x["place"],L) if x.get("place") else "") if v))}</p></div><div class="act">{btn}{more}</div></li>'
    up = [row(x, False) for x in evs if x["date"] >= TODAY]
    past = [x for x in evs if x["date"] < TODAY]
    for q in load("news.json"):
        if q.get("stream"): continue
        if q.get("dates"):
            past += [{"date":d,"time":t_,"title":q.get("evtitle",q["title"]),"place":p_,"url":q.get("url")} for d, t_, p_ in q["dates"] if d < TODAY]
        elif q["date"] < TODAY and q.get("when") is None:
            past.append({"date":q["date"],"title":q["title"],"place":q.get("place"),"url":q.get("url")})
    pa = [row(x, True) for x in sorted(past, key=lambda x: x["date"], reverse=True)]
    h = f'<section class="page"><h1>{e(tr(next(n for n in S["nav"] if n["id"]=="calendar")["title"],L))}</h1><h2>{tr(u["upcoming"],L)}</h2>'
    h += f'<ul class="evs">{"".join(up)}</ul>' if up else f'<p class="muted">{tr(u["none"],L)}</p>'
    if pa: h += f'<h2>{tr(u["past"],L)}</h2><ul class="evs">{"".join(pa)}</ul>'
    return h + f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script></section>'

import unicodedata
def music_page(L, P):
    u = S["ui"]; t = lambda k: e(tr(u[k], L)); W = load("works.json"); items = []
    flat = lambda v: " ".join(v.values()) if isinstance(v, dict) else (v or "")
    for w in W:
        title = tr(w["title"], L); sc = tr(w["scoring"], L) if w.get("scoring") else ""
        meta = " · ".join(v for v in (w["year"], w["dur"]) if v)
        if w.get("note"): meta = (meta + " · " if meta else "") + tr(w["note"], L)
        cats = w["cat"] if isinstance(w["cat"], list) else [w["cat"]]
        play = (f'<button class="play" type="button" data-src="{P}assets/audio/{e(w["audio"])}" data-title="{e(title)}" aria-label="{t("playx")}: {e(title)}"><i></i></button>' if w.get("audio") else '<span class="play none"></span>')
        links = "".join(f'<a href="{e(url)}" rel="noopener" target="_blank">{e(lab)}</a>' for lab, url in w["links"])
        q = unicodedata.normalize("NFD", (flat(w["title"]) + " " + flat(w["scoring"]) + " " + w["year"]).lower()); q = "".join(c for c in q if not unicodedata.combining(c))
        items.append(f'<li class="work" data-cat="{" ".join(cats)}" data-q="{e(q)}">{play}<div class="wtxt"><h2>{e(title)}</h2>' + (f'<p class="scoring">{e(sc)}</p>' if sc else "") + f'<p class="meta">{e(meta)}</p></div><div class="wlinks">{links}</div></li>')
    chips = "".join(f'<button type="button" class="chip{" on" if k=="all" else ""}" data-cat="{k}">{t(k)}</button>' for k in ("all","stage","orch","chamber","vocal"))
    title = e(tr(next(n for n in S["nav"] if n["id"]=="music")["title"], L))
    return (f'<section class="page music"><h1>{title}</h1><p class="cta"><a class="btn" href="{e(S["spotify_artist"])}" rel="noopener" target="_blank">Spotify</a><a class="btn" href="{e(S["youtube_channel"])}" rel="noopener" target="_blank">YouTube</a></p>'
            f'<aside class="note"><div><b>{t("sc_title")}</b><p>{t("sc_text")}</p></div><a class="btn ghost" href="{href(L,"contact",len(P)//3)}" data-open data-subject="{t("sc_subj")}">{t("sc_btn")}</a></aside>'
            f'<div class="tools"><input class="wsearch" type="search" placeholder="{t("search")}" aria-label="{t("search")}"><div class="chips">{chips}</div></div>'
            f'<ul class="works">{"".join(items)}</ul><p class="muted nores" hidden>{t("nores")}</p>'
            f'<details class="abbr"><summary>{t("abbr")}</summary><dl>' + "".join(f'<div><dt>{e(g["k"])}</dt><dd>{e(g[L])}</dd></div>' for g in S["legend"]) + '</dl></details></section>'
            f'<div class="player" hidden data-err="{t("perr")}"><button class="pp" type="button" aria-label="Play/Pause"></button><div class="pt"><b class="ptitle"></b><span class="ptime"></span></div><input class="pbar" type="range" min="0" max="1000" value="0" aria-label="Position"><button class="px" type="button" aria-label="{e(tr(u["close"],L))}">×</button></div>')


def watch_page(L, P):
    u = S["ui"]; out = []
    for v in load("watch.json"):
        title = tr(v["title"], L); k = v["kind"]
        if k in ("youtube", "vimeo"):
            emb = (f'https://www.youtube-nocookie.com/embed/{v["vid"]}?autoplay=1&rel=0' + (f'&start={v["t"]}' if v.get("t") else "")) if k == "youtube" else f'https://player.vimeo.com/video/{v["vid"]}?h={v["h"]}&autoplay=1'
            cov = f'<img src="{P}assets/news/{os.path.splitext(v["cover"])[0]}.webp" alt="" loading="lazy">' if v.get("cover") else f'<span class="phl">{"YouTube" if k == "youtube" else "Vimeo"}</span>'
            media = f'<button class="media" type="button" data-embed="{e(emb)}" aria-label="{e(tr(u["w_play"],L))}: {e(title)}">{cov}<span class="pl"></span></button>'
            lab = tr(u["w_yt"] if k == "youtube" else u["w_vm"], L)
        else:
            lab = tr(v["label"], L)
            inner = f'<img src="{P}assets/news/{os.path.splitext(v["cover"])[0]}.webp" alt="" loading="lazy">' if v.get("cover") else f'<span class="phl">{e(tr(v["ph"],L))}</span>'
            media = f'<a class="media" href="{e(v["url"])}" rel="noopener" target="_blank" aria-label="{e(lab)}">{inner}<span class="pl"></span></a>'
        cr = "".join(f'<div><dt>{e(tr(r,L))}</dt><dd>{e(tr(nm,L))}</dd></div>' for r, nm, _ in v.get("credits", []))
        pl = f'<p class="place">{e(tr(v["place"],L))}</p>' if v.get("place") else ""
        out.append(f'<article class="vcard">{media}<div class="cbody"><h2>{e(title)}</h2><p>{e(tr(v["text"],L))}</p><dl>{cr}</dl>{pl}<p class="cta"><a class="btn ghost" href="{e(v["url"])}" rel="noopener" target="_blank">{e(lab)}</a></p></div></article>')
    return f'<section class="page"><h1>{e(tr(next(n for n in S["nav"] if n["id"]=="watch")["title"],L))}</h1><div class="cards vcards">{"".join(out)}</div></section>'

def gallery_page(L, P):
    u = S["ui"]; t = lambda k: e(tr(u[k], L)); items = []
    for i, g in enumerate(NEWPH + load("gallery.json")):
        if g.get("hide"): continue
        cap = f'{tr(u["photo"],L)}: {g["credit"]}' if g.get("credit") else ""
        items.append(f'<li data-cat="{" ".join(g["cat"]) if isinstance(g["cat"], list) else g["cat"]}" style="--a:{g["tw"]/g["th"]:.4f}"><button class="gi" type="button" data-full="{P}assets/img/{g["id"]}.webp" data-cap="{e(cap)}" aria-label="{e(tr(u["photo"],L))} {i+1}"><img src="{P}assets/thumbs/{g["id"]}.webp" width="{g["tw"]}" height="{g["th"]}" alt="" loading="lazy"></button></li>')
    chips = "".join(f'<button type="button" class="gchip{" on" if k=="all" else ""}" data-cat="{k}">{t(kk)}</button>' for k, kk in (("all","all"),("portrait","portrait"),("stage","stage2")))
    title = e(tr(next(n for n in S["nav"] if n["id"]=="gallery")["title"], L))
    lb = (f'<dialog class="lbx" aria-label="{title}"><button class="lclose" type="button" aria-label="{t("close")}">×</button><button class="lprev" type="button" aria-label="{t("prev")}">‹</button>'
          f'<figure><img alt=""><figcaption><span class="cap"></span><span class="cnt"></span></figcaption></figure><button class="lnext" type="button" aria-label="{t("next")}">›</button></dialog>')
    return f'<section class="page galp"><h1>{title}</h1><p class="muted">{t("g_note")}</p><div class="chips gchips">{chips}</div><ul class="gal">{"".join(items)}</ul></section>{lb}'

def pname(i, k):
    c = unicodedata.normalize("NFKD", k.get("credit") or "").encode("ascii", "ignore").decode()
    return f"Silvija-Miliunaite_{i+1:02d}_foto-{re.sub(r'[^A-Za-z0-9]+','-',c).strip('-') or 'autorius'}.jpg"

def press_page(L, P):
    u = S["ui"]; t = lambda k: e(tr(u[k], L)); out = []; depth = len(P)//3
    for p in load("press.json"):
        qt = tr(p["quote"], L); qt = qt.replace("„", "«").replace("“", "»") if L == "lt" else qt.replace("“", "‘").replace("”", "’")
        src = e(tr(p["source"], L)) + (f' · {p["year"]}' if p.get("year") else "")
        lk = f'<a href="{e(p["url"])}" rel="noopener" target="_blank">{e(tr(u["p_read"],L))} →</a>' if p.get("url") else ""
        o, c = ("„", "“") if L == "lt" else ("“", "”")
        out.append(f'<blockquote class="q"><p>{o}{e(qt)}{c}</p><footer><cite>{src}</cite>{lk}</footer></blockquote>')
    note = f'<p class="muted">{e(tr(u["p_tr"],L))}</p>' if tr(u["p_tr"], L) else ""
    title = e(tr(next(n for n in S["nav"] if n["id"]=="press")["title"], L))
    return f'<section class="page presp"><h1>{title}</h1>{note}<div class="quotes">{"".join(out)}</div></section>'

def pname(i, k):
    c = unicodedata.normalize("NFKD", k.get("credit") or "").encode("ascii", "ignore").decode()
    return f"Silvija-Miliunaite_{i+1:02d}_foto-{re.sub(r'[^A-Za-z0-9]+','-',c).strip('-') or 'autorius'}.jpg"

def presskit_page(L, P):
    u = S["ui"]; t = lambda k: e(tr(u[k], L)); depth = len(P)//3; kit = load("presskit.json")
    lb = "".join(f"<p>{e(x)}</p>" for x in tr(S["bio"], L))
    photos = "".join(f'<li><img src="{P}assets/thumbs/{k["id"]}.webp" alt="" loading="lazy"><div><span class="cr">{t("photo")}: {e(k["credit"])}</span><a class="btn ghost" href="{P}assets/press/{k["id"]}.jpg" download="{pname(i,k)}">{t("dlj")}</a></div></li>' for i, k in enumerate(kit))
    return (f'<section class="page presp"><p class="muted"><a href="{href(L,"press",depth)}">{t("back_press")}</a></p><h1>{t("kit")}</h1><div class="kit"><p class="muted">{t("kit_intro")}</p>'
            f'<div class="biobox"><b>{t("sbio")}</b><div class="biotxt"><p>{e(tr(S["bio_short"],L))}</p></div><button class="btn ghost copy" type="button" data-ok="{t("copied")}">{t("copy")}</button></div>'
            f'<details class="bio"><summary>{t("lbio")}</summary><div class="biotxt">{lb}</div><button class="btn ghost copy" type="button" data-ok="{t("copied")}">{t("copy")}</button></details>'
            f'<h2>{t("photos")}</h2><p class="muted">{t("photo_hint")}</p><p class="cta"><a class="btn" href="{P}assets/press/photos.zip" download="Silvija-Miliunaite_press-photos.zip">{t("dlall")}</a></p><ul class="pk">{photos}</ul>'
            f'<h2>{t("wl")}</h2><p class="cta"><a class="btn ghost" href="{href(L,"worklist",depth)}">{t("wl_btn")}</a></p></div></section>')

def worklist_page(L, P):
    u = S["ui"]; t = lambda k: e(tr(u[k], L))
    rows = "".join(f'<tr><td>{e(tr(w["title"],L))}</td><td>{e(tr(w["scoring"],L)) if w.get("scoring") else ""}</td><td>{e(w["year"])}</td><td>{e(w["dur"])}</td></tr>' for w in load("works.json"))
    title = e(tr(next(n for n in S["nav"] if n["id"]=="worklist")["title"], L))
    return (f'<section class="page wl"><h1>{title}</h1><p class="noprint"><button class="btn" type="button" onclick="window.print()">{t("wl_print")}</button></p>'
            f'<p class="printonly">{e(S["name"])} · {e(S["email"])}</p><div class="tw"><table><thead><tr><th>{t("c_title")}</th><th>{t("c_sc")}</th><th>{t("c_year")}</th><th>{t("c_dur")}</th></tr></thead><tbody>{rows}</tbody></table></div></section>')

def write(L, pid, html_, title):
    slug = next(n["slug"][L] for n in S["nav"] if n["id"] == pid)
    out = D/L/slug/"index.html"; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html_, encoding="utf-8")

def fig(ph, L, cls=""):
    return f'<figure class="{cls}"><img src="{{P}}assets/img/{ph["id"]}.webp" alt="{e(S["name"])}"><figcaption>{tr(S["ui"]["photo"],L)}: {e(ph["credit"] or "")}</figcaption></figure>'

for L in ("lt", "en"):
    ui = S["ui"]; name = e(S["name"])
    for n in S["nav"]:
        pid = n["id"]; depth = 2 if n["slug"][L] else 1; P = "../"*depth
        if pid == "home":
            ps = "".join(f"<p>{e(p)}</p>" for p in tr(S["home_intro"], L))
            first, last = S["name"].split(" ", 1)
            body = (f'<div class="bg"><img src="{P}assets/img/{S["hero"]["id"]}.webp" alt="" style="--focus:{S["hero"].get("focus","60% 40%")}"><div class="shade"></div><div class="dim"></div></div>'
                    f'<section class="hero-full"><div class="copy"><h1><span>{e(first)}</span> <span>{e(last)}</span></h1><p class="cta"><a class="btn" href="{href(L,"bio",depth)}">{tr(ui["read"],L)}</a><a class="btn ghost" href="{href(L,"contact",depth)}" data-open>{tr(ui["write"],L)}</a></p></div></section>'
                    f'<section class="over"><div class="prose">{ps}</div></section>')
            title = f"{S['name']} — {tr(S['tagline'],L)}"
        elif pid == "bio":
            ps = "".join(f"<p>{e(p)}</p>" for p in tr(S["bio"], L))
            body = f'<section class="page bio"><h1>{e(tr(n["title"],L))}</h1><div class="cols"><div class="prose">{ps}</div>{fig(S["bio_photo"],L,"portrait sticky").replace("{P}",P)}</div><aside class="note"><div><b>{tr(ui["pk_t"],L)}</b><p>{tr(ui["pk_p"],L)}</p></div><a class="btn" href="{href(L,"presskit",depth)}">{tr(ui["pk_btn"],L)}</a></aside></section>'
            title = f"{tr(n['title'],L)} — {S['name']}"
        elif pid == "news":
            body = news_page(L, P); title = f"{tr(n['title'],L)} — {S['name']}"
        elif pid == "music":
            body = music_page(L, P); title = f"{tr(n['title'],L)} — {S['name']}"
        elif pid == "watch":
            body = watch_page(L, P); title = f"{tr(n['title'],L)} — {S['name']}"
        elif pid == "gallery":
            body = gallery_page(L, P); title = f"{tr(n['title'],L)} — {S['name']}"
        elif pid == "press":
            body = press_page(L, P); title = f"{tr(n['title'],L)} — {S['name']}"
        elif pid == "presskit":
            body = presskit_page(L, P); title = f"{tr(n['title'],L)} — {S['name']}"
        elif pid == "worklist":
            body = worklist_page(L, P); title = f"{tr(n['title'],L)} — {S['name']}"
        elif pid == "calendar":
            body = calendar_page(L, P); title = f"{tr(n['title'],L)} — {S['name']}"
        else:
            form = mform(L)
            links = "".join(f'<li><a href="{u}" rel="noopener" target="_blank">{e(tr(nm,L))}</a></li>' for nm, u in S["social"])
            body = f'<section class="page contact"><h1>{e(tr(n["title"],L))}</h1><a class="mail" href="mailto:{S["email"]}">{S["email"]}</a>{form}<aside class="note"><div><b>{tr(ui["sc_title"],L)}</b><p>{tr(ui["sc_text"],L)} <a href="mailto:{S["email"]}?subject={tr(ui["sc_subj"],L)}">{S["email"]}</a></p></div></aside><h2>{tr(ui["find"],L)}</h2><ul class="pills">{links}</ul></section>'
            title = f"{tr(n['title'],L)} — {S['name']}"
        write(L, pid, layout(L, pid, title, body, pid == "home"), title)
with zipfile.ZipFile(D/"assets/press/photos.zip", "w", zipfile.ZIP_STORED) as z:
    for i, k in enumerate(load("presskit.json")): z.write(R/f"assets/press/{k['id']}.jpg", pname(i, k))

# 404, robots.txt ir sitemap.xml
nf = "".join(f'<p><a href="/{l}/">{e(tr(S["ui"]["nf_t"],l))} · {l.upper()}</a></p>' for l in ("lt", "en"))
(D/"404.html").write_text(f'<!doctype html><html lang="lt" data-theme="wine"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>404 — {e(S["name"])}</title><meta name="robots" content="noindex"><link rel="stylesheet" href="/assets/css/style.css"></head><body><main class="page" style="min-height:70vh"><h1>404</h1><p class="muted">{e(tr(S["ui"]["nf_t"],"lt"))}. {e(tr(S["ui"]["nf_p"],"lt"))}<br>{e(tr(S["ui"]["nf_t"],"en"))}. {e(tr(S["ui"]["nf_p"],"en"))}</p><div class="cta">{nf}</div></main></body></html>', encoding="utf-8")
urls = ""
for n in S["nav"]:
    alts = {l: S["domain"] + "/" + l + "/" + ((n["slug"][l] + "/") if n["slug"][l] else "") for l in ("lt", "en")}
    for l in ("lt", "en"):
        urls += f'<url><loc>{alts[l]}</loc>' + "".join(f'<xhtml:link rel="alternate" hreflang="{a}" href="{h}"/>' for a, h in alts.items()) + '</url>'
(D/"sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">{urls}</urlset>', encoding="utf-8")
(D/"robots.txt").write_text(f'User-agent: *\nAllow: /\n\nSitemap: {S["domain"]}/sitemap.xml\n', encoding="utf-8")
(D/"index.html").write_text('<!doctype html><meta charset="utf-8"><title>Silvija Miliūnaitė</title><script>location.replace((navigator.language||"lt").toLowerCase().startsWith("lt")?"lt/":"en/")</script><noscript><a href="lt/">LT</a> · <a href="en/">EN</a></noscript>', encoding="utf-8")
print("OK:", sum(1 for _ in D.rglob("*.html")), "puslapiai")
