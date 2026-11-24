/* mobilefix 1.0.0 (2026-11-11): reviews link lands below the navbar; timeline popover kept on screen */
(function(){
function navH(){var n=document.querySelector('.navbar');return(n&&n.offsetHeight||64)+24}
function go(y){y=Math.max(0,Math.round(y));var r=matchMedia('(prefers-reduced-motion: reduce)').matches;
if(typeof lenis!=='undefined'&&lenis&&lenis.scrollTo){lenis.scrollTo(y,{immediate:r})}else{scrollTo({top:y,behavior:r?'auto':'smooth'})}}
document.addEventListener('click',function(e){
var a=e.target.closest&&e.target.closest('[data-rtk-more]');if(!a)return;
var t=document.getElementById('lt-rv')||document.getElementById('client-reviews');if(!t)return;
e.preventDefault();e.stopPropagation();
var s=t.closest('section')||t,w=document.createTreeWalker(s,NodeFilter.SHOW_TEXT,{acceptNode:function(n){return n.nodeValue.trim()&&n.parentElement.getClientRects().length?1:3}}),f=w.nextNode(),el=f?f.parentElement:s;
go(el.getBoundingClientRect().top+pageYOffset-navH());
if(history.replaceState)history.replaceState(null,'','#lt-rv');
},true);
function watch(p){new MutationObserver(function(){
if(!p.classList.contains('tl-on')||innerWidth>900)return;
requestAnimationFrame(function(){var r=p.getBoundingClientRect(),top=navH()-8,d=0;
if(r.top<top)d=r.top-top;else if(r.bottom>innerHeight-12)d=Math.min(r.bottom-innerHeight+12,r.top-top);
if(Math.abs(d)>2)go(pageYOffset+d)})}).observe(p,{attributes:true,attributeFilter:['class']})}
function init(){var p=document.querySelector('.tl-pop');if(p){watch(p);return true}}
if(!init()){var mo=new MutationObserver(function(){if(init())mo.disconnect()});mo.observe(document.documentElement,{childList:true,subtree:true});setTimeout(function(){mo.disconnect()},15000)}
})();