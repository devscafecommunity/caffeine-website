/* Caffeine documentation: progressive enhancement only. Every page works without this file. */
(() => {
  "use strict";

  const html = document.documentElement;
  const body = document.body;
  const root = body.dataset.root || ".";
  const lang = body.dataset.lang || "en";

  const store = {
    get(key) { try { return localStorage.getItem(key); } catch (e) { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch (e) { /* private mode */ } },
  };

  /* ---------- Theme ---------- */
  const themeBtn = document.querySelector("[data-theme-toggle]");
  const systemDark = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  const effectiveTheme = () => html.dataset.theme || (systemDark && systemDark.matches ? "dark" : "light");
  themeBtn && themeBtn.addEventListener("click", () => {
    const next = effectiveTheme() === "dark" ? "light" : "dark";
    html.dataset.theme = next;
    store.set("caf-theme", next);
  });

  /* ---------- Mobile navigation drawer ---------- */
  const navBtn = document.querySelector(".nav-toggle");
  const setNav = (open) => {
    html.classList.toggle("nav-open", open);
    if (navBtn) navBtn.setAttribute("aria-expanded", String(open));
  };
  navBtn && navBtn.addEventListener("click", () => setNav(!html.classList.contains("nav-open")));
  document.querySelectorAll("[data-nav-close]").forEach((el) => el.addEventListener("click", () => setNav(false)));
  document.querySelectorAll(".sidebar a").forEach((a) => a.addEventListener("click", () => setNav(false)));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setNav(false); });

  // Keep the current page visible in the sidebar without scrolling the window.
  const sidebar = document.querySelector(".sidebar");
  const current = sidebar && sidebar.querySelector('[aria-current="page"]');
  if (sidebar && current) {
    const r = current.getBoundingClientRect();
    const s = sidebar.getBoundingClientRect();
    if (r.top < s.top || r.bottom > s.bottom) {
      sidebar.scrollTop += (r.top - s.top) - sidebar.clientHeight / 2;
    }
  }

  /* ---------- Reading progress ---------- */
  const bar = document.querySelector(".progress");
  const onScroll = () => {
    if (!bar) return;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = `scaleX(${max > 0 ? Math.min(1, window.scrollY / max) : 0})`;
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Table of contents scroll-spy ---------- */
  const tocLinks = new Map();
  document.querySelectorAll(".toc-rail .toc a").forEach((a) => tocLinks.set(a.hash.slice(1), a));
  const setActive = (id) => {
    tocLinks.forEach((a, key) => a.classList.toggle("is-active", key === id));
  };
  const headings = [...tocLinks.keys()].map((id) => document.getElementById(id)).filter(Boolean);
  if ("IntersectionObserver" in window && headings.length) {
    const io = new IntersectionObserver((entries) => {
      const visible = entries.filter((e) => e.isIntersecting).map((e) => e.target.id);
      if (visible.length) setActive(visible[0]);
    }, { rootMargin: "-18% 0px -68% 0px" });
    headings.forEach((h) => io.observe(h));
  }

  /* ---------- Copy buttons ---------- */
  document.querySelectorAll("button[data-copy]").forEach((btn) => {
    const label = btn.textContent;
    btn.addEventListener("click", async () => {
      const code = btn.closest(".codeblock");
      const text = code ? code.querySelector("pre").innerText : "";
      let done = false;
      try {
        await navigator.clipboard.writeText(text);
        done = true;
      } catch (e) {
        const area = document.createElement("textarea");
        area.value = text;
        area.setAttribute("readonly", "");
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        try { done = document.execCommand("copy"); } catch (err) { done = false; }
        area.remove();
      }
      btn.textContent = done ? body.dataset.copied || "Copied" : "×";
      btn.classList.toggle("is-done", done);
      setTimeout(() => { btn.textContent = label; btn.classList.remove("is-done"); }, 1600);
    });
  });

  /* ---------- Search palette ---------- */
  const dialog = document.getElementById("palette");
  const input = document.getElementById("palette-input");
  const list = document.getElementById("palette-results");
  const hint = dialog ? dialog.querySelector(".palette__hint") : null;
  let index = null;
  let loading = null;
  let items = [];
  let active = -1;

  const loadIndex = () => {
    if (index) return Promise.resolve(index);
    if (loading) return loading;
    loading = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = `${root}/assets/search-${lang}.js`;
      s.async = true;
      s.onload = () => {
        index = (window.CAFFEINE_SEARCH && window.CAFFEINE_SEARCH[lang]) || [];
        resolve(index);
      };
      s.onerror = () => reject(new Error("search index failed to load"));
      document.head.appendChild(s);
    });
    return loading;
  };

  const terms = (q) => q.toLowerCase().trim().split(/\s+/).filter(Boolean);

  const search = (q) => {
    const t = terms(q);
    if (!t.length || !index) return [];
    const scored = [];
    for (const e of index) {
      const title = e.t.toLowerCase();
      const heads = e.h.toLowerCase();
      const body = e.b.toLowerCase();
      const section = e.s.toLowerCase();
      const desc = e.d.toLowerCase();
      let score = 0;
      let ok = true;
      for (const term of t) {
        const inTitle = title.includes(term);
        const inHead = heads.includes(term);
        const inDesc = desc.includes(term);
        const inBody = body.includes(term);
        const inSection = section.includes(term);
        if (!(inTitle || inHead || inDesc || inBody || inSection)) { ok = false; break; }
        score += (inTitle ? 12 : 0) + (inHead ? 4 : 0) + (inDesc ? 2 : 0) + (inBody ? 1 : 0) + (inSection ? 1 : 0);
      }
      if (ok) scored.push([score, e]);
    }
    scored.sort((a, b) => b[0] - a[0] || a[1].t.localeCompare(b[1].t));
    return scored.slice(0, 30).map(([, e]) => e);
  };

  const snippet = (e, t) => {
    const lower = e.b.toLowerCase();
    let pos = -1;
    for (const term of t) {
      const p = lower.indexOf(term);
      if (p >= 0 && (pos < 0 || p < pos)) pos = p;
    }
    if (pos < 0) return e.d;
    const start = Math.max(0, pos - 60);
    return (start > 0 ? "…" : "") + e.b.slice(start, pos + 150).trim() + "…";
  };

  const highlight = (parent, text, t) => {
    parent.textContent = "";
    if (!t.length) { parent.textContent = text; return; }
    const pattern = new RegExp("(" + t.map((x) => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")", "ig");
    text.split(pattern).forEach((part, i) => {
      if (i % 2) {
        const mark = document.createElement("mark");
        mark.textContent = part;
        parent.appendChild(mark);
      } else if (part) {
        parent.appendChild(document.createTextNode(part));
      }
    });
  };

  const setActiveItem = (i) => {
    if (!items.length) return;
    active = (i + items.length) % items.length;
    items.forEach((el, n) => {
      el.setAttribute("aria-selected", String(n === active));
      if (n === active) el.scrollIntoView({ block: "nearest" });
    });
  };

  const render = (q) => {
    if (!list) return;
    list.textContent = "";
    items = [];
    active = -1;
    const t = terms(q);
    if (!index) {
      if (hint) hint.textContent = body.dataset.loading || "";
      return;
    }
    if (!t.length) {
      if (hint) hint.textContent = body.dataset.hint || "";
      return;
    }
    const results = search(q);
    if (hint) hint.textContent = results.length ? "" : `${body.dataset.noResults || ""} “${q}”`;
    results.forEach((e) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.className = "palette__item";
      a.href = `${root}/${e.u}`;
      a.setAttribute("role", "option");
      const small = document.createElement("small");
      small.textContent = e.s;
      const strong = document.createElement("strong");
      highlight(strong, e.t, t);
      const snip = document.createElement("span");
      snip.className = "snip";
      highlight(snip, snippet(e, t), t);
      a.append(small, strong, snip);
      li.appendChild(a);
      list.appendChild(li);
      items.push(a);
    });
    if (items.length) setActiveItem(0);
  };

  const openSearch = () => {
    if (!dialog || typeof dialog.showModal !== "function") {
      window.location.href = `${root}/`;
      return;
    }
    if (!dialog.open) dialog.showModal();
    input.value = "";
    render("");
    input.focus();
    loadIndex().then(() => render(input.value)).catch(() => { if (hint) hint.textContent = "⚠"; });
  };

  document.querySelectorAll("[data-open-search]").forEach((el) => el.addEventListener("click", openSearch));

  if (dialog && input) {
    input.addEventListener("input", () => render(input.value));
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { e.preventDefault(); setActiveItem(active + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setActiveItem(active - 1); }
      else if (e.key === "Enter") {
        const target = items[active] || items[0];
        if (target) { e.preventDefault(); window.location.href = target.href; }
      }
    });
    dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  }

  const typing = (el) => el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName));
  document.addEventListener("keydown", (e) => {
    const k = e.key.toLowerCase();
    if ((k === "k" && (e.metaKey || e.ctrlKey)) || (k === "/" && !typing(document.activeElement) && !e.metaKey && !e.ctrlKey && !e.altKey)) {
      e.preventDefault();
      openSearch();
    }
  });
})();
