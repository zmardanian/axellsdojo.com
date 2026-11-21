"""axellsdojo.com - a static site (no framework, no build tools beyond this script): the home page and one page per
plugin, generated from the same content as the repositories' README pages (~/axell-windows-port/brand/content.py and
typeset_suite.py). Screenshots are converted to WebP. Downloads resolve to the newest release files at view time
(GitHub's public releases API), with the release page as the fallback. Output: public/ (what Cloudflare serves)."""
import html, json, os, shutil, sys
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
SPEC = {r: T.P[r][5].replace("VST3", "VST\u00ae3", 1) for r in ORDER}
# Steinberg's VST Compatible logo beside the VST3 claim on every page that promotes the plugins (VST usage guidelines;
# a footer-only logo is not enough). Official artwork from steinbergmedia/vst3_doc (artwork/), negative variant.
HOSTS = ('<p class="hosts"><img class="vst-logo" src="/img/vst-compatible.svg" width="64" height="41" alt="VST Compatible">'
         '<span>Works in any DAW that loads VST3, on Windows and Linux &mdash; FL Studio, Ableton Live, Cubase, Studio One, Bitwig, REAPER, Ardour'
         '<br><span class="tm">VST is a registered trademark of Steinberg Media Technologies GmbH.</span></span></p>')
e = html.escape
import hashlib
# a fingerprint per asset in its URL: a browser can never keep an outdated stylesheet or script after an update
CSS = open(f"{SITE}/src/fonts.css").read() + open(f"{SITE}/src/style.css").read()   # the site serves its own fonts (tools/fetch_fonts.py)
def media_url(path):
    """a media file's URL with its content hash: a replaced clip or loop gets a new URL, so no browser plays the old one
    from its cache (audio is cached for 7 days)"""
    return f"{path}?v={hashlib.sha256(open(f'{SITE}/src{path}', 'rb').read()).hexdigest()[:10]}"
VER = {"style.css": hashlib.sha256(CSS.encode()).hexdigest()[:10], "site.js": hashlib.sha256(open(f"{SITE}/src/site.js", "rb").read()).hexdigest()[:10]}
import re
FONT_URL = {n: u for u, n in re.findall(r"url\((/fonts/([a-z-]+?)-\d[^)]*)\)", CSS)}
PRELOAD = "".join(f'<link rel="preload" href="{FONT_URL[n]}" as="font" type="font/woff2" crossorigin>\n' for n in ("great-vibes", "jost", "cormorant-garamond", "yuji-syuku"))   # yuji: the 7 KB kanji seal, part of every hero title

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
    if w > 1000: webp(f"{HOME}/{repo}/{path}", f"{OUT}/img/{SLUG[repo]}/{name[:-5]}-800.webp", 800)
    return f"/img/{SLUG[repo]}/{name}", w, h

SIZES = dict(card="(max-width: 860px) 100vw, 400px", gallery="(max-width: 860px) 100vw, 600px", shot="(max-width: 860px) 100vw, 660px",
             hero="(max-width: 1100px) 100vw, 1100px")
def tag(u, w, h, alt, kind):
    """the <img>: phones get the 800 px file, the first image of a page loads first, the rest when scrolled to"""
    small = u[:-5] + "-800.webp"
    ss = f' srcset="{small} 800w, {u} {w}w" sizes="{SIZES[kind]}"' if os.path.exists(OUT + small) else ""
    load = ' fetchpriority="high"' if kind == "hero" else ' loading="lazy" decoding="async"'
    return f'<img src="{u}"{ss} width="{w}" height="{h}" alt="{e(alt)}"{load}>'

def seal(r, cls="seal"):
    k = KANJI[r]
    if not k: return f'<span class="{cls} seal-76" aria-hidden="true">76</span>'
    return f'<span class="{cls}{" seal-wide" if len(k) > 1 else ""}" aria-hidden="true">{e(k)}</span>'

STATS = [  # big numbers on the home page: every one from the plugin's own measured section
    ("axell-76", "0.44 dB", "from a real 1176LN on notes it never trained on - level with Universal Audio's own UADx 1176"),
    ("axell-velvet", "30&ndash;80&times;", "gentler on your vowels than a leading sibilance-aware de-esser"),
    ("axell-master", "0", "clipped samples after Opus, Vorbis, AAC and MP3 - the codecs streaming services use"),
    ("axell-gate", "7.7 dB", "less damage to the voice than a classic gate tuned perfectly for every take"),
    ("axell-duo-compressor", "0.6 dB", "from a real LA-2A's gain reduction, on music the model never saw"),
    ("axell-dereverb", "4.13", "speech quality (ViSQOL) from 3.96 - the research standard reaches 3.99"),
]

def ldjson(d):
    """structured data for search engines"""
    import json
    return "" if not d else '\n<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "</script>"

AUTHOR = {"@type": "Person", "name": "Axell Yobag", "url": "https://www.axellsdojo.com/contact/"}
def app_ld(name, desc, path, og, os_="Windows 10, Windows 11, Linux", repo=None):
    d = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": name, "description": desc, "url": f"https://www.axellsdojo.com{path}",
         "image": f"https://www.axellsdojo.com/img/{og}", "applicationCategory": "MultimediaApplication", "applicationSubCategory": "Audio plugin (VST3)",
         "operatingSystem": os_, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "author": AUTHOR,
         "isAccessibleForFree": True, "license": "https://www.gnu.org/licenses/agpl-3.0.html"}
    if repo:   # the released version and where the files and the source are (no ratings: there are none to show)
        import json
        rel = json.load(open(f"{SITE}/src/downloads.json")).get(DLSLUG(repo), {})
        ver = (rel.get("windows") or rel.get("linux") or {}).get("version")
        if ver: d["softwareVersion"] = ver
        d["downloadUrl"] = f"{GH}/{repo}/releases/latest"
        d["sameAs"] = f"{GH}/{repo}"
    return d

def head(title, desc, accent="#c9a25e", path="/", og="og.jpg", ld=None):
    return f"""<!doctype html>
<html lang="en" class="no-js"><script>document.documentElement.className="js"</script>
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
{PRELOAD}<link rel="stylesheet" href="/style.css?v={VER['style.css']}">
<style>:root{{--acc:{accent}}}</style>{ldjson(ld)}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="nav">
  <a class="brand" href="/"><span class="seal seal-wide seal-sm" aria-hidden="true">道場</span><span>Axell's Dojo</span></a>
  <nav><a href="/#hear">Listen</a><a href="/#arsenal">Plugins</a><a href="/#proof">Proof</a><a href="/dojo/">The Dojo</a><a href="/contact/">About</a><a class="nav-support" href="{KOFI}" rel="noopener" aria-label="Support on Ko-fi">{CUP}<span>Support</span></a><a class="nav-cta" href="/#get">Download</a></nav>
</header>
"""

def foot():
    links = " ".join(f'<a href="/{SLUG[r]}/">{e(NAME[r])}</a>' for r in PLUGINS)
    return f"""<footer class="foot">
  <div class="foot-brand"><span class="script">Axell's Dojo</span><p>Free, open-source audio plugins for Windows and Linux, built from measurement.</p></div>
  <div class="foot-links">{links}<a href="/dojo/">Axell Signature Dojo</a></div>
  <div class="foot-small">
    <p>Made by <a href="/contact/">Axell Yobag</a> &middot; <a href="/credits/">Credits</a> &middot; <a href="mailto:contact@axellsdojo.com">contact@axellsdojo.com</a> &middot; <a href="{GH}">GitHub</a> &middot; <a href="{KOFI}" rel="noopener">Support on Ko-fi</a> &middot; <a href="/impressum/">Impressum</a> &middot; <a href="/privacy/">Privacy</a> &middot; <a href="/code-signing/">Code signing policy</a> &middot; Licensed under the GNU AGPLv3.</p>
    <p>VST is a registered trademark of Steinberg Media Technologies GmbH. 1176, 1176LN, LA-2A, UADx and Universal Audio are trademarks of their owners. The Axell plugins are independent works, not affiliated with or endorsed by them; the names describe what was measured and compared.</p>
  </div>
</footer>
<script src="/site.js?v={VER['site.js']}" defer></script>
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "ce09d7285b9247608354813fd8e4a526"}}'></script>
</body>
</html>
"""

