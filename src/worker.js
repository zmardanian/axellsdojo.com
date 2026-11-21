// The site is static (public/); this Worker only answers /get/<plugin>/<windows|linux>: it notes the download in the
// D1 database (time, plugin, system, version, country, the page it came from - never an IP address) and redirects to
// the newest release file on GitHub. Without the database, or if GitHub's API does not answer, it still redirects:
// to the file known when the site was built, or to the release page.
// bot: 0 = a person, 1 = a bot by its User-Agent, 2 = from a data centre, 3 = both systems in the same second (a link
// checker), 4 = the owner's own device (opened /get/not-me once). Past 10 a minute from one address it only redirects.
import BAKED from "./downloads.json";
import { EmailMessage } from "cloudflare:email";

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS downloads (id INTEGER PRIMARY KEY, time TEXT NOT NULL, plugin TEXT NOT NULL, system TEXT NOT NULL,
     version TEXT, file TEXT, country TEXT, city TEXT, from_page TEXT, device TEXT, browser TEXT, bot INTEGER NOT NULL DEFAULT 0,
     network TEXT)`,
  `CREATE INDEX IF NOT EXISTS downloads_time ON downloads (time)`,
  `CREATE VIEW IF NOT EXISTS totals_by_plugin AS SELECT plugin, system, count(*) AS downloads, max(time) AS last FROM downloads WHERE bot = 0 GROUP BY plugin, system ORDER BY downloads DESC`,
  `CREATE VIEW IF NOT EXISTS totals_by_day AS SELECT substr(time, 1, 10) AS day, count(*) AS downloads FROM downloads WHERE bot = 0 GROUP BY day ORDER BY day DESC`,
  `CREATE VIEW IF NOT EXISTS totals_by_country AS SELECT country, count(*) AS downloads FROM downloads WHERE bot = 0 GROUP BY country ORDER BY downloads DESC`,
  `CREATE VIEW IF NOT EXISTS latest_downloads AS SELECT time, plugin, system, version, country, city, network, from_page, device, browser FROM downloads WHERE bot = 0 ORDER BY id DESC LIMIT 200`,
];
let ready = false;

function device(ua) {
  return /Windows/.test(ua) ? "Windows" : /Android/.test(ua) ? "Android" : /iPhone|iPad/.test(ua) ? "iOS" : /Mac OS X/.test(ua) ? "macOS" : /Linux|X11/.test(ua) ? "Linux" : "other";
}
function browser(ua) {
  return /Edg\//.test(ua) ? "Edge" : /OPR\//.test(ua) ? "Opera" : /Firefox\//.test(ua) ? "Firefox" : /Chrome\//.test(ua) ? "Chrome" : /Safari\//.test(ua) ? "Safari" : "other";
}
// cloud and hosting networks; iCloud Private Relay (Cloudflare, Akamai, Fastly) is left out, its users are people
const DATACENTRE = new Set([15169, 396982, 19527, 16509, 14618, 8075, 8068, 16276, 24940, 14061, 63949, 31898, 45102,
  132203, 20473, 51167, 60781, 16125, 12876, 9009, 212238, 46606, 26496, 36352, 55286, 23470, 35540, 202425, 39351, 200651]);
const HOSTING = /hosting|server|data ?cent|cloud|vps|colo/i;
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
    const [time, plugin, system, , , , city] = row;
    if (row[10] === 0) {
      // the other system of the same plugin from the same place within 3 seconds: a link checker, not a person
      const twin = await env.DB.prepare("UPDATE downloads SET bot = 3 WHERE bot = 0 AND plugin = ? AND system != ? AND city IS ? AND time >= datetime(?, '-3 seconds')")
        .bind(plugin, system, city, time).run();
      if (twin.meta.changes) row[10] = 3;
    }
    await env.DB.prepare("INSERT INTO downloads (time, plugin, system, version, file, country, city, from_page, device, browser, bot, network) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)")
      .bind(...row).run();
    if (row[10] === 0) {
      // again after the insert: two requests in the same instant both pass the check above before either row exists
      await env.DB.prepare("UPDATE downloads SET bot = 3 WHERE bot = 0 AND plugin = ? AND city IS ? AND time BETWEEN datetime(?, '-3 seconds') AND datetime(?, '+3 seconds')"
        + " AND EXISTS (SELECT 1 FROM downloads o WHERE o.plugin = downloads.plugin AND o.city IS downloads.city AND o.system != downloads.system"
        + " AND o.time BETWEEN datetime(downloads.time, '-3 seconds') AND datetime(downloads.time, '+3 seconds'))")
        .bind(plugin, city, time, time).run();
    }
    await env.DB.prepare("DELETE FROM downloads WHERE time < datetime('now', '-24 months')").run();   // kept 24 months (privacy policy)
  } catch (e) { console.log("download not noted:", e.message); }
}

const KOFI = "https://ko-fi.com/axellyobag";
// _headers only covers the static files: every response this Worker makes gets the same protection here
const SEC = { "Strict-Transport-Security": "max-age=31536000; includeSubDomains", "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY", "Referrer-Policy": "strict-origin-when-cross-origin", "Cross-Origin-Opener-Policy": "same-origin",
  "X-Robots-Tag": "noindex", "Cache-Control": "no-store" };
const CSP = "default-src 'none'; style-src 'unsafe-inline'; font-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
// the page shown while the download starts: one second, then the browser fetches the file from GitHub
function thanks(name, system, hit, to) {
  const what = name === "Signature Suite + Dojo" ? (system === "windows" ? "the Axell Signature Suite installer" : "the Axell Signature Dojo") : name;
  const file = hit ? `${esc(hit.file)} &middot; version ${esc(hit.version)}` : "the release page on GitHub";
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="1;url=${esc(to)}"><meta name="robots" content="noindex"><title>Thank you - Axell's Dojo</title>
<link rel="icon" href="/img/favicon.png"><style>
@font-face{font-family:GV;src:url(/fonts/great-vibes-400.woff2) format("woff2")}@font-face{font-family:JO;src:url(/fonts/jost-400.woff2) format("woff2")}
@font-face{font-family:YU;src:url(/fonts/yuji-syuku-400-kanji.woff2) format("woff2")}
:root{--g:#c9a25e}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(90% 70% at 50% 0%,#1b1712,#0b0d12 70%);
color:#efe6d6;font:17px/1.6 JO,system-ui,sans-serif;padding:24px 16px;text-align:center}
.k{font-family:YU,serif;font-size:42px;color:#fff3e6;background:#c0362c;display:inline-block;padding:2px 12px;border-radius:5px;transform:rotate(-4deg)}
h1{font-family:GV,cursive;font-weight:400;color:var(--g);font-size:clamp(54px,12vw,86px);line-height:1.1;margin:18px 0 4px}
p{color:#a99d8d;max-width:520px;margin:8px auto}.f{font-size:13px;color:#8a806f}a{color:var(--g)}
.b{display:inline-flex;flex-direction:column;align-items:center;margin:26px 0 10px;padding:16px 34px 12px;border-radius:10px;background:var(--g);color:#0b0d12;
text-decoration:none;box-shadow:0 10px 40px rgba(201,162,94,.35);transition:transform .15s}.b:hover{transform:translateY(-2px)}
.b b{letter-spacing:.16em;text-transform:uppercase;font-weight:500}.b small{font-size:12px;letter-spacing:.06em;opacity:.8}
.s{width:34px;height:34px;margin-bottom:4px}.h{margin-top:28px;font-size:13px;letter-spacing:.14em;text-transform:uppercase}</style></head><body><main>
<span class="k" aria-hidden="true">道場</span><h1>Thank you.</h1>
<p>Your download of <b style="color:#efe6d6">${esc(what)}</b> is starting. If it doesn't, <a href="${esc(to)}">click here</a>.</p>
<p class="f">${file}</p>
<p style="margin-top:22px">Everything in the Dojo is free and stays free &mdash; no subscriptions, no licence keys. If it earns a place in your mixes, a coffee keeps it going.</p>
<a class="b" href="${KOFI}" rel="noopener"><svg class="s" viewBox="0 0 32 32" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
<path d="M10 4c-1.5 2 1.5 3 0 5M15 3c-1.5 2 1.5 3 0 5M20 4c-1.5 2 1.5 3 0 5"/><path d="M5 13h19v7a7 7 0 0 1-7 7h-5a7 7 0 0 1-7-7z"/><path d="M24 15h1.5a3.5 3.5 0 0 1 0 7H23.5"/></g>
<path d="M14.5 23.2l-3-2.9a1.9 1.9 0 0 1 2.7-2.7l.3.3.3-.3a1.9 1.9 0 0 1 2.7 2.7z" fill="currentColor"/></svg><b>Buy Axell a coffee</b><small>on Ko-fi &middot; from &euro;3</small></a>
<p class="h"><a href="/">Back to the Dojo</a> &nbsp;&middot;&nbsp; <a href="https://github.com/zmardanian">GitHub</a></p></main></body></html>`;
}

