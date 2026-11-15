"""axellsdojo.com - a static site (no framework, no build tools beyond this script): the home page and one page per
plugin, generated from the same content as the repositories' README pages (~/axell-windows-port/brand/content.py and
typeset_suite.py). Screenshots are converted to WebP. Downloads resolve to the newest release files at view time
(GitHub's public releases API), with the release page as the fallback. Output: public/ (what Cloudflare serves)."""
import html, os, shutil, sys
from PIL import Image
sys.path.insert(0, os.path.expanduser("~/axell-windows-port/brand"))
from content import C, ORDER, SUITE_LINE
import typeset_suite as T

HOME = os.path.expanduser("~"); SITE = os.path.dirname(os.path.abspath(__file__)); OUT = f"{SITE}/public"
GH = "https://github.com/zmardanian"
PLUGINS = [r for r in ORDER if r != "axell-signature-dojo"]
SLUG = {r: r.replace("axell-", "") for r in ORDER}
NAME = {r: ("Axell 76" if r == "axell-76" else f"Axell {T.P[r][0]}") for r in ORDER}
KANJI = {r: T.P[r][1] for r in ORDER}
ACC = {r: T.P[r][2] for r in ORDER}            # the dark-theme accent: the site is dark
TAG = {r: T.P[r][4] for r in ORDER}
SPEC = {r: T.P[r][5] for r in ORDER}
e = html.escape
import hashlib
# a fingerprint per asset in its URL: a browser can never keep an outdated stylesheet or script after an update
VER = {f: hashlib.sha256(open(f"{SITE}/src/{f}", "rb").read()).hexdigest()[:10] for f in ("style.css", "site.js")}

def webp(src, dst, width=1600):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src); im = im.convert("RGBA") if im.mode in ("P", "LA") else im
    if im.width > width: im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=86, method=6)
    return im.size

def img(repo, path, width=1600):
    """copy a repository image into the site as WebP; returns (url, w, h)"""
    name = os.path.splitext(os.path.basename(path))[0] + ".webp"
    w, h = webp(f"{HOME}/{repo}/{path}", f"{OUT}/img/{SLUG[repo]}/{name}", width)
    return f"/img/{SLUG[repo]}/{name}", w, h

def seal(r, cls="seal"):
    k = KANJI[r]
    if not k: return f'<span class="{cls} seal-76" aria-hidden="true">76</span>'
    return f'<span class="{cls}{" seal-wide" if len(k) > 1 else ""}" aria-hidden="true">{e(k)}</span>'

STATS = [  # big numbers on the home page: every one from the plugin's own measured section
    ("axell-76", "2&times;", "closer to a real 1176LN than Universal Audio's own UADx 1176"),
    ("axell-velvet", "30&ndash;80&times;", "gentler on your vowels than a leading sibilance-aware de-esser"),
    ("axell-master", "0", "clipped samples after Opus, Vorbis, AAC and MP3 - the codecs streaming services use"),
    ("axell-gate", "7.7 dB", "less damage to the voice than a classic gate tuned perfectly for every take"),
    ("axell-duo-compressor", "0.6 dB", "from a real LA-2A's gain reduction, on music the model never saw"),
    ("axell-dereverb", "4.13", "speech quality (ViSQOL) from 3.96 - the research standard reaches 3.99"),
]

def head(title, desc, accent="#c9a25e", path="/", og="og.jpg"):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0b0d12">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://www.axellsdojo.com{path}">
<meta property="og:image" content="https://www.axellsdojo.com/img/{og}">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://www.axellsdojo.com{path}">
<link rel="icon" href="/img/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Great+Vibes&family=Jost:wght@400;500&family=Yuji+Syuku&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css?v={VER['style.css']}">
<style>:root{{--acc:{accent}}}</style>
</head>
<body>
<header class="nav">
  <a class="brand" href="/"><span class="seal seal-wide seal-sm" aria-hidden="true">道場</span><span>Axell's Dojo</span></a>
  <nav><a href="/#hear">Listen</a><a href="/#arsenal">Plugins</a><a href="/#proof">Proof</a><a href="/dojo/">The Dojo</a><a class="nav-cta" href="/#get">Download</a></nav>
