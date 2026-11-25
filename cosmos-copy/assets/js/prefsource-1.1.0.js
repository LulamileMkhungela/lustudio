/* prefsource 1.1.0 (2026-11-09): official Google 'Add to preferred sources' button on the right of the Sources heading of blog posts (Lulamile: not in the sidebar, Google style). Roll back: re-apply 1.0.0 or remove the page script. */
(function(){var d=document;
function build(){var box=d.querySelector('[data-sources]');if(!box||d.querySelector('[data-pref-src]'))return;var h=box.querySelector('h2');if(!h)return;
var row=d.createElement('div');row.setAttribute('data-pref-src','1');row.style.cssText='display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap';
h.parentNode.insertBefore(row,h);row.appendChild(h);h.style.margin='0';
var b=d.createElement('div');b.setAttribute('google-add-preferred-source-btn','');b.setAttribute('data-lang','en');
b.setAttribute('data-theme',matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');row.appendChild(b);
var s=d.createElement('script');s.async=true;s.src='https://news.google.com/swg/js/v1/publisher.js';d.head.appendChild(s);}
d.readyState==='loading'?d.addEventListener('DOMContentLoaded',build):build();})();