KOFI = "https://ko-fi.com/axellyobag"
CUP = ('<svg class="cup" viewBox="0 0 32 32" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">'
       '<path class="steam" d="M10 4c-1.5 2 1.5 3 0 5M15 3c-1.5 2 1.5 3 0 5M20 4c-1.5 2 1.5 3 0 5"/><path d="M5 13h19v7a7 7 0 0 1-7 7h-5a7 7 0 0 1-7-7z"/>'
       '<path d="M24 15h1.5a3.5 3.5 0 0 1 0 7H23.5"/></g><path d="M14.5 23.2l-3-2.9a1.9 1.9 0 0 1 2.7-2.7l.3.3.3-.3a1.9 1.9 0 0 1 2.7 2.7z" fill="currentColor"/></svg>')
def support(what, label="SUPPORT THE DOJO"):
    """the Ko-fi card: one per page, in the page's accent colour"""
    return f"""<section class="section support reveal">
  <div class="support-card">
    <div class="support-bg" aria-hidden="true">道</div>
    <div class="support-text">
      <p class="label">{label}</p>
      <h2>Free forever. <span class="script">Kept alive by you.</span></h2>
      <p class="lede">{what} costs nothing and never will &mdash; no subscriptions, no licence keys, no ads. If it has earned a place in your mixes, a tip keeps the Dojo going: test gear, this website and the long nights between releases.</p>
      <ul class="support-points"><li>One-time or monthly</li><li>From &euro;3, or any amount</li><li>No account needed</li></ul>
    </div>
    <div class="support-cta">
      <a class="btn btn-primary btn-kofi" href="{KOFI}" rel="noopener">{CUP}<b>Support on Ko-fi</b><small>ko-fi.com/axellyobag</small></a>
      <p class="support-note">Secure checkout on Ko-fi. Every supporter is part of the Dojo &mdash; thank you.</p>
    </div>
  </div>
</section>"""

DLSLUG = lambda repo: "dojo" if repo == "axell-signature-dojo" else SLUG[repo]
# a release whose notes open without a short bold headline gets one here (from its notes / README)
NEWS_POINT = {("axell-forbidden-seal", "v4.0.2"): "Faster, the same sound",
              # the November 2026 round: the user-facing fix first (the changelog opens with the wordmark title)
              ("axell-gate", "v4.0.3"): "Your DAW remembers the chosen preset; works with screen readers",
              ("axell-dereverb", "v4.0.2"): "Your DAW remembers the chosen preset; works with screen readers",
              ("axell-penta-eq", "v3.0.2"): "Your DAW remembers the chosen preset; works with screen readers",
              ("axell-duo-compressor", "v4.0.4"): "Your DAW remembers the chosen preset; works with screen readers",
              ("axell-velvet", "v3.0.5"): "Your DAW remembers the chosen preset; works with screen readers",
              ("axell-space", "v4.0.2"): "Your DAW remembers the chosen preset; works with screen readers",
              ("axell-forbidden-seal", "v4.0.3"): "Your DAW remembers the chosen preset; works with screen readers",
              ("axell-master", "v4.0.4"): "Your DAW remembers the chosen preset; works with screen readers",
              ("axell-76", "v3.2.1"): "Your DAW remembers the chosen preset; works with screen readers",
              ("axell-signature-dojo", "v3.3.4"): "Installs only releases signed by the suite's key"}

def downloads_manifest():
    """src/downloads.json for the Worker: per plugin the release files known now (its fallback when GitHub's API does not answer)"""
    import json, subprocess
    out, news = {}, {}
    for r in ORDER:
        rels = json.loads(subprocess.run(["gh", "api", f"repos/zmardanian/{r}/releases?per_page=6"], capture_output=True, text=True, check=True).stdout)
        suf = {"windows": "windows-x64-setup.exe" if r == "axell-signature-dojo" else "windows-x64.tar.gz", "linux": "linux-x86_64.tar.gz"}
        en = {"repo": r, "name": NAME[r] if r != "axell-signature-dojo" else "Signature Suite + Dojo", "suffix": suf}
        for k, sfx in suf.items():
            en[k] = next(({"url": a["browser_download_url"], "file": a["name"], "version": rel["tag_name"].lstrip("v")}
                          for rel in rels if not rel["draft"] and not rel["prerelease"] for a in rel["assets"] if a["name"].endswith(sfx)), None)
            if not en[k]: raise SystemExit(f"{r}: no {k} release file")
        out[DLSLUG(r)] = en
        # "what's new" for the page: the newest release's first bold point (or its heading), its date and link
        rel = next(x for x in rels if not x["draft"] and not x["prerelease"])
        body = rel.get("body") or ""
        m = re.search(r"^[-*] \*\*(.+?)\*\*", body, re.M) or re.search(r"^#+ .*? - (?!\d{4}-)(.+)$", body, re.M) or re.search(r"^[-*] (.{20,90}?)[.;,(]", body, re.M)
        news[DLSLUG(r)] = {"version": rel["tag_name"].lstrip("v"), "date": rel["published_at"][:10], "url": rel["html_url"],
                           "point": NEWS_POINT.get((r, rel["tag_name"])) or (m.group(1).strip().rstrip(".") if m else "")}
        if news[DLSLUG(r)]["point"]: news[DLSLUG(r)]["point"] = news[DLSLUG(r)]["point"][0].upper() + news[DLSLUG(r)]["point"][1:]
    json.dump(out, open(f"{SITE}/src/downloads.json", "w"), indent=1)
    json.dump(news, open(f"{SITE}/src/news.json", "w"), indent=1)

# SignPath Foundation asks the download page to say the project uses them for code signing (while applying: being set up;
# once accepted: "Free code signing provided by SignPath.io, certificate by SignPath Foundation")
SIGNPATH = ('<p class="dl-trust">Windows code signing: being set up with the <a href="https://signpath.org/" rel="noopener">SignPath '
            'Foundation</a>, free signing for open-source software &middot; <a href="/code-signing/">code signing policy</a></p>')

def dl_buttons(repo, windows_label="Download for Windows", sub_w="Windows 10 / 11 &middot; 64-bit &middot; VST3", sub_l="Ubuntu 22.04+ &middot; Debian 12+ &middot; Fedora", extras=True):
    rel = f"{GH}/{repo}/releases/latest"
    pat_w = "setup.exe" if repo == "axell-signature-dojo" else "windows-x64.tar.gz"
    return f"""<div class="dl" data-repo="{repo}">
  <a class="btn btn-primary" href="/get/{DLSLUG(repo)}/windows" rel="nofollow"><b>{windows_label}</b><small>{sub_w}</small></a>
  <a class="btn btn-ghost" href="/get/{DLSLUG(repo)}/linux" rel="nofollow"><b>Download for Linux</b><small>{sub_l}</small></a>
  <p class="dl-meta"><span class="ver">{ver_of(repo)}</span> &middot; <a href="{rel}">all files &amp; checksums</a> &middot; <a href="{GH}/{repo}">source on GitHub</a></p>{whats_new(repo)}
  <p class="dl-trust">No account &middot; no email &middot; no licence key &middot; open source &middot; <a href="/code-signing/">signed releases</a>{accessible(repo)}</p>{SIGNPATH if repo == "axell-signature-dojo" and extras else ""}{SAFE if repo == "axell-signature-dojo" and extras else ""}
</div>"""

# every control named for screen readers (JUCE's accessibility: Windows Narrator, macOS VoiceOver) from these releases on
ACCESSIBLE_FROM = {"gate": "4.0.3", "dereverb": "4.0.2", "penta-eq": "3.0.2", "duo-compressor": "4.0.4", "velvet": "3.0.5",
                   "space": "4.0.2", "forbidden-seal": "4.0.3", "master": "4.0.4", "76": "3.2.1"}
def ver_of(repo):
    import json
    try: v = json.load(open(f"{SITE}/src/news.json")).get(DLSLUG(repo), {}).get("version")
    except OSError: v = None
    return f"Version {v}" if v else "Latest release"

def accessible(repo):
    import json
    try: v = json.load(open(f"{SITE}/src/news.json")).get(DLSLUG(repo), {}).get("version", "0")
    except OSError: return ""
    need = ACCESSIBLE_FROM.get(DLSLUG(repo))
    t = lambda x: tuple(int(n) for n in x.split("."))
    return " &middot; works with screen readers" if need and t(v) >= t(need) else ""

