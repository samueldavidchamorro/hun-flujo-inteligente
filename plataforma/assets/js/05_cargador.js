/* Pantalla de carga: avanza con hitos reales (fuentes, layout de Dash, primer cuadro 3D)
   y se retira sola. Nunca bloquea más de 4,5 s, aunque el 3D falle o no haya WebGL. */
(function (H) {
  "use strict";
  var hitos = { fuentes: false, layout: false, hero: false };
  var retirada = false;

  function pintar() {
    var hechos = Object.keys(hitos).filter(function (k) { return hitos[k]; }).length;
    var barra = document.getElementById("cargador-progreso");
    if (barra) barra.style.width = (20 + 80 * hechos / 3) + "%";
    if (hitos.hero && hitos.layout) retirar();
  }

  function retirar() {
    if (retirada) return;
    retirada = true;
    var el = document.getElementById("cargador");
    if (!el) return;
    setTimeout(function () {
      el.classList.add("fuera");
      document.documentElement.classList.add("cargado");
      document.dispatchEvent(new CustomEvent("hun:cargado"));
      setTimeout(function () { el.remove(); }, 1000);
    }, H.reducido ? 0 : 250);
  }

  /* Las escenas 3D avisan con HUN.listo("hero") al dibujar su primer cuadro */
  H.listo = function (nombre) { if (nombre in hitos) { hitos[nombre] = true; pintar(); } };

  /* Modo captura (?captura=<id>): para generar imágenes de documentación sin animaciones.
     Retira la pantalla de carga y deja visible solo el bloque pedido (y sus ancestros), arriba
     de la página: las capturas headless no se llevan bien con el scroll. */
  var captura = /[?&]captura=([^&#]*)/.exec(location.search);
  if (captura) {
    document.documentElement.classList.add("modo-captura");
    var id = decodeURIComponent(captura[1]);
    var aislar = function (el) {
      for (var n = el; n && n.parentElement && n !== document.body; n = n.parentElement) {
        Array.prototype.forEach.call(n.parentElement.children, function (h) {
          if (h !== n && h.id !== "nav" && !h.contains(document.getElementById("nav"))) h.style.display = "none";
        });
      }
      el.style.marginTop = "84px";
    };
    H.esperar("#cierre", function () {
      retirar();
      var el = id && document.getElementById(id);
      // Un gráfico se muestra con su panel (pregunta + lectura) y, si va en rejilla, con sus vecinos
      if (el && el.id === "gemelo-lienzo") el = el.parentElement;   // lienzo + panel de controles
      if (el && el.classList.contains("dash-graph")) {
        el = el.closest(".rejilla-2, .rejilla-3, .rejilla-12-7") || el.closest(".panel") || el;
      }
      if (el) aislar(el);
    });
  }

  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { hitos.fuentes = true; pintar(); });
  else hitos.fuentes = true;
  H.esperar("#cierre", function () { hitos.layout = true; pintar(); });
  setTimeout(retirar, 4500);
  setTimeout(function () { if (H.terminarIntro) H.terminarIntro(); }, 12000);
})(window.HUN);
