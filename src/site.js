// Download buttons point at the release page; when GitHub's public API answers, they are upgraded to the newest
// release's files (and the version is shown). Scroll reveals for elements marked .reveal.
(function () {
  const cache = {};
  function latest(repo) {
    if (!cache[repo]) {
      cache[repo] = fetch("https://api.github.com/repos/zmardanian/" + repo + "/releases/latest", { headers: { Accept: "application/vnd.github+json" } })
        .then(function (r) { return r.ok ? r.json() : null; })
        .catch(function () { return null; });
    }
    return cache[repo];
  }
  document.querySelectorAll(".dl[data-repo]").forEach(function (box) {
    latest(box.dataset.repo).then(function (rel) {
      if (!rel || !rel.assets) return;
      box.querySelectorAll("[data-asset]").forEach(function (a) {
        const hit = rel.assets.find(function (x) { return x.name.indexOf(a.dataset.asset) !== -1; });
        if (hit) a.href = hit.browser_download_url;
      });
      const v = box.querySelector("[data-version]");
      if (v && rel.tag_name) v.textContent = "Version " + rel.tag_name.replace(/^v/, "");
    });
  });
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
  function audioCtx() {
    if (!ctx) {
      // Safari (iOS 16.4+): play as media, so the ring/silent switch does not mute the examples
      try { if (navigator.audioSession) navigator.audioSession.type = "playback"; } catch (e) {}
      ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return ctx;
  }
  function load(url) { return fetch(url).then(function (r) { return r.arrayBuffer(); }).then(function (b) { return new Promise(function (ok, no) { audioCtx().decodeAudioData(b, ok, no); }); }); }
  document.querySelectorAll(".ab").forEach(function (el) {
    const play = el.querySelector(".ab-play"), pos = el.querySelector(".ab-pos"), bar = el.querySelector(".ab-bar");
    const sw = el.querySelectorAll(".ab-switch button");
    let bufs = null, srcs = null, gains = null, t0 = 0, off = 0, side = "a", raf = 0, loading = false;
    function dur() { return bufs ? Math.min(bufs.a.duration, bufs.b.duration) : 1; }
    function now() { return srcs ? off + (ctx.currentTime - t0) : off; }
    function draw() { pos.style.width = (100 * Math.min(1, now() / dur())) + "%"; if (srcs) raf = requestAnimationFrame(draw); }
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
    play.addEventListener("click", function () {
      if (srcs) { stop(true); return; }
      if (bufs) { start(off >= dur() - 0.05 ? 0 : off); return; }
      if (loading) return; loading = true; el.classList.add("loading"); audioCtx().resume();
      Promise.all([load(el.dataset.a), load(el.dataset.b)]).then(function (r) { bufs = { a: r[0], b: r[1] }; el.classList.remove("loading"); start(0); })
        .catch(function () { el.classList.remove("loading"); loading = false; play.textContent = "!"; });
    });
    sw.forEach(function (b) {
      b.addEventListener("click", function () {
        side = b.dataset.side; sw.forEach(function (x) { x.classList.toggle("on", x === b); });
        if (srcs && gains) { const t = ctx.currentTime; ["a", "b"].forEach(function (k) {
          gains[k].gain.cancelScheduledValues(t); gains[k].gain.setValueAtTime(gains[k].gain.value, t);
          gains[k].gain.linearRampToValueAtTime(k === side ? 1 : 0, t + 0.015); }); }
      });
    });
    bar.addEventListener("click", function (ev) {
      const r = bar.getBoundingClientRect(), at = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)) * dur();
      if (srcs) { stop(true); start(at); } else { off = at; draw(); }
    });
  });
})();