def whats_new(repo):
    """the newest release's headline and date, from src/news.json (written with downloads.json)"""
    import json, datetime
    try: n = json.load(open(f"{SITE}/src/news.json")).get(DLSLUG(repo))
    except OSError: return ""
    if not n or not n.get("point"): return ""
    d = datetime.date.fromisoformat(n["date"]).strftime("%-d %b %Y")
    return f'\n  <p class="dl-news">New in {e(n["version"])} <span>({d})</span>: {e(n["point"])} &middot; <a href="{e(n["url"])}">release notes</a></p>'

# the suite installer is not code-signed (yet): say so before Windows does, and how to check the file
SAFE = """
  <details class="dl-help"><summary>Windows says &ldquo;Windows protected your PC&rdquo;?</summary>
  <p>The installer is free and not yet code-signed, so SmartScreen doesn't know it. Click <b>More info</b>, then <b>Run anyway</b>.
  To be sure it's the original file, compare its fingerprint with <code>SHA256SUMS.txt</code> on the release page &mdash; in PowerShell:
  <code>Get-FileHash .\\AxellSignatureSuite-*-setup.exe</code>. On Linux: <code>sha256sum -c SHA256SUMS.txt</code>.
  Every file is built from the public source on GitHub, and the checksums are signed &mdash; see the <a href="/code-signing/">code signing policy</a>.</p></details>"""

HIDE_AUDIO = set()
FEATURED = [("axell-forbidden-seal", "boom-bap"), ("axell-gate", "trap"), ("axell-penta-eq", "lo-fi")]     # one per genre
def featured():
    cards = []
    for r, cat in FEATURED:
        it = next((x for x in AUDIO.get(SLUG[r], []) if x["cat"] == cat), None)
        if it: cards.append(ab_card(r, it, show_plugin=True))
    if not cards: return ""
    return f"""<section id="hear" class="section listen"><p class="label">HEAR THE DIFFERENCE</p><h2>Press play. Flip the switch.</h2>
<p class="lede">The same excerpt, before and after &mdash; both play in sync, so the only thing that changes is the plugin. Every plugin page has its own boom bap, trap and lo-fi examples.</p>
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
        cards.append(f"""<a class="card reveal" href="/{SLUG[r]}/" style="--acc:{ACC[r]}; --vt:seal-{SLUG[r]}">
  <div class="card-shot"{' style="--pos:50% 45%"' if r == "axell-76" else ""}>{tag(u, w, h, "", "card")}</div>
  <div class="card-body">{seal(r)}<h3>{e(NAME[r] if r == "axell-76" else NAME[r].replace("Axell ", ""))}</h3><p class="card-tag">{e(TAG[r])}</p>
  <p class="card-line">{e(SUITE_LINE[r])}</p></div></a>""")
    stats = "".join(f"""<a class="stat reveal" href="/{SLUG[r]}/" style="--acc:{ACC[r]}"><span class="stat-n">{n}</span>
  <span class="stat-t">{t}</span><span class="stat-p">{e(NAME[r])}</span></a>""" for r, n, t in STATS)
    seals = "".join(f'<a href="/{SLUG[r]}/" style="--acc:{ACC[r]}">{seal(r)}<span class="sr-only">{e(NAME[r])}</span></a>' for r in PLUGINS)
    d, dw, dh = img("axell-signature-dojo", C["axell-signature-dojo"]["shot"], 1600)
    body = f"""
<main>
<section class="hero">
  <div class="hero-bg" aria-hidden="true">道場</div>
  <p class="eyebrow">AXELL SIGNATURE &middot; THE SUITE</p>
  <h1 class="script hero-title">Axell's Dojo</h1>
  <p class="hero-tag">Nine plugins forged for the voice. Every claim, measured.</p>
  <p class="spec">WINDOWS &nbsp;&middot;&nbsp; LINUX &nbsp;&middot;&nbsp; VST&reg;3 &nbsp;&middot;&nbsp; FREE &amp; OPEN SOURCE</p>
  {dl_buttons("axell-signature-dojo", "Get the whole suite for Windows", "One installer &middot; the Dojo + all nine plugins", "The Dojo installs the plugins", extras=False)}
  <div class="hero-shot hero-home">{tag(d, dw, dh, "The Axell Signature Dojo: all nine plugins installed, checked and updated in one place", "hero")}</div>
  <div class="seal-row">{seals}</div>
  {HOSTS}
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
{support("The whole suite &mdash; nine plugins and the Dojo &mdash;")}

<section class="section split reveal">
  <div><p class="label">03 &nbsp; THE DOJO</p><h2>Your chain, tuned to your voice.</h2>
  <p class="lede">Record or drop one dry take. The Dojo measures your voice and your room, tunes a complete vocal chain by rendering your take through the plugins, and saves it as presets inside the plugins &mdash; so your signature sound opens in whatever DAW you use, on Windows or Linux.</p>
  <ul class="ticks"><li>Installs, updates and restores every plugin &mdash; checksum-verified, for every DAW</li><li>Voice Profile: loudness, noise, pitch, esses, room and low end &mdash; tuned presets for Gate, Penta EQ, Duo Compressor and Velvet</li><li>Streaming Preview: hear your master as Spotify, Apple Music and YouTube will play it</li><li>REAPER extras: one-click sessions and twelve ready-made FX chains</li></ul>
  <a class="more" href="/dojo/">Inside the Dojo &rarr;</a></div>
  <div class="shot">{tag(d, dw, dh, "Axell Signature Dojo - the Plugins page", "shot")}</div>
</section>

<section id="get" class="section windows reveal">
  <p class="label">04 &nbsp; GET IT</p><h2>First-class on Windows. Native on Linux.</h2>
  <div class="tri">
    <div><h3>One installer</h3><p>The Axell Signature Suite installer puts the Dojo and all nine plugins on Windows 10 / 11 in one step &mdash; each one optional.</p></div>
    <div><h3>Tested on every build</h3><p>Every Windows build is made and tested by GitHub Actions and checked to sound the same as the Linux build &mdash; most of them bit for bit. None of them allocates memory while it processes audio (pluginval 2.0, strictest level).</p></div>
    <div><h3>Free, for good</h3><p>Open source under the AGPLv3. No accounts, no licence keys, no subscriptions, no telemetry &mdash; the Dojo only asks GitHub for new versions.</p></div>
  </div>
  {dl_buttons("axell-signature-dojo", "Get the suite for Windows", "One installer &middot; the Dojo + all nine plugins", "The Dojo, then the plugins from its Plugins page")}
</section>
</main>
"""
    return head("Free Vocal Plugins (VST3) for Windows & Linux - Axell's Dojo", "Nine free, open-source VST3 vocal plugins for Windows and Linux: a 1176 compressor, LA-2A style opto, neural de-esser, de-reverb, noise gate, EQ, saturation, reverb and a mastering limiter - each measured against the real thing.", ld={"@context": "https://schema.org", "@type": "WebSite", "name": "Axell's Dojo", "url": "https://www.axellsdojo.com/", "author": AUTHOR}) + body + foot()


AUDIO = {}
GRAPHS = {}
GENRE = {"boom-bap": "boom bap", "rnb": "R&B"}
WF_BINS = 96
_WF_CACHE = f"{SITE}/.wf-cache.json"
_wf = json.load(open(_WF_CACHE)) if os.path.exists(_WF_CACHE) else {}
def wf_peaks(url):
    """the clip's loudness outline: WF_BINS peak values 0-100, decoded once with ffmpeg, cached by the file's hash"""
    import array, subprocess
    path = f"{SITE}/src{url}"; h = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    if h not in _wf:
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
        s = array.array("h", pcm); n = len(s) // WF_BINS
        _wf[h] = [max((abs(v) for v in s[i * n:(i + 1) * n]), default=0) for i in range(WF_BINS)]
        json.dump(_wf, open(_WF_CACHE, "w"))
    return _wf[h]

def wf_svg(a, b):
    """both clips' outlines on one scale (a level change stays visible), mirrored around the centre line"""
    top = max(max(a), max(b), 1)
    def path(p):
        y = [max(0.6, 19 * v / top) for v in p]
        up = " ".join(f"L{i + .5:.1f} {20 - v:.1f}" for i, v in enumerate(y)); dn = " ".join(f"L{i + .5:.1f} {20 + v:.1f}" for i, v in reversed(list(enumerate(y))))
        return f"M0 20 {up} L{WF_BINS} 20 {dn} Z"
    return (f'<svg viewBox="0 0 {WF_BINS} 40" preserveAspectRatio="none" aria-hidden="true">'
            f'<path class="wa" d="{path(a)}"/><path class="wb" d="{path(b)}"/></svg>')

