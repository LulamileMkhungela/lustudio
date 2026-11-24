/* /_m/native/blog/embeds-v3.js – shows third-party deck embeds open, loading each when it comes near the viewport.
   Scope: only [data-embed-src]. Allow-list: LinkedIn and Pitch embed routes. No storage, no cookies of ours.
   The placeholder stays behind the frame, and a 34px strip with the link to the original stays under it, so a blocked or failed frame still shows the link. */
(function () {
  'use strict';
  var els = document.querySelectorAll('[data-embed-src]');
  if (!els.length) return;
  var ok = /^https:\/\/(www\.linkedin\.com\/embed\/|pitch\.com\/embed\/)/;
  function load(el) {
    if (el.getAttribute('data-embed-loaded')) return;
    var src = el.getAttribute('data-embed-src');
    if (!ok.test(src)) return;
    el.setAttribute('data-embed-loaded', '1');
    var f = document.createElement('iframe');
    f.title = el.getAttribute('data-embed-title') || 'Embedded pitch deck';
    f.setAttribute('allowfullscreen', '');
    f.setAttribute('referrerpolicy', 'no-referrer');
    f.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:calc(100% - 34px);border:0;z-index:1;background:transparent';
    var p = el.querySelector('[data-embed-placeholder]');
    if (p) p.style.zIndex = '0'; // stays behind the frame: if the frame is blocked or fails, the link is still there
    // Fallback strip inside the frame area (the wrapper reserves 34px for it in the page markup). A blocked or failed frame
    // (ad blocker, firewall) shows the browser's own error page, so the link must not sit under the frame.
    var a = p && p.querySelector('a');
    if (a) {
      var bar = document.createElement('div');
      bar.style.cssText = 'position:absolute;left:0;right:0;bottom:0;height:34px;display:flex;align-items:center;justify-content:center;gap:6px;font-size:14px;line-height:1;z-index:2;color:' + getComputedStyle(p).color;
      bar.appendChild(document.createTextNode('Deck not showing? '));
      var l = a.cloneNode(true); l.style.cssText = 'color:inherit;text-decoration:underline'; bar.appendChild(l);
      el.appendChild(bar);
    }
    f.src = src;
    el.appendChild(f);
  }
  if (!('IntersectionObserver' in window)) { Array.prototype.forEach.call(els, load); return; }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) { io.unobserve(e.target); load(e.target); } });
  }, { rootMargin: '300px 0px' });
  Array.prototype.forEach.call(els, function (el) { io.observe(el); });
})();
