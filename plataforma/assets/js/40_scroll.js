/* Animaciones de desplazamiento (GSAP + ScrollTrigger) y navegación.
   - Sin secuestro del scroll: el desplazamiento es nativo; GSAP solo anima al entrar.
   - Animaciones activas por defecto; con ?movimiento=0 todo queda visible y sin animación.
   - Si GSAP no carga (sin red), la página funciona igual: nada queda oculto. */
(function (H) {
  "use strict";

  function navegar(id) {
    var destino = document.getElementById(id);
    if (!destino) return;
    destino.scrollIntoView({ behavior: H.reducido ? "auto" : "smooth", block: "start" });
    history.replaceState(null, "", "#" + id);
  }

  function iniciarNavegacion() {
    var nav = document.getElementById("nav");
    var menu = document.getElementById("nav-menu");
    document.addEventListener("click", function (e) {
      var a = e.target.closest("a[href^='#']");
      if (!a) return;
      var id = a.getAttribute("href").slice(1);
      if (!id || !document.getElementById(id)) return;
      e.preventDefault();
      navegar(id);
      nav.classList.remove("abierta");
      if (menu) menu.setAttribute("aria-expanded", "false");
    });
    if (menu) menu.addEventListener("click", function () {
      var abierta = nav.classList.toggle("abierta");
      menu.setAttribute("aria-expanded", abierta);
    });

    // Presentación en vivo: teclas 1–6 saltan a una sección; → a la siguiente y ← a la anterior.
    // ↑ ↓ conservan el desplazamiento normal del navegador.
    var orden = ["inicio", "datos", "modelo", "operativa", "resultados", "cierre"];
    // Sección actual = la última cuyo inicio ya pasó por debajo de la barra de navegación
    function seccionActual() {
      var actual = 0;
      orden.forEach(function (id, i) {
        var el = document.getElementById(id);
        if (el && el.getBoundingClientRect().top <= 120) actual = i;
      });
      return actual;
    }
    document.addEventListener("keydown", function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      var t = e.target;
      // Los controles que ya usan teclas (deslizador del gemelo, selectores de opciones, campos) conservan su comportamiento
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) return;
      var n = parseInt(e.key, 10);
      if (n >= 1 && n <= orden.length) { irA(n - 1); return; }
      var paso = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (!paso) return;
      e.preventDefault();   // en lugar de desplazar unos píxeles, salta de sección
      // Si el desplazamiento anterior aún no termina, se avanza desde su destino (pulsaciones seguidas)
      var base = performance.now() - ultimo.t < 1200 ? ultimo.i : seccionActual();
      irA(Math.max(0, Math.min(orden.length - 1, base + paso)));
    });
    var ultimo = { i: -1, t: 0 };
    function irA(i) { ultimo = { i: i, t: performance.now() }; navegar(orden[i]); }

    // Sección activa, fondo de la barra y progreso (sin GSAP: IntersectionObserver + scroll)
    var enlaces = document.querySelectorAll(".nav-enlaces a[data-ir]");
    var subenlaces = document.querySelectorAll(".subnav a[data-sub]");
    var progreso = document.getElementById("progreso");
    function marcar(lista, atributo, id) {
      Array.prototype.forEach.call(lista, function (a) {
        var activo = a.getAttribute(atributo) === id;
        a.classList.toggle("activo", activo);
        if (activo) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
      });
    }
    var obs = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (!e.isIntersecting) return;
        var id = e.target.getAttribute("data-seccion");
        if (id) marcar(enlaces, "data-ir", id);
        else marcar(subenlaces, "data-sub", e.target.id);
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    document.querySelectorAll("[data-seccion], .bloque").forEach(function (s) { obs.observe(s); });

    var pendiente = false;
    function alDesplazar() {
      if (pendiente) return;
      pendiente = true;
      requestAnimationFrame(function () {
        pendiente = false;
        var max = document.documentElement.scrollHeight - window.innerHeight;
        progreso.style.transform = "scaleX(" + (max > 0 ? window.scrollY / max : 0) + ")";
        nav.classList.toggle("con-fondo", window.scrollY > 40);
      });
    }
    window.addEventListener("scroll", alDesplazar, { passive: true });
    alDesplazar();

    if (location.hash && document.getElementById(location.hash.slice(1))) {
      setTimeout(function () { navegar(location.hash.slice(1)); }, 300);
    }
  }

  /* Contador numérico de los KPI (data-contar = valor final) */
  function contar(el) {
    var final = parseFloat(el.getAttribute("data-contar"));
    var dec = parseInt(el.getAttribute("data-decimales") || "0", 10);
    if (H.reducido || !window.gsap) { el.textContent = H.fmt(final, dec); return; }
    var obj = { v: 0 };
    gsap.to(obj, { v: final, duration: 1.6, ease: "expo.out", onUpdate: function () { el.textContent = H.fmt(obj.v, dec); } });
    gsap.fromTo(el.parentElement, { filter: "blur(8px)", opacity: 0.35, y: 10 },
      { filter: "blur(0px)", opacity: 1, y: 0, duration: 1.1, ease: "power3.out", clearProps: "filter" });
  }

  /* Ejecuta fn una vez cuando el elemento entra. La animación se crea en ese momento:
     un gsap.from con scrollTrigger "once" puede quedar detenido al eliminarse el disparador. */
  function alEntrar(el, inicio, fn) {
    if (!el) return;
    var hecho = false;
    var ejecutar = function () { if (!hecho) { hecho = true; fn(); } };
    ScrollTrigger.create({ trigger: el, start: inicio, onEnter: ejecutar, onEnterBack: ejecutar,
      onRefresh: function (self) { if (self.progress > 0) ejecutar(); } });
  }

  function iniciarAnimaciones() {
    var kpis = document.querySelectorAll("[data-contar]");
    if (!window.gsap || !window.ScrollTrigger || H.reducido) {
      // Sin animación: los KPI ya traen su valor final desde el servidor
      if (H.terminarIntro) H.terminarIntro();
      return;
    }
    var hayGsapSplit = !!window.SplitText;
    gsap.registerPlugin(ScrollTrigger);
    if (hayGsapSplit) gsap.registerPlugin(SplitText);
    // Sin "lag smoothing": en un equipo lento las animaciones terminan a tiempo en vez de quedarse a medias
    gsap.ticker.lagSmoothing(0);
    document.documentElement.classList.add("js-anim");

    // Entrada del inicio: letra por letra (SplitText), cuando se retira la pantalla de carga
    var letras = null;
    if (hayGsapSplit) {
      letras = [];
      // La línea con degradado (.acento) no se parte: background-clip:text no sobrevive al split
      document.querySelectorAll(".hero-titulo .linea > span:not(.acento)").forEach(function (el) {
        letras = letras.concat(new SplitText(el, { type: "chars", charsClass: "letra" }).chars);
      });
      letras = letras.concat(Array.prototype.slice.call(document.querySelectorAll(".hero-titulo .acento")));
    }
    // Primero la cámara se acerca al edificio (~6 s); el texto entra hacia el final del recorrido.
    // Scroll, clic o tecla durante la intro la adelantan: nunca se bloquea la lectura.
    // La animación de entrada se crea en el momento de mostrar el texto (estados inicial y final
    // explícitos): un "from" creado al inicio, con el texto oculto por la intro, puede quedar varado.
    var titular = (letras && letras.length) ? letras : document.querySelectorAll(".hero-titulo .linea > span");
    var acompanan = ".aviso-escena, .hero-indicador, .nav";
    var INTRO_MS = 4300;
    var textoMostrado = false;
    var mostrarTexto = function () {
      if (textoMostrado) return;
      textoMostrado = true;
      ["wheel", "keydown", "pointerdown", "touchstart"].forEach(function (ev) { window.removeEventListener(ev, mostrarTexto); });
      gsap.set(titular, { yPercent: 115, rotate: 6, opacity: 0 });
      gsap.set(".hero-entrada", { y: 26, opacity: 0 });
      gsap.set(acompanan, { opacity: 0 });
      if (H.terminarIntro) H.terminarIntro();
      gsap.timeline()
        .to(titular, { yPercent: 0, rotate: 0, opacity: 1, duration: 1.1, ease: "expo.out", stagger: 0.022 }, 0)
        .to(".hero-entrada", { y: 0, opacity: 1, duration: 1.1, ease: "power3.out", stagger: 0.08 }, 0.45)
        .to(acompanan, { opacity: 1, duration: 1 }, 0.9);
      // Respaldo: si el navegador frena los cuadros (pestaña en segundo plano), el texto queda en su estado final
      setTimeout(function () {
        gsap.set(titular, { yPercent: 0, rotate: 0, opacity: 1 });
        gsap.set(".hero-entrada", { y: 0, opacity: 1 });
        gsap.set(acompanan, { opacity: 1 });
      }, 3200);
    };
    var arrancar = function () {
      setTimeout(mostrarTexto, INTRO_MS);
      ["wheel", "keydown", "pointerdown", "touchstart"].forEach(function (ev) { window.addEventListener(ev, mostrarTexto, { passive: true }); });
    };
    if (document.documentElement.classList.contains("cargado")) arrancar();
    else document.addEventListener("hun:cargado", arrancar, { once: true });

    // Titulares de sección: líneas que suben desde una máscara
    if (hayGsapSplit) {
      document.querySelectorAll(".titulo-seccion").forEach(function (t) {
        t.classList.remove("revelar");
        var partes = new SplitText(t, { type: "lines", linesClass: "linea-split", mask: "lines" });
        gsap.set(partes.lines, { yPercent: 105 });
        alEntrar(t, "top 86%", function () {
          gsap.to(partes.lines, { yPercent: 0, duration: 0.9, ease: "expo.out", stagger: 0.08 });
        });
      });
    }

    // Manifiesto: cada palabra se ilumina al ritmo del scroll (scrub, sin fijar la página)
    var palabras = document.querySelectorAll(".manifiesto .palabra");
    if (palabras.length) {
      gsap.to(palabras, {
        color: "rgba(244,247,252,1)", stagger: 0.12, ease: "none",
        scrollTrigger: { trigger: ".manifiesto", start: "top 78%", end: "bottom 42%", scrub: 0.4 }
      });
    }

    // Números de capítulo: se desplazan más lento que el contenido (parallax)
    document.querySelectorAll(".numero-capitulo").forEach(function (n) {
      gsap.fromTo(n, { yPercent: 10, opacity: 0 }, {
        yPercent: -12, opacity: 1, ease: "none",
        scrollTrigger: { trigger: n.closest(".seccion"), start: "top bottom", end: "top -40%", scrub: 0.8 }
      });
    });

    // Pistas de los KPI: la barra "después" crece desde la de "antes"
    document.querySelectorAll("[data-pista]").forEach(function (b) {
      gsap.set(b, { scaleX: 0 });
      alEntrar(b, "top 90%", function () { gsap.to(b, { scaleX: 1, duration: 1.6, ease: "expo.out", delay: 0.25 }); });
    });

    // El texto del inicio se aleja con el scroll (parallax suave, scrub)
    gsap.fromTo(".hero-contenido", { yPercent: 0, opacity: 1 }, {
      yPercent: -12, opacity: 0.15, ease: "none",
      scrollTrigger: { trigger: "#inicio", start: "top top", end: "bottom top", scrub: 0.6 }
    });

    // Revelado progresivo por lotes
    ScrollTrigger.batch(".revelar", {
      start: "top 90%", once: true,
      onEnter: function (lote) { gsap.to(lote, { opacity: 1, y: 0, duration: 0.95, ease: "power3.out", stagger: 0.07, overwrite: true }); }
    });

    // KPI: contar al entrar
    Array.prototype.forEach.call(kpis, function (el) {
      el.textContent = H.fmt(0, parseInt(el.getAttribute("data-decimales") || "0", 10));
      ScrollTrigger.create({ trigger: el, start: "top 88%", once: true, onEnter: function () { contar(el); } });
    });

    // Etapas del pipeline: aparecen en cadena
    gsap.set(".etapa", { y: 20, opacity: 0 });
    alEntrar(document.querySelector(".pipeline"), "top 85%", function () {
      gsap.to(".etapa", { y: 0, opacity: 1, duration: 0.7, ease: "power3.out", stagger: 0.07 });
    });

    // Lema final palabra por palabra
    gsap.set(".lema span", { yPercent: 40, opacity: 0 });
    alEntrar(document.querySelector(".lema"), "top 85%", function () {
      gsap.to(".lema span", { yPercent: 0, opacity: 1, duration: 1.2, ease: "expo.out", stagger: 0.18 });
    });

    // Los gráficos de Plotly cambian la altura de la página al dibujarse: recalcular
    var refrescar = function () { ScrollTrigger.refresh(); };
    window.addEventListener("load", function () { setTimeout(refrescar, 400); });
    setTimeout(refrescar, 1500);
    setTimeout(refrescar, 4000);
    if ("ResizeObserver" in window) {
      var t = null;
      new ResizeObserver(function () { clearTimeout(t); t = setTimeout(refrescar, 250); }).observe(document.querySelector("main"));
    }
    // Red de seguridad sin GSAP: si el navegador frena requestAnimationFrame (pestaña en segundo
    // plano, ahorro de energía), GSAP no avanza. Todo lo que esté en pantalla y siga oculto
    // 1,2 s después se muestra directamente, y los KPI toman su valor final.
    var forzar = function (el) {
      if (parseFloat(getComputedStyle(el).opacity) < 0.5) { el.style.opacity = "1"; el.style.transform = "none"; }
      // Líneas de titulares y pistas de KPI que se quedaron a mitad de camino
      el.querySelectorAll(".linea-split, [data-pista], .etapa, .lema span").forEach(function (x) {
        if (getComputedStyle(x).transform !== "none") gsap.set(x, { clearProps: "transform,opacity" });
      });
      el.querySelectorAll("[data-contar]").forEach(function (k) {
        var dec = parseInt(k.getAttribute("data-decimales") || "0", 10), final = parseFloat(k.getAttribute("data-contar"));
        if (k.textContent === H.fmt(0, dec)) k.textContent = H.fmt(final, dec);
      });
    };
    var vigia = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (!e.isIntersecting) return;
        vigia.unobserve(e.target);
        setTimeout(function () { forzar(e.target); }, 2400);
      });
    });
    document.querySelectorAll(".revelar, .titulo-seccion").forEach(function (el) { vigia.observe(el); });
  }

  // El layout lo monta Dash: esperar al último bloque (cierre) antes de iniciar
  H.esperar("#cierre", function () {
    // setTimeout y no requestAnimationFrame: rAF no corre si la pestaña arranca en segundo plano
    setTimeout(function () {
      iniciarNavegacion();
      // SplitText mide las líneas: hay que esperar a las fuentes (máx. 2 s)
      var hecho = false;
      var animar = function () { if (!hecho) { hecho = true; iniciarAnimaciones(); } };
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(animar);
      setTimeout(animar, 2000);
    }, 0);
  });
})(window.HUN);
