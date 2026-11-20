#!/usr/bin/env python3
"""
Builds the website into the  public/  folder.

    python build.py            build public/
    python build.py --zip      build, then create dist/site-upload-YYYYMMDD.zip for upload
    python build.py --serve    build, then preview at http://localhost:8000

Needs only Python 3.8+ (no extra packages).

Where things live:
    site.json                 phone, email, hours, season bar, legal details, switches
    src/pages/el/*.html       Greek pages (content only, no header/footer)
    src/pages/en/*.html       English pages
    src/partials/<lang>/      blocks reused on several pages
    src/assets/               CSS, JavaScript, fonts, images
    src/static/               files copied as-is to the site root
"""
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import struct
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "public"
S = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
TODAY = dt.date.today()
LANGS = ("el", "en")

# ---------------------------------------------------------------- pages
# key: (Greek file, English file, shown in menu)
PAGES = {
    "home":       ("index.html",         "index.html",      True),
    "services":   ("ypiresies.html",     "services.html",   True),
    "story":      ("istoria.html",       "our-story.html",  True),
    "facilities": ("egkatastaseis.html", "the-mill.html",   True),
    "oil":        ("to-ladi-mas.html",   "our-oil.html",    "oil_page"),
    "contact":    ("epikoinonia.html",   "contact.html",    True),
    "privacy":    ("aporrito.html",      "privacy.html",    False),
    "thanks":     ("efharistoume.html",  "thank-you.html",  False),
}
NAV = {
    "el": {"home": "Αρχική", "services": "Υπηρεσίες", "story": "Η ιστορία μας",
           "facilities": "Το ελαιοτριβείο", "oil": "Το λάδι μας", "contact": "Επικοινωνία"},
    "en": {"home": "Home", "services": "Services", "story": "Our story",
           "facilities": "The mill", "oil": "Our oil", "contact": "Contact"},
}
T = {  # interface text
    "el": {
        "skip": "Μετάβαση στο περιεχόμενο", "menu": "Μενού", "close": "Κλείσιμο",
        "main_nav": "Κύριο μενού", "other_lang": "English", "other_lang_code": "en",
        "call": "Κλήση", "directions": "Οδηγίες", "home_alt": "Ελαιοτριβείο Μαρκόπουλος, αρχική σελίδα",
        "f_about": "Οικογενειακό ελαιοτριβείο στη Μαλεσίνα Φθιώτιδας, από το 1963.",
        "f_contact": "Επικοινωνία", "f_hours": "Ωράριο σεζόν", "f_pages": "Σελίδες",
        "phone": "Τηλέφωνο", "email": "Email", "address": "Διεύθυνση", "maps": "Οδηγίες στο Google Maps",
        "privacy": "Πολιτική απορρήτου", "vat": "ΑΦΜ", "gemi": "ΓΕΜΗ", "offseason": "Εκτός σεζόν",
        "season_open": "σε λειτουργία", "season_closed": "εκτός λειτουργίας",
    },
    "en": {
        "skip": "Skip to content", "menu": "Menu", "close": "Close",
        "main_nav": "Main menu", "other_lang": "Ελληνικά", "other_lang_code": "el",
        "call": "Call", "directions": "Directions", "home_alt": "Markopoulos Olive Mill, home page",
        "f_about": "Family-run olive mill in Malesina, Fthiotida, Greece, since 1963.",
        "f_contact": "Contact", "f_hours": "Season hours", "f_pages": "Pages",
        "phone": "Phone", "email": "Email", "address": "Address", "maps": "Directions on Google Maps",
        "privacy": "Privacy policy", "vat": "VAT no.", "gemi": "GEMI", "offseason": "Off-season",
        "season_open": "open", "season_closed": "closed",
    },
}


def feature_on(flag):
    return flag is True or (isinstance(flag, str) and S.get("features", {}).get(flag) is True)


def page_path(key, lang):
    """Path of a page relative to the site root ('' = home)."""
    f = PAGES[key][0 if lang == "el" else 1]
    if f == "index.html":
        f = ""
    return f if lang == "el" else "en/" + f


def url(key, lang):
    return S["domain"].rstrip("/") + "/" + page_path(key, lang)


def rel(root, target):
    r = root + target
    return r if r else "./"


# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(str(s), quote=True)


def jpeg_size(p: Path):
    data = p.read_bytes()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        seg = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + seg
    raise ValueError(f"no size in {p}")