</header>
"""

def foot():
    links = " ".join(f'<a href="/{SLUG[r]}/">{e(NAME[r])}</a>' for r in PLUGINS)
    return f"""<footer class="foot">
  <div class="foot-brand"><span class="script">Axell's Dojo</span><p>Free, open-source audio plugins for Windows and Linux, built from measurement.</p></div>
  <div class="foot-links">{links}<a href="/dojo/">Axell Signature Dojo</a></div>
  <div class="foot-small">
    <p>Made by Axell Yobag &middot; <a href="/credits/">Credits</a> &middot; <a href="mailto:axellpetre@protonmail.com">axellpetre@protonmail.com</a> &middot; <a href="{GH}">GitHub</a> &middot; Licensed under the GNU AGPLv3.</p>
    <p>1176, 1176LN, LA-2A, UADx and Universal Audio are trademarks of their owners. The Axell plugins are independent works, not affiliated with or endorsed by them; the names describe what was measured and compared.</p>
  </div>
</footer>
<script src="/site.js?v={VER['site.js']}" defer></script>
</body>
</html>
"""

def dl_buttons(repo, windows_label="Download for Windows", sub_w="Windows 10 / 11 &middot; 64-bit &middot; VST3", sub_l="x86_64 &middot; one-line install"):
    rel = f"{GH}/{repo}/releases/latest"
    pat_w = "setup.exe" if repo == "axell-signature-dojo" else "windows-x64.tar.gz"
    return f"""<div class="dl" data-repo="{repo}">
  <a class="btn btn-primary" href="{rel}" data-asset="{pat_w}"><b>{windows_label}</b><small>{sub_w}</small></a>
  <a class="btn btn-ghost" href="{rel}" data-asset="linux-x86_64.tar.gz"><b>Download for Linux</b><small>{sub_l}</small></a>
  <p class="dl-meta"><span class="ver" data-version>Latest release</span> &middot; <a href="{rel}">all files &amp; checksums</a> &middot; <a href="{GH}/{repo}">source on GitHub</a></p>
</div>"""

FEATURED = [("axell-gate", "vocals"), ("axell-dereverb", "vocals"), ("axell-master", "mix")]
def featured():
    cards = []
    for r, cat in FEATURED:
        it = next((x for x in AUDIO.get(SLUG[r], []) if x["cat"] == cat), None)
        if it: cards.append(ab_card(r, it, show_plugin=True))
    if not cards: return ""
    return f"""<section id="hear" class="section listen"><p class="label">HEAR THE DIFFERENCE</p><h2>Press play. Flip the switch.</h2>
