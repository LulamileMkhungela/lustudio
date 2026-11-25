/* LulaZel Hub – home "Timeline & Process" 1.0.0 (11 Nov 2026). Approved by Lulamile (prototype v5).
   Replaces the content of the home .features_timeline card: three service tabs (Product / Website / Brand), gantt with arrows on
   desktop, vertical steps with a popover on phones (<=900px). Colors come from the site's Colors variables; .features_timeline is one
   of the always-dark islands (site dark theme resets the palette inside it), so the card looks the same in both themes.
   The gradient is the site's Book a Call gradient (conic, 6s, 1.6s on hover).
   Roll back: remove page script "timeline" from Home – the original Webflow markup is untouched in the Designer. */
(function(){
'use strict';
var IMG='https://res.cloudinary.com/wtugnojd/image/upload/site/team/';
var C='var(--_colors---grey--650,#1c1d1f)',H='var(--_colors---grey--600,#282829)',CH='var(--_colors---grey--550,#353636)';
var CSS='@property --tlba{syntax:"<angle>";initial-value:0deg;inherits:false}@keyframes tlba{to{--tlba:360deg}}'+
'.tl{--tl-fg:var(--_colors---primary--paper,#f5f5f5);--tl-mute:var(--_colors---grey--200,#b6b6b6);--tl-dim:#8a8a8a;--tl-line:var(--_colors---white--20,#fff3);--tl-soft:#ffffff14;--tl-panel:'+C+';--tl-head:'+H+';--tl-chip:'+CH+';--tl-pop:#2a2b2e;'+
'--tl-conic:conic-gradient(from var(--tlba),#ff6ec4,#ffb35c,#7ad8ff,#8b7bff,#ff6ec4);--tl-lin:linear-gradient(120deg,#ff6ec4,#ffb35c,#7ad8ff,#8b7bff);--tl-e:cubic-bezier(.25,1,.5,1);'+
'position:relative;width:100%;display:flex;flex-direction:column;color:var(--tl-fg);text-align:left;font-variant-numeric:tabular-nums}'+
'.tl *{box-sizing:border-box}.tl button{font:inherit;color:inherit;letter-spacing:inherit}'+
'.tl-head{background:var(--tl-head);display:flex;flex-wrap:wrap;gap:1rem 1.5rem;align-items:center;justify-content:space-between;padding:1.75rem 1.125rem .875rem 1.375rem}'+
'.tl-ttl{display:flex;flex-direction:column;gap:.375rem;min-width:0;flex:1 1 20rem}'+
'.tl-ttl h3{margin:0;font-size:clamp(1.25rem,2.2vw,1.625rem);line-height:1.2;font-weight:500;letter-spacing:-.01em;color:var(--tl-fg);text-wrap:balance}'+
'.tl-ttl p{margin:0;color:var(--tl-mute);font-size:.875rem;line-height:1.5;max-width:58ch}.tl-ttl em{font-style:normal;color:var(--tl-fg)}'+
'.tl-meta{display:flex;flex-wrap:wrap;gap:.75rem 1rem;align-items:center}'+
'.tl-team{display:flex;align-items:center;gap:.75rem}.tl-ava{display:flex}'+
'.tl-ava button{all:unset;position:relative;width:40px;height:40px;border-radius:50%;margin-left:-10px;border:2px solid var(--tl-head);transition:transform .3s var(--tl-e)}'+
'.tl-ava button:first-child{margin-left:0}.tl-ava button:hover,.tl-ava button:focus-visible{transform:translateY(-3px);z-index:2}'+
'.tl-ava img{width:100%;height:100%;border-radius:50%;object-fit:cover;display:block}'+
'.tl-tip{position:absolute;bottom:calc(100% + 8px);left:50%;transform:translate(-50%,4px);white-space:nowrap;background:#fff;color:#0f1011;font-size:.75rem;line-height:1.3;padding:6px 9px;border-radius:8px;opacity:0;pointer-events:none;transition:.2s var(--tl-e)}'+
'.tl-tip small{display:block;color:#666;font-size:.6875rem}.tl-ava button:hover .tl-tip,.tl-ava button:focus-visible .tl-tip{opacity:1;transform:translate(-50%,0)}'+
'.tl-team>span{font-size:.8125rem;color:var(--tl-mute);line-height:1.3}.tl-team>span b{color:var(--tl-fg);font-weight:500;display:block}'+
'.tl-time{display:flex;align-items:stretch;border-radius:.5rem;background:var(--tl-chip);overflow:clip}'+
'.tl-time i{display:grid;place-items:center;width:44px;border-right:1px solid var(--tl-soft)}'+
'.tl-time div{padding:9px 14px;display:flex;flex-direction:column;gap:2px}'+
'.tl-time small{font-size:.6875rem;color:var(--tl-dim);text-transform:uppercase;letter-spacing:.06em;line-height:1.2}'+
'.tl-time strong{font-weight:500;font-size:.9375rem;line-height:1.2;white-space:nowrap}'+
'.tl-roll{display:inline-block;height:1.2em;overflow:hidden;vertical-align:bottom}.tl-roll>span{display:block;transition:transform .6s var(--tl-e)}.tl-roll span span{display:block;line-height:1.2em}'+
'.tl-bar{display:flex;flex-wrap:wrap;gap:.75rem 1.25rem;align-items:center;justify-content:space-between;padding:1.25rem 1.375rem 0}'+
'.tl-tabs{display:flex;gap:4px;background:var(--tl-head);padding:4px;border-radius:999px;position:relative;max-width:100%}'+
'.tl-pill{position:absolute;top:4px;bottom:4px;border-radius:999px;background:var(--tl-fg);transition:left .55s var(--tl-e),width .55s var(--tl-e)}'+
'.tl-tab{all:unset;position:relative;z-index:1;cursor:pointer;padding:10px 16px;border-radius:999px;font-size:.875rem;line-height:1.2;font-weight:500;color:var(--tl-mute);white-space:nowrap;transition:color .3s}'+
'.tl-tab:hover{color:var(--tl-fg)}.tl-tab[aria-selected="true"]{color:#0f1011}.tl-tab:focus-visible{outline:2px solid #8b7bff;outline-offset:2px}'+
'.tl-tab .tl-s{display:none}.tl-prog{position:absolute;left:16px;right:16px;bottom:5px;height:2px;border-radius:2px;overflow:hidden;opacity:0;transition:opacity .3s}'+
'.tl-prog:after{content:"";position:absolute;inset:0;background:var(--tl-lin);transform:scaleX(var(--p,0));transform-origin:left}.tl-tabs.tl-auto .tl-tab[aria-selected="true"] .tl-prog{opacity:1}'+
'.tl-chips{display:flex;flex-wrap:wrap;gap:6px;min-height:28px}'+
'.tl-chip{font-size:.75rem;line-height:1.2;color:var(--tl-mute);border:1px solid var(--tl-line);border-radius:999px;padding:5px 10px;transition:opacity .35s var(--tl-e),transform .35s var(--tl-e)}'+
'.tl-chips.tl-out .tl-chip{opacity:0;transform:translateY(4px)}'+
/* desktop gantt */
'.tl-chart{position:relative;margin:1.25rem 1.375rem 0;padding-top:28px}'+
'.tl-grid{position:absolute;inset:0;display:grid;pointer-events:none}.tl-grid div{border-left:1px dashed #ffffff1f;position:relative}.tl-grid div:last-child{border-right:1px dashed #ffffff1f}'+
'.tl-grid span{position:absolute;top:0;left:8px;font-size:.6875rem;line-height:1;color:var(--tl-dim)}'+
'.tl-rows{position:relative;display:flex;flex-direction:column;gap:16px;padding-bottom:24px}'+
'.tl-row{position:relative;height:50px;transition:height .5s var(--tl-e),opacity .4s,margin .5s var(--tl-e)}'+
'.tl-row.tl-off{height:0;opacity:0;margin-top:-16px;pointer-events:none}'+
'.tl-con{position:absolute;top:-16px;width:9px;height:16px;margin-left:-4px;transition:left .7s var(--tl-e),opacity .4s;pointer-events:none}.tl-con svg{display:block}'+
'.tl-row:first-child .tl-con,.tl-row.tl-off .tl-con{opacity:0}'+
'.tl-ph{all:unset;box-sizing:border-box;cursor:pointer;position:absolute;top:0;height:50px;border:1px solid var(--tl-line);border-radius:8px;background:var(--tl-panel);display:flex;align-items:center;justify-content:center;gap:8px;padding:0 32px 0 14px;overflow:hidden;transition:left .7s var(--tl-e),width .7s var(--tl-e),border-color .3s,background .3s}'+
'.tl-ph:hover{border-color:#ffffff73;background:#222325}.tl-ph:focus-visible{outline:2px solid #8b7bff;outline-offset:2px}'+
'.tl-nm{font-size:.9375rem;line-height:1.2;font-weight:500;white-space:nowrap;transition:opacity .22s}'+
'.tl-ix{position:absolute;top:6px;right:10px;font-size:.6875rem;line-height:1;color:var(--tl-dim)}.tl-arr{opacity:.7;transition:transform .3s var(--tl-e)}.tl-ph:hover .tl-arr{transform:translateX(3px)}'+
'.tl-ph.tl-sel{border-color:var(--tl-fg);background:#232426}'+
'.tl-ph.tl-live{border-color:transparent;isolation:isolate}'+
'.tl-ph.tl-live:before,.tl-ph.tl-live:after{content:"";position:absolute;inset:-1px;border-radius:inherit;z-index:-2;background:var(--tl-conic);animation:tlba 6s linear infinite}'+
'.tl-ph.tl-live:after{animation-duration:1.6s;opacity:0;transition:opacity .35s ease}.tl-ph.tl-live:hover:after,.tl-ph.tl-live.tl-sel:after{opacity:1}'+
'.tl-fill{display:none}.tl-ph.tl-live .tl-fill{display:block;position:absolute;inset:1px;border-radius:7px;z-index:-1;background:linear-gradient(90deg,#ff6ec41a,#ffb35c12,#7ad8ff14,#8b7bff1f),var(--tl-panel)}.tl-ph.tl-live.tl-sel .tl-fill{inset:1.5px}'+
'.tl-tag{font-size:.625rem;line-height:1.2;letter-spacing:.06em;text-transform:uppercase;padding:3px 6px;border-radius:5px;background:#ffffff14;color:var(--tl-fg);white-space:nowrap;font-weight:500}'+
'.tl-ph.tl-sup{border-color:transparent;background:transparent;justify-content:flex-start;padding-right:14px;isolation:isolate}'+
'.tl-ph.tl-sup:before{content:"";position:absolute;inset:0;border:1px solid var(--tl-line);border-right:none;border-radius:8px 0 0 8px;background:var(--tl-panel);z-index:-1;-webkit-mask:linear-gradient(90deg,#000 45%,transparent);mask:linear-gradient(90deg,#000 45%,transparent)}'+
'.tl-ph.tl-sup:hover:before,.tl-ph.tl-sup.tl-sel:before{border-color:var(--tl-fg)}.tl-ph.tl-sup .tl-ix{display:none}'+
'.tl-inf{font-size:1rem;line-height:1;background:var(--tl-lin);-webkit-background-clip:text;background-clip:text;color:transparent}'+
'.tl-ph.tl-fade .tl-nm,.tl-ph.tl-fade .tl-tag{opacity:0}'+
'.tl-det{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:1rem 2rem;border-top:1px solid var(--tl-soft);padding:1.375rem;transition:opacity .25s}.tl-det.tl-out{opacity:0}'+
'.tl-det h4,.tl-pop h4{margin:0 0 6px;font-size:1.125rem;line-height:1.3;font-weight:500;color:var(--tl-fg);display:flex;gap:8px 10px;align-items:center;flex-wrap:wrap}'+
'.tl-wk{font-size:.75rem;color:var(--tl-dim);font-weight:400}'+
'.tl-det p,.tl-pop p{margin:0;color:var(--tl-mute);font-size:.875rem;line-height:1.6;max-width:62ch}'+
'.tl-det ul,.tl-pop ul{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:8px}'+
'.tl-det li,.tl-pop li{font-size:.875rem;display:flex;gap:10px;line-height:1.45;color:var(--tl-fg);margin:0}'+
'.tl-det li:before,.tl-pop li:before{content:"";flex:none;width:6px;height:6px;border-radius:50%;margin-top:.5em;background:var(--tl-lin)}'+
'.tl-who{margin-top:12px;font-size:.75rem;color:var(--tl-dim)}'+
/* phones: vertical steps + popover */
'.tl-steps{display:none;list-style:none;margin:0;padding:1.125rem 1.125rem 1.375rem}'+
'.tl-st{position:relative;display:grid;grid-template-columns:34px minmax(0,1fr);column-gap:12px;padding:0 0 22px;margin:0;transition:opacity .4s var(--tl-e),transform .4s var(--tl-e)}'+
'.tl-st:last-child{padding-bottom:0}.tl-st.tl-in{opacity:0;transform:translateY(8px)}'+
'.tl-st:not(:last-child):before{content:"";position:absolute;left:16.5px;top:38px;bottom:6px;width:1px;background:var(--tl-line)}'+
'.tl-st:not(:last-child):after{content:"";position:absolute;left:13px;bottom:4px;width:7px;height:7px;border-right:1px solid var(--tl-mute);border-bottom:1px solid var(--tl-mute);transform:rotate(45deg)}'+
'.tl-node{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;font-size:.6875rem;color:var(--tl-mute);background:var(--tl-panel);border:1px solid var(--tl-line);position:relative;isolation:isolate}'+
'.tl-st.tl-live .tl-node{border-color:transparent;color:var(--tl-fg)}'+
'.tl-st.tl-live .tl-node:before{content:"";position:absolute;inset:-1px;border-radius:50%;z-index:-2;background:var(--tl-conic);animation:tlba 6s linear infinite}'+
'.tl-st.tl-live .tl-node:after{content:"";position:absolute;inset:1px;border-radius:50%;z-index:-1;background:var(--tl-panel)}'+
'.tl-st.tl-sup .tl-node{color:transparent}.tl-i8{position:absolute;inset:0;display:grid;place-items:center;font-size:.9375rem;background:var(--tl-lin);-webkit-background-clip:text;background-clip:text;color:transparent}'+
'.tl-sb{all:unset;box-sizing:border-box;cursor:pointer;display:flex;flex-direction:column;gap:8px;min-width:0;padding:7px 10px 10px;margin:-7px -10px 0;border-radius:10px;transition:background .25s}'+
'.tl-sb:focus-visible{outline:2px solid #8b7bff}.tl-st.tl-open .tl-sb{background:#ffffff0d}'+
'.tl-stop{display:flex;justify-content:space-between;align-items:baseline;gap:10px}.tl-stop b{font-size:.9375rem;line-height:1.3;font-weight:500;min-width:0}'+
'.tl-stop small{font-size:.75rem;color:var(--tl-dim);white-space:nowrap}'+
'.tl-trk{position:relative;height:6px;border-radius:3px;background:#ffffff12;overflow:hidden}'+
'.tl-trk i{position:absolute;top:0;bottom:0;border-radius:3px;background:#ffffff66}.tl-st.tl-live .tl-trk i{background:var(--tl-lin)}.tl-st.tl-sup .tl-trk i{background:linear-gradient(90deg,#ffffff66,transparent)}'+
'.tl-trk:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent calc(100% - 2px),var(--tl-panel) 0);background-size:calc(100% / var(--n,8)) 100%}'+
'.tl-pop{position:absolute;z-index:20;left:1.125rem;right:1.125rem;background:var(--tl-pop);border:1px solid var(--tl-line);border-radius:14px;padding:16px 16px 18px;box-shadow:0 18px 50px #000000b3;display:flex;flex-direction:column;gap:12px;opacity:0;transform:translateY(6px);pointer-events:none;transition:opacity .2s var(--tl-e),transform .25s var(--tl-e)}'+
'.tl-pop.tl-on{opacity:1;transform:none;pointer-events:auto}'+
'.tl-pop:before{content:"";position:absolute;left:var(--nx,40px);width:12px;height:12px;background:var(--tl-pop);border-left:1px solid var(--tl-line);border-top:1px solid var(--tl-line);transform:rotate(45deg)}'+
'.tl-pop.tl-below:before{top:-7px}.tl-pop.tl-above:before{bottom:-7px;transform:rotate(225deg)}.tl-pop h4{margin:0;font-size:1rem;padding-right:28px}'+
'.tl-x{all:unset;cursor:pointer;position:absolute;top:10px;right:10px;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;color:var(--tl-mute)}'+
'.tl-x:hover,.tl-x:focus-visible{background:#ffffff14;color:var(--tl-fg)}.tl-pop .tl-who{margin:0}'+
'@media (max-width:1199px){.tl-ph .tl-tag,.tl-ph .tl-ix,.tl-ph .tl-arr{display:none}.tl-ph{padding:0 10px}.tl-nm{font-size:.875rem}}'+
'@media (max-width:991px){.tl-bar{flex-direction:column;align-items:flex-start}}'+
'@media (max-width:900px){.tl-head{flex-direction:column;align-items:flex-start;padding:1.5rem 1.125rem 1rem}.tl-ttl{flex:none}.tl-meta{width:100%;justify-content:space-between}'+
'.tl-bar{padding:1.125rem 1.125rem 0}.tl-tabs{width:100%}.tl-tab{flex:1;text-align:center;padding:11px 8px}.tl-tab .tl-l{display:none}.tl-tab .tl-s{display:inline}.tl-prog{left:10px;right:10px}'+
'.tl-chart,.tl-det{display:none}.tl-steps{display:block}.tl-time i{display:none}}'+
'@media (max-width:400px){.tl-team>span{display:none}}'+
'@media (prefers-reduced-motion:reduce){.tl *{transition:none!important;animation:none!important}}';

var TABS=[
 {id:"product",name:"UI/UX & Product Design",short:"Product",scale:8,from:4,chips:["Mobile apps","SaaS & CRM","Web portals","Defense"],def:2,ph:[
  {n:"Discovery",s:0,e:1,d:"Interviews, competitors and goals – in days, not weeks.",o:["Customer interviews (The Mom Test)","Competitor and market scan","Success metrics agreed"],w:"Alex, Daria"},
  {n:"UX flows",s:.6,e:2.2,d:"Roles, user flows and the customer journey – processed with AI, decided by people.",o:["User roles and flows","Customer journey map","Information architecture"],w:"Designers, Alex"},
  {n:"Live prototype",s:.5,e:5,live:1,tag:"AI-accelerated",d:"From week 1 you click through a real coded prototype, not a Figma picture. It grows into the production frontend.",o:["Clickable coded prototype from week 1","Several concepts to compare","Feedback in the real product, on your devices"],w:"UI engineers"},
  {n:"UI & design system",s:2.2,e:6,d:"Visual design built straight into components – the design system is code from day one.",o:["Design system in code","Responsive screens and states","Motion and micro-interactions"],w:"UI engineers, Alex"},
  {n:"Backend & integrations",s:4,e:7.3,d:"Our backend engineers connect the frontend to data, auth and APIs.",o:["Node.js, Python or Supabase backend","Integrations and security review","Mobile builds when needed"],w:"Backend engineers"},
  {n:"QA & launch",s:6.8,e:8,d:"Testing on real devices, release and analytics.",o:["Cross-device QA","Release to production","Analytics set up"],w:"Daria, engineers"},
  {n:"Support",s:7.2,e:8,sup:1,d:"After launch we stay: fixes, new features and UX improvements from real data.",o:["Hour packages (retainer)","Improvements based on analytics","Same team that built it"],w:"Daria, Anna"}]},
 {id:"web",name:"Website Design & Development",short:"Website",scale:4,from:1,chips:["Landing pages","Multi-page CMS sites","Webflow & custom code"],def:2,ph:[
  {n:"Discovery",s:0,e:.6,d:"Goals, audience and competitors in one short sprint.",o:["Goals and audience","Competitor scan","Sitemap draft"],w:"Alex, Anna"},
  {n:"Structure & copy",s:.4,e:1.3,d:"Page structure and messaging before any pixels.",o:["Sitemap and wireframes","Key messages and copy","SEO and AI-search structure"],w:"Designers"},
  {n:"Live design",s:.7,e:2.8,live:1,tag:"In code",d:"We design right in the browser. What you review is already the website, not a mockup to be rebuilt.",o:["Working pages from week 1","Real responsive behaviour","Fast rounds of feedback"],w:"UI engineers"},
  {n:"Motion",s:1.8,e:3,d:"Animations that support the story, tuned for speed.",o:["Page and scroll motion","Hover and micro-interactions","Performance budget kept"],w:"UI engineers"},
  {n:"CMS & SEO",s:2.5,e:3.6,d:"Content you can edit yourself, ready for search and AI answers.",o:["CMS collections","SEO and AI-search setup","Forms and integrations"],w:"Engineers"},
  {n:"Launch",s:3.4,e:4,d:"QA on all breakpoints, then go live.",o:["QA on all devices","Domain and analytics","Go live"],w:"Daria, engineers"},
  {n:"Support",s:3.6,e:4,sup:1,d:"New pages, A/B tests and improvements after launch.",o:["Hour packages (retainer)","New pages and tests","Speed and SEO care"],w:"Daria, Anna"}]},
 {id:"brand",name:"Brand Identity",short:"Brand",scale:3,from:1,chips:["Startups","Rebrands","Defense & tech"],def:3,ph:[
  {n:"Research",s:0,e:.6,d:"Market, competitors and moodboards to find your space.",o:["Competitor audit","Moodboards","Positioning brief"],w:"Alex"},
  {n:"Concepts",s:.5,e:1.4,d:"Several directions, each shown in real use.",o:["2–3 identity concepts","Naming and tone options","Shown on real surfaces"],w:"Alex, designers"},
  {n:"Identity system",s:1.2,e:2.3,d:"Logo, colour, type and graphics as one system.",o:["Logo and variations","Colour and typography","Graphic language"],w:"Designers"},
  {n:"Brand in action",s:1.6,e:3,live:1,tag:"In code",d:"Your identity lives in code: a working brand page, animated logo and key screens.",o:["Live brand page","Animated logo","Key product or site screens"],w:"UI engineers"},
  {n:"Guidelines",s:2.2,e:2.8,d:"Everything your team needs to use the brand.",o:["Brand guidelines","Source files and assets","Social and print templates"],w:"Designers"},
  {n:"Support",s:2.6,e:3,sup:1,d:"After handoff we stay: new brand assets, campaigns, pitch decks and site updates in the same style.",o:["Hour packages (retainer)","New assets and templates","Brand kept consistent as you grow"],w:"Daria, Anna"}]}
];
var TEAM=[["daria","Daria","Project Manager"],["alex","Alex","Design Director"],["anna","Anna","Client Partner"]];
var MAXR=7,SUPMIN=118,DUR=9000;
var ARROW='<svg width="9" height="16" viewBox="0 0 9 16" aria-hidden="true"><path d="M4.5 0V14" stroke="#ffffff80" stroke-width="1.2"/><path d="M1 10.5 4.5 14 8 10.5" fill="none" stroke="#ffffffbf" stroke-width="1.2"/></svg>';

function wk(s,e){var a=Math.floor(s)+1,b=Math.max(a,Math.ceil(e));return a===b?'week '+a:'weeks '+a+'–'+b}
function when(p){return p.sup?'after launch':wk(p.s,p.e)}
function pad(n){return (n<10?'0':'')+n}
function tagH(p){return p.tag?' <span class="tl-tag">'+p.tag+'</span>':''}
function list(p){return '<ul>'+p.o.map(function(x){return '<li>'+x+'</li>'}).join('')+'</ul>'}

function mount(card){
  if(card.getAttribute('data-tl'))return;card.setAttribute('data-tl','1');
  if(!document.getElementById('tl-css')){var st=document.createElement('style');st.id='tl-css';st.textContent=CSS;document.head.appendChild(st)}
  var root=document.createElement('div');root.className='tl';
  root.innerHTML='<div class="tl-head"><div class="tl-ttl"><h3>Timeline &amp; Process</h3><p>No static mockups. <em>You see a working frontend from week 1</em> – our engineers finish the backend.</p></div>'+
   '<div class="tl-meta"><div class="tl-team"><div class="tl-ava">'+TEAM.map(function(t){return '<button type="button" aria-label="'+t[1]+' – '+t[2]+'"><img alt="" loading="lazy" width="40" height="40" src="'+IMG+t[0]+'-160.jpg"><span class="tl-tip">'+t[1]+'<small>'+t[2]+'</small></span></button>'}).join('')+'</div><span><b>Your contacts</b>+ design &amp; engineering team</span></div>'+
   '<div class="tl-time"><i><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg></i><div><small>Project time</small><strong>from <span class="tl-roll"><span>'+[1,2,3,4,5,6,7,8].map(function(n){return '<span>'+n+'</span>'}).join('')+'</span></span> <span class="tl-wkw">weeks</span></strong></div></div></div></div>'+
   '<div class="tl-bar"><div class="tl-tabs" role="tablist" aria-label="Service"><span class="tl-pill"></span></div><div class="tl-chips"></div></div>'+
   '<div class="tl-chart"><div class="tl-grid" aria-hidden="true"></div><div class="tl-rows" role="tabpanel"></div></div><div class="tl-det" aria-live="polite"></div>'+
   '<ol class="tl-steps" role="tabpanel"></ol><div class="tl-pop" role="dialog" aria-modal="false"></div>';
  while(card.firstChild)card.removeChild(card.firstChild);
  card.appendChild(root);
  var q=function(s){return root.querySelector(s)};
  var tabsEl=q('.tl-tabs'),pill=q('.tl-pill'),rows=q('.tl-rows'),grid=q('.tl-grid'),chips=q('.tl-chips'),det=q('.tl-det'),rollIn=q('.tl-roll>span'),steps=q('.tl-steps'),pop=q('.tl-pop');
  var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches,mq=matchMedia('(max-width:900px)');
  var cur=0,stopped=false,hover=false,inView=false,elapsed=0,last=0,openStep=-1;
  function tabBtn(i){return tabsEl.querySelectorAll('.tl-tab')[i]}
  TABS.forEach(function(t,i){var b=document.createElement('button');b.type='button';b.className='tl-tab';b.setAttribute('role','tab');
    b.innerHTML='<span class="tl-l">'+t.name+'</span><span class="tl-s">'+t.short+'</span><span class="tl-prog"></span>';
    b.addEventListener('click',function(){stop();go(i)});tabsEl.appendChild(b)});
  tabsEl.addEventListener('keydown',function(e){var k={ArrowRight:1,ArrowLeft:-1}[e.key];if(!k)return;e.preventDefault();stop();var n=(cur+k+TABS.length)%TABS.length;go(n);tabBtn(n).focus()});
  var rowEls=[];
  for(var i=0;i<MAXR;i++)(function(i){var r=document.createElement('div');r.className='tl-row';
    r.innerHTML='<span class="tl-con">'+ARROW+'</span><button type="button" class="tl-ph"><span class="tl-fill"></span><span class="tl-nm"></span><span class="tl-tag" hidden></span><span class="tl-arr" aria-hidden="true">→</span><span class="tl-inf" hidden>∞</span><span class="tl-ix"></span></button>';
    r.querySelector('.tl-ph').addEventListener('click',function(){stop();selPh(i)});rows.appendChild(r);rowEls.push(r)})(i);
  function placePill(){var b=tabBtn(cur);pill.style.left=b.offsetLeft+'px';pill.style.width=b.offsetWidth+'px'}
  function leftOf(p,t){return p.sup?'min('+(p.s/t.scale*100)+'%, calc(100% - '+SUPMIN+'px))':(p.s/t.scale*100)+'%'}
  function renderSteps(t,first){
    closePop();steps.style.setProperty('--n',t.scale);
    steps.innerHTML=t.ph.map(function(p,k){return '<li class="tl-st'+(p.live?' tl-live':'')+(p.sup?' tl-sup':'')+(first||reduce?'':' tl-in')+'"><span class="tl-node" aria-hidden="true">'+pad(k+1)+(p.sup?'<span class="tl-i8">∞</span>':'')+'</span>'+
      '<button type="button" class="tl-sb" aria-expanded="false"><span class="tl-stop"><b>'+p.n+'</b><small>'+when(p)+'</small></span><span class="tl-trk" aria-hidden="true"><i style="left:'+(p.s/t.scale*100)+'%;width:'+(((p.sup?t.scale:p.e)-p.s)/t.scale*100)+'%"></i></span></button></li>'}).join('');
    [].forEach.call(steps.children,function(li,k){
      li.querySelector('.tl-sb').addEventListener('click',function(e){e.stopPropagation();stop();openStep===k?closePop():openPop(k)});
      if(!first&&!reduce)setTimeout(function(){li.classList.remove('tl-in')},40+k*50)});
  }
  function openPop(k){
    var t=TABS[cur],p=t.ph[k],li=steps.children[k],btn=li.querySelector('.tl-sb');
    [].forEach.call(steps.children,function(x,j){x.classList.toggle('tl-open',j===k);x.querySelector('.tl-sb').setAttribute('aria-expanded',j===k)});
    openStep=k;
    pop.innerHTML='<button type="button" class="tl-x" aria-label="Close"><svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M1 1l10 10M11 1 1 11" stroke="currentColor" stroke-width="1.5"/></svg></button>'+
      '<h4>'+p.n+tagH(p)+'<span class="tl-wk">'+when(p)+'</span></h4><p>'+p.d+'</p>'+list(p)+'<div class="tl-who">Led by '+p.w+'</div>';
    pop.querySelector('.tl-x').addEventListener('click',function(e){e.stopPropagation();closePop(true)});
    var sr=root.getBoundingClientRect(),br=btn.getBoundingClientRect();
    pop.classList.remove('tl-on','tl-above','tl-below');pop.style.top='0px';
    var h=pop.offsetHeight,below=br.bottom-sr.top+10,above=br.top-sr.top-h-10,useAbove=below+h>root.offsetHeight-8&&above>8;
    pop.classList.add(useAbove?'tl-above':'tl-below');pop.style.top=(useAbove?above:below)+'px';
    pop.style.setProperty('--nx',Math.max(14,br.left-sr.left-18+12)+'px');
    requestAnimationFrame(function(){pop.classList.add('tl-on')});
  }
  function closePop(refocus){
    if(openStep<0)return;var k=openStep;openStep=-1;pop.classList.remove('tl-on');
    [].forEach.call(steps.children,function(x){x.classList.remove('tl-open');x.querySelector('.tl-sb').setAttribute('aria-expanded','false')});
    if(refocus&&steps.children[k])steps.children[k].querySelector('.tl-sb').focus();
  }
  pop.addEventListener('click',function(e){e.stopPropagation()});
  document.addEventListener('click',function(){closePop()});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closePop(true)});
  function go(i,first){
    cur=i;var t=TABS[i];
    [].forEach.call(tabsEl.querySelectorAll('.tl-tab'),function(b,k){b.setAttribute('aria-selected',k===i);b.tabIndex=k===i?0:-1;b.style.setProperty('--p',0)});
    placePill();elapsed=0;
    rollIn.style.transform='translateY('+(-(t.from-1)*1.2)+'em)';q('.tl-wkw').textContent=t.from===1?'week':'weeks';
    chips.classList.add('tl-out');setTimeout(function(){chips.innerHTML=t.chips.map(function(c){return '<span class="tl-chip">'+c+'</span>'}).join('');requestAnimationFrame(function(){chips.classList.remove('tl-out')})},first?0:250);
    grid.style.gridTemplateColumns='repeat('+t.scale+',1fr)';var g='';for(var w=1;w<=t.scale;w++)g+='<div><span>W'+w+'</span></div>';grid.innerHTML=g;
    renderSteps(t,first);
    rowEls.forEach(function(r,k){
      var p=t.ph[k],ph=r.querySelector('.tl-ph'),con=r.querySelector('.tl-con');
      setTimeout(function(){
        if(!p){r.classList.add('tl-off');ph.style.width='0%';return}
        r.classList.remove('tl-off');ph.classList.add('tl-fade');
        setTimeout(function(){
          ph.querySelector('.tl-nm').textContent=p.n;
          var tg=ph.querySelector('.tl-tag');tg.hidden=!p.tag;tg.textContent=p.tag||'';
          ph.querySelector('.tl-ix').textContent=pad(k+1);
          ph.querySelector('.tl-inf').hidden=!p.sup;ph.querySelector('.tl-arr').hidden=!!p.sup;
          ph.classList.toggle('tl-live',!!p.live);ph.classList.toggle('tl-sup',!!p.sup);
          ph.setAttribute('aria-label',p.n+', '+(p.sup?'ongoing after launch':wk(p.s,p.e)));
          ph.classList.remove('tl-fade');
        },first?0:200);
        ph.style.left=leftOf(p,t);
        ph.style.width=p.sup?'max('+((t.scale-p.s)/t.scale*100)+'%, '+SUPMIN+'px)':((p.e-p.s)/t.scale*100)+'%';
        var prev=t.ph[k-1];if(prev)con.style.left='calc(max('+leftOf(p,t)+', '+leftOf(prev,t)+') + 16px)';
      },first||reduce?0:k*60);
    });
    selPh(t.def,first);
  }
  function selPh(k,first){
    var p=TABS[cur].ph[k];if(!p)return;
    rowEls.forEach(function(r,j){r.querySelector('.tl-ph').classList.toggle('tl-sel',j===k)});
    det.classList.add('tl-out');
    setTimeout(function(){
      det.innerHTML='<div><h4>'+p.n+tagH(p)+'<span class="tl-wk">'+(p.sup?'after launch · ongoing':wk(p.s,p.e))+'</span></h4><p>'+p.d+'</p><div class="tl-who">Led by '+p.w+'</div></div>'+list(p);
      det.classList.remove('tl-out');
    },first?0:180);
  }
  function stop(){stopped=true;tabsEl.classList.remove('tl-auto')}
  function tick(ts){
    var dt=last?ts-last:0;last=ts;
    tabsEl.classList.toggle('tl-auto',!stopped&&!mq.matches&&!reduce);
    if(!stopped&&!reduce&&!mq.matches&&inView&&!hover&&!document.hidden){elapsed+=Math.min(dt,100);tabBtn(cur).style.setProperty('--p',Math.min(1,elapsed/DUR));if(elapsed>=DUR)go((cur+1)%TABS.length)}
    requestAnimationFrame(tick);
  }
  if('IntersectionObserver' in window)new IntersectionObserver(function(es){inView=es[0].isIntersecting},{threshold:.4}).observe(root);else inView=true;
  root.addEventListener('mouseenter',function(){hover=true});root.addEventListener('mouseleave',function(){hover=false});
  root.addEventListener('focusin',function(){hover=true});root.addEventListener('focusout',function(){hover=false});
  root.addEventListener('touchstart',stop,{passive:true});
  window.addEventListener('resize',function(){placePill();closePop()});
  if(mq.addEventListener)mq.addEventListener('change',function(){placePill();closePop()});
  go(0,true);requestAnimationFrame(tick);
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(placePill);
  setTimeout(placePill,600);
}
function init(){var c=document.querySelector('.features_timeline');if(c)mount(c)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