def png_size(p: Path):
    w, h = struct.unpack(">II", p.read_bytes()[16:24])
    return w, h


IMG_DIR = SRC / "assets" / "img"


def picture(root, spec):
    """{{img:name|alt text|sizes|extra-class|eager}}"""
    parts = spec.split("|")
    name, alt = parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""
    sizes = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "(min-width: 60rem) 50vw, 100vw"
    cls = parts[3].strip() if len(parts) > 3 else ""
    eager = len(parts) > 4 and parts[4].strip() == "eager"
    big = IMG_DIR / f"{name}-1400.jpg"
    if not big.exists():
        raise SystemExit(f"Image not found: {big} (run tools/make_images.py)")
    w, h = jpeg_size(big)
    w8, _ = jpeg_size(IMG_DIR / f"{name}-800.jpg")
    base = f"{root}assets/img/{name}"
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<picture{" class=" + chr(34) + esc(cls) + chr(34) if cls else ""}>'
            f'<source type="image/webp" srcset="{base}-800.webp {w8}w, {base}-1400.webp {w}w" sizes="{sizes}">'
            f'<img src="{base}-1400.jpg" srcset="{base}-800.jpg {w8}w, {base}-1400.jpg {w}w" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{esc(alt)}" {load}></picture>')


def maps_url():
    return "https://www.google.com/maps/search/?api=1&query=" + quote(S["maps_query"])


def season_dates():
    y, m = TODAY.year, TODAY.month
    start = y if m >= 10 else (y - 1 if m == 1 else y)
    vf, vt = S["hours"]["schema"]["valid_from"], S["hours"]["schema"]["valid_through"]
    return f"{start}-{vf}", f"{start + 1}-{vt}"


def address_line(lang):
    a = S["address"]
    bits = [a["street"]] if a.get("street") else []
    bits.append(f'{a["town"][lang]} {a["postcode"]}')
    bits.append(a["region"][lang])
    if lang == "en":
        bits.append("Greece")
    return ", ".join(bits)


ICON = {
    "phone": '<svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>',
    "pin": '<svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>',
    "facebook": '<svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.8c0-.9.3-1.5 1.6-1.5h1.6V4.4c-.3 0-1.3-.1-2.4-.1-2.4 0-4 1.4-4 4.1v2.4H7.6V14h2.7v8z"/></svg>',
    "instagram": '<svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M12 7.3A4.7 4.7 0 1 0 12 16.7 4.7 4.7 0 0 0 12 7.3zm0 7.7a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm6-7.9a1.1 1.1 0 1 1-2.2 0 1.1 1.1 0 0 1 2.2 0zM21.9 8c-.1-1.6-.4-3-1.6-4.2S17.6 2.2 16 2.1C14.4 2 9.6 2 8 2.1 6.4 2.2 5 2.5 3.8 3.7S2.2 6.4 2.1 8C2 9.6 2 14.4 2.1 16c.1 1.6.4 3 1.6 4.2s2.6 1.5 4.2 1.6c1.6.1 6.4.1 8 0 1.6-.1 3-.4 4.2-1.6s1.5-2.6 1.6-4.2c.1-1.6.1-6.4 0-8z"/></svg>',
}


# ---------------------------------------------------------------- blocks
def contact_list(lang, root):
    t = T[lang]
    rows = [
        f'<div><dt>{t["phone"]}</dt><dd><a href="tel:{S["phone"]}">{esc(S["phone_display"] if lang == "el" else S["phone_display_intl"])}</a></dd></div>',
    ]
    if S.get("email"):
        rows.append(f'<div><dt>{t["email"]}</dt><dd><a href="mailto:{esc(S["email"])}">{esc(S["email"])}</a></dd></div>')
    rows.append(f'<div><dt>{t["address"]}</dt><dd>{esc(address_line(lang))}<br>'
                f'<a href="{esc(maps_url())}" rel="noopener" target="_blank">{t["maps"]}</a></dd></div>')
    return '<dl class="facts">' + "".join(rows) + "</dl>"


def hours_list(lang):
    h = S["hours"]
    rows = [f'<div><dt>{esc(h["months"][lang])}</dt><dd>{esc(h["days"][lang])} {esc(h["time"])}</dd></div>']
    if h["offseason"].get(lang):
        rows.append(f'<div><dt>{T[lang]["offseason"]}</dt><dd>{esc(h["offseason"][lang])}</dd></div>')
    return '<dl class="facts">' + "".join(rows) + "</dl>"


