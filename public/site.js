// Scroll reveals for elements marked .reveal (the release version is written into the page at build time).
(function () {
  const els = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) { els.forEach(function (el) { el.classList.add("in"); }); return; }
  const io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
  }, { rootMargin: "0px 0px -8% 0px" });
  els.forEach(function (el) { io.observe(el); });
})();

// Before/after players: both versions decoded and started together, switched with a 15 ms crossfade (no gap, no
// drift); one player at a time; the bar seeks. Loaded on the first press (no audio downloaded until then).
(function () {
  let ctx = null, current = null;
  let unlocked = false;
  function unlockIOS() {
    if (unlocked) return; unlocked = true;
    try { const a = new Audio("data:audio/wav;base64,UklGRpYDAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YXIDAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="); a.loop = true; a.setAttribute("playsinline", ""); a.play().catch(function () {}); } catch (e) {}
  }
  function audioCtx() {
    if (!ctx) {
      // Safari (iOS 16.4+): play as media, so the ring/silent switch does not mute the examples
      try { if (navigator.audioSession) navigator.audioSession.type = "playback"; } catch (e) {}
      ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return ctx;
  }
  // the files start downloading when the pointer or a finger reaches a player, so Play answers sooner
  const raw = {};
  function get(url) { return raw[url] || (raw[url] = fetch(url).then(function (r) { if (!r.ok) throw 0; return r.arrayBuffer(); }).catch(function (x) { delete raw[url]; throw x; })); }
  function load(url) { return get(url).then(function (b) { delete raw[url]; return new Promise(function (ok, no) { audioCtx().decodeAudioData(b, ok, no); }); }); }
  document.querySelectorAll(".ab").forEach(function (el) {
    const play = el.querySelector(".ab-play"), pos = el.querySelector(".ab-pos"), bar = el.querySelector(".ab-bar");
    const sw = el.querySelectorAll(".ab-switch button");
    let bufs = null, srcs = null, gains = null, t0 = 0, off = 0, side = "a", raf = 0, loading = false;
    function dur() { return bufs ? Math.min(bufs.a.duration, bufs.b.duration) : 1; }
    function now() { return srcs ? off + (ctx.currentTime - t0) : off; }
    function draw() { pos.style.clipPath = "inset(0 " + (100 - 100 * Math.min(1, now() / dur())) + "% 0 0)"; if (srcs) raf = requestAnimationFrame(draw); }
    function stop(keep) {
      if (srcs) { off = keep ? now() : 0; srcs.a.onended = null; srcs.a.stop(); srcs.b.stop(); srcs = null; }
      cancelAnimationFrame(raf); play.innerHTML = "&#9654;"; play.setAttribute("aria-label", "Play"); el.classList.remove("playing"); draw();
    }
    function start(at) {
      if (current && current !== api) current.stop(true);
      current = api; const c = audioCtx(); c.resume();
      gains = { a: c.createGain(), b: c.createGain() }; srcs = {};
      ["a", "b"].forEach(function (k) {
        gains[k].gain.value = (k === side) ? 1 : 0; gains[k].connect(c.destination);
        srcs[k] = c.createBufferSource(); srcs[k].buffer = bufs[k]; srcs[k].connect(gains[k]);
      });
      off = at; t0 = c.currentTime + 0.05; srcs.a.start(t0, at); srcs.b.start(t0, at);
      srcs.a.onended = function () { if (srcs) stop(false); };
      play.innerHTML = "&#10074;&#10074;"; play.setAttribute("aria-label", "Pause"); el.classList.add("playing"); draw();
    }
    const api = { stop: stop };
    function warm() { if (!bufs && !loading && !(navigator.connection && navigator.connection.saveData)) { get(el.dataset.a).catch(function () {}); get(el.dataset.b).catch(function () {}); } }
    el.addEventListener("pointerenter", warm, { once: true }); el.addEventListener("touchstart", warm, { once: true, passive: true });
    el.addEventListener("focusin", warm, { once: true });
    play.addEventListener("click", function () {
      if (srcs) { stop(true); return; }
      if (bufs) { start(off >= dur() - 0.05 ? 0 : off); return; }
      if (loading) return; loading = true; el.classList.add("loading"); unlockIOS(); audioCtx().resume();
      Promise.all([load(el.dataset.a), load(el.dataset.b)]).then(function (r) { bufs = { a: r[0], b: r[1] }; el.classList.remove("loading"); start(0); })
        .catch(function () { el.classList.remove("loading"); loading = false; play.textContent = "!"; play.setAttribute("aria-label", "Could not load the audio - try again"); });
    });
    sw.forEach(function (b) {
      b.addEventListener("click", function () {
        side = b.dataset.side; el.dataset.side = side; sw.forEach(function (x) { x.classList.toggle("on", x === b); x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        if (srcs && gains) { const t = ctx.currentTime; ["a", "b"].forEach(function (k) {
          gains[k].gain.cancelScheduledValues(t); gains[k].gain.setValueAtTime(gains[k].gain.value, t);
          gains[k].gain.linearRampToValueAtTime(k === side ? 1 : 0, t + 0.015); }); }
      });
    });
    sw.forEach(function (x) { x.setAttribute("aria-pressed", x.classList.contains("on") ? "true" : "false"); });
    bar.setAttribute("role", "slider"); bar.setAttribute("tabindex", "0"); bar.setAttribute("aria-label", "Position");
    bar.setAttribute("aria-valuemin", "0"); bar.setAttribute("aria-valuemax", "14"); bar.setAttribute("aria-valuenow", "0");
    bar.addEventListener("keydown", function (ev) {   // arrows: 1 s steps, Home/End: start/end
      const k = ev.key, d = dur(); let at = null;
      if (k === "ArrowRight" || k === "ArrowUp") at = Math.min(d, now() + 1);
      else if (k === "ArrowLeft" || k === "ArrowDown") at = Math.max(0, now() - 1);
      else if (k === "Home") at = 0; else if (k === "End") at = Math.max(0, d - 0.1);
      if (at === null) return; ev.preventDefault(); bar.setAttribute("aria-valuenow", at.toFixed(0));
      if (srcs) { stop(true); start(at); } else { off = at; draw(); }
    });
    bar.addEventListener("click", function (ev) {
      const r = bar.getBoundingClientRect(), at = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)) * dur();
      if (srcs) { stop(true); start(at); } else { off = at; draw(); }
    });
  });
})();

// the visitor's own system first: on Linux the Linux button becomes the main one; on a Mac a note says why there is none
(function () {
  const ua = navigator.userAgent || "", p = (navigator.userAgentData && navigator.userAgentData.platform) || "";
  const linux = /linux/i.test(p) || (/Linux|X11/.test(ua) && !/Android/.test(ua));
  const mac = /mac/i.test(p) || (/Macintosh/.test(ua) && !("ontouchend" in document));
  document.querySelectorAll(".dl").forEach(function (dl) {
    const w = dl.querySelector(".btn-primary"), l = dl.querySelector(".btn-ghost");
    if (!w || !l) return;
    if (linux) {
      w.classList.replace("btn-primary", "btn-ghost"); l.classList.replace("btn-ghost", "btn-primary"); dl.insertBefore(l, w);
    } else if (/Android|iPhone|iPad|iPod/.test(ua) || (mac && "ontouchend" in document)) {
      const n = document.createElement("p"); n.className = "dl-mac";
      n.textContent = "Desktop plugins for Windows and Linux - open this page on your computer. ";
      if (navigator.share) {
        const b = document.createElement("button"); b.type = "button"; b.className = "dl-share"; b.textContent = "Send the link to yourself";
        b.addEventListener("click", function () { navigator.share({ title: document.title, url: location.href }).catch(function () {}); });
        n.appendChild(b);
      }
      dl.insertBefore(n, dl.querySelector(".dl-meta"));
    } else if (mac) {
      const n = document.createElement("p"); n.className = "dl-mac";
      n.textContent = "On a Mac? There is no macOS version yet - the plugins run on Windows and Linux.";
      dl.insertBefore(n, dl.querySelector(".dl-meta"));
    }
  });
})();
