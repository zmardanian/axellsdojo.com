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