def messaging_buttons(lang):
    m = S.get("mobile", "").replace(" ", "")
    if not m:
        return ""
    digits = m.lstrip("+")
    return ('<p class="msg-buttons">'
            f'<a class="btn btn-ghost" href="viber://chat?number=%2B{digits}">Viber</a> '
            f'<a class="btn btn-ghost" href="https://wa.me/{digits}" rel="noopener" target="_blank">WhatsApp</a></p>')


def social_links():
    out = [f'<a href="{esc(u)}" rel="noopener" target="_blank" aria-label="{k.capitalize()}">{ICON[k]}</a>'
           for k, u in S.get("social", {}).items() if not k.startswith("_") and u and k in ICON]
    return f'<p class="social">{"".join(out)}</p>' if out else ""


def legal_line(lang):
    L = S.get("legal", {})
    bits = []
    if L.get("vat"):
        bits.append(f'{T[lang]["vat"]} {esc(L["vat"])}')
    if L.get("gemi"):
        bits.append(f'{T[lang]["gemi"]} {esc(L["gemi"])}')
    return "".join(f"<span>{b}</span>" for b in bits)


# ---------------------------------------------------------------- templating
FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def read_page(path: Path):
    text = path.read_text(encoding="utf-8")
    meta = {}
    m = FRONT.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    return meta, text


def fill(text, lang, root):
    def inc(m):
        p = SRC / "partials" / lang / f"{m.group(1)}.html"
        return p.read_text(encoding="utf-8")
    for _ in range(3):
        text = re.sub(r"\{\{include:([\w-]+)\}\}", inc, text)

    h = S["hours"]
    simple = {
        "root": root,
        "phone": S["phone"],
        "tel": "tel:" + S["phone"],
        "phone_display": S["phone_display"],
        "phone_intl": S["phone_display_intl"],
        "email": S.get("email", ""),
        "name": S["name"][lang],
        "founded": str(S["founded"]),
        "year": str(TODAY.year),
        "hours_months": h["months"][lang],
        "hours_days": h["days"][lang],
        "hours_time": h["time"],
        "town": S["address"]["town"][lang],
        "region": S["address"]["region"][lang],
        "postcode": S["address"]["postcode"],
        "address": address_line(lang),
        "maps_url": maps_url(),
        "season_label": S["season"]["label"][lang],
        "contact_list": contact_list(lang, root),
        "hours_list": hours_list(lang),
        "messaging_buttons": messaging_buttons(lang),
        "company": S["legal"].get("company_name") or S["name"][lang],
        "legal_ids": ", ".join(b for b in (
            f'{T[lang]["vat"]} {S["legal"]["vat"]}' if S["legal"].get("vat") else "",
            f'{T[lang]["gemi"]} {S["legal"]["gemi"]}' if S["legal"].get("gemi") else "") if b),
        "privacy_email": S.get("email") or S["phone_display_intl"],
        "season_state": T[lang]["season_open" if S["season"].get("open") else "season_closed"].capitalize(),
        "season_cta": SEASON_CTA[lang][bool(S["season"].get("open"))],
        "icon_phone": ICON["phone"],
        "maps_embed": "https://maps.google.com/maps?q=" + quote(S["maps_query"]) + "&t=m&z=14&ie=UTF8&output=embed",
        "email_block": (f'<section><h2>Email</h2><p><a href="mailto:{esc(S["email"])}">{esc(S["email"])}</a></p></section>'
                        if S.get("email") else ""),
    }
    raw = {"root", "maps_url", "maps_embed", "tel", "contact_list", "hours_list", "messaging_buttons",
           "icon_phone", "email_block"}
    text = re.sub(r"\{\{img:([^}]+)\}\}", lambda m: picture(root, m.group(1)), text)
    text = re.sub(r"\{\{href:([\w-]+)\}\}", lambda m: rel(root, page_path(m.group(1), lang)), text)
    text = re.sub(r"\{\{href-(el|en):([\w-]+)\}\}", lambda m: rel(root, page_path(m.group(2), m.group(1))), text)

    def var(m):
        k = m.group(1)
        if k not in simple:
            raise SystemExit(f"Unknown placeholder {{{{{k}}}}}")
        return simple[k] if k in raw else esc(simple[k])
    return re.sub(r"\{\{([\w-]+)\}\}", var, text)