SHORT ={"axell-penta-eq": "Penta EQ", "axell-duo-compressor": "Duo", "axell-gate": "Gate", "axell-dereverb": "De-Reverb", "axell-velvet": "Velvet", "axell-master": "Master", "axell-space": "Space", "axell-forbidden-seal": "Seal", "axell-76": "Axell 76"}
def ab_card(r, it, show_plugin=False):
    lvl = "level-matched" if it["matched"] else "not level-matched - loudness is the point"
    sim = f' &middot; <span class="sim">{e(it["simulated"])}</span>' if it["simulated"] else ""
    tag = f'<a class="ab-plugin" href="/{SLUG[r]}/" style="--acc:{ACC[r]}">{seal(r, "seal seal-sm")} {e(NAME[r])}</a>' if show_plugin else ""
    return f"""<div class="ab reveal" style="--acc:{ACC[r]}" data-side="a" data-a="{media_url(it['a'])}" data-b="{media_url(it['b'])}">
  {tag}<div class="ab-head"><span class="ab-cat">{e(GENRE.get(it['cat'], it['cat']).upper())}</span><h3>{e(it['title'])}</h3></div>
  <p class="ab-note">{e(it['note'])}</p>
  <div class="ab-ctl">
    <button class="ab-play" aria-label="Play">&#9654;</button>
    <div class="ab-switch" role="group" aria-label="Compare"><button class="on" data-side="a">Original</button><button data-side="b">{e(SHORT[r])}</button></div>
  </div>
  <div class="ab-bar" title="Click to jump">{(w := wf_svg(wf_peaks(it['a']), wf_peaks(it['b'])))}<div class="ab-pos">{w}</div></div>
  <p class="ab-meta">Preset <b>{e(it['preset'])}</b> &middot; {lvl}{sim}<br>Source: {e(it['source'])} &middot; <a href="/credits/">{e(it.get('license', 'CC BY-SA 4.0'))}</a></p>
</div>"""

def md_html(md):
    """the small Markdown subset of the plugin READMEs (bold, italic, code, links, nested lists, tables, paragraphs);
    raw HTML lines pass through, images and <picture> headings are dropped (the manual brings its own screenshots)"""
    import re
    def inline(t):
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
        return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m.group(2) if m.group(2).startswith("http") else "#"}">{m.group(1)}</a>', t)
    out, para, stack, table = [], [], [], []
    def flush():
        if para: out.append("<p>" + inline(" ".join(para)) + "</p>"); para.clear()
        while stack: out.append("</li></ul>"); stack.pop()
        if table:
            rows = [r for r in table if not re.match(r"^\|[\s:|-]+\|$", r)]
            cells = lambda r, t: "".join(f"<{t}>{inline(c.strip())}</{t}>" for c in r.strip().strip("|").split("|"))
            out.append("<div class='tbl'><table><thead><tr>" + cells(rows[0], "th") + "</tr></thead><tbody>"
                       + "".join("<tr>" + cells(r, "td") + "</tr>" for r in rows[1:]) + "</tbody></table></div>"); table.clear()
    for line in md.split("\n"):
        if re.match(r"\s*<(/?picture|source|img|br|/?p|/?div)\b", line) or not line.strip():
            flush(); continue
        if line.startswith("|"): para and flush(); table.append(line); continue
        m = re.match(r"^(\s*)[-*] (.*)", line)
        if m:
            if para: out.append("<p>" + inline(" ".join(para)) + "</p>"); para.clear()
            depth = len(m.group(1)) // 2
            while len(stack) > depth + 1: out.append("</li></ul>"); stack.pop()
            if len(stack) == depth + 1: out.append("</li><li>")
            else: out.append("<ul><li>"); stack.append(depth)
            out.append(inline(m.group(2))); continue
        if stack and line.startswith("  "): out.append(" " + inline(line.strip())); continue
        if stack: flush()
        para.append(line.strip())
    flush()
    return "\n".join(out)

MANUAL_SECTIONS = ("What it does", "How to use it", "The instrument")
def manual_text(r):
    """the README's own control reference: its 'What it does' / 'How to use it' / 'The instrument' sections"""
    import re
    md = open(f"{HOME}/{r}/README.md").read()
    parts = re.split(r'<picture>\s*<source[^>]*>\s*<img alt="0\d ([^"]*?) - [^"]*"[^>]*>\s*</picture>', md)
    return "".join(f"<h2>{e(parts[i])}</h2>\n" + md_html(parts[i + 1]) for i in range(1, len(parts) - 1, 2) if parts[i] in MANUAL_SECTIONS)

def manual_page(r):
    c = C[r]; u, w, h = img(r, c["shot"], 1800)
    gal = "".join(f'<figure>{tag(*img(r, p, 1200), t, "gallery")}<figcaption>{e(t)}</figcaption></figure>' for p, t in c.get("gallery", []))
    steps = f"""<ol class="steps">
  <li><b>Install.</b> Windows: run the Axell Signature Suite installer (or copy <code>{e(NAME[r])}.vst3</code> to
  <code>C:\\Program Files\\Common Files\\VST3</code>). Linux: unpack the archive and run <code>./install.sh</code>.</li>
  <li><b>Rescan.</b> Let your DAW rescan its VST3 plugins; {e(NAME[r])} appears under the vendor <i>Axell Yobag</i>.</li>
  <li><b>Insert it</b> on the track or bus it is made for, and start from a factory preset close to your material.</li>
  <li><b>Listen, then adjust</b> the few controls described below; A/B compares two settings without losing either.</li>
</ol>"""
    body = f"""
<main style="--acc:{ACC[r]}">
<section class="section legal manual">
  <p class="label">MANUAL &middot; {e(SUITE_LINE[r].upper())}</p><h1 class="h2">{e(NAME[r])}: getting started and every control</h1>
  <p class="lede">{e(TAG[r])} This page explains every control, with the plugin's own screens. <a href="/{SLUG[r]}/">Back to {e(NAME[r])}</a>.</p>
  <h2>Getting started</h2>{steps}
  <figure class="man-shot">{tag(u, w, h, c["alt"], "hero")}<figcaption>The full window, as it opens.</figcaption></figure>
  {closeup(r)}
  {manual_text(r)}
  {('<h2>Every screen, every mode</h2><div class="gallery">' + gal + '</div>') if gal else ""}
  <p class="note">The complete reference, measurements and version history are in the
  <a href="{GH}/{r}">repository on GitHub</a>.</p>
  {dl_buttons(r)}
</section>
</main>
"""
    return head(f"{NAME[r]} manual - getting started and every control", f"How to use {NAME[r]}: installing, the presets and every control explained, with screenshots.", path=f"/{SLUG[r]}/manual/") + body + foot()

def hero_loop(r):
    """the real plugin window, filmed while audio runs through it (each repo's GuiSnapshot with AXELL_VIDEO_DIR):
    a silent loop laid exactly over the screenshot; site.js starts it only when visible and motion is welcome"""
    v = f"/video/{SLUG[r]}.mp4"
    if not os.path.exists(f"{SITE}/src{v}"): return ""
    return f'<video class="hero-loop" muted loop playsinline preload="none" aria-hidden="true" tabindex="-1" data-src="{media_url(v)}"></video>'

def closeup(r):
    """one tight crop of the plugin's signature control with a short callout (src/img/closeups, cut from the screenshot)"""
    import json
    try: m = json.load(open(f"{SITE}/src/img/closeups/closeups.json")).get(r)
    except OSError: m = None
    if not m: return ""
    return (f'<figure class="closeup reveal"><img src="{m["src"]}" width="{m["w"]}" height="{m["h"]}" alt="{e(m["cap"])}" loading="lazy" decoding="async">'
            f'<figcaption><span class="dot" aria-hidden="true"></span>{e(m["cap"])}</figcaption></figure>')