// The contact form (/contact/#write): one email to the owner through Cloudflare's email service. The site keeps no copy -
// only the time of each sent message (contact_sends), to cap mass sending, deleted after 30 days (privacy policy).
const CAP_PER_DAY = 40;
function page(title, text, status = 200) {
  return new Response(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>${esc(title)} - Axell's Dojo</title><link rel="icon" href="/img/favicon.png"><style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0b0d12;color:#efe6d6;font:18px/1.6 system-ui,sans-serif;padding:24px 16px;text-align:center}
h1{font-weight:400;color:#c9a25e}p{color:#a99d8d;max-width:520px;margin:8px auto}a{color:#c9a25e}</style></head><body><main>
<h1>${esc(title)}</h1><p>${text}</p><p style="margin-top:24px"><a href="/contact/">Back</a> &middot; <a href="/">Axell's Dojo</a></p></main></body></html>`,
    { status, headers: { ...SEC, "Content-Type": "text/html; charset=utf-8", "Content-Security-Policy": CSP } });
}
function b64(str) {
  const bytes = new TextEncoder().encode(str);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}
async function contact(request, env) {
  if (request.method !== "POST") return Response.redirect(new URL("/contact/#write", request.url).toString(), 303);
  const ip = request.headers.get("CF-Connecting-IP") || "";
  if (env.LIMIT && !(await env.LIMIT.limit({ key: "contact:" + ip })).success)
    return page("Slow down", "Too many messages in a minute. Please wait a little, or write to contact@axellsdojo.com.", 429);
  let f;
  try { f = await request.formData(); } catch (e) { return page("Not sent", "The form could not be read. Please try again.", 400); }
  const one = (k, max) => String(f.get(k) || "").replace(/[\r\n]+/g, " ").trim().slice(0, max);   // header-safe, one line
  const name = one("name", 100), email = one("email", 254), message = String(f.get("message") || "").trim();
  if (one("website", 200)) return page("Thank you", "Your message is on its way.");   // the hidden trap field: a bot, quietly dropped
  // Turnstile (Cloudflare's privacy-friendly bot check): the browser's token, verified with Cloudflare before anything is sent
  if (env.TURNSTILE_SECRET) {
    const token = String(f.get("cf-turnstile-response") || "");
    let ok = false;
    if (token) {
      try {
        const v = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
          method: "POST", body: new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: token, remoteip: ip }) });
        ok = (await v.json()).success === true;
      } catch (e) { console.log("turnstile verify failed:", e.message); }
    }
    if (!ok) return page("Not sent", "The spam check did not go through. Please go back, wait for the check to finish and send again - or write to <a href=\"mailto:contact@axellsdojo.com\">contact@axellsdojo.com</a>.", 403);
  }
  if (!/^[^\s@<>",;]+@[^\s@<>",;]+\.[^\s@<>",;]{2,}$/.test(email))
    return page("Not sent", "That email address does not look right - I need it to answer you. Please go back and check it.", 400);
  if (message.length < 10 || message.length > 5000)
    return page("Not sent", "The message should be between 10 and 5000 characters. Please go back and adjust it.", 400);
  if (!env.MAIL || !env.CONTACT_TO) return page("Not sent", "The form is not available right now. Please write to <a href=\"mailto:contact@axellsdojo.com\">contact@axellsdojo.com</a>.", 503);
  if (env.DB) {
    try {
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS contact_sends (time TEXT NOT NULL)").run();
      await env.DB.prepare("DELETE FROM contact_sends WHERE time < datetime('now', '-30 days')").run();
      const n = await env.DB.prepare("SELECT count(*) AS n FROM contact_sends WHERE time >= datetime('now', '-1 day')").first("n");
      if (n >= CAP_PER_DAY) return page("Not sent", "The form has had too many messages today. Please write to <a href=\"mailto:contact@axellsdojo.com\">contact@axellsdojo.com</a>.", 429);
    } catch (e) { console.log("contact cap not checked:", e.message); }
  }
  const from = "website@axellsdojo.com", subject = "Contact form: " + (name || email);
  const raw = [
    `From: "axellsdojo.com" <${from}>`, `To: <${env.CONTACT_TO}>`, `Reply-To: ${name ? `"=?UTF-8?B?${b64(name)}?=" ` : ""}<${email}>`,
    `Subject: =?UTF-8?B?${b64(subject)}?=`, `Date: ${new Date().toUTCString()}`, `Message-ID: <${crypto.randomUUID()}@axellsdojo.com>`,
    "MIME-Version: 1.0", "Content-Type: text/plain; charset=utf-8", "Content-Transfer-Encoding: base64", "",
    b64(`From: ${name || "(no name)"} <${email}>\n\n${message}\n`).replace(/.{76}/g, "$&\r\n"),
  ].join("\r\n");
  try {
    await env.MAIL.send(new EmailMessage(from, env.CONTACT_TO, raw));
  } catch (e) {
    console.log("contact mail failed:", e.message);
    return page("Not sent", "Something went wrong on my side. Please write to <a href=\"mailto:contact@axellsdojo.com\">contact@axellsdojo.com</a>.", 502);
  }
  if (env.DB) { try { await env.DB.prepare("INSERT INTO contact_sends (time) VALUES (datetime('now'))").run(); } catch (e) {} }
  return page("Thank you", `Your message is on its way. I'll answer at <b>${esc(email)}</b>.`);
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/contact/send") return contact(request, env);
    if (url.pathname.replace(/\/$/, "") === "/get/not-me") {
      return new Response("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>Not counted</title>" +
        "<p style='font:18px system-ui;margin:3em auto;max-width:30em;padding:0 1em'>Downloads from this browser are no longer counted. <a href='/'>Back to the Dojo</a></p>",
        { headers: { ...SEC, "Content-Type": "text/html; charset=utf-8", "Content-Security-Policy": CSP,
          "Set-Cookie": "axell_owner=1; Max-Age=315360000; Path=/get; Secure; HttpOnly; SameSite=Lax" } });
    }
    const m = url.pathname.match(/^\/get\/([a-z0-9-]+)\/(windows|linux)\/?$/);
    if (!m || !BAKED[m[1]] || !BAKED[m[1]].suffix[m[2]]) {
      const nf = await env.ASSETS.fetch(new URL("/404", url));
      return new Response(nf.body, { status: 404, headers: { ...SEC, "Content-Type": "text/html; charset=utf-8" } });
    }
    const entry = BAKED[m[1]], system = m[2], page = "https://github.com/zmardanian/" + entry.repo + "/releases/latest";
    if (request.method !== "GET") return new Response(null, { status: 302, headers: { ...SEC, Location: page } });
    const hit = await newest(entry, system, ctx), ua = request.headers.get("User-Agent") || "", cf = request.cf || {};
    let bot = BOT.test(ua) ? 1 : DATACENTRE.has(cf.asn) || HOSTING.test(cf.asOrganization || "") ? 2 : 0;
    if (/(^|;\s*)axell_owner=1/.test(request.headers.get("Cookie") || "")) bot = 4;
    // a few downloads a minute is a person; past that the link still works but is not stored, so nobody can flood the counter
    const limited = env.LIMIT && !(await env.LIMIT.limit({ key: request.headers.get("CF-Connecting-IP") || "" })).success;
    let from = "";
    try { const ref = new URL(request.headers.get("Referer")); from = ref.hostname === "axellsdojo.com" || ref.hostname.endsWith(".axellsdojo.com") ? ref.pathname : ref.hostname; } catch (e) {}
    if (!limited) ctx.waitUntil(note(env, [new Date().toISOString().slice(0, 19).replace("T", " "), entry.name, system, hit ? hit.version : null, hit ? hit.file : null,
      cf.country || null, cf.city || null, from || "(direct)", device(ua), browser(ua), bot, cf.asOrganization || null]));
    // a person gets a thank-you page that starts the download itself (and asks for a tip); tools and bots get the plain redirect
    // only ever to GitHub: a changed or broken API answer can never send a visitor somewhere else
    const to = hit && /^https:\/\/github\.com\/zmardanian\//.test(hit.url) ? hit.url : page;
    if (bot === 1 || !/text\/html/.test(request.headers.get("Accept") || ""))
      return new Response(null, { status: 302, headers: { ...SEC, Location: to } });
    return new Response(thanks(entry.name, system, hit, to), { headers: { ...SEC, "Content-Type": "text/html; charset=utf-8", "Content-Security-Policy": CSP } });
  },
};