SEASON_CTA = {
    "el": {True: "Η σεζόν τρέχει. Κλείστε τη σειρά σας με ένα τηλεφώνημα.",
           False: "Η επόμενη σεζόν ξεκινά τον Οκτώβριο. Καλέστε μας για πληροφορίες."},
    "en": {True: "The season is on. Book your milling slot with one call.",
           False: "The next season starts in October. Call us for information."},
}


def json_ld(lang):
    a = S["address"]
    vf, vt = season_dates()
    biz = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": S["domain"] + "/#mill",
        "name": S["name"][lang],
        "alternateName": S["name"]["en" if lang == "el" else "el"],
        "description": T[lang]["f_about"],
        "url": url("home", lang),
        "telephone": S["phone"],
        "image": S["domain"] + "/assets/img/og-image.jpg",
        "logo": S["domain"] + "/assets/img/logo.png",
        "foundingDate": str(S["founded"]),
        "address": {k: v for k, v in {
            "@type": "PostalAddress",
            "streetAddress": a.get("street") or None,
            "addressLocality": a["town"][lang],
            "addressRegion": a["region"][lang],
            "postalCode": a["postcode"].replace(" ", ""),
            "addressCountry": a["country"],
        }.items() if v},
        "hasMap": maps_url(),
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "opens": S["hours"]["schema"]["opens"],
            "closes": S["hours"]["schema"]["closes"],
            "validFrom": vf,
            "validThrough": vt,
        }],
    }
    if S.get("email"):
        biz["email"] = S["email"]
    if S["geo"].get("lat") and S["geo"].get("lng"):
        biz["geo"] = {"@type": "GeoCoordinates", "latitude": S["geo"]["lat"], "longitude": S["geo"]["lng"]}
    same = [u for k, u in S.get("social", {}).items() if not k.startswith("_") and u]
    if same:
        biz["sameAs"] = same
    return '<script type="application/ld+json">' + json.dumps(biz, ensure_ascii=False) + "</script>"


ASSET_V = ""


