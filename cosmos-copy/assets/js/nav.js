
(function () {
  "use strict";
  var root = document.documentElement;
  var toggle = document.querySelector("[data-audience-toggle]");
  var menu = document.getElementById("tf-audience-menu");
  var label = document.querySelector("[data-audience-label]");
  var dot = document.querySelector("[data-audience-dot]");
  var status = document.getElementById("tf-view-status");
  var items = Array.prototype.slice.call(document.querySelectorAll("[data-view-option]"));
  var wrapper = document.querySelector(".tf-audience");
  if (!toggle || !menu || !label || !dot || !wrapper) return;

  var dotClasses = {
    marketing: "tf-dot tf-dot-marketing",
    you: "tf-dot tf-dot-you",
    tech: "tf-dot tf-dot-tech",
    else: "tf-dot tf-dot-else"
  };
  var labels = {
    marketing: "For Marketing Teams",
    you: "For You",
    tech: "For Tech",
    else: "Something Else"
  };

  function close() {
    wrapper.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    menu.hidden = true;
  }
  function open() {
    wrapper.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
    menu.hidden = false;
  }
  function isOpen() { return !menu.hidden; }

  function applyView(view, persist) {
    if (!labels[view]) view = "marketing";
    label.textContent = labels[view];
    dot.className = dotClasses[view];
    items.forEach(function (item) {
      var selected = item.getAttribute("data-view-option") === view;
      item.classList.toggle("is-selected", selected);
      item.setAttribute("aria-checked", selected ? "true" : "false");
    });
    // "For You" is the default captured view. Other views deliberately stay
    // on that default until their specific layouts are supplied.
    var state = "default";
    root.setAttribute("data-view", state);
    root.setAttribute("data-view-label", labels[view]);
    if (status) {
      status.textContent = view === "you"
        ? "For You is showing the default LulaZel Hub view."
        : labels[view] + " is selected. Its custom view direction is pending; the default LulaZel Hub view remains visible.";
    }
    document.dispatchEvent(new CustomEvent("lulazel:viewchange", {
      detail: { view: view, label: labels[view], state: state }
    }));
    if (persist !== false) {
      try { sessionStorage.setItem("lulazel-view", view); } catch (e) {}
    }
  }

  toggle.addEventListener("click", function (e) {
    e.stopPropagation();
    isOpen() ? close() : open();
  });
  items.forEach(function (item, index) {
    item.addEventListener("click", function () {
      applyView(item.getAttribute("data-view-option"));
      close();
      toggle.focus();
    });
    item.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        var next = (index + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
        items[next].focus();
      } else if (e.key === "Escape") {
        close(); toggle.focus();
      }
    });
  });
  toggle.addEventListener("keydown", function (e) {
    if ((e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") && !isOpen()) {
      e.preventDefault(); open(); items[0].focus();
    } else if (e.key === "Escape" && isOpen()) { close(); }
  });
  document.addEventListener("click", function (e) {
    if (isOpen() && !wrapper.contains(e.target)) close();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && isOpen()) close();
  });

  var saved = null;
  try { saved = sessionStorage.getItem("lulazel-view"); } catch (e) {}
  applyView(saved || "you", false);
})();