def graph_svg(r):
    """what the plugin did to its trap example, measured: the average spectrum and the level over time, before (ink,
    dashed) and after (the plugin's colour). Inline SVG: no script, no image request."""
    g = GRAPHS.get(SLUG[r])
    if not g: return ""
    import math
    W, H, P = 520, 220, 34
    def poly(xs, ys, x0, x1, y0, y1):
        pts = []
        for x, y in zip(xs, ys):
            px = P + (x - x0) / (x1 - x0) * (W - 2 * P); py = 14 + (1 - (min(max(y, y0), y1) - y0) / (y1 - y0)) * (H - 40)
            pts.append(f"{px:.1f},{py:.1f}")
        return " ".join(pts)
    lx = [math.log10(f) for f in g["freq"]]; x0, x1 = math.log10(40), math.log10(18000)
    ticks = "".join(f'<text x="{P + (math.log10(f) - x0) / (x1 - x0) * (W - 2 * P):.0f}" y="{H - 8}">{t}</text>'
                    for f, t in [(100, "100"), (1000, "1k"), (10000, "10k")])
    spec = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Average spectrum before and after">{ticks}'
            f'<polyline class="g-a" points="{poly(lx, g["a"], x0, x1, -60, 0)}"/><polyline class="g-b" points="{poly(lx, g["b"], x0, x1, -60, 0)}"/></svg>')
    t = [i * 0.1 for i in range(len(g["la"]))]; lo = min(min(g["la"]), min(g["lb"])); lo = max(lo, max(max(g["la"]), max(g["lb"])) - 48)
    hi = max(max(g["la"]), max(g["lb"])) + 2
    lvl = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Level over time before and after"><text x="{P}" y="{H - 8}">0 s</text>'
           f'<text x="{W - P - 24}" y="{H - 8}">{t[-1]:.0f} s</text>'
           f'<polyline class="g-a" points="{poly(t, g["la"], 0, t[-1], lo, hi)}"/><polyline class="g-b" points="{poly(t, g["lb"], 0, t[-1], lo, hi)}"/></svg>')
    lv = "level-matched" if g["matched"] else "not level-matched"
    return f"""<div class="graphs reveal"><figure><figcaption>Tone: average spectrum</figcaption>{spec}</figure>
<figure><figcaption>Dynamics: level over time</figcaption>{lvl}</figure>
<p class="g-key"><span class="k-a">Original</span> <span class="k-b">{e(SHORT[r])}</span> &middot; measured on the &ldquo;{e(g["clip"])}&rdquo; example above ({lv})</p></div>"""

def listen(r):
    items = AUDIO.get(SLUG[r], [])
    if r in HIDE_AUDIO: items = []          # examples being redone (a synthetic room was a poor test for De-Reverb)
    if not items: return ""
    cards = [ab_card(r, it) for it in items]
    return f"""<section class="section listen"><p class="label">HEAR IT</p><h2>Before and after.</h2>
<p class="lede">The same excerpt, the original and through {e(NAME[r])} with a factory preset. Press play, then switch &mdash; both play in sync, so you hear only the plugin. Headphones recommended.</p>
<div class="abs">{"".join(cards)}</div>{graph_svg(r)}</section>"""

def plugin_page(r):
    c = C[r]; u, w, h = img(r, c["shot"], 1800)
    why = "".join(f'<div class="why reveal"><h3>{e(a)}</h3><p>{b}</p></div>' for a, b in c["why"])
    gal = []
    for p, t in c.get("gallery", []):
        if "workstation" in p: continue
        gu, gw, gh = img(r, p, 1200)
        gal.append(f'<figure class="reveal">{tag(gu, gw, gh, t, "gallery")}<figcaption>{e(t)}</figcaption></figure>')
    others = "".join(f'<a href="/{SLUG[o]}/" style="--acc:{ACC[o]}">{seal(o)}<span>{e(NAME[o])}</span></a>' for o in PLUGINS if o != r)
    gallery = f'<section class="section"><p class="label">02 &nbsp; A CLOSER LOOK</p><h2>Every screen, every mode.</h2><div class="gallery">{"".join(gal)}</div></section>' if gal else ""
    body = f"""
<main style="--acc:{ACC[r]}; --vt:seal-{SLUG[r]}">
<section class="hero hero-plugin">
  <div class="hero-bg" aria-hidden="true">{e(KANJI[r] or "76")}</div>
  <p class="eyebrow">AXELL SIGNATURE &middot; {e(SUITE_LINE[r].upper())}</p>
  <h1 class="script hero-title">{e(NAME[r])} {seal(r, "seal seal-lg")}</h1>
  <p class="hero-tag">{e(TAG[r])}</p>
  <p class="spec">{e(SPEC[r])}</p>
  {dl_buttons(r)}
  <p class="suite-up">Want all nine? One installer, one updater &rarr; <a href="/dojo/">get the whole suite</a> &middot; <a href="/{SLUG[r]}/manual/">read the manual</a></p>
  <div class="hero-shot rise">{tag(u, w, h, c["alt"], "hero")}{hero_loop(r)}</div>
  <p class="pitch"><b>{c['pitch'][0]}</b> {c['pitch'][1]}</p>
  {closeup(r)}
</section>
{listen(r)}
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
  {HOSTS}
</section>
{support(e(NAME[r]))}
<section class="section family"><p class="label">THE SUITE</p><div class="family-row">{others}</div></section>
</main>
"""
    return head(f"{NAME[r]} - free {SUITE_LINE[r]} plugin (VST3, Windows & Linux)", f"{NAME[r]}: {TAG[r]} {c['pitch'][0]} Free and open-source VST3 for Windows and Linux.", ACC[r], f"/{SLUG[r]}/", f"og-{SLUG[r]}.jpg", ld=app_ld(NAME[r], c['pitch'][0], f"/{SLUG[r]}/", f"og-{SLUG[r]}.jpg", repo=r)) + body + foot()

def dojo_page():
    r = "axell-signature-dojo"; c = C[r]; u, w, h = img(r, c["shot"], 1800)
    why = "".join(f'<div class="why reveal"><h3>{e(a)}</h3><p>{b}</p></div>' for a, b in c["why"])
    gal = []
    for p, t in c["gallery"]:
        if "workstation" in p: continue
        gu, gw, gh = img(r, p, 1400); gal.append(f'<figure class="reveal">{tag(gu, gw, gh, t, "gallery")}<figcaption>{e(t)}</figcaption></figure>')
    body = f"""
<main style="--acc:{ACC[r]}; --vt:seal-{SLUG[r]}">
<section class="hero hero-plugin">
  <div class="hero-bg" aria-hidden="true">道場</div>
  <p class="eyebrow">AXELL SIGNATURE &middot; THE SUITE'S HOME</p>
  <h1 class="script hero-title">Signature Dojo {seal(r, "seal seal-lg")}</h1>
  <p class="hero-tag">{e(TAG[r])}</p>
  <p class="spec">{e(SPEC[r])}</p>
  {dl_buttons(r, "Get the suite for Windows", "One installer &middot; the Dojo + all nine plugins", "The Dojo installs the plugins")}
  {HOSTS}
  <div class="hero-shot rise">{tag(u, w, h, c["alt"], "hero")}{hero_loop(r)}</div>
  <p class="pitch"><b>{c['pitch'][0]}</b> {c['pitch'][1]}</p>
</section>
<section class="section"><p class="label">01 &nbsp; WHAT IT DOES</p><h2>Everything around the plugins.</h2><div class="whys">{why}</div></section>
<section class="section"><p class="label">02 &nbsp; A CLOSER LOOK</p><h2>Every page.</h2><div class="gallery">{"".join(gal)}</div></section>
{support("The Dojo, like every Axell plugin,")}
</main>
"""
    return head("Axell Signature Dojo - free vocal chain tuner and plugin installer (Windows & Linux)", "Installs and updates the Axell plugins, tunes a complete vocal chain to your voice from one dry take, opens it in REAPER. One Windows installer carries the whole suite.", ACC[r], "/dojo/", "og-dojo.jpg",
        ld=dict(app_ld("Axell Signature Dojo", "Installs and updates the Axell plugins and tunes a complete vocal chain to your voice from one dry take.",
                       "/dojo/", "og-dojo.jpg", repo=r), applicationSubCategory="Audio plugin manager and vocal chain tuner")) + body + foot()