def layout(key, lang, meta, body, root, is404=False):
    t = T[lang]
    other = "en" if lang == "el" else "el"
    title = meta.get("title", S["name"][lang])
    desc = meta.get("description", "")
    hidden = key == "oil" and not feature_on("oil_page")
    robots = meta.get("robots", "noindex" if hidden else "")
    canonical = url(key, lang) if key else ""

    alt_links = ""
    if key and not robots:
        alt_links = (f'<link rel="alternate" hreflang="el" href="{url(key, "el")}">'
                     f'<link rel="alternate" hreflang="en" href="{url(key, "en")}">'
                     f'<link rel="alternate" hreflang="x-default" href="{url(key, "el")}">')

    # menu
    items = []
    for k, (_, _, show) in PAGES.items():
        if not feature_on(show):
            continue
        cur = ' aria-current="page"' if k == key else ""
        items.append(f'<li><a href="{rel(root, page_path(k, lang))}"{cur}>{NAV[lang][k]}</a></li>')
    other_href = rel(root, page_path(key or "home", other))

    season = ""
    if S["season"].get("show"):
        state = t["season_open"] if S["season"].get("open") else t["season_closed"]
        season = (f'<div class="season-bar{"" if S["season"].get("open") else " is-closed"}"><div class="wrap">'
                  f'<span class="season-dot" aria-hidden="true"></span>'
                  f'<strong>{esc(S["season"]["label"][lang])}</strong><span class="sr-only"> ({state})</span>'
                  f'<span class="season-text">{esc(S["season"]["text"][lang])}</span>'
                  f'<a class="season-phone" href="tel:{S["phone"]}">{esc(S["phone_display"] if lang == "el" else S["phone_display_intl"])}</a></div></div>')

    logo = (f'<picture><source type="image/webp" srcset="{root}assets/img/logo.webp">'
            f'<img src="{root}assets/img/logo.png" width="560" height="292" alt="{esc(t["home_alt"])}"></picture>')

    footer_nav = "".join(
        f'<li><a href="{rel(root, page_path(k, lang))}">{NAV[lang][k]}</a></li>'
        for k, (_, _, show) in PAGES.items() if feature_on(show))
    footer_nav += f'<li><a href="{rel(root, page_path("privacy", lang))}">{t["privacy"]}</a></li>'

    preload = "".join(
        f'<link rel="preload" href="{root}assets/fonts/{f}" as="font" type="font/woff2" crossorigin>'
        for f in (["gfs-didot-greek-400-normal.woff2", "commissioner-greek-wght-normal.woff2"] if lang == "el"
                  else ["gfs-didot-latin-400-normal.woff2", "commissioner-latin-wght-normal.woff2"]))

    og_locale = "el_GR" if lang == "el" else "en_GB"
    phone_label = esc(S["phone_display"] if lang == "el" else S["phone_display_intl"])
    page_class = meta.get("body_class", f"page-{key or '404'}")
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
{f'<meta name="description" content="{esc(desc)}">' if desc else ''}
{f'<meta name="robots" content="{robots}">' if robots else ''}
{f'<link rel="canonical" href="{canonical}">' if canonical and not robots else ''}
{alt_links}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(S['name'][lang])}">
<meta property="og:title" content="{esc(title)}">
{f'<meta property="og:description" content="{esc(desc)}">' if desc else ''}
{f'<meta property="og:url" content="{canonical}">' if canonical else ''}
<meta property="og:image" content="{S['domain']}/assets/img/og-image.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc('Φρέσκο ελαιόλαδο από τη γραμμή του ελαιοτριβείου Μαρκόπουλος' if lang == 'el' else 'Fresh olive oil flowing from the Markopoulos mill line')}">
<meta property="og:locale" content="{og_locale}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#2b3820">
{preload}
<link rel="stylesheet" href="{root}assets/css/style.css?v={ASSET_V}">
<link rel="icon" href="{root}favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="{root}assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="{root}assets/img/apple-touch-icon.png">
<script>document.documentElement.classList.add('js')</script>
{json_ld(lang)}
</head>
<body class="{page_class}">
<a class="skip-link" href="#main">{t['skip']}</a>
{season}
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{rel(root, page_path('home', lang))}">{logo}</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" data-open="{t['menu']}" data-close="{t['close']}"><span class="nav-toggle-bars" aria-hidden="true"></span><span class="nav-toggle-text">{t['menu']}</span></button>
    <nav id="site-nav" class="site-nav" aria-label="{t['main_nav']}">
      <ul>{''.join(items)}</ul>
      <div class="nav-extra">
        <a class="lang-switch" href="{other_href}" hreflang="{t['other_lang_code']}" lang="{t['other_lang_code']}">{t['other_lang']}</a>
        <a class="btn btn-call" href="tel:{S['phone']}">{ICON['phone']}<span>{phone_label}</span></a>
      </div>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div class="f-brand">
      <a class="brand" href="{rel(root, page_path('home', lang))}"><img src="{root}assets/img/logo.png" width="560" height="292" alt="{esc(S['name'][lang])}" loading="lazy"></a>
      <p>{t['f_about']}</p>
      {social_links()}
    </div>
    <div class="f-col">
      <h2 class="f-title">{t['f_contact']}</h2>
      {contact_list(lang, root)}
    </div>
    <div class="f-col">
      <h2 class="f-title">{t['f_hours']}</h2>
      {hours_list(lang)}
    </div>
    <nav class="f-col" aria-label="{t['f_pages']}">
      <h2 class="f-title">{t['f_pages']}</h2>
      <ul class="f-links">{footer_nav}</ul>
    </nav>
  </div>
  <div class="wrap"><div class="f-legal">
    <span>© {TODAY.year} {esc(S['legal'].get('company_name') or S['name'][lang])}</span>
    {legal_line(lang)}
    <a href="{other_href}" hreflang="{t['other_lang_code']}" lang="{t['other_lang_code']}">{t['other_lang']}</a>
  </div></div>
</footer>
<div class="callbar" role="region" aria-label="{t['call']}">
  <a class="callbar-call" href="tel:{S['phone']}">{ICON['phone']}<span>{t['call']} {phone_label}</span></a>
  <a class="callbar-map" href="{esc(maps_url())}" rel="noopener" target="_blank">{ICON['pin']}<span>{t['directions']}</span></a>
