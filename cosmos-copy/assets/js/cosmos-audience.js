(function(){
  function init(){
    document.querySelectorAll('[data-cosmos-audience]').forEach(function(root){
      var trigger=root.querySelector('.cosmos-audience_trigger');
      var current=root.querySelector('[data-cosmos-audience-current]');
      var options=Array.prototype.slice.call(root.querySelectorAll('[data-view-option]'));
      var selected=root.querySelector('.is-selected')||options.filter(function(o){return o.getAttribute('data-view-option')==='you';})[0]||options[0];
      function apply(option){
        options.forEach(function(o){o.classList.toggle('is-selected',o===option);o.setAttribute('aria-selected',o===option?'true':'false');});
        if(current)current.textContent=option.textContent.trim();
        document.documentElement.setAttribute('data-view',option.getAttribute('data-view-option')||'you');
        document.documentElement.setAttribute('data-view-label',option.textContent.trim());
      }
      if(selected)apply(selected);
      if(trigger)trigger.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();var open=root.classList.toggle('is-open');trigger.setAttribute('aria-expanded',open?'true':'false');});
      options.forEach(function(option){option.addEventListener('click',function(){apply(option);root.classList.remove('is-open');if(trigger)trigger.setAttribute('aria-expanded','false');});});
    });
    document.addEventListener('click',function(e){document.querySelectorAll('[data-cosmos-audience].is-open').forEach(function(root){if(!root.contains(e.target)){root.classList.remove('is-open');var t=root.querySelector('.cosmos-audience_trigger');if(t)t.setAttribute('aria-expanded','false');}});});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