OWNER = ("Alexandru Georgian Petre", "Bahnhofstraße 62", "64404 Bickenbach", "Germany")
def owner_block():
    return "<p>" + "<br>".join(e(x) for x in OWNER) + '<br>Email: <a href="mailto:contact@axellsdojo.com">contact@axellsdojo.com</a>' \
        '<br>Contact form: <a href="/contact/#write">axellsdojo.com/contact</a></p>'

def impressum_page():
    body = f"""<main><section class="section legal"><p class="label">IMPRESSUM &middot; LEGAL NOTICE</p><h2>Impressum</h2>
<p class="lede">Angaben gem&auml;&szlig; &sect; 5 DDG &middot; Information according to &sect; 5 of the German Digital Services Act (DDG)</p>
<h3>Anbieter &middot; Provider</h3>{owner_block()}
<p>Axell Yobag is the artist name of the provider. Axell's Dojo and the Axell Signature plugins are a private
open-source project; voluntary tips are accepted on <a href="{KOFI}" rel="noopener">Ko-fi</a>.</p>
<h3>Verantwortlich f&uuml;r den Inhalt &middot; Responsible for the content</h3>
<p>according to &sect; 18 (2) MStV: Alexandru Georgian Petre, address as above.</p>
<h3>Haftung f&uuml;r Links &middot; Links</h3>
<p>This site links to external websites (GitHub, Ko-fi, the sources named on the credits page). Their operators are responsible
for their content. When the links were set, no unlawful content was apparent; if any becomes known, the link will be removed.</p>
<h3>Urheberrecht &middot; Copyright and licences</h3>
<p>The plugins, their source code and this website are published under the GNU AGPLv3. The audio examples are licensed under
CC BY-SA 4.0 (see <a href="/credits/">Credits</a>); the typefaces under the SIL Open Font License. VST is a registered trademark of
Steinberg Media Technologies GmbH. 1176, 1176LN, LA-2A, UADx and
Universal Audio are trademarks of their owners; the Axell plugins are independent works, not affiliated with or endorsed by them.</p>
<p class="note">Privacy: see the <a href="/privacy/">privacy policy</a>.</p>
</section></main>"""
    return head("Impressum - Axell's Dojo", "Legal notice (Impressum) of axellsdojo.com.", path="/impressum/") + body + foot()

def privacy_page():
    body = f"""<main><section class="section legal"><p class="label">PRIVACY &middot; DATENSCHUTZERKL&Auml;RUNG</p><h2>Privacy policy</h2>
<p class="lede">What happens to your data when you visit axellsdojo.com - in short: no accounts, no advertising, no tracking cookies,
and no IP address is ever stored by this site. As of 20 November 2026.</p>

<h3>1. Who is responsible</h3>{owner_block()}

<h3>2. Hosting and delivery (Cloudflare)</h3>
<p>The site is served by Cloudflare, Inc., 101 Townsend St., San Francisco, CA 94107, USA, which processes data on my behalf
(data processing agreement under Art. 28 GDPR). To deliver pages and protect the site against attacks, Cloudflare processes your
IP address, the time, the page requested, your browser's user agent and the referring page in its server logs, briefly and under its own
retention rules. Cloudflare is certified under the EU-U.S. Data Privacy Framework (Art. 45 GDPR); its data processing agreement also contains
the EU standard contractual clauses (Art. 46 GDPR) as a further safeguard. Legal basis: Art. 6 (1) (f) GDPR -
the legitimate interest in a secure, working website.</p>
<p>Cloudflare's bot protection may set a technically necessary cookie (<code>__cf_bm</code>, valid 30 minutes) that tells people from
automated attacks; it is required for the service you asked for (&sect; 25 (2) no. 2 TDDDG) and not used for anything else.</p>

<h3>3. Visitor statistics (Cloudflare Web Analytics)</h3>
<p>The pages load Cloudflare Web Analytics, which counts page views and load times without cookies, without storing IP addresses
and without following you across sites; I only see totals. Legal basis: Art. 6 (1) (f) GDPR - the legitimate interest in knowing
which pages are used.</p>

<h3>4. The download counter</h3>
<p>The download buttons go through <code>axellsdojo.com/get/...</code> before they forward you to the file on GitHub. Each download
stores: the time, the plugin, Windows or Linux, the version, the country and city and the name of your internet provider (derived by
Cloudflare from your IP address), the page you came from, your device type (e.g. Windows, iOS) and browser family. <b>Your IP
address itself is not stored.</b> It is used only for a moment to limit downloads from one address to ten a minute, so the counter
cannot be flooded. The records are kept in Cloudflare's D1 database and deleted automatically after 24 months. Legal basis:
Art. 6 (1) (f) GDPR - the legitimate interest in knowing how often and where the plugins are used.</p>
<p>If you open <code>axellsdojo.com/get/not-me</code>, a cookie (<code>axell_owner</code>, 10 years) marks your browser's downloads as
the author's own tests. It is only ever set when you open that address yourself.</p>

<h3>5. Downloads, Ko-fi and other links</h3>
<p>Plugin files are downloaded from GitHub (GitHub, Inc., USA); tips are handled by Ko-fi (Ko-fi Labs Limited, UK) and its
payment providers. When you follow such a link, the respective provider processes your data under its own privacy policy. This site
embeds nothing from them - no scripts, no frames, no tracking pixels. Fonts, images and audio are served from this site only; no
request goes to a font or media service.</p>

<h3>6. Email and the contact form</h3>
<p>If you write to contact@axellsdojo.com, the message is forwarded by Cloudflare Email Routing to my mailbox and kept as long as
needed to answer it and for any follow-up. Legal basis: Art. 6 (1) (b) or (f) GDPR.</p>
<p>The <a href="/contact/#write">contact form</a> sends your name (optional), your email address and your message the same way:
as an email through Cloudflare's email service to my mailbox, where it is kept as long as needed to answer it. The website itself
keeps no copy; it notes only the time of each sent message (no content, no address, no IP address) to stop mass sending, and deletes
that note after 30 days. Legal basis: Art. 6 (1) (b) or (f) GDPR.</p>

<h3>7. Your rights</h3>
<p>You have the right to access (Art. 15), rectification (Art. 16), erasure (Art. 17), restriction of processing (Art. 18), data
portability (Art. 20) and to <b>object</b> to processing based on legitimate interests (Art. 21 GDPR). Write to
contact@axellsdojo.com. You may also complain to a data protection authority - for me, Der Hessische Beauftragte f&uuml;r Datenschutz
und Informationsfreiheit, Wiesbaden (datenschutz.hessen.de). There is no automated decision-making or profiling.</p>
</section></main>"""
    return head("Privacy policy - Axell's Dojo", "Privacy policy (Datenschutzerklärung) of axellsdojo.com.", path="/privacy/") + body + foot()

MINISIGN_PUB = open(os.path.expanduser("~/.minisign/axell.pub")).read().split("\n")[1].strip()

