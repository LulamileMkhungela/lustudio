
(function () {
  "use strict";
  var root = document.documentElement;
  var switches = Array.prototype.slice.call(document.querySelectorAll('[data-lz-view-switch]'));
  var status = document.getElementById('lz-view-status');
  if (!switches.length) return;

  var labels = {
    marketing: 'For Marketing Teams',
    you: 'For You',
    tech: 'For Tech',
    else: 'Something Else'
  };

  function buttons(scope) {
    return Array.prototype.slice.call(scope.querySelectorAll('[data-view-option]'));
  }
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
      buttons(sw).forEach(function (item) {
        var selected = item.getAttribute('data-view-option') === view;
        item.classList.toggle('is-selected', selected);
        item.setAttribute('aria-checked', selected ? 'true' : 'false');
      });
    });
    // For You is the LulaZel Hub/default view. Other option views are deliberately
    // not invented; they keep this default until their layouts are supplied.
    root.setAttribute('data-view', 'default');
    root.setAttribute('data-view-label', labels[view]);
    if (status) {
      status.textContent = view === 'you'
        ? 'For You is showing the default LulaZel Hub / LulaZel Hub view.'
        : labels[view] + ' is selected. Its custom view direction is pending; the default LulaZel Hub / LulaZel Hub view remains visible.';
    }
    document.dispatchEvent(new CustomEvent('lulazel:viewchange', {
      detail: { view: view, label: labels[view], state: 'default' }
    }));
    if (persist !== false) {
      try { sessionStorage.setItem('lulazel-view', view); } catch (e) {}
    }
  }

  switches.forEach(function (sw) {
    var toggle = sw.querySelector('[data-view-toggle]');
    var menu = sw.querySelector('.lz-view-menu');
    var items = buttons(sw);
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
    toggle.addEventListener('keydown', function (e) {
      if ((e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') && menu.hidden) {
        e.preventDefault();
        closeAll();
        sw.classList.add('is-open');
        toggle.setAttribute('aria-expanded', 'true');
        menu.hidden = false;
        if (items[0]) items[0].focus();
      } else if (e.key === 'Escape' && !menu.hidden) {
        closeAll(); toggle.focus();
      }
    });
    items.forEach(function (item, index) {
      item.addEventListener('click', function () {
        applyView(item.getAttribute('data-view-option'));
        closeAll();
        toggle.focus();
      });
      item.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          e.preventDefault();
          var next = (index + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
          items[next].focus();
        } else if (e.key === 'Escape') {
          closeAll(); toggle.focus();
        }
      });
    });
  });

  document.addEventListener('click', function (e) {
    if (!switches.some(function (sw) { return sw.contains(e.target); })) closeAll();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeAll();
  });

  var saved = null;
  try { saved = sessionStorage.getItem('lulazel-view'); } catch (e) {}
  applyView(saved || 'you', false);
})();
