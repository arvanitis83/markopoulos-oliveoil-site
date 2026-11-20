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
      ".call-band .wrap > *, .band-quote, .archive > figure, .offer-cards > li, .tips > div, .frame, .big-year";
    var els = [].slice.call(document.querySelectorAll(sel)).filter(function (el) {
      return !el.closest(".hero") && !el.closest(".hero-full") && !el.closest(".page-head") && !el.closest(".gallery");
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

  /* Gallery: slideshow with thumbnails, swipe, keyboard and full-screen view */
  var galleries = [].slice.call(document.querySelectorAll("[data-gallery]"));
  var lightbox = null, lbState = null;
  var openLightbox = function (g, k) {
    if (!lightbox) {
      lightbox = document.createElement("dialog");
      lightbox.className = "lightbox";
      lightbox.innerHTML =
        '<button class="g-btn lb-close" type="button">×</button>' +
        '<button class="g-btn lb-prev" type="button"></button>' +
        '<figure class="lb-figure"><img alt=""><figcaption><span class="g-count"></span><span class="g-cap"></span></figcaption></figure>' +
        '<button class="g-btn lb-next" type="button"></button>';
      var arrow = g.el.querySelector(".g-prev svg").outerHTML;
      lightbox.querySelector(".lb-prev").innerHTML = arrow;
      lightbox.querySelector(".lb-next").innerHTML = arrow;
      document.body.appendChild(lightbox);
      lightbox.querySelector(".lb-close").addEventListener("click", function () { lightbox.close(); });
      lightbox.querySelector(".lb-prev").addEventListener("click", function () { lbShow(lbState.i - 1); });
      lightbox.querySelector(".lb-next").addEventListener("click", function () { lbShow(lbState.i + 1); });
      lightbox.addEventListener("click", function (e) { if (e.target === lightbox) lightbox.close(); });
      lightbox.addEventListener("keydown", function (e) {
        if (e.key === "ArrowLeft") lbShow(lbState.i - 1);
        if (e.key === "ArrowRight") lbShow(lbState.i + 1);
      });
      lightbox.addEventListener("close", function () { if (lbState) { lbState.g.show(lbState.i); lbState.g.resume(); } });
      var sx = null;
      lightbox.addEventListener("touchstart", function (e) { sx = e.touches[0].clientX; }, { passive: true });
      lightbox.addEventListener("touchend", function (e) {
        if (sx === null) return;
        var dx = e.changedTouches[0].clientX - sx; sx = null;
        if (Math.abs(dx) > 40) lbShow(lbState.i + (dx < 0 ? 1 : -1));
      });
    }
    lightbox.querySelector(".lb-close").setAttribute("aria-label", g.el.dataset.lClose);
    lightbox.querySelector(".lb-prev").setAttribute("aria-label", g.el.dataset.lPrev);
    lightbox.querySelector(".lb-next").setAttribute("aria-label", g.el.dataset.lNext);
    lbState = { g: g, i: k };
    lbShow(k);
    g.hold();
    if (typeof lightbox.showModal === "function") lightbox.showModal();
    else window.open(g.slides[k].dataset.full, "_blank");
  };
  var lbShow = function (k) {
    var g = lbState.g, n = g.slides.length;
    lbState.i = (k + n) % n;
    var s = g.slides[lbState.i], img = lightbox.querySelector("img");
    img.src = s.dataset.full;
    img.alt = s.querySelector(".g-img").alt;
    lightbox.querySelector(".lb-figure .g-count").textContent = s.querySelector(".g-count").textContent;
    lightbox.querySelector(".lb-figure .g-cap").textContent = s.querySelector(".g-cap").textContent;
    var fig = lightbox.querySelector(".lb-figure");
    fig.style.animation = "none"; void fig.offsetWidth; fig.style.animation = "";
  };

  galleries.forEach(function (el) {
    var slides = [].slice.call(el.querySelectorAll(".g-slide"));
    var thumbs = [].slice.call(el.querySelectorAll(".g-thumb"));
    var bar = el.querySelector(".g-progress span");
    var playBtn = el.querySelector(".g-play");
    var stage = el.querySelector(".g-stage");
    var n = slides.length, i = 0, timer = null, DUR = 5500;
    var paused = calm, inView = false, hovering = false, held = false;
    var g = { el: el, slides: slides };

    var restart = function () {
      clearTimeout(timer);
      if (bar) { bar.style.transition = "none"; bar.style.width = "0"; }
      if (paused || !inView || hovering || held) return;
      window.requestAnimationFrame(function () {
        if (bar) { void bar.offsetWidth; bar.style.transition = "width " + DUR + "ms linear"; bar.style.width = "100%"; }
      });
      timer = setTimeout(function () { show(i + 1); }, DUR);
    };
    var show = function (k) {
      i = (k + n) % n;
      slides.forEach(function (s, j) { s.classList.toggle("is-active", j === i); });
      thumbs.forEach(function (t, j) {
        t.classList.toggle("is-active", j === i);
        if (j === i) t.setAttribute("aria-current", "true"); else t.removeAttribute("aria-current");
      });
      [slides[(i + 1) % n], slides[(i - 1 + n) % n]].forEach(function (s) {
        s.querySelectorAll("img[loading]").forEach(function (im) { im.loading = "eager"; });
      });
      restart();
    };
    g.show = show;
    g.hold = function () { held = true; restart(); };
    g.resume = function () { held = false; restart(); };

    el.querySelector(".g-prev").addEventListener("click", function () { show(i - 1); });
    el.querySelector(".g-next").addEventListener("click", function () { show(i + 1); });
    thumbs.forEach(function (t) { t.addEventListener("click", function () { show(+t.dataset.go); }); });
    var setPlayLabel = function () {
      playBtn.classList.toggle("is-paused", paused);
      playBtn.setAttribute("aria-label", paused ? el.dataset.lPlay : el.dataset.lPause);
    };
    if (playBtn) {
      setPlayLabel();
      playBtn.addEventListener("click", function () { paused = !paused; setPlayLabel(); restart(); });
    }
    el.querySelector(".g-zoom").addEventListener("click", function () { openLightbox(g, i); });
    slides.forEach(function (s, j) {
      s.querySelector(".g-img").addEventListener("click", function () { openLightbox(g, j); });
    });
    stage.addEventListener("mouseenter", function () { hovering = true; restart(); });
    stage.addEventListener("mouseleave", function () { hovering = false; restart(); });
    el.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { show(i - 1); e.preventDefault(); }
      if (e.key === "ArrowRight") { show(i + 1); e.preventDefault(); }
    });
    var sx = null;
    stage.addEventListener("touchstart", function (e) { sx = e.touches[0].clientX; }, { passive: true });
    stage.addEventListener("touchend", function (e) {
      if (sx === null) return;
      var dx = e.changedTouches[0].clientX - sx; sx = null;
      if (Math.abs(dx) > 40) show(i + (dx < 0 ? 1 : -1));
    });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        inView = entries[0].isIntersecting; restart();
      }, { threshold: 0.4 }).observe(stage);
    } else { inView = true; }
    show(0);
  });

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
        location.hostname === "127.0.0.1" || /\.github\.io$/.test(location.hostname) || window.self !== window.top;
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