def signing_page():
    body = f"""<main><section class="section legal"><p class="label">SECURITY &middot; CODE SIGNING POLICY</p><h2>Code signing policy</h2>
<p class="lede">How the Axell plugins and the Dojo are built, signed and checked, so you can trust that a download is exactly what was
published from the open source code. As of 20 November 2026.</p>

<h3>1. What is built, and where</h3>
<p>Every release is built from the public source code on <a href="{GH}">GitHub</a> (GNU AGPLv3). The Windows files - the nine plugins
(<code>.vst3</code>), the Axell Signature Dojo and the Axell Signature Suite installer - are built only by GitHub Actions, from the commit
and tag named in each release, and tested there (the plugins' own test suites, pluginval at strictness 10, a sound match with the Linux
build). The Linux archives are built on Ubuntu 22.04 from the same tag.</p>

<h3>2. Windows code signing</h3>
<p>Windows code signing is being set up with the SignPath Foundation, which signs open source software for free. Until that is in place,
the Windows files are not code-signed, and Windows SmartScreen may show "Windows protected your PC" for the suite installer (choose
More info, then Run anyway). Once it is active, signed releases carry:
<i>Free code signing provided by <a href="https://about.signpath.io">SignPath.io</a>, certificate by <a href="https://signpath.org">SignPath Foundation</a></i>.
Only builds from GitHub Actions are ever submitted for signing, and every signing request is approved by hand.</p>

<h3>3. Team and roles</h3>
<p>The Axell suite is made by one person, Axell Yobag (<a href="{GH}">github.com/zmardanian</a>), who holds every role:</p>
<ul>
<li><b>Committers and reviewers:</b> Axell Yobag. Changes proposed by anyone else (pull requests) are reviewed before they are merged.</li>
<li><b>Approvers:</b> Axell Yobag approves every release and every signing request.</li>
</ul>
<p>The GitHub account uses two-factor authentication, and the release branches and tags are protected against deletion and rewriting.</p>

<h3>4. Checking a download yourself</h3>
<p>Every release has a <code>SHA256SUMS.txt</code> with the fingerprint of each file, and from 20 November 2026 a
<code>SHA256SUMS.txt.minisig</code> that signs it with the suite's release key (<a href="https://jedisct1.github.io/minisign/">minisign</a>).
The public key:</p>
<pre class="key">{MINISIGN_PUB}</pre>
<p>On Linux: <code>minisign -Vm SHA256SUMS.txt -P {MINISIGN_PUB}</code>, then <code>sha256sum -c --ignore-missing SHA256SUMS.txt</code>.
On Windows (PowerShell): <code>Get-FileHash &lt;file&gt;</code> and compare it with the line in <code>SHA256SUMS.txt</code>.
The suite installer also carries a GitHub build attestation: <code>gh attestation verify &lt;file&gt; -R zmardanian/axell-signature-dojo</code>.
The Axell Signature Dojo checks the fingerprint of every download before it installs anything.</p>

<h3>5. Privacy</h3>
<p>This program will not transfer any information to other networked systems unless specifically requested by the user or the person
installing or operating it. The plugins never connect to the internet. The Dojo contacts GitHub (<code>api.github.com</code> and
<code>github.com</code>) only when you click to check for updates or to install, to read the list of releases and download them; it
sends nothing about you or your computer. See the <a href="/privacy/">privacy policy</a> for this website.</p>

<h3>6. Reporting a problem</h3>
<p>Security problems: please report them privately - see the security policy in each repository, or write to
<a href="mailto:contact@axellsdojo.com">contact@axellsdojo.com</a>.</p>
</section></main>"""
    return head("Code signing policy - Axell's Dojo", "How the Axell plugins and the Signature Dojo are built, signed and verified.", path="/code-signing/") + body + foot()

def tracks_used():
    """the songs and stems the published examples come from, read from the manifest so the list never goes stale"""
    import re
    songs = {}
    for items in AUDIO.values():
        for it in items:
            m = re.match(r"(.+?) - OnAir Music( feat\. [^(]+)? \((.+)\)$", it["source"])
            if m:
                parts = songs.setdefault((m.group(1), (m.group(2) or "").strip()), set()); parts.add(m.group(3))
                if it["simulated"] == "beat bleed simulated": parts.add("instrumental")     # the bleed is the song's own beat
    parts = [f"<i>{e(t)}</i>{' (' + e(f) + ')' if f else ''} - {e(', '.join(sorted(p)))}" for (t, f), p in sorted(songs.items())]
    return "; ".join(parts)

def cc_tracks():
    """the a cappellas from ccMixter: title, artist, link and licence for each (CC BY asks for all four)"""
    seen = {}
    for items in AUDIO.values():
        for it in items:
            if it.get("cc"): seen[it["cc"]["url"]] = it["cc"]
    if not seen: return ""
    rows = "".join(f'<li><a href="{e(c["url"])}" rel="noopener"><i>{e(c["title"])}</i></a> by {e(c["artist"])} - '
                   f'<a href="{e(c["license_url"])}" rel="noopener">{e(c["license"])}</a></li>' for c in sorted(seen.values(), key=lambda c: c["title"]))
    return (f"""<p>The a cappella vocals come from <a href="https://ccmixter.org/" rel="noopener">ccMixter</a>, shared by their singers and
rappers under Creative Commons Attribution licences:</p><ul>{rows}</ul>
<p>Changes made to them: 14-second excerpts, set to a working level, processed through the Axell plugins as described above
(the De-Reverb examples first get a modelled small room); the processed excerpts are shared under the same licence as their source.</p>""")

def credits_page():
    body = """<main><section class="section"><p class="label">CREDITS</p><h1 class="h2">The music in the examples.</h1>
<p class="lede">The before/after examples on this site are made from openly licensed recordings: stems from the <a href="https://github.com/OnAir-Music/OnAir-Music-Dataset">OnAir Music Dataset</a>
- royalty-free songs by the <b>OnAir Music</b> project (Hrag, the Crescent MTL Project and SevagH), featuring <b>KXNE</b>,
released under the <a href="https://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International</a> licence.</p>
<p>Tracks used: TRACKS_USED.</p>
<p><b>Changes made:</b> 14-second excerpts, set to a working level (-18 LUFS; -20 LUFS for the mastering examples), processed through the
Axell plugins with their factory presets, the processed version matched to the original's loudness, short fades. The drum examples sum the
song's kick, snare and break stems; the mastering examples sum all of a song's stems (an unmastered mix), and their "before" is that mix
turned up to the master's loudness without a limiter. Where marked, a small room (De-Reverb) or headphone bleed of the song's instrumental
(Gate) was simulated before processing.
The processed excerpts are shared under the same licence, CC BY-SA 4.0. No endorsement by the artists or the OnAir Music project is implied.</p>
CC_TRACKS
<p>Typefaces: Great Vibes, Cormorant Garamond, Jost and Yuji Syuku (<a href="/fonts/OFL.txt">SIL Open Font License</a>), served from this site - no request goes to a font service.</p>
</section></main>"""
    body = body.replace("TRACKS_USED", tracks_used()).replace("CC_TRACKS", cc_tracks())
    return head("Credits - Axell's Dojo", "The music used in the before/after examples and its licence.", path="/credits/") + body + foot()

def contact_page():
    body = """<main style="--acc:#d3ad66">
<section class="hero hero-plugin"><div class="hero-bg" aria-hidden="true">道場</div>
  <p class="eyebrow">ABOUT &middot; CONTACT</p>
  <h1 class="script hero-title">Axell Yobag</h1>
</section>
<section class="section split reveal">
  <div><p class="label">01 &nbsp; THE STORY</p><h2>From the booth to the code.</h2>
  <p class="lede">I'm Axell Yobag &mdash; a rap artist and producer. I write and record in English and Romanian, over boom bap, trap and lo-fi beats, mostly in a home setup like most artists today: a mic, a room that isn't a studio, and a laptop.</p>
  <p class="lede">The tools I could find either cost a fortune, didn't run where I work, or treated a voice like any other sound. So I started building my own &mdash; a gate that knows my voice from my room, a de-esser that recognises an S instead of guessing, a compressor that holds my words together, a master that survives the streaming services.</p>
  <p class="lede">That became the Axell Signature suite: nine plugins and the Dojo that ties them together. Every one is tested against real hardware and the references engineers trust, and every claim on this site is a measurement you can check.</p></div>
  <div><p class="label">02 &nbsp; WHAT I BELIEVE</p><h2>Free, honest, measured.</h2>
  <ul class="ticks">
    <li><b>Free and open source</b> &mdash; no subscriptions, no accounts, no licence keys. Good tools shouldn't depend on your budget.</li>
    <li><b>Windows and Linux</b> &mdash; made where I work, built for wherever you work, in any DAW.</li>
    <li><b>Measured, not marketed</b> &mdash; if a number is on the page, there's a test behind it.</li>
    <li><b>Made for the voice</b> &mdash; rap vocals first, because that's what I make.</li>
  </ul></div>
</section>
<section id="contact" class="section windows reveal">
  <p class="label">03 &nbsp; CONTACT</p><h2>Say hello.</h2>
  <p class="lede">Questions, bug reports, ideas for the next plugin, collaborations &mdash; I read everything.</p>
  <div class="tri">
    <div><h3>Email</h3><p><a href="mailto:contact@axellsdojo.com">contact@axellsdojo.com</a></p></div>
    <div><h3>Bugs &amp; ideas</h3><p>Open an issue on the plugin's <a href="https://github.com/zmardanian">GitHub</a> page &mdash; it helps everyone who hits the same thing.</p></div>
    <div><h3>Get the suite</h3><p><a href="/download">axellsdojo.com/download</a> &mdash; Windows installer and Linux, free.</p></div>
  </div>
  <form id="write" class="contact-form" method="post" action="/contact/send">
    <h3>Or write here</h3>
    <div class="cf-row"><label>Your name <small>(optional)</small><input name="name" maxlength="100" autocomplete="name"></label>
    <label>Your email <small>(for the answer)</small><input name="email" type="email" required maxlength="254" autocomplete="email"></label></div>
    <label>Message<textarea name="message" required minlength="10" maxlength="5000" rows="6"></textarea></label>
    <label class="cf-trap" aria-hidden="true">Leave this empty<input name="website" tabindex="-1" autocomplete="off"></label>
    <p class="cf-note">Sent to me as an email; this site keeps no copy &mdash; see the <a href="/privacy/">privacy policy</a>.</p>
    <button class="btn btn-primary" type="submit"><b>Send message</b></button>
  </form>
</section>
</main>"""
    return head("About & contact - Axell Yobag, Axell's Dojo", "Axell Yobag - rap artist and producer, maker of the free Axell Signature audio plugins for Windows and Linux. Contact: contact@axellsdojo.com.", "#d3ad66", "/contact/") + body.replace("\n</main>", "\n" + support("Everything here", "04 &nbsp; SUPPORT") + "\n</main>") + foot()