<p class="lede">The same excerpt, before and after &mdash; both play in sync, so the only thing that changes is the plugin. Every plugin page has its own drums, melodic and vocal examples.</p>
<div class="abs">{"".join(cards)}</div></section>"""

from PIL import ImageDraw, ImageFont, ImageFilter
FONTS = {"script": f"{HOME}/axell-76/Resources/fonts/GreatVibes-Regular.ttf", "serif_i": f"{HOME}/axell-76-data/fonts/CormorantGaramond-MediumItalic.ttf",
         "sans": f"{HOME}/axell-76-data/fonts/Jost-Medium.ttf", "brush": f"{HOME}/axell-windows-port/brand/YujiSyuku-subset.ttf"}
def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def og_card(r, title, tag, shot_src, out):
    """a 1200x630 share card: the plugin's colour, its script name and seal, the tagline, the real interface"""
    W, H = 1200, 630; acc = hexrgb(ACC[r]) if r else hexrgb("#d3ad66")
    img = Image.new("RGB", (W, H), (11, 13, 18))
    glow = Image.new("RGB", (W, H), (11, 13, 18)); gd = ImageDraw.Draw(glow)
    gd.ellipse((-200, -300, 900, 500), fill=tuple(int(11 + (c - 11) * 0.30) for c in acc)); glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.blend(img, glow, 0.9); d = ImageDraw.Draw(img)
    if shot_src:
        sh = Image.open(shot_src).convert("RGB"); sh.thumbnail((700, 520))
        mask = Image.new("L", sh.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, sh.width - 1, sh.height - 1), 14, fill=255)
        shadow = Image.new("RGBA", (sh.width + 80, sh.height + 80), (0, 0, 0, 0)); ImageDraw.Draw(shadow).rounded_rectangle((40, 50, sh.width + 40, sh.height + 50), 18, fill=(0, 0, 0, 200))
        shadow = shadow.filter(ImageFilter.GaussianBlur(24)); x, y = 660, max(90, (H - sh.height) // 2 + 30)
        img.paste(shadow, (x - 40, y - 40), shadow); img.paste(sh, (x, y), mask)
    f = lambda k, n: ImageFont.truetype(FONTS[k], n)
    d.text((64, 70), "AXELL SIGNATURE", font=f("sans", 22), fill=acc, spacing=0)
    name = title; size = 120
    while d.textlength(name, font=f("script", size)) > 570 and size > 60: size -= 4
    d.text((58, 108), name, font=f("script", size), fill=acc)
    k = KANJI.get(r) if r else "道場"
    if k:
        sz = 76; sx = 64; sy = 108 + size + 34
        w = sz if len(k) == 1 else int(sz * 1.75)
        d.rounded_rectangle((sx, sy, sx + w, sy + sz), 6, fill=(192, 54, 44))
        d.text((sx + w / 2, sy + sz / 2), k, font=f("brush", int(sz * (0.62 if len(k) == 1 else 0.5))), fill=(255, 243, 230), anchor="mm")
        ty = sy + sz + 26
    else: ty = 108 + size + 40
    words = tag.split(); lines = [""]
    for wd in words:
        t = (lines[-1] + " " + wd).strip()
        if d.textlength(t, font=f("serif_i", 38)) > 540: lines.append(wd)
        else: lines[-1] = t
    for i, l in enumerate(lines[:3]): d.text((64, ty + i * 44), l, font=f("serif_i", 38), fill=(239, 230, 214))
    d.text((64, H - 92), "FREE  ·  WINDOWS  ·  LINUX  ·  VST3", font=f("sans", 20), fill=(169, 157, 141)); d.text((64, H - 60), "axellsdojo.com", font=f("sans", 22), fill=acc)
    img.save(out, quality=88)

def home():
    cards = []
    for r in PLUGINS:
        u, w, h = img(r, C[r]["shot"], 1200)
        cards.append(f"""<a class="card reveal" href="/{SLUG[r]}/" style="--acc:{ACC[r]}">
  <div class="card-shot"><img src="{u}" width="{w}" height="{h}" alt="{e(NAME[r])}" loading="lazy"></div>
  <div class="card-body">{seal(r)}<h3 class="script">{e(NAME[r])}</h3><p class="card-tag">{e(TAG[r])}</p>
  <p class="card-line">{e(SUITE_LINE[r])}</p></div></a>""")
    stats = "".join(f"""<a class="stat reveal" href="/{SLUG[r]}/" style="--acc:{ACC[r]}"><span class="stat-n">{n}</span>
  <span class="stat-t">{t}</span><span class="stat-p">{e(NAME[r])}</span></a>""" for r, n, t in STATS)
    seals = "".join(f'<a href="/{SLUG[r]}/" title="{e(NAME[r])}" style="--acc:{ACC[r]}">{seal(r)}</a>' for r in PLUGINS)
    d, dw, dh = img("axell-signature-dojo", C["axell-signature-dojo"]["shot"], 1600)
    body = f"""
<main>
<section class="hero">
  <div class="hero-bg" aria-hidden="true">道場</div>
  <p class="eyebrow">AXELL SIGNATURE &middot; THE SUITE</p>
  <h1 class="script hero-title">Axell's Dojo</h1>
  <p class="hero-tag">Nine plugins forged for the voice. Every claim, measured.</p>
  <p class="spec">WINDOWS &nbsp;&middot;&nbsp; LINUX &nbsp;&middot;&nbsp; VST3 &nbsp;&middot;&nbsp; FREE &amp; OPEN SOURCE</p>
  {dl_buttons("axell-signature-dojo", "Get the whole suite for Windows", "One installer &middot; the Dojo + all nine plugins", "The Dojo installs the plugins")}
  <p class="hosts">Works in any DAW that loads VST3, on Windows and Linux &mdash; FL Studio, Ableton Live, Cubase, Studio One, Bitwig, REAPER, Ardour</p>
  <div class="seal-row">{seals}</div>
</section>

{featured()}
<section id="arsenal" class="section">
  <p class="label">01 &nbsp; THE ARSENAL</p><h2>Nine plugins. One core.</h2>
  <p class="lede">Built as one family: they share a core library, so a breakthrough in one becomes a feature of the next &mdash; Velvet's sibilance network guards the esses in four of its siblings; Gate's voice detector holds the gain through your pauses in two more.</p>
  <div class="cards">{"".join(cards)}</div>
</section>

<section id="proof" class="section proof">
  <p class="label">02 &nbsp; PROOF, NOT PROMISES</p><h2>Measured against the real thing.</h2>
  <p class="lede">Every number below comes from published tests &mdash; against real hardware recordings, research benchmarks and the respected commercial plugins &mdash; with the scripts in each repository, so anyone can check them.</p>
  <div class="stats">{stats}</div>
</section>

<section class="section split reveal">
  <div><p class="label">03 &nbsp; THE DOJO</p><h2>Your chain, tuned to your voice.</h2>
  <p class="lede">Record or drop one dry take. The Dojo measures your voice and your room, tunes a complete vocal chain by rendering your take through the plugins, and saves it as presets inside the plugins &mdash; so your signature sound opens in whatever DAW you use, on Windows or Linux.</p>
  <ul class="ticks"><li>Installs, updates and restores every plugin &mdash; checksum-verified, for every DAW</li><li>Voice Profile: loudness, noise, pitch, esses, room and low end &mdash; tuned presets for Gate, Penta EQ, Duo Compressor and Velvet</li><li>Streaming Preview: hear your master as Spotify, Apple Music and YouTube will play it</li><li>REAPER extras: one-click sessions and twelve ready-made FX chains</li></ul>
  <a class="more" href="/dojo/">Inside the Dojo &rarr;</a></div>
  <div class="shot"><img src="{d}" width="{dw}" height="{dh}" alt="Axell Signature Dojo - the Plugins page" loading="lazy"></div>
</section>

<section id="get" class="section windows reveal">
  <p class="label">04 &nbsp; GET IT</p><h2>First-class on Windows. Native on Linux.</h2>
  <div class="tri">
    <div><h3>One installer</h3><p>The Axell Signature Suite installer puts the Dojo and all nine plugins on Windows 10 / 11 in one step &mdash; each one optional.</p></div>
    <div><h3>Tested on every build</h3><p>Every Windows build is made and tested by GitHub Actions and checked to sound the same as the Linux build &mdash; most of them bit for bit.</p></div>
    <div><h3>Free, for good</h3><p>Open source under the AGPLv3. No accounts, no licence keys, no subscriptions, nothing phoning home.</p></div>
  </div>
  {dl_buttons("axell-signature-dojo", "Get the suite for Windows", "One installer &middot; the Dojo + all nine plugins", "The Dojo, then the plugins from its Plugins page")}
</section>
</main>
"""
    return head("Axell's Dojo - nine audio plugins forged for the voice", "Free, open-source VST3 plugins for Windows and Linux - EQ, compression, gating, de-reverb, de-essing, saturation, reverb and mastering, each measured against the real thing.") + body + foot()


AUDIO = {}
SHORT = {"axell-penta-eq": "Penta EQ", "axell-duo-compressor": "Duo", "axell-gate": "Gate", "axell-dereverb": "De-Reverb", "axell-velvet": "Velvet", "axell-master": "Master", "axell-space": "Space", "axell-forbidden-seal": "Seal", "axell-76": "Axell 76"}
def ab_card(r, it, show_plugin=False):
    lvl = "level-matched" if it["matched"] else "not level-matched - loudness is the point"
    sim = f' &middot; <span class="sim">{e(it["simulated"])}</span>' if it["simulated"] else ""
    tag = f'<a class="ab-plugin" href="/{SLUG[r]}/" style="--acc:{ACC[r]}">{seal(r, "seal seal-sm")} {e(NAME[r])}</a>' if show_plugin else ""
    return f"""<div class="ab reveal" style="--acc:{ACC[r]}" data-a="{it['a']}" data-b="{it['b']}">
  {tag}<div class="ab-head"><span class="ab-cat">{e(it['cat'].upper())}</span><h3>{e(it['title'])}</h3></div>
  <p class="ab-note">{e(it['note'])}</p>
  <div class="ab-ctl">
    <button class="ab-play" aria-label="Play">&#9654;</button>
    <div class="ab-switch" role="group" aria-label="Compare"><button class="on" data-side="a">Original</button><button data-side="b">{e(SHORT[r])}</button></div>
  </div>
  <div class="ab-bar"><div class="ab-pos"></div></div>
  <p class="ab-meta">Preset <b>{e(it['preset'])}</b> &middot; {lvl}{sim}<br>Source: {e(it['source'])} &middot; <a href="/credits/">CC BY-SA 4.0</a></p>
</div>"""

def listen(r):
    items = AUDIO.get(SLUG[r], [])
    if not items: return ""
    cards = [ab_card(r, it) for it in items]
    return f"""<section class="section listen"><p class="label">HEAR IT</p><h2>Before and after.</h2>
<p class="lede">The same excerpt, the original and through {e(NAME[r])} with a factory preset. Press play, then switch &mdash; both play in sync, so you hear only the plugin. Headphones recommended.</p>
<div class="abs">{"".join(cards)}</div></section>"""

def plugin_page(r):
    c = C[r]; u, w, h = img(r, c["shot"], 1800)
    why = "".join(f'<div class="why reveal"><h3>{e(a)}</h3><p>{b}</p></div>' for a, b in c["why"])
    gal = []
    for p, t in c.get("gallery", []):
        if "workstation" in p: continue
        gu, gw, gh = img(r, p, 1200)
        gal.append(f'<figure class="reveal"><img src="{gu}" width="{gw}" height="{gh}" alt="{e(t)}" loading="lazy"><figcaption>{e(t)}</figcaption></figure>')
    others = "".join(f'<a href="/{SLUG[o]}/" style="--acc:{ACC[o]}">{seal(o)}<span>{e(NAME[o])}</span></a>' for o in PLUGINS if o != r)
    gallery = f'<section class="section"><p class="label">02 &nbsp; A CLOSER LOOK</p><h2>Every screen, every mode.</h2><div class="gallery">{"".join(gal)}</div></section>' if gal else ""
    body = f"""
<main style="--acc:{ACC[r]}">
<section class="hero hero-plugin">
  <div class="hero-bg" aria-hidden="true">{e(KANJI[r] or "76")}</div>
  <p class="eyebrow">AXELL SIGNATURE &middot; {e(SUITE_LINE[r].upper())}</p>
  <h1 class="script hero-title">{e(NAME[r])} {seal(r, "seal seal-lg")}</h1>
  <p class="hero-tag">{e(TAG[r])}</p>
  <p class="spec">{e(SPEC[r])}</p>
  {dl_buttons(r)}
  <div class="hero-shot reveal"><img src="{u}" width="{w}" height="{h}" alt="{e(c['alt'])}"></div>
  <p class="pitch"><b>{c['pitch'][0]}</b> {c['pitch'][1]}</p>
</section>
<section class="section">
  <p class="label">01 &nbsp; WHY IT'S DIFFERENT</p><h2>Five reasons, all measured.</h2>
  <div class="whys">{why}</div>
  <p class="note">Every figure comes from the plugin's own test suites and published benchmarks &mdash; the full measurements, the method and every version's history are on <a href="{GH}/{r}">GitHub</a>.</p>
</section>
{gallery}
{listen(r)}
<section class="section windows reveal">
  <p class="label">{"03" if gal else "02"} &nbsp; GET IT</p><h2>Windows first. Linux too.</h2>
  <p class="lede">Free and open source. Copy one folder into your VST3 folder &mdash; or install the whole suite in one go with the Axell Signature Suite installer, and let the Dojo keep everything up to date.</p>
  {dl_buttons(r)}
  <p class="hosts">Works in any DAW that loads VST3, on Windows and Linux &mdash; FL Studio, Ableton Live, Cubase, Studio One, Bitwig, REAPER, Ardour</p>
</section>
<section class="section family"><p class="label">THE SUITE</p><div class="family-row">{others}</div></section>
</main>
"""
    return head(f"{NAME[r]} - {TAG[r]}", f"{NAME[r]}: {c['pitch'][0]} Free VST3 for Windows and Linux.", ACC[r], f"/{SLUG[r]}/", f"og-{SLUG[r]}.jpg") + body + foot()

def dojo_page():
    r = "axell-signature-dojo"; c = C[r]; u, w, h = img(r, c["shot"], 1800)
    why = "".join(f'<div class="why reveal"><h3>{e(a)}</h3><p>{b}</p></div>' for a, b in c["why"])
    gal = []
    for p, t in c["gallery"]:
        if "workstation" in p: continue
        gu, gw, gh = img(r, p, 1400); gal.append(f'<figure class="reveal"><img src="{gu}" width="{gw}" height="{gh}" alt="{e(t)}" loading="lazy"><figcaption>{e(t)}</figcaption></figure>')
    body = f"""
<main style="--acc:{ACC[r]}">
<section class="hero hero-plugin">
  <div class="hero-bg" aria-hidden="true">道場</div>
  <p class="eyebrow">AXELL SIGNATURE &middot; THE SUITE'S HOME</p>
  <h1 class="script hero-title">Signature Dojo {seal(r, "seal seal-lg")}</h1>
  <p class="hero-tag">{e(TAG[r])}</p>
  <p class="spec">{e(SPEC[r])}</p>
  {dl_buttons(r, "Get the suite for Windows", "One installer &middot; the Dojo + all nine plugins", "The Dojo installs the plugins")}
  <p class="hosts">Works in any DAW that loads VST3, on Windows and Linux &mdash; FL Studio, Ableton Live, Cubase, Studio One, Bitwig, REAPER, Ardour</p>
  <div class="hero-shot reveal"><img src="{u}" width="{w}" height="{h}" alt="{e(c['alt'])}"></div>
  <p class="pitch"><b>{c['pitch'][0]}</b> {c['pitch'][1]}</p>
</section>
<section class="section"><p class="label">01 &nbsp; WHAT IT DOES</p><h2>Everything around the plugins.</h2><div class="whys">{why}</div></section>
<section class="section"><p class="label">02 &nbsp; A CLOSER LOOK</p><h2>Every page.</h2><div class="gallery">{"".join(gal)}</div></section>
</main>
"""
    return head("Axell Signature Dojo - your vocal chain, tuned to your voice", "Installs and updates the Axell plugins, tunes a complete vocal chain to your voice from one dry take, opens it in REAPER. One Windows installer carries the whole suite.", ACC[r], "/dojo/", "og-dojo.jpg") + body + foot()


def credits_page():
    body = """<main><section class="section"><p class="label">CREDITS</p><h2>The music in the examples.</h2>
<p class="lede">Every before/after example on this site is made from the <a href="https://github.com/OnAir-Music/OnAir-Music-Dataset">OnAir Music Dataset</a>
- stems of royalty-free songs by the <b>OnAir Music</b> project (Hrag, the Crescent MTL Project and SevagH), featuring <b>KXNE</b> and <b>Holocene</b>,
released under the <a href="https://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International</a> licence.</p>
<p>Tracks used: <i>Ronin</i> (feat. KXNE) - verse, drums, instrumental, full mix; <i>Set Me Free</i> - vocal; <i>Under My Skin</i> - piano;
<i>Bouncin Around</i> - drums; <i>Autumn in NY</i> - keys.</p>
<p><b>Changes made:</b> 14-second excerpts, set to a working level (-18 LUFS; -20 LUFS for the mastering examples), processed through the
Axell plugins with their factory presets, the processed version matched to the original's loudness (except the mastering examples), short
fades. Where marked, a small room (De-Reverb) or headphone bleed of the song's instrumental (Gate) was simulated before processing.
The processed excerpts are shared under the same licence, CC BY-SA 4.0. No endorsement by the artists or the OnAir Music project is implied.</p>
<p>Typefaces: Great Vibes, Cormorant Garamond, Jost and Yuji Syuku (SIL Open Font License), served by Google Fonts.</p>
</section></main>"""
    return head("Credits - Axell's Dojo", "The music used in the before/after examples and its licence.", path="/credits/") + body + foot()

def build():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(f"{OUT}/img", exist_ok=True)
    for f in ("style.css", "site.js", "_headers"): shutil.copy(f"{SITE}/src/{f}", f"{OUT}/{f}")
    import json
    AUDIO.update(json.load(open(f"{SITE}/src/audio/audio.json")))
    shutil.copytree(f"{SITE}/src/audio", f"{OUT}/audio", ignore=shutil.ignore_patterns("audio.json"))
    os.makedirs(f"{OUT}/credits", exist_ok=True); open(f"{OUT}/credits/index.html", "w").write(credits_page())
    open(f"{OUT}/index.html", "w").write(home())
    for r in PLUGINS:
        os.makedirs(f"{OUT}/{SLUG[r]}", exist_ok=True); open(f"{OUT}/{SLUG[r]}/index.html", "w").write(plugin_page(r))
    os.makedirs(f"{OUT}/dojo", exist_ok=True); open(f"{OUT}/dojo/index.html", "w").write(dojo_page())
    open(f"{OUT}/404.html", "w").write(head("Not found - Axell's Dojo", "This page does not exist.") + '<main><section class="hero"><div class="hero-bg" aria-hidden="true">迷</div>'
        '<p class="eyebrow">404</p><h1 class="script hero-title">Lost in the dojo</h1><p class="hero-tag">This page does not exist - but nine plugins do.</p>'
        '<p><a class="btn btn-primary" href="/"><b>Back to the suite</b></a></p></section></main>' + foot())
    for r in PLUGINS: og_card(r, NAME[r], TAG[r], f"{HOME}/{r}/{C[r]['shot']}", f"{OUT}/img/og-{SLUG[r]}.jpg")
    og_card("axell-signature-dojo", "Signature Dojo", TAG["axell-signature-dojo"], f"{HOME}/axell-signature-dojo/{C['axell-signature-dojo']['shot']}", f"{OUT}/img/og-dojo.jpg")
    # favicon: the Dojo's seal; social card: the home hero's look
    T.wideseal(f"{OUT}/img/favicon.png", "道場", "dark", 64)
    og_card("", "Axell's Dojo", "Nine plugins forged for the voice. Every claim, measured.", f"{HOME}/axell-gate/{C['axell-gate']['shot']}", f"{OUT}/img/og.jpg")
    open(f"{OUT}/robots.txt", "w").write("User-agent: *\nAllow: /\nSitemap: https://www.axellsdojo.com/sitemap.xml\n")
    urls = ["/"] + [f"/{SLUG[r]}/" for r in PLUGINS] + ["/dojo/"]
    open(f"{OUT}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>https://www.axellsdojo.com{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    print("built", OUT, sum(len(fs) for _, _, fs in os.walk(OUT)), "files")

if __name__ == "__main__": build()
