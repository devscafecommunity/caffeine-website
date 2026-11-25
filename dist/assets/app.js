// Caffeine site behaviour: theme, navigation, search, code copy, image zoom. No dependencies.
(function () {
  'use strict';
  var doc = document;
  var cfg = window.CAFFEINE || { lang: 'en' };
  var $ = function (sel, root) { return (root || doc).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); };
  function store(key, value) {
    try { if (value === undefined) return localStorage.getItem(key); localStorage.setItem(key, value); } catch (e) { /* storage may be blocked */ }
    return null;
  }

  // Theme ------------------------------------------------------------
  var themeBtn = $('.theme-btn');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var root = doc.documentElement;
      var current = root.getAttribute('data-theme') ||
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = current === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      store('caffeine-theme', next);
    });
  }
  $$('.lang').forEach(function (a) {
    a.addEventListener('click', function () { store('caffeine-lang', a.getAttribute('hreflang')); });
  });

  // Mobile navigation ----------------------------------------------------
  var menuBtn = $('.menu-btn');
  function setNav(open) {
    doc.body.classList.toggle('nav-open', open);
    if (menuBtn) menuBtn.setAttribute('aria-expanded', String(open));
  }
  if (menuBtn) {
    menuBtn.addEventListener('click', function () { setNav(!doc.body.classList.contains('nav-open')); });
    doc.addEventListener('click', function (e) {
      if (doc.body.classList.contains('nav-open') && !e.target.closest('.sidebar') && !e.target.closest('.menu-btn')) setNav(false);
    });
  }

  // Collapsible sidebar tree -------------------------------------------
  $$('.nav-dir').forEach(function (dir) {
    var toggle = $('.nav-toggle', dir);
    var label = $(':scope > .nav-dir-row > .nav-dir-label', dir);
    function flip() {
      var open = dir.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    }
    toggle.addEventListener('click', flip);
    if (label) label.addEventListener('click', flip);
  });
  var active = $('.sidebar .nav-link.active');
  if (active) {
    var box = $('.sidebar');
    var top = active.getBoundingClientRect().top - box.getBoundingClientRect().top;
    if (top > box.clientHeight - 80 || top < 0) box.scrollTop += top - box.clientHeight / 3;
  }

  // Code copy ----------------------------------------------------------
  doc.addEventListener('click', function (e) {
    var btn = e.target.closest('.code-copy');
    if (!btn) return;
    var code = $('code', btn.closest('.code-block'));
    var text = code ? code.textContent : '';
    function done() {
      var old = btn.textContent;
      btn.textContent = cfg.lang === 'pt' ? 'Copiado' : 'Copied';
      btn.classList.add('done');
      setTimeout(function () { btn.textContent = old; btn.classList.remove('done'); }, 1400);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () {});
    } else {
      var area = doc.createElement('textarea');
      area.value = text; doc.body.appendChild(area); area.select();
      try { doc.execCommand('copy'); done(); } catch (err) { /* ignore */ }
      doc.body.removeChild(area);
    }
  });

  // Table of contents scroll spy ------------------------------------------
  var tocLinks = $$('.toc a');
  if (tocLinks.length && 'IntersectionObserver' in window) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
    var heads = $$('.doc h2[id], .doc h3[id]');
    var current = null;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          if (current) current.classList.remove('active');
          current = byId[entry.target.id];
          if (current) current.classList.add('active');
        }
      });
    }, { rootMargin: '-70px 0px -70% 0px' });
    heads.forEach(function (h) { observer.observe(h); });
  }

  // Image zoom ---------------------------------------------------------
  doc.addEventListener('click', function (e) {
    var img = e.target.closest('.doc img, .tour-shots img, .hero-shot img');
    if (!img || img.closest('a')) return;
    var box = doc.createElement('div');
    box.className = 'lightbox';
    var big = doc.createElement('img');
    big.src = img.currentSrc || img.src; big.alt = img.alt;
    box.appendChild(big);
    if (img.alt) { var cap = doc.createElement('p'); cap.textContent = img.alt; box.appendChild(cap); }
    function close() { box.remove(); doc.removeEventListener('keydown', onKey); }
    function onKey(ev) { if (ev.key === 'Escape') close(); }
    box.addEventListener('click', close);
    doc.addEventListener('keydown', onKey);
    doc.body.appendChild(box);
  });

  // Mermaid, loaded only on pages that use it ---------------------------
  if (cfg.mermaid && $('.mermaid')) {
    var script = doc.createElement('script');
    script.src = cfg.mermaid;
    script.onload = function () {
      var dark = doc.documentElement.getAttribute('data-theme') === 'dark' ||
        (!doc.documentElement.getAttribute('data-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
      window.mermaid.initialize({ startOnLoad: false, theme: dark ? 'dark' : 'default' });
      window.mermaid.run({ querySelector: '.mermaid' });
    };
    doc.head.appendChild(script);
  }

  // Search -------------------------------------------------------------
  var modal = $('.search-modal');
  if (!modal) return;
  var input = $('.search-input', modal);
  var list = $('.search-results', modal);
  var tip = $('.search-tip', modal);
  var index = null;
  var loading = null;
  var selected = 0;
  var shown = [];

  function load() {
    if (index) return Promise.resolve(index);
    if (!loading) {
      loading = fetch(cfg.search).then(function (r) { return r.json(); }).then(function (rows) {
        index = rows.map(function (r) {
          return { title: r[0], url: r[1], group: r[2], heads: r[3], text: r[4], lt: r[0].toLowerCase(), lh: r[3].toLowerCase(), lx: r[4].toLowerCase() };
        });
        return index;
      });
    }
    return loading;
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function marked(text, terms) {
    var out = esc(text);
    terms.forEach(function (t) {
      if (!t) return;
      out = out.replace(new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig'), '<mark>$1</mark>');
    });
    return out;
  }
  function snippet(row, terms) {
    var at = -1;
    for (var i = 0; i < terms.length && at < 0; i++) at = row.lx.indexOf(terms[i]);
    if (at < 0) return row.text.slice(0, 140);
    var start = Math.max(0, at - 50);
    return (start ? '… ' : '') + row.text.slice(start, start + 150);
  }
  function score(row, terms) {
    var total = 0;
    for (var i = 0; i < terms.length; i++) {
      var t = terms[i], hit = 0;
      if (row.lt === t) hit += 60;
      if (row.lt.indexOf(t) === 0) hit += 24;
      else if (row.lt.indexOf(t) > 0) hit += 16;
      if (row.lh.indexOf(t) >= 0) hit += 7;
      if (row.lx.indexOf(t) >= 0) hit += 2;
      if (!hit) return 0;
      total += hit;
    }
    return total;
  }
  function render(query) {
    var terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    list.innerHTML = '';
    shown = [];
    selected = 0;
    if (!terms.length) { tip.hidden = false; return; }
    tip.hidden = true;
    var ranked = index.map(function (row) { return { row: row, s: score(row, terms) }; })
      .filter(function (x) { return x.s > 0; })
      .sort(function (a, b) { return b.s - a.s; })
      .slice(0, 12);
    if (!ranked.length) {
      var li = doc.createElement('li');
      li.className = 'search-empty';
      li.textContent = (cfg.lang === 'pt' ? 'Sem resultados para ' : 'No results for ') + '"' + query + '"';
      list.appendChild(li);
      return;
    }
    ranked.forEach(function (x, i) {
      var li = doc.createElement('li');
      if (i === 0) li.className = 'sel';
      li.innerHTML = '<a href="' + x.row.url + '"><span class="r-title"><span>' + marked(x.row.title, terms) + '</span>' +
        '<span class="r-group">' + esc(x.row.group) + '</span></span><span class="r-snip">' +
        marked(snippet(x.row, terms), terms) + '</span></a>';
      list.appendChild(li);
      shown.push(li);
    });
  }
  function open() {
    modal.hidden = false;
    doc.body.style.overflow = 'hidden';
    input.value = '';
    render('');
    load().then(function () { input.focus(); });
    input.focus();
  }
  function close() { modal.hidden = true; doc.body.style.overflow = ''; }
  function move(delta) {
    if (!shown.length) return;
    shown[selected].classList.remove('sel');
    selected = (selected + delta + shown.length) % shown.length;
    shown[selected].classList.add('sel');
    shown[selected].scrollIntoView({ block: 'nearest' });
  }
  $$('.search-btn').forEach(function (b) { b.addEventListener('click', open); });
  $('[data-close]', modal).addEventListener('click', close);
  input.addEventListener('input', function () { load().then(function () { render(input.value); }); });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Enter' && shown[selected]) { location.href = $('a', shown[selected]).getAttribute('href'); }
  });
  doc.addEventListener('keydown', function (e) {
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test((doc.activeElement || {}).tagName || '');
    if ((e.key === 'k' && (e.ctrlKey || e.metaKey)) || (e.key === '/' && !typing)) {
      e.preventDefault();
      modal.hidden ? open() : close();
    } else if (e.key === 'Escape' && !modal.hidden) { close(); }
  });
})();
