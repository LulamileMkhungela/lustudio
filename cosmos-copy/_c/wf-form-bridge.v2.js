/* wf-form-bridge.v2.js – loaded right after jQuery on pages that carry a Turnstile form (ARCHITECTURE.md §5.1, §6.1).
   Webflow's forms module keeps doing everything (validation alerts, "Please wait…", success redirect to
   /thank-you, the .w-form-fail box). This script only
     1. sends the form POST to our own /api/form instead of webflow.com,
     2. aborts any other jQuery ajax call to Webflow hosts and blocks fetch/sendBeacon to webflow.com/.io,
     3. after a FAILED submit: resets Turnstile (when the server said the token is unusable). The error box stays
        exactly as live Webflow shows it (owner ruling 17.11, D6 closed): the email/WhatsApp line is added only when
        window.CS_FORM_ALT === true; the "Try again" link needs CS_FORM_ALT AND CS_FORM_RETRY === true. Both default off.
     4. lets Webflow's forms module initialise only once per page (one Turnstile api.js, one widget per form):
        Finsweet fs-toc / fs-inject (blog posts) call Webflow.destroy() + Webflow.ready() after building the table of contents, and the forms
        module is not idempotent – each ready() injects another api.js and binds another render handler per form
        (2–4 widgets). Every other Webflow module still restarts as before.
     5. (v2) Turnstile `appearance: 'interaction-only'`: Webflow's forms chunk calls the global turnstile.render(div, {sitekey,
        callback, 'error-callback'}) with no appearance. The widget box now appears only when the visitor has to click; the token
        is still obtained invisibly and the same callback fires. Done by wrapping turnstile.render right after api.js has loaded
        (capture-phase script load listener; 25 ms poll as backup) (explicit `appearance` or `data-appearance` is never overridden). The Webflow chunk stays untouched.
   It never touches the page on success. */
