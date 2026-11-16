// The site is static (public/); this Worker only answers /get/<plugin>/<windows|linux>: it notes the download in the
// D1 database (time, plugin, system, version, country, the page it came from - never an IP address) and redirects to
// the newest release file on GitHub. Without the database, or if GitHub's API does not answer, it still redirects:
// to the file known when the site was built, or to the release page.
import BAKED from "./downloads.json";

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS downloads (id INTEGER PRIMARY KEY, time TEXT NOT NULL, plugin TEXT NOT NULL, system TEXT NOT NULL,
     version TEXT, file TEXT, country TEXT, city TEXT, from_page TEXT, device TEXT, browser TEXT, bot INTEGER NOT NULL DEFAULT 0)`,
  `CREATE INDEX IF NOT EXISTS downloads_time ON downloads (time)`,
  `CREATE VIEW IF NOT EXISTS totals_by_plugin AS SELECT plugin, system, count(*) AS downloads, max(time) AS last FROM downloads WHERE bot = 0 GROUP BY plugin, system ORDER BY downloads DESC`,
  `CREATE VIEW IF NOT EXISTS totals_by_day AS SELECT substr(time, 1, 10) AS day, count(*) AS downloads FROM downloads WHERE bot = 0 GROUP BY day ORDER BY day DESC`,
  `CREATE VIEW IF NOT EXISTS totals_by_country AS SELECT country, count(*) AS downloads FROM downloads WHERE bot = 0 GROUP BY country ORDER BY downloads DESC`,
  `CREATE VIEW IF NOT EXISTS latest_downloads AS SELECT time, plugin, system, version, country, city, from_page, device, browser FROM downloads WHERE bot = 0 ORDER BY id DESC LIMIT 200`,
];
let ready = false;

function device(ua) {
  return /Windows/.test(ua) ? "Windows" : /Android/.test(ua) ? "Android" : /iPhone|iPad/.test(ua) ? "iOS" : /Mac OS X/.test(ua) ? "macOS" : /Linux|X11/.test(ua) ? "Linux" : "other";
}
function browser(ua) {
  return /Edg\//.test(ua) ? "Edge" : /OPR\//.test(ua) ? "Opera" : /Firefox\//.test(ua) ? "Firefox" : /Chrome\//.test(ua) ? "Chrome" : /Safari\//.test(ua) ? "Safari" : "other";
}
const BOT = /bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|discord|curl|wget|python|headless|monitor|scan|fetch|http-client|go-http|okhttp|^$/i;

// the newest release that has the file (a release can be published before its Windows build is attached)
async function newest(entry, system, ctx) {
  const api = "https://api.github.com/repos/zmardanian/" + entry.repo + "/releases?per_page=6", key = new Request(api);
  try {
    let r = await caches.default.match(key);
    if (!r) {
      r = await fetch(api, { headers: { Accept: "application/vnd.github+json", "User-Agent": "axellsdojo.com" } });
      if (!r.ok) throw new Error("github " + r.status);
      r = new Response(r.body, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=900" } });
      ctx.waitUntil(caches.default.put(key, r.clone()));
    }
    for (const rel of await r.json()) {
      if (rel.draft || rel.prerelease) continue;
      const a = rel.assets.find((x) => x.name.endsWith(entry.suffix[system]));
      if (a) return { url: a.browser_download_url, file: a.name, version: rel.tag_name.replace(/^v/, "") };
    }
  } catch (e) {}
  return entry[system] || null;
}

async function note(env, row) {
  if (!env.DB) return;
  try {
    if (!ready) { await env.DB.batch(SCHEMA.map((s) => env.DB.prepare(s))); ready = true; }
    await env.DB.prepare("INSERT INTO downloads (time, plugin, system, version, file, country, city, from_page, device, browser, bot) VALUES (?,?,?,?,?,?,?,?,?,?,?)")
      .bind(...row).run();
  } catch (e) { console.log("download not noted:", e.message); }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url), m = url.pathname.match(/^\/get\/([a-z0-9-]+)\/(windows|linux)\/?$/);
    if (!m || !BAKED[m[1]] || !BAKED[m[1]].suffix[m[2]]) return env.ASSETS.fetch(new Request(new URL("/404.html", url), request));
    const entry = BAKED[m[1]], system = m[2], page = "https://github.com/zmardanian/" + entry.repo + "/releases/latest";
    if (request.method !== "GET") return Response.redirect(page, 302);
    const hit = await newest(entry, system, ctx), ua = request.headers.get("User-Agent") || "", cf = request.cf || {};
    let from = "";
    try { const ref = new URL(request.headers.get("Referer")); from = ref.hostname.endsWith("axellsdojo.com") ? ref.pathname : ref.hostname; } catch (e) {}
    ctx.waitUntil(note(env, [new Date().toISOString().slice(0, 19).replace("T", " "), entry.name, system, hit ? hit.version : null, hit ? hit.file : null,
      cf.country || null, cf.city || null, from || "(direct)", device(ua), browser(ua), BOT.test(ua) ? 1 : 0]));
    return new Response(null, { status: 302, headers: { Location: hit ? hit.url : page, "Cache-Control": "no-store", "X-Robots-Tag": "noindex" } });
  },
};
