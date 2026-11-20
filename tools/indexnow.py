"""Tell the IndexNow search engines (Bing, Yandex, Seznam, Naver) which pages changed: every URL in the live
sitemap. Run after a deploy: python3 tools/indexnow.py"""
import json, os, re, urllib.request

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "www.axellsdojo.com"
key = next(f[:-4] for f in os.listdir(f"{SITE}/src") if re.fullmatch(r"[0-9a-f]{32}\.txt", f))
UA = {"User-Agent": "axellsdojo-indexnow/1.0 (+https://www.axellsdojo.com/)"}     # the default Python agent is blocked as a bot
sitemap = urllib.request.urlopen(urllib.request.Request(f"https://{HOST}/sitemap.xml", headers=UA)).read().decode()
urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
body = json.dumps({"host": HOST, "key": key, "keyLocation": f"https://{HOST}/{key}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", body, {"Content-Type": "application/json; charset=utf-8", **UA})
with urllib.request.urlopen(req) as r:
    print(f"IndexNow: {len(urls)} URLs, HTTP {r.status}")