(function (window, document) {
  'use strict';
  var $ = window.jQuery;
  if (!$ || !$.ajaxPrefilter) return;

  // 4. forms.ready once. The bridge runs before webflow.js; the runtime assigns window.Webflow (until then an array of
  // callbacks) before any module is defined, so wrapping define() there catches the forms module before its first ready().
  (function () {
    function onceReady(mod) {
      if (!mod || typeof mod.ready !== 'function') return mod;
      var ready = mod.ready, ran = false;
      mod.ready = function () {
        if (ran) return;
        ran = true;
        return ready.apply(this, arguments);
      };
      return mod;
    }
    function guard(wf) {
      if (wf.__csFormsOnce) return;
      try { Object.defineProperty(wf, '__csFormsOnce', { value: true }); } catch (e) { wf.__csFormsOnce = true; }
      var define = wf.define;
      wf.define = function (name, factory) {
        var args = Array.prototype.slice.call(arguments);
        if (name === 'forms' && typeof factory === 'function') {
          args[1] = function () { return onceReady(factory.apply(this, arguments)); };
        }
        return define.apply(this, args);
      };
    }
    var cur = window.Webflow;
    if (cur && typeof cur.define === 'function') return;   // runtime already up: too late to wrap safely, leave as is
    try {
      Object.defineProperty(window, 'Webflow', {
        configurable: true, enumerable: true,
        get: function () { return cur; },
        set: function (v) {
          cur = v;
          if (v && typeof v.define === 'function') {
            guard(v);
            Object.defineProperty(window, 'Webflow', { value: v, writable: true, configurable: true, enumerable: true });
          }
        }
      });
    } catch (e) {}
  })();

  // 5. Turnstile interaction-only. Pure helper (also unit-tested): returns params with appearance merged in, never overriding.
  function withAppearance(params) {
    if (!params || typeof params !== 'object') return params;
    if (params.appearance != null) return params;
    var out = {}, k;
    for (k in params) if (Object.prototype.hasOwnProperty.call(params, k)) out[k] = params[k];
    out.appearance = 'interaction-only';
    return out;
  }
  (function () {
    function wrap(ts) {
      if (!ts || typeof ts.render !== 'function' || ts.render.__csInteractionOnly) return ts;
      var render = ts.render;
      var wrapped = function (container, params) {
        var args = Array.prototype.slice.call(arguments), self = this, wid, merged = false;
        try {
          var el = typeof container === 'string' ? document.querySelector(container) : container;
          var attr = el && el.getAttribute && el.getAttribute('data-appearance');
          if (!attr) {
            var next = withAppearance(params);
            if (next !== params) {
              merged = true;
              // R1: a hidden widget must not hide a failure. On the FIRST error of this widget remove it and render it again
              // with the caller's ORIGINAL params (no interaction-only), so the visitor sees v1's visible failure state.
              // The original error-callback still runs; the re-render keeps it, and is never wrapped again (no loop).
              var origErr = params['error-callback'], retried = false;
              next['error-callback'] = function () {
                var r;
                if (typeof origErr === 'function') r = origErr.apply(this, arguments);
                if (!retried) {
                  retried = true;
                  try { ts.remove(wid); } catch (e) {}
                  try { render.call(self, container, params); } catch (e) {}
                }
                return r;
              };
              args[1] = next;
            }
          }
        } catch (e) {}
        wid = render.apply(self, args);
        return wid;
      };
      wrapped.__csInteractionOnly = true;
      try { ts.render = wrapped; } catch (e) {}
      return ts;
    }
    // Do NOT define window.turnstile ourselves: api.js refuses to start when the property already exists
    // ("Turnstile already has been loaded"). Instead wrap right after api.js has run: a capture-phase load listener
    // (script load events do not bubble) fires before Webflow's script.onload that triggers the first render.
    var API = /^https:\/\/challenges\.cloudflare\.com\/turnstile\/v0\/api\.js(\?|$)/;
    function tryWrap() { if (window.turnstile) { wrap(window.turnstile); return true; } return false; }
    document.addEventListener('load', function (e) {
      var t = e && e.target;
      if (t && t.tagName === 'SCRIPT' && API.test(t.src || '')) tryWrap();
    }, true);
    if (tryWrap()) return;
    var n = 0, iv = setInterval(function () { if (tryWrap() || ++n > 400) clearInterval(iv); }, 25);   // backup, <=10 s
  })();

  var FORM = /^https:\/\/(formdata\.)?webflow\.com\/api\/v1\/form\/[0-9a-f]+$/i;
  var WF = /^(https?:)?\/\/([a-z0-9-]+\.)*(webflow\.com|webflow\.io|website-files\.com)(\/|$|\?|#)/i;
  var WF_HTTP = /^(https?:)?\/\/([a-z0-9-]+\.)*(webflow\.com|webflow\.io)(\/|$|\?|#)/i;

  function esc(s) { return String(s); }

  function failBoxes() {
    return $('.w-form-fail').filter(function () { return $(this).css('display') !== 'none'; });
  }

  function addHelp(box) {
    if (window.CS_FORM_ALT !== true) return;     // owner ruling 17.11: error box exactly as live – no extra line by default
    if (box.find('.cs-alt').length) return;
    var alt = $('<div class="cs-alt" style="margin-top:12px"></div>')
      .append(document.createTextNode('You can also email '))
      .append($('<a href="mailto:hello@cosmos.studio">hello@cosmos.studio</a>'))
      .append(document.createTextNode(' or message us on '))
      .append($('<a href="https://wa.me/380638324731" target="_blank" rel="noopener">WhatsApp</a>'))
      .append(document.createTextNode('.'));
    box.append(alt);
    if (window.CS_FORM_RETRY !== true) return;   // "Try again" is OFF by default (ruling 3); owner opt-in only
    var form = box.closest('.w-form').find('form').first();
    if (!form.length) return;
    var retry = $('<div class="cs-retry" style="margin-top:8px"><a href="#" role="button">Try again</a></div>');
    retry.find('a').on('click', function (e) {
      e.preventDefault();
      box.find('.cs-alt, .cs-retry').remove();
      box.hide();
      form.show();
    });
    box.append(retry);
  }

  function resetTurnstile() {
    var ts = window.turnstile;
    if (!ts || typeof ts.reset !== 'function') return;
    var done = false;
    $('form[data-turnstile-sitekey]').each(function () {
      $(this).children('div').each(function () {
        if ($(this).find('iframe, input[name="cf-turnstile-response"]').length || /^cf-/.test(this.id || '')) {
          try { ts.reset(this); done = true; } catch (e) {}
        }
      });
    });
    if (!done) { try { ts.reset(); } catch (e) {} }
  }

  // Webflow shows the error box in its own .done/.fail handler, which is attached after ours (prefilter
  // runs first), so wait one tick and retry briefly.
  function afterFailure(status) {
    if (status >= 400 && status < 500) resetTurnstile();   // 4xx: token spent/invalid; 5xx/0: same token can be retried
    var tries = 0;
    (function look() {
      var boxes = failBoxes();
      if (boxes.length) { boxes.each(function () { addHelp($(this)); }); return; }
      if (++tries < 10) setTimeout(look, 50);
    })();
  }

  $.ajaxPrefilter(function (options, original, jqXHR) {
    var url = String(options.url || '');
    if (FORM.test(url)) {
      options.url = '/api/form';
      options.crossDomain = false;
      jqXHR.done(function (res) { if (!res || res.code !== 200) afterFailure(200); });
      jqXHR.fail(function (x) { afterFailure(x && x.status || 0); });
      return;
    }
    if (WF.test(url)) jqXHR.abort();
  });

  // Other transports: never let a request reach Webflow hosts.
  try {
    var nativeFetch = window.fetch;
    if (typeof nativeFetch === 'function') {
      window.fetch = function (input, init) {
        var u = typeof input === 'string' ? input : (input && input.url) || '';
        if (WF_HTTP.test(String(u))) return Promise.reject(new TypeError('Blocked: ' + esc('webflow host')));
        return nativeFetch.apply(this, arguments);
      };
    }
    var nativeBeacon = navigator.sendBeacon;
    if (typeof nativeBeacon === 'function') {
      navigator.sendBeacon = function (u) {
        if (WF_HTTP.test(String(u))) return false;
        return nativeBeacon.apply(navigator, arguments);
      };
    }
  } catch (e) {}
})(window, document);
