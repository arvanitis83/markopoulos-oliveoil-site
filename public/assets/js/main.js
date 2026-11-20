/* Markopoulos Olive Mill: small enhancements. The site works without this file. */
(function () {
  "use strict";
  var lang = document.documentElement.lang === "en" ? "en" : "el";

  /* Mobile menu */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    var label = toggle.querySelector(".nav-toggle-text");
    var setOpen = function (open) {
      nav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (label) label.textContent = open ? toggle.dataset.close : toggle.dataset.open;
    };
    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) { setOpen(false); toggle.focus(); }
    });
  }

  /* The oil line fills once when it scrolls into view */
  var line = document.querySelector(".line");
  var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (line && "IntersectionObserver" in window && !calm) {
    line.classList.add("will-flow");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { line.classList.add("is-flowing"); io.disconnect(); }
      });
    }, { threshold: 0.35 });
    io.observe(line);
  }

  var motion = !calm;
  if (motion) document.documentElement.classList.add("motion");

  /* Sections fade up as they scroll into view */
  if (motion && "IntersectionObserver" in window) {
    var sel = ".section-head, .offer > li, .cols-3 > div, .steps > li, .service-list > li, .faq details, " +
      ".print, .spec > li, .heritage > div:first-child, .prose, .contact-facts > section, .form, " +
      ".call-band .wrap > *, .band-quote, .archive > figure";
    var els = [].slice.call(document.querySelectorAll(sel)).filter(function (el) {
      return !el.closest(".hero") && !el.closest(".page-head");
    });
    var ro = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); ro.unobserve(en.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    els.forEach(function (el) {
      var sibs = [].filter.call(el.parentNode.children, function (c) { return els.indexOf(c) > -1; });
      el.style.setProperty("--i", Math.min(sibs.indexOf(el), 6));
      el.classList.add("will-reveal");
      ro.observe(el);
    });
  }

  /* Background photos drift slower than the page (parallax) */
  var bgs = [].slice.call(document.querySelectorAll(".bg"));
  if (motion && bgs.length) {
    var ticking = false;
    var update = function () {
      var vh = window.innerHeight;
      bgs.forEach(function (b) {
        var r = b.parentElement.getBoundingClientRect();
        if (r.bottom < -100 || r.top > vh + 100) return;
        var p = (r.top + r.height / 2 - vh / 2) / vh;
        b.style.setProperty("--py", (p * -70).toFixed(1) + "px");
      });
      ticking = false;
    };
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* Header gets a soft shadow once the page scrolls */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 8); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* Google map loads only after a click (no Google requests before that) */
  var mapBtn = document.querySelector("[data-map-src]");
  if (mapBtn) {
    mapBtn.addEventListener("click", function () {
      var box = mapBtn.closest(".map-box");
      var f = document.createElement("iframe");
      f.src = mapBtn.getAttribute("data-map-src");
      f.title = mapBtn.getAttribute("data-map-title") || "Map";
      f.loading = "lazy";
      f.referrerPolicy = "no-referrer-when-downgrade";
      box.innerHTML = "";
      box.appendChild(f);
      box.classList.add("is-loaded");
    });
  }

  /* Contact form */
  var form = document.querySelector("form.form");
  if (form) {
    var t = form.querySelector('input[name="t"]');
    if (t) t.value = Math.floor(Date.now() / 1000);
    var msg = form.querySelector(".form-msg");
    var text = {
      el: {
        missing: "Συμπληρώστε το όνομά σας, το μήνυμα και ένα τηλέφωνο ή email, και αποδεχτείτε την πολιτική απορρήτου.",
        email: "Το email δεν φαίνεται σωστό. Ελέγξτε το και ξαναστείλτε.",
        send: "Το μήνυμα δεν στάλθηκε λόγω τεχνικού προβλήματος. Καλέστε μας στο 22330 51298.",
        local: "Αυτή είναι προεπισκόπηση: η φόρμα στέλνει μηνύματα μόνο όταν η ιστοσελίδα είναι ανεβασμένη στον server."
      },
      en: {
        missing: "Please add your name, your message and a phone number or email, and accept the privacy policy.",
        email: "That email address doesn’t look right. Check it and send again.",
        send: "The message couldn’t be sent because of a technical problem. Please call +30 22330 51298.",
        local: "This is a preview: the form only sends messages once the site is on the web server."
      }
    }[lang];
    var show = function (code) {
      if (!msg) return;
      msg.textContent = text[code] || text.missing;
      msg.hidden = false;
    };
    var m = location.search.match(/[?&]error=(\w+)/);
    if (m) show(m[1]);
    form.addEventListener("submit", function (e) {
      var preview = location.protocol === "file:" || location.hostname === "localhost" ||
        location.hostname === "127.0.0.1" || window.self !== window.top;
      if (preview) {
        e.preventDefault(); show("local"); return;
      }
      var v = function (n) { var el = form.elements[n]; return el ? el.value.trim() : ""; };
      var consent = form.elements.consent && form.elements.consent.checked;
      if (!v("name") || !v("message") || (!v("email") && !v("phone")) || !consent) {
        e.preventDefault(); show("missing"); return;
      }
      if (v("email") && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v("email"))) {
        e.preventDefault(); show("email");
      }
    });
  }
})();
