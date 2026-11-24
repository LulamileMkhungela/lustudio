/* Vimeo iframes start only when near the viewport, after page load. */
window.__ccV=window.__ccV||(function(){var L=[],o=null,r=0;function S(f){if(f.__ccOn)return;f.__ccOn=1;f.src=f.getAttribute('data-ccsrc')}function W(f){if(o)o.observe(f);else if(r)S(f);else L.push(f)}function G(){r=1;if('IntersectionObserver' in window){o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){o.unobserve(e.target);S(e.target)}})},{rootMargin:'500px 500px'})}L.splice(0).forEach(W)}if(document.readyState==='complete')G();else addEventListener('load',G,{once:true});return function(f,u){f.setAttribute('data-ccsrc',u);W(f)}})();
try{
(function(){var D={1031482701:[1920,1080],1031489649:[1920,1168],1031492647:[1400,1060],1031860183:[1920,1080],1031864234:[1980,1080],1031879752:[1440,1464],1031883347:[1920,1080]};
document.querySelectorAll('video').forEach(function(v){
var s=v.querySelector('source'),src=(s&&s.getAttribute('src'))||v.getAttribute('src')||'',m=src.match(/vimeo\.com\/(?:video\/)?(\d+)/);if(!m)return;
var id=m[1],w=v.parentElement,f=document.createElement('iframe');
window.__ccV(f,'https://player.vimeo.com/video/'+id+'?background=1&autoplay=1&loop=1&muted=1&dnt=1');
f.setAttribute('allow','autoplay; fullscreen; picture-in-picture');f.setAttribute('title',(document.title.split('|')[0]||'Case').trim()+' video');f.setAttribute('frameborder','0');f.setAttribute('data-vid',id);
f.style.cssText='position:absolute;top:-1px;left:-1px;width:calc(100% + 2px);height:calc(100% + 2px);border:0;';
if(getComputedStyle(w).position==='static')w.style.position='relative';w.style.overflow='hidden';
v.replaceWith(f);
if(!w.classList.contains('work_image-wrap'))return;
function ar(a,b){if(w.dataset.fix)return;w.style.height='auto';w.style.aspectRatio=a+' / '+b;}
if(D[id])ar(D[id][0],D[id][1]);else fetch('https://vimeo.com/api/oembed.json?url=https%3A//vimeo.com/'+id).then(function(r){return r.json()}).then(function(j){if(j.width&&j.height)ar(j.width,j.height)}).catch(function(){});
});})();
}catch(e){console.error("casevimeoembed-1.2.0.js",e)}
try{
(function(){if(!/^\/projects\/zeuss(-[a-z-]+)?\/?$/.test(location.pathname))return;
function W(k){var e=document.querySelector('.work_image-wrap img[src*="'+k+'"],.work_image-wrap iframe[data-vid="'+k+'"]');return e&&e.closest('.work_image-wrap');}
var H={'0582c314':3658,'10ad79e0':3085,'5e138d35':5203,'394caab6':5665,'04ec4d75':6150,'bc947e04':1003,'4ab302b3':1089,'e5fcac4e':3141,'9362a568':1899,'79e0c618':3491,'036fc2f9':1983,'002cc42e':3654};
document.querySelectorAll('.work_image-wrap:not(.portrait) img').forEach(function(i){var w=i.closest('.work_image-wrap');function ar(a,b){w.style.aspectRatio=a+' / '+b;w.style.height='auto';}for(var k in H){if(i.src.indexOf(k)>-1)ar(2360,H[k]);}i.addEventListener('load',function(){if(i.naturalWidth)ar(i.naturalWidth,i.naturalHeight);});});
['0582c314','e5fcac4e','79e0c618','002cc42e','1031879752'].forEach(function(k){var w=W(k);if(w){w.style.width='66%';w.style.justifySelf='center';w.style.marginLeft='auto';w.style.marginRight='auto';}});
[[['1031492647','10ad79e0','5e138d35','394caab6','04ec4d75'],1],[['bc947e04','1031864234','4ab302b3'],1],[['036fc2f9','1031879752','002cc42e'],0]].forEach(function(G){
var g=G[0],s=G[1],ws=g.map(W).filter(Boolean);if(ws.length<2)return;
var a=ws.filter(function(w){return w.querySelector('img')})[0]||ws[0],p=a.closest('.w-dyn-list')||a.parentElement;
var r=getComputedStyle(ws[0]).borderRadius,c=document.createElement('div');
c.style.cssText='display:flex;flex-direction:column;align-items:center;width:100%;margin-bottom:12px;'+(s?'gap:0;overflow:hidden;border-radius:'+r+';':'gap:12px;');
p.parentNode.insertBefore(c,p);
ws.forEach(function(w){if(s){w.style.borderRadius='0';w.style.width='100%';w.style.margin='0';}else if(!w.style.width){w.style.width='100%';}c.appendChild(w);});
});})();
}catch(e){console.error("zeusscaselayout-1.2.0.js",e)}
try{
(function(){var C=(window.CML||{})[location.pathname.replace(/\/$/,'').split('/').pop()];if(!C)return;
function W(k){var e=document.querySelector('.work_image-wrap img[src*="'+k+'"],.work_image-wrap iframe[data-vid="'+k+'"]');return e&&e.closest('.work_image-wrap');}
function A(w,a,b){w.style.aspectRatio=a+' / '+b;w.style.height='auto';w.dataset.fix=1;}
document.querySelectorAll('.work_image-wrap:not(.portrait) img').forEach(function(i){var w=i.closest('.work_image-wrap');function f(){if(i.naturalWidth&&!w.dataset.fix)A(w,i.naturalWidth,i.naturalHeight);}i.addEventListener('load',f);if(i.complete)f();});
var d=C.d||{},n=C.n||{},k,w;for(k in d){w=W(k);if(w)A(w,d[k][0],d[k][1]);}
for(k in n){w=W(k);if(w){w.style.width=n[k]+'%';w.style.justifySelf='center';w.style.marginLeft=w.style.marginRight='auto';}}
(C.g||[]).forEach(function(g){var ws=g.map(function(x){return W(x.replace('+',''))});var f=null;ws.forEach(function(x){if(!f&&x&&x.querySelector('img'))f=x;});f=f||ws.filter(Boolean)[0];if(!f)return;
var p=f.closest('.w-dyn-list')||f.parentElement,c=document.createElement('div');c.style.cssText='display:flex;flex-direction:column;align-items:center;width:100%;';
p.parentNode.insertBefore(c,p);var r=getComputedStyle(f).borderRadius,pv=null;
g.forEach(function(x,i){var w=ws[i];if(!w)return;var j=x.charAt(0)=='+'&&pv;w.style.marginTop=(c.children.length&&!j)?'12px':'0';w.style.marginBottom='0';if(!w.style.width)w.style.width='100%';w.style.overflow='hidden';w.style.borderRadius=r;
if(j){pv.style.borderBottomLeftRadius=pv.style.borderBottomRightRadius='0';w.style.borderTopLeftRadius=w.style.borderTopRightRadius='0';}c.appendChild(w);pv=w;});});
document.querySelectorAll('section.section_work').forEach(function(s){if(!s.querySelector('.work_image-wrap')&&!s.innerText.trim())s.style.display='none';});
})();
}catch(e){console.error("caselayoutengine-1.0.0.js",e)}
try{
(function(){var s=location.pathname.replace(/\/$/,'').split('/').pop(),C=(window.CMC||{})[s];if(!C)return;
document.querySelectorAll('.work_image-wrap img').forEach(function(i){var k=(i.src.split('_').pop()||'').slice(0,8),c=C[k];if(!c)return;var w=i.closest('.work_image-wrap');
function go(){var W=c[4]||i.naturalWidth,H=c[5]||i.naturalHeight;if(!W)return;var t=c[0],r=c[1],b=c[2],l=c[3],fw=1-l-r,fh=1-t-b;
w.style.aspectRatio=(W*fw)+' / '+(H*fh);w.style.height='auto';w.style.position='relative';w.style.overflow='hidden';w.dataset.fix=1;
i.style.position='absolute';i.style.maxWidth='none';i.style.objectFit='fill';i.style.width=(100/fw)+'%';i.style.height=(100/fh)+'%';i.style.left=(-l/fw*100)+'%';i.style.top=(-t/fh*100)+'%';}
go();i.addEventListener('load',function(){setTimeout(go,0)});});})();
}catch(e){console.error("casecrop-1.0.0.js",e)}
try{
(function(){var p=location.pathname.replace(/\/$/,'').split('/').pop();var C=(window.CXV||{})[p];var X=["remroom-sleep-tech-brand","ply-procurement-saas-design","solochat-ai-mac-app-design","fastmates-fasting-app-design"];if(!C&&X.indexOf(p)<0)return;
function A(w,a,b){w.style.aspectRatio=a+' / '+b;w.style.height='auto';w.dataset.fix=1;}
document.querySelectorAll('.work_image-wrap:not(.portrait) img').forEach(function(i){var w=i.closest('.work_image-wrap');function f(){if(i.naturalWidth&&!w.dataset.fix)A(w,i.naturalWidth,i.naturalHeight);}i.addEventListener('load',f);if(i.complete)f();});
if(!C)return;function W(k){var i=document.querySelector('.work_image-wrap img[src*="'+k+'"]');return i&&i.closest('.work_image-wrap');}var L={};
C.forEach(function(e){var k=e.slice(0,8),m=e.charAt(8),id=e.slice(9),w=W(k);if(!w)return;var n=document.createElement('div');n.className=w.className;n.style.cssText='position:relative;overflow:hidden;height:auto;aspect-ratio:16 / 9;';
var f=document.createElement('iframe');window.__ccV(f,'https://player.vimeo.com/video/'+id+'?background=1&autoplay=1&loop=1&muted=1&dnt=1');f.setAttribute('allow','autoplay; fullscreen; picture-in-picture');f.setAttribute('frameborder','0');f.setAttribute('data-vid',id);f.setAttribute('title',(document.title.split('|')[0]||'Case').trim()+' video');f.style.cssText='position:absolute;top:-1px;left:-1px;width:calc(100% + 2px);height:calc(100% + 2px);border:0;';n.appendChild(f);
if(m=='a'){var r=L[k]||w;r.parentNode.insertBefore(n,r.nextSibling);L[k]=n;}else w.parentNode.insertBefore(n,w);
fetch('https://vimeo.com/api/oembed.json?url=https%3A//vimeo.com/'+id).then(function(r){return r.json()}).then(function(j){if(j.width&&j.height)n.style.aspectRatio=j.width+' / '+j.height;}).catch(function(){});});})();
}catch(e){console.error("casevideosinject-1.0.0.js",e)}
try{
(function(){var M=window.RCM||{};
function run(){var p=location.pathname.replace(/\/$/,'').split('/').pop();var me=M[p]||'';var list=document.querySelector('.work-other_list');if(!list)return;
var items=[].slice.call(list.querySelectorAll('.work-other_item'));var sc=[];
items.forEach(function(it,i){var a=it.querySelector('a');var s=a?a.getAttribute('href').replace(/\/$/,'').split('/').pop():'';var t=M[s];var v=-1;
if(s&&s!==p){v=0;(t||'').split('').forEach(function(x){if(me.indexOf(x)>-1)v+=x>'Z'?10:1;});}sc.push({it:it,v:v,i:i});});
sc.sort(function(a,b){return b.v-a.v||a.i-b.i;});
sc.forEach(function(o,k){if(k<3&&o.v>=0){o.it.style.display='';list.appendChild(o.it);}else{o.it.style.display='none';}});
list.classList.add('is-related');var c=list.closest('.work-other_component');if(c){var h=c.querySelector('.heading-style-h6');if(h)h.textContent='Related case studies';var w=c.closest('.container-tiny');if(w)w.style.maxWidth='80rem';}}
var st=document.createElement('style');st.textContent='.work-other_list{display:none}.work-other_list.is-related{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.5rem}@media (max-width:767px){.work-other_list.is-related{grid-template-columns:1fr}}';document.head.appendChild(st);
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();})();
(function(){function f(){var s=[].slice.call(document.querySelectorAll('main .padding-section-small.is-case')).filter(function(e){return e.offsetHeight>0;});var last=null;s.forEach(function(e){var t=e.getBoundingClientRect().top;if(last&&t-last.getBoundingClientRect().bottom<40){e.style.display='none';}else{last=e;}});}if(document.readyState==='complete')setTimeout(f,300);else window.addEventListener('load',function(){setTimeout(f,300);});})();
}catch(e){console.error("relatedcases-1.1.0.js",e)}