def build():
    downloads_manifest()
    # sitemap <lastmod>: a page keeps its date until its HTML changes (search engines only trust accurate dates)
    old = {}
    if os.path.isdir(OUT):
        sm = f"{OUT}/sitemap.xml"
        dates = dict(re.findall(r"<loc>https://www.axellsdojo.com([^<]*)</loc><lastmod>([^<]*)</lastmod>", open(sm).read())) if os.path.exists(sm) else {}
        for u in ["/"] + [f"/{SLUG[r]}/" for r in PLUGINS] + ["/dojo/", "/contact/"]:
            f = f"{OUT}{u}index.html"
            if os.path.exists(f): old[u] = (dates.get(u), hashlib.sha256(open(f, "rb").read()).hexdigest())
        shutil.rmtree(OUT)
    os.makedirs(f"{OUT}/img", exist_ok=True)
    for f in ("site.js", "_headers", "_redirects"): shutil.copy(f"{SITE}/src/{f}", f"{OUT}/{f}")
    shutil.copy(f"{SITE}/src/img/vst-compatible.svg", f"{OUT}/img/vst-compatible.svg")
    shutil.copytree(f"{SITE}/src/img/closeups", f"{OUT}/img/closeups", dirs_exist_ok=True, ignore=shutil.ignore_patterns("closeups.json"))
    shutil.copytree(f"{SITE}/src/video", f"{OUT}/video", dirs_exist_ok=True)
    for f in os.listdir(f"{SITE}/src"):   # the IndexNow key (Bing, Yandex, Seznam, Naver): a 32-hex-character .txt
        if len(f) == 36 and f.endswith(".txt"): shutil.copy(f"{SITE}/src/{f}", f"{OUT}/{f}")
    open(f"{OUT}/style.css", "w").write(CSS); shutil.copytree(f"{SITE}/src/fonts", f"{OUT}/fonts", ignore=shutil.ignore_patterns("KANJI.txt"))
    import json
    AUDIO.update(json.load(open(f"{SITE}/src/audio/audio.json")))
    if os.path.exists(f"{SITE}/src/audio/graphs.json"): GRAPHS.update(json.load(open(f"{SITE}/src/audio/graphs.json")))
    shutil.copytree(f"{SITE}/src/audio", f"{OUT}/audio", ignore=shutil.ignore_patterns("audio.json", "graphs.json"))
    os.makedirs(f"{OUT}/contact", exist_ok=True); open(f"{OUT}/contact/index.html", "w").write(contact_page())
    os.makedirs(f"{OUT}/credits", exist_ok=True); open(f"{OUT}/credits/index.html", "w").write(credits_page())
    for slug, page in (("impressum", impressum_page), ("privacy", privacy_page), ("code-signing", signing_page)):
        os.makedirs(f"{OUT}/{slug}", exist_ok=True); open(f"{OUT}/{slug}/index.html", "w").write(page())
    open(f"{OUT}/index.html", "w").write(home())
    for r in PLUGINS:
        os.makedirs(f"{OUT}/{SLUG[r]}", exist_ok=True); open(f"{OUT}/{SLUG[r]}/index.html", "w").write(plugin_page(r))
        os.makedirs(f"{OUT}/{SLUG[r]}/manual", exist_ok=True); open(f"{OUT}/{SLUG[r]}/manual/index.html", "w").write(manual_page(r))
    os.makedirs(f"{OUT}/dojo", exist_ok=True); open(f"{OUT}/dojo/index.html", "w").write(dojo_page())
    open(f"{OUT}/404.html", "w").write(head("Not found - Axell's Dojo", "This page does not exist.") + '<main><section class="hero"><div class="hero-bg" aria-hidden="true">迷</div>'
        '<p class="eyebrow">404</p><h1 class="script hero-title">Lost in the dojo</h1><p class="hero-tag">This page does not exist - but nine plugins do.</p>'
        '<p><a class="btn btn-primary" href="/"><b>Back to the suite</b></a></p></section></main>' + foot())
    for r in PLUGINS: og_card(r, NAME[r], TAG[r], f"{HOME}/{r}/{C[r]['shot']}", f"{OUT}/img/og-{SLUG[r]}.jpg")
    og_card("axell-signature-dojo", "Signature Dojo", TAG["axell-signature-dojo"], f"{HOME}/axell-signature-dojo/{C['axell-signature-dojo']['shot']}", f"{OUT}/img/og-dojo.jpg")
    # favicon: the Dojo's seal; social card: the home hero's look
    T.wideseal(f"{OUT}/img/favicon.png", "道場", "dark", 64)
    og_card("", "Axell's Dojo", "Nine plugins forged for the voice. Every claim, measured.", f"{HOME}/axell-gate/{C['axell-gate']['shot']}", f"{OUT}/img/og.jpg")
    open(f"{OUT}/robots.txt", "w").write("User-agent: *\nAllow: /\nDisallow: /get/\nSitemap: https://www.axellsdojo.com/sitemap.xml\n")
    os.makedirs(f"{OUT}/.well-known", exist_ok=True)
    import datetime
    open(f"{OUT}/.well-known/security.txt", "w").write("Contact: mailto:contact@axellsdojo.com\nExpires: " + (datetime.date.today() + datetime.timedelta(days=360)).isoformat()
        + "T00:00:00Z\nPreferred-Languages: en, de\nCanonical: https://www.axellsdojo.com/.well-known/security.txt\n")
    urls = ["/"] + [f"/{SLUG[r]}/" for r in PLUGINS] + [f"/{SLUG[r]}/manual/" for r in PLUGINS] + ["/dojo/", "/contact/"]
    today = datetime.date.today().isoformat()
    def lastmod(u):
        d, h = old.get(u, (None, None))
        return d if d and h == hashlib.sha256(open(f"{OUT}{u}index.html", "rb").read()).hexdigest() else today
    open(f"{OUT}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>https://www.axellsdojo.com{u}</loc><lastmod>{lastmod(u)}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    have = open(f"{SITE}/src/fonts/KANJI.txt").read()
    for d_, _, fs in os.walk(OUT):
        for f in fs:
            if f.endswith(".html"):   # the skip link's target: every page's <main>
                h = open(f"{d_}/{f}").read()
                if 'id="main"' not in h: open(f"{d_}/{f}", "w").write(h.replace("<main", '<main id="main"', 1))
                miss = set(re.findall(r"[\u3000-\u9fff]", open(f"{d_}/{f}").read())) - set(have)
                if miss: raise SystemExit(f"{f}: kanji {miss} not in the brush font - run tools/fetch_fonts.py")
    print("built", OUT, sum(len(fs) for _, _, fs in os.walk(OUT)), "files")

if __name__ == "__main__": build()
