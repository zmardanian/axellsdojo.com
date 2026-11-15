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

def head(title, desc, accent="#c9a25e", path="/"):
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
<meta property="og:image" content="https://www.axellsdojo.com/img/og.jpg">
<link rel="canonical" href="https://www.axellsdojo.com{path}">
<link rel="icon" href="/img/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Great+Vibes&family=Jost:wght@400;500&family=Yuji+Syuku&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
<style>:root{{--acc:{accent}}}</style>
</head>
<body>
<header class="nav">
  <a class="brand" href="/"><span class="seal seal-wide seal-sm" aria-hidden="true">道場</span><span>Axell's Dojo</span></a>
  <nav><a href="/#arsenal">Plugins</a><a href="/#proof">Proof</a><a href="/dojo/">The Dojo</a><a class="nav-cta" href="/#get">Download</a></nav>
</header>
"""

def foot():
    links = " ".join(f'<a href="/{SLUG[r]}/">{e(NAME[r])}</a>' for r in PLUGINS)
    return f"""<footer class="foot">
  <div class="foot-brand"><span class="script">Axell's Dojo</span><p>Free, open-source audio plugins for Windows and Linux, built from measurement.</p></div>
  <div class="foot-links">{links}<a href="/dojo/">Axell Signature Dojo</a></div>
  <div class="foot-small">
    <p>Made by Axell Yobag &middot; <a href="mailto:axellpetre@protonmail.com">axellpetre@protonmail.com</a> &middot; <a href="{GH}">GitHub</a> &middot; Licensed under the GNU AGPLv3.</p>
    <p>1176, 1176LN, LA-2A, UADx and Universal Audio are trademarks of their owners. The Axell plugins are independent works, not affiliated with or endorsed by them; the names describe what was measured and compared.</p>
  </div>
</footer>
<script src="/site.js" defer></script>
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
  <p class="hosts">Runs in any VST3 host &mdash; FL Studio, Ableton Live, Cubase, Studio One, Bitwig, REAPER</p>
  <div class="seal-row">{seals}</div>
</section>

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
  <p class="lede">Record or drop one dry take. The Dojo measures your voice and your room, tunes a complete vocal chain by rendering your take through the plugins, and opens it in REAPER &mdash; your signature sound, one click away.</p>
  <ul class="ticks"><li>Installs, updates and restores every plugin &mdash; checksum-verified</li><li>Voice Profile: loudness, noise, pitch, esses, room and low end</li><li>Streaming Preview: hear your master as Spotify, Apple Music and YouTube will play it</li><li>Twelve ready-made REAPER chains</li></ul>
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
<section class="section windows reveal">
  <p class="label">{"03" if gal else "02"} &nbsp; GET IT</p><h2>Windows first. Linux too.</h2>
  <p class="lede">Free and open source. Copy one folder into your VST3 folder &mdash; or install the whole suite in one go with the Axell Signature Suite installer, and let the Dojo keep everything up to date.</p>
  {dl_buttons(r)}
  <p class="hosts">Runs in any VST3 host &mdash; FL Studio, Ableton Live, Cubase, Studio One, Bitwig, REAPER</p>
</section>
<section class="section family"><p class="label">THE SUITE</p><div class="family-row">{others}</div></section>
</main>
"""
    return head(f"{NAME[r]} - {TAG[r]}", f"{NAME[r]}: {c['pitch'][0]} Free VST3 for Windows and Linux.", ACC[r], f"/{SLUG[r]}/") + body + foot()

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
  <div class="hero-shot reveal"><img src="{u}" width="{w}" height="{h}" alt="{e(c['alt'])}"></div>
  <p class="pitch"><b>{c['pitch'][0]}</b> {c['pitch'][1]}</p>
</section>
<section class="section"><p class="label">01 &nbsp; WHAT IT DOES</p><h2>Everything around the plugins.</h2><div class="whys">{why}</div></section>
<section class="section"><p class="label">02 &nbsp; A CLOSER LOOK</p><h2>Every page.</h2><div class="gallery">{"".join(gal)}</div></section>
</main>
"""
    return head("Axell Signature Dojo - your vocal chain, tuned to your voice", "Installs and updates the Axell plugins, tunes a complete vocal chain to your voice from one dry take, opens it in REAPER. One Windows installer carries the whole suite.", ACC[r], "/dojo/") + body + foot()

def build():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(f"{OUT}/img", exist_ok=True)
    for f in ("style.css", "site.js", "_headers"): shutil.copy(f"{SITE}/src/{f}", f"{OUT}/{f}")
    open(f"{OUT}/index.html", "w").write(home())
    for r in PLUGINS:
        os.makedirs(f"{OUT}/{SLUG[r]}", exist_ok=True); open(f"{OUT}/{SLUG[r]}/index.html", "w").write(plugin_page(r))
    os.makedirs(f"{OUT}/dojo", exist_ok=True); open(f"{OUT}/dojo/index.html", "w").write(dojo_page())
    # favicon: the Dojo's seal; social card: the home hero's look
    T.wideseal(f"{OUT}/img/favicon.png", "道場", "dark", 64)
    og = Image.open(f"{HOME}/axell-signature-dojo/{C['axell-signature-dojo']['shot']}").convert("RGB"); og.thumbnail((1200, 1200))
    canvas = Image.new("RGB", (1200, 630), (11, 13, 18)); canvas.paste(og.crop((0, 0, 1200, 630)), (0, 0)); canvas.save(f"{OUT}/img/og.jpg", quality=85)
    open(f"{OUT}/robots.txt", "w").write("User-agent: *\nAllow: /\nSitemap: https://www.axellsdojo.com/sitemap.xml\n")
    urls = ["/"] + [f"/{SLUG[r]}/" for r in PLUGINS] + ["/dojo/"]
    open(f"{OUT}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>https://www.axellsdojo.com{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    print("built", OUT, sum(len(fs) for _, _, fs in os.walk(OUT)), "files")

if __name__ == "__main__": build()
