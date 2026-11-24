
(function () {
  "use strict";
  var root = document.documentElement;

  /* Light Cosmos dropdowns. */
  document.querySelectorAll('.w-dropdown').forEach(function (dd) {
    var toggle = dd.querySelector('.w-dropdown-toggle');
    var list = dd.querySelector('.dropdown-list');
    if (!toggle || !list) return;
    function open() { list.classList.add('w--open'); dd.classList.add('is-open'); }
    function close() { list.classList.remove('w--open'); dd.classList.remove('is-open'); }
    dd.addEventListener('mouseenter', open);
    dd.addEventListener('mouseleave', close);
    toggle.addEventListener('click', function (e) {
      e.preventDefault();
      dd.classList.contains('is-open') ? close() : open();
    });
  });

  /* Mobile menu. */
  var openBtn = document.querySelector('.navbar_menu-open');
  var menu = document.querySelector('.menu');
  var closeBtn = document.querySelector('.menu_close');
  var menuBg = document.querySelector('.menu_bg');
  function setMenu(open) {
    if (!menu || !openBtn) return;
    menu.classList.toggle('is-open', open);
    openBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (menuBg) menuBg.style.display = open ? 'block' : '';
  }
  if (openBtn) openBtn.addEventListener('click', function () { setMenu(!menu.classList.contains('is-open')); });
  if (closeBtn) closeBtn.addEventListener('click', function () { setMenu(false); });
  if (menuBg) menuBg.addEventListener('click', function () { setMenu(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });

  /* For You is the default Cosmos view; other options stay pending. */
  var switches = Array.prototype.slice.call(document.querySelectorAll('[data-lz-view-switch]'));
  var status = document.getElementById('lz-view-status');
  var labels = { marketing:'For Marketing Teams', you:'For You', tech:'For Tech', 'else':'Something Else' };
  function closeAll() {
    switches.forEach(function (sw) {
      sw.classList.remove('is-open');
      var toggle = sw.querySelector('[data-view-toggle]');
      var menu = sw.querySelector('.lz-view-menu');
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
      if (menu) menu.hidden = true;
    });
  }
  function applyView(view, persist) {
    if (!labels[view]) view = 'you';
    switches.forEach(function (sw) {
      var label = sw.querySelector('[data-view-label]');
      var toggle = sw.querySelector('[data-view-toggle]');
      if (label) label.textContent = labels[view];
      if (toggle) toggle.setAttribute('aria-label', 'View: ' + labels[view]);
      sw.querySelectorAll('[data-view-option]').forEach(function (item) {
        var selected = item.getAttribute('data-view-option') === view;
        item.classList.toggle('is-selected', selected);
        item.setAttribute('aria-checked', selected ? 'true' : 'false');
      });
    });
    root.setAttribute('data-view', 'default');
    root.setAttribute('data-view-label', labels[view]);
    if (status) status.textContent = view === 'you'
      ? 'For You is showing the default LulaZel Hub / Cosmos view.'
      : labels[view] + ' is selected. Its custom view direction is pending; the default LulaZel Hub / Cosmos view remains visible.';
    if (persist !== false) { try { sessionStorage.setItem('lulazel-view', view); } catch (e) {} }
  }
  switches.forEach(function (sw) {
    var toggle = sw.querySelector('[data-view-toggle]');
    var menu = sw.querySelector('.lz-view-menu');
    if (!toggle || !menu) return;
    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      var willOpen = menu.hidden;
      closeAll();
      if (willOpen) {
        sw.classList.add('is-open');
        toggle.setAttribute('aria-expanded', 'true');
        menu.hidden = false;
      }
    });
    sw.querySelectorAll('[data-view-option]').forEach(function (item) {
      item.addEventListener('click', function () { applyView(item.getAttribute('data-view-option')); closeAll(); });
    });
  });
  document.addEventListener('click', function (e) {
    if (!switches.some(function (sw) { return sw.contains(e.target); })) closeAll();
  });
  var saved = null;
  try { saved = sessionStorage.getItem('lulazel-view'); } catch (e) {}
  applyView(saved || 'you', false);

  /* Works filters. */
  var cards = Array.prototype.slice.call(document.querySelectorAll('.lz-work-card'));
  if (cards.length) {
    var service = document.querySelector('[data-filter="service"]');
    var industry = document.querySelector('[data-filter="industry"]');
    var search = document.querySelector('[data-filter="search"]');
    var empty = document.querySelector('.lz-empty-works');
    function filterWorks() {
      var sv = service ? service.value : '';
      var ind = industry ? industry.value : '';
      var q = search ? search.value.trim().toLowerCase() : '';
      var visible = 0;
      cards.forEach(function (card) {
        var services = (card.getAttribute('data-services') || '').toLowerCase();
        var industries = (card.getAttribute('data-industries') || '').toLowerCase();
        var text = (card.getAttribute('data-title') || '').toLowerCase();
        var ok = (!sv || services.indexOf(sv.toLowerCase()) !== -1) &&
                 (!ind || industries.indexOf(ind.toLowerCase()) !== -1) &&
                 (!q || text.indexOf(q) !== -1);
        card.classList.toggle('is-hidden', !ok);
        if (ok) visible += 1;
      });
      if (empty) empty.classList.toggle('is-visible', visible === 0);
    }
    [service, industry, search].forEach(function (el) { if (el) el.addEventListener('input', filterWorks); });
    filterWorks();
  }

  /* Cosmos footer clocks in South African time. */
  document.querySelectorAll('.timer-card').forEach(function (card) {
    var time = card.querySelector('.timer.time');
    var pm = card.querySelector('.time-pm');
    var date = card.querySelector('.date-time');
    if (!time) return;
    function tick() {
      var now = new Date();
      var parts = new Intl.DateTimeFormat('en-GB', {
        timeZone: 'Africa/Johannesburg', hour: 'numeric', minute: '2-digit', hour12: true
      }).formatToParts(now);
      var hour = parts.find(function (p) { return p.type === 'hour'; });
      var minute = parts.find(function (p) { return p.type === 'minute'; });
      var period = parts.find(function (p) { return p.type === 'dayPeriod'; });
      time.textContent = (hour ? hour.value : '0') + ':' + (minute ? minute.value : '00');
      if (pm && period) pm.textContent = period.value.toLowerCase();
      if (date) {
        var d = new Intl.DateTimeFormat('en-GB', {
          timeZone: 'Africa/Johannesburg', weekday: 'long', month: 'long', day: 'numeric'
        }).format(now);
        var label = card.querySelector('.date-time_text');
        if (label) label.textContent = d + ' · SAST';
      }
    }
    tick();
    setInterval(tick, 30000);
  });
})();
