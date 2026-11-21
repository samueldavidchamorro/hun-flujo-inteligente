/* Utilidades compartidas por las escenas y las animaciones.
   Dash monta el layout después de cargar los scripts: por eso todo arranca con
   HUN.esperar(selector), que espera a que el elemento exista en el DOM. */
window.HUN = window.HUN || {};
(function (H) {
  "use strict";

  // ?movimiento=1 fuerza las animaciones aunque el sistema pida reducir movimiento (útil al presentar)
  // Las animaciones están activas por defecto (la plataforma se presenta en vivo), aunque el sistema
  // pida reducir movimiento. ?movimiento=0 en la URL las desactiva todas.
  H.reducido = /[?&](movimiento=0|captura=)/.test(location.search);
  if (!H.reducido) document.documentElement.classList.add("movimiento-forzado");
  // Intro: primero la animación 3D, después el texto. No aplica con reducir movimiento ni en modo captura.
  if (!H.reducido && !/[?&]captura=/.test(location.search)) document.documentElement.classList.add("intro-pendiente");
  H.terminarIntro = function () { document.documentElement.classList.remove("intro-pendiente"); };

  H.esperar = function (selector, alListo, limiteMs) {
    var el = document.querySelector(selector);
    if (el) { alListo(el); return; }
    var obs = new MutationObserver(function () {
      var e = document.querySelector(selector);
      if (e) { obs.disconnect(); clearTimeout(t); alListo(e); }
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
    var t = setTimeout(function () { obs.disconnect(); }, limiteMs || 30000);
  };

  H.webgl = function () {
    try {
      var c = document.createElement("canvas");
      return !!(window.WebGLRenderingContext && (c.getContext("webgl") || c.getContext("experimental-webgl")));
    } catch (e) { return false; }
  };

  /* Formato colombiano: coma decimal, punto de miles */
  H.fmt = function (n, dec) {
    dec = dec === undefined ? 1 : dec;
    var s = Number(n).toFixed(dec).split(".");
    s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return s.join(",");
  };

  /* Llama a cb(true/false) cuando el elemento entra o sale de pantalla */
  H.alVer = function (el, cb, margen) {
    if (!("IntersectionObserver" in window)) { cb(true); return; }
    new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) { cb(e.isIntersecting); });
    }, { rootMargin: margen || "120px" }).observe(el);
  };

  /* Generador pseudoaleatorio con semilla (mulberry32): mismas escenas en cada carga */
  H.aleatorio = function (semilla) {
    var a = semilla >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  H.limitar = function (v, a, b) { return Math.max(a, Math.min(b, v)); };
  H.suavizar = function (t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };

  H.COLOR = {
    fondo: 0x070b14, fondo2: 0x0d1422, tarjeta: 0x111c2d, azul: 0x3984ff, cian: 0x31d6e8,
    verde: 0x25d69a, naranja: 0xffaa45, rojo: 0xff5d70, gris: 0x6b7c93, texto: 0xf3f7fc
  };

  /* Renderer común: limita el pixel ratio para cuidar el rendimiento */
  H.crearRenderer = function (contenedor, opciones) {
    opciones = opciones || {};
    var r = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    r.setPixelRatio(Math.min(window.devicePixelRatio || 1, opciones.maxRatio || 1.75));
    r.setSize(contenedor.clientWidth || 1, contenedor.clientHeight || 1, false);
    r.outputEncoding = THREE.sRGBEncoding;
    r.toneMapping = THREE.ACESFilmicToneMapping;
    r.toneMappingExposure = opciones.exposicion || 1.05;
    r.setClearColor(0x000000, 0);
    if (opciones.sombras) { r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap; }
    contenedor.appendChild(r.domElement);
    r.domElement.addEventListener("webglcontextlost", function (e) {
      e.preventDefault();
      contenedor.classList.add("sin-webgl");
    });
    return r;
  };

  /* Libera geometrías, materiales y texturas de un objeto 3D */
  H.liberar = function (objeto) {
    objeto.traverse(function (o) {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        (Array.isArray(o.material) ? o.material : [o.material]).forEach(function (m) {
          ["map", "emissiveMap"].forEach(function (k) { if (m[k]) m[k].dispose(); });
          m.dispose();
        });
      }
    });
  };
})(window.HUN);
