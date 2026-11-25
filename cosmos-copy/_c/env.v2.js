/* env.v2 – docs/RELEASE.md */
(function () {
  try {
    if (location.hostname === 'www.cosmos.studio') return;
    var w = window;
    w['ga-disable-G-HJZ3TL30YN'] = true;
    w.__csStaging = true;
    w.__csStagingLog = w.__csStagingLog || [];
    var MAIL = /^(script\.google\.com|script\.googleusercontent\.com)$/i;
    var STATS = /(^|\.)(clarity\.ms|google-analytics\.com|analytics\.google\.com|doubleclick\.net)$/i;
    var GTM = /(^|\.)googletagmanager\.com$/i;
    var OK = 'data:application/json,%7B%22ok%22%3Atrue%2C%22staging%22%3Atrue%7D';
    function parse(u) {
      try { return new URL(String(u && u.url ? u.url : u), location.href); } catch (e) { return null; }
    }
    /* 'mail' | 'stats' | '' */
    function kind(u) {
      var p = parse(u);
      if (!p) return '';
      if (MAIL.test(p.hostname)) return 'mail';
      if (STATS.test(p.hostname)) return 'stats';
      if (GTM.test(p.hostname) && /collect/i.test(p.pathname)) return 'stats';
      return '';
    }
    function scriptBlocked(u) {
      var p = parse(u);
      return !!p && /(^|\.)clarity\.ms$/i.test(p.hostname);
    }
    function log(k, u, body) {
      try {
        var b = body;
        if (b && typeof b !== 'string') b = String(b);
        var e = { kind: k, url: String(u && u.url ? u.url : u).slice(0, 300), body: b ? String(b).slice(0, 8192) : '' };
        w.__csStagingLog.push(e);
        var a = JSON.parse(sessionStorage.getItem('cs_staging_log') || '[]');
        a.push(e);
        sessionStorage.setItem('cs_staging_log', JSON.stringify(a.slice(-50)));
      } catch (e) {}
    }
    var of = w.fetch;
    if (typeof of === 'function') {
      w.fetch = function (input, init) {
        var k = kind(input);
        if (k) {
          log(k, input, init && init.body);
          return Promise.resolve(k === 'mail'
            ? new Response('{"ok":true,"staging":true}', { status: 200, headers: { 'content-type': 'application/json' } })
            : new Response(null, { status: 204 }));
        }
        return of.apply(this, arguments);
      };
    }
    var X = w.XMLHttpRequest && w.XMLHttpRequest.prototype;
    if (X) {
      var oo = X.open, os = X.send;
      X.open = function (m, u) {
        var k = kind(u);
        if (k) {
          this.__csK = k; this.__csU = u;
          var a = Array.prototype.slice.call(arguments);
          a[0] = 'GET'; a[1] = OK;
          return oo.apply(this, a);
        }
        this.__csK = null;
        return oo.apply(this, arguments);
      };
      X.send = function (body) {
        if (this.__csK) { log(this.__csK, this.__csU, body); return os.call(this); }
        return os.apply(this, arguments);
      };
    }
    var nav = w.navigator;
    if (nav && typeof nav.sendBeacon === 'function') {
      var ob = nav.sendBeacon;
      nav.sendBeacon = function (u, d) {
        var k = kind(u);
        if (k) { log(k, u, d); return true; }
        return ob.apply(nav, arguments);
      };
    }
    var SE = w.HTMLScriptElement && w.HTMLScriptElement.prototype;
    var d = SE && Object.getOwnPropertyDescriptor(SE, 'src');
    if (d && d.set) {
      Object.defineProperty(SE, 'src', {
        configurable: true, enumerable: d.enumerable, get: d.get,
        set: function (v) { if (scriptBlocked(v)) { log('script', v); return; } d.set.call(this, v); }
      });
    }
    var sa = w.Element && w.Element.prototype.setAttribute;
    if (sa) {
      w.Element.prototype.setAttribute = function (n, v) {
        if (String(n).toLowerCase() === 'src' && this instanceof w.HTMLScriptElement && scriptBlocked(v)) { log('script', v); return; }
        return sa.apply(this, arguments);
      };
    }
    var swap = function () {
      var nodes = document.querySelectorAll('[data-turnstile-sitekey]');
      for (var i = 0; i < nodes.length; i++) nodes[i].setAttribute('data-turnstile-sitekey', '1x00000000000000000000AA');
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', swap);
    else swap();
  } catch (e) {}
})();