</div>
<script src="{root}assets/js/main.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------- extra files
def sitemap():
    rows = []
    for k, (_, _, show) in PAGES.items():
        if k in ("thanks",) or (k == "oil" and not feature_on("oil_page")):
            continue
        for lang in LANGS:
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{url(k, l)}"/>' for l in LANGS)
            rows.append(f"<url><loc>{url(k, lang)}</loc><lastmod>{TODAY.isoformat()}</lastmod>{alts}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(rows) + "\n</urlset>\n")


def robots():
    return f"User-agent: *\nDisallow: /contact.php\n\nSitemap: {S['domain']}/sitemap.xml\n"


def php_str(s):
    return "'" + str(s).replace("\\", "\\\\").replace("'", "\\'") + "'"


def contact_php():
    tpl = (SRC / "static-templates" / "contact.php").read_text(encoding="utf-8")
    return (tpl.replace("%%TO%%", php_str(S.get("email", "")))
               .replace("%%FROM%%", php_str(S.get("form_sender", "")))
               .replace("%%SITE%%", php_str(S["name"]["el"]))
               .replace("%%THANKS_EL%%", php_str("/" + page_path("thanks", "el")))
               .replace("%%THANKS_EN%%", php_str("/" + page_path("thanks", "en")))
               .replace("%%BACK_EL%%", php_str("/" + page_path("contact", "el")))
               .replace("%%BACK_EN%%", php_str("/" + page_path("contact", "en"))))


# ---------------------------------------------------------------- checks
def check_links():
    problems = []
    for f in OUT.rglob("*.html"):
        txt = f.read_text(encoding="utf-8")
        for m in re.finditer(r'(?:href|src|srcset)="([^"]+)"', txt):
            for ref in m.group(1).split(","):
                ref = ref.strip().split(" ")[0]
                if not ref or ref.startswith(("http", "mailto:", "tel:", "#", "viber:", "data:")):
                    continue
                ref = ref.split("#")[0].split("?")[0]
                if f.name == "404.html" and ref.startswith("/"):
                    target = OUT / ref.lstrip("/")
                else:
                    target = (f.parent / ref).resolve()
                if target.is_dir():
                    target = target / "index.html"
                if not target.exists():
                    problems.append(f"{f.relative_to(OUT)} -> {ref}")
    return problems


def check_todos():
    found = []
    for f in OUT.rglob("*.html"):
        if f.stem in ("to-ladi-mas", "our-oil") and not feature_on("oil_page"):
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if "[[" in line:
                found.append(f"{f.relative_to(OUT)}:{n}")
    return found


# ---------------------------------------------------------------- main
def build():
    global ASSET_V
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SRC / "assets", OUT / "assets")
    for p in (SRC / "static").iterdir():
        (shutil.copytree if p.is_dir() else shutil.copy2)(p, OUT / p.name)
    h = hashlib.sha1()
    for p in sorted((SRC / "assets").rglob("*.*")):
        if p.suffix in (".css", ".js"):
            h.update(p.read_bytes())
    ASSET_V = h.hexdigest()[:8]

    count = 0
    for lang in LANGS:
        root = "" if lang == "el" else "../"
        for key, files in PAGES.items():
            src = SRC / "pages" / lang / files[0 if lang == "el" else 1]
            meta, body = read_page(src)
            html_out = layout(key, lang, meta, fill(body, lang, root), root)
            pp = page_path(key, lang)
            dest = OUT / (pp + "index.html" if pp in ("", "en/") else pp)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html_out, encoding="utf-8")
            count += 1

    meta, body = read_page(SRC / "pages" / "404.html")
    (OUT / "404.html").write_text(layout(None, "el", meta, fill(body, "el", "/"), "/", True), encoding="utf-8")

    (OUT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (OUT / "robots.txt").write_text(robots(), encoding="utf-8")
    shutil.copy2(SRC / "static-templates" / "htaccess.txt", OUT / ".htaccess")
    (OUT / "contact.php").write_text(contact_php(), encoding="utf-8")

    print(f"Built {count + 1} pages into {OUT.relative_to(ROOT)}/")
    bad = check_links()
    if bad:
        print("BROKEN LINKS:\n  " + "\n  ".join(bad))
        sys.exit(1)
    print("Links: all internal links OK")
    todos = check_todos()
    if todos:
        print("Unfinished text markers [[...]] in visible pages:\n  " + "\n  ".join(todos))
    if not S.get("email"):
        print("Note: no email in site.json, the contact form cannot deliver messages.")


def make_zip():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    z = dist / f"site-upload-{TODAY:%Y%m%d}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(OUT).as_posix())
    print(f"Upload package: {z.relative_to(ROOT)}  ({z.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
    if "--zip" in sys.argv:
        make_zip()
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Preview: http://localhost:8000   (Ctrl+C to stop; the contact form needs the real host)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
