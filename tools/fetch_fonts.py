"""Fetches the site's four typefaces (all SIL OFL) as WOFF2 into src/fonts and writes src/fonts.css, so the site
serves its own fonts: no request to Google, one origin. Latin slices for the text faces; the brush face only with
the kanji the site shows. Run again when a new kanji is added (build.py checks)."""
import os, re, sys, urllib.request, urllib.parse
sys.path.insert(0, os.path.expanduser("~/axell-windows-port/brand"))
import typeset_suite as T
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f"{SITE}/src/fonts"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
KANJI = "".join(sorted(set("道場迷" + "".join(p[1] or "" for p in T.P.values()))))
def get(url): return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()
def faces(query):
    css = get("https://fonts.googleapis.com/css2?" + query + "&display=swap").decode()
    return re.findall(r"/\* ([\w-]+) \*/\s*@font-face \{(.*?)\}", css, flags=re.S) or [("text", b) for b in re.findall(r"@font-face \{(.*?)\}", css, flags=re.S)]
out = []
def take(query, slices, tag=""):
    for sl, body in faces(query):
        if sl not in slices: continue
        fam = re.search(r"font-family: '([^']+)'", body).group(1); st = re.search(r"font-style: (\w+)", body).group(1)
        wt = re.search(r"font-weight: ([\d ]+)", body).group(1).strip(); url = re.search(r"url\((https://[^)]+)\)", body).group(1)
        rng = re.search(r"unicode-range: ([^;]+);", body)
        name = f"{fam.lower().replace(' ', '-')}-{wt.replace(' ', '_')}{'-italic' if st == 'italic' else ''}{tag}.woff2"
        data = get(url); open(f"{OUT}/{name}", "wb").write(data); print(f"{name:44s} {len(data):7d}")
        out.append(f"@font-face {{ font-family: \"{fam}\"; font-style: {st}; font-weight: {wt}; font-display: swap; src: url(/fonts/{name}) format(\"woff2\");"
                   + (f" unicode-range: {rng.group(1)};" if rng and sl != "text" else "") + " }")
take("family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500", {"latin"})
take("family=Jost:wght@400;500", {"latin"})
take("family=Great+Vibes", {"latin"})
take("family=Yuji+Syuku&text=" + urllib.parse.quote(KANJI + "迷"), {"text"}, "-kanji")
open(f"{OUT}/KANJI.txt", "w").write(KANJI)
open(f"{SITE}/src/fonts.css", "w").write("\n".join(dict.fromkeys(out)) + "\n")
# the variable faces come back as one file per weight: keep one file, declare its weight range
import hashlib, collections
g = collections.OrderedDict()
for line in dict.fromkeys(out):
    fn = re.search(r"/fonts/([^)]+)\)", line).group(1); h = hashlib.sha256(open(f"{OUT}/{fn}", "rb").read()).hexdigest()
    g.setdefault(h, []).append((fn, line))
css = []
for h, items in g.items():
    fn, line = items[0]; ws = sorted(int(re.search(r"font-weight: (\d+)", l).group(1)) for _, l in items)
    if len(ws) > 1: line = re.sub(r"font-weight: \d+", f"font-weight: {ws[0]} {ws[-1]}", line)
    for other, _ in items[1:]: os.remove(f"{OUT}/{other}")
    css.append(line.replace(f"/fonts/{fn}", f"/fonts/{fn}?v={h[:10]}"))
open(f"{SITE}/src/fonts.css", "w").write("\n".join(css) + "\n")
