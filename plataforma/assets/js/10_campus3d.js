/* Escena exterior del hospital (inicio y cierre).
   Es un edificio ILUSTRATIVO generado por código: el HUN no entregó planos.
   Se reutiliza en dos lienzos con dos recorridos de cámara distintos.

   Técnicas (ver referencias del proyecto): resplandor con UnrealBloomPass, cielo con
   degradado, suelo con reflejos, instancias para árboles / faroles / aletas, cámara con
   inercia y parallax del ratón. El lienzo del cierre se crea solo al acercarse. */
(function (H) {
  "use strict";
  if (!window.THREE) return;
  var C = H.COLOR;

  /* Textura de fachada: ventanas encendidas al azar (semilla fija) */
  function texturaVentanas(columnas, pisos, semilla, encendido) {
    var rnd = H.aleatorio(semilla);
    var cw = 12, ch = 16;
    var lienzo = document.createElement("canvas");
    lienzo.width = Math.max(16, columnas * cw);
    lienzo.height = Math.max(16, pisos * ch);
    var g = lienzo.getContext("2d");
    g.fillStyle = "#02050b";
    g.fillRect(0, 0, lienzo.width, lienzo.height);
    for (var p = 0; p < pisos; p++) {
      // Algunos pisos completos encendidos (guardias nocturnas), otros casi apagados
      var pisoActivo = rnd() < 0.35 ? 0.92 : encendido;
      for (var c = 0; c < columnas; c++) {
        if (rnd() < pisoActivo) {
          var tono = rnd();
          g.fillStyle = tono < 0.62 ? "rgba(150,205,255," + (0.55 + 0.45 * rnd()) + ")"
            : tono < 0.86 ? "rgba(49,214,232," + (0.55 + 0.4 * rnd()) + ")" : "rgba(255,236,205,0.9)";
        } else {
          g.fillStyle = "rgba(40,70,120," + (0.1 + 0.12 * rnd()) + ")";
        }
        g.fillRect(c * cw + 2, p * ch + 3, cw - 4, ch - 7);
      }
      g.fillStyle = "rgba(57,132,255,0.08)";
      g.fillRect(0, p * ch + ch - 2, lienzo.width, 1);
    }
    var t = new THREE.CanvasTexture(lienzo);
    t.encoding = THREE.sRGBEncoding;
    t.anisotropy = 4;
    return t;
  }

  function bloque(grupo, ancho, alto, fondo, x, y, z, semilla, encendido) {
    var pisos = Math.round(alto / 3.6);
    function fachada(cols, s) {
      return new THREE.MeshStandardMaterial({
        color: 0x0a1322, metalness: 0.5, roughness: 0.34,
        emissive: 0xffffff, emissiveMap: texturaVentanas(cols, pisos, s, encendido), emissiveIntensity: 1.0
      });
    }
    var techo = new THREE.MeshStandardMaterial({ color: 0x0f1a2c, metalness: 0.3, roughness: 0.7 });
    var lado = fachada(Math.round(fondo / 2.4), semilla + 7), frente = fachada(Math.round(ancho / 2.4), semilla);
    var geo = new THREE.BoxGeometry(ancho, alto, fondo);
    var malla = new THREE.Mesh(geo, [lado, lado, techo, techo, frente, frente]);
    malla.position.set(x, y + alto / 2, z);
    grupo.add(malla);
    var bordes = new THREE.LineSegments(new THREE.EdgesGeometry(geo),
      new THREE.LineBasicMaterial({ color: C.cian, transparent: true, opacity: 0.35 }));
    bordes.position.copy(malla.position);
    grupo.add(bordes);
    // Cornisa luminosa en la azotea (brilla con el bloom)
    var cornisa = new THREE.Mesh(new THREE.BoxGeometry(ancho + 0.4, 0.25, fondo + 0.4),
      new THREE.MeshBasicMaterial({ color: 0x9fe9ff, transparent: true, opacity: 0.55 }));
    cornisa.position.set(x, y + alto + 0.1, z);
    grupo.add(cornisa);
    return malla;
  }

  /* Aletas verticales de la fachada principal (una sola malla instanciada) */
  function aletas(grupo, x0, x1, y0, alto, z) {
    var n = Math.round((x1 - x0) / 2.4);
    var malla = new THREE.InstancedMesh(new THREE.BoxGeometry(0.22, alto, 0.9),
      new THREE.MeshStandardMaterial({ color: 0x1a2a46, metalness: 0.8, roughness: 0.3 }), n);
    var m = new THREE.Matrix4();
    for (var i = 0; i < n; i++) malla.setMatrixAt(i, m.makeTranslation(x0 + i * 2.4 + 1.2, y0 + alto / 2, z));
    grupo.add(malla);
  }

  function cielo(escena) {
    var mat = new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false,
      uniforms: { arriba: { value: new THREE.Color(0x03060d) }, horizonte: { value: new THREE.Color(0x10275a) } },
      vertexShader: "varying vec3 vP; void main(){ vP = (modelMatrix * vec4(position,1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",
      fragmentShader: "uniform vec3 arriba; uniform vec3 horizonte; varying vec3 vP; void main(){ float h = normalize(vP).y; float t = pow(clamp(1.0 - h, 0.0, 1.0), 4.0); gl_FragColor = vec4(mix(arriba, horizonte, t), 1.0); }"
    });
    escena.add(new THREE.Mesh(new THREE.SphereGeometry(600, 32, 16), mat));
  }

  /* Construye el campus y devuelve {grupo, actualizar(t)} */
  H.crearCampus = function (escena) {
    var grupo = new THREE.Group();
    escena.add(grupo);
    cielo(escena);

    // Suelo oscuro y metálico: refleja el resplandor de las fachadas
    var suelo = new THREE.Mesh(new THREE.CircleGeometry(300, 64),
      new THREE.MeshStandardMaterial({ color: 0x060b15, metalness: 0.75, roughness: 0.42 }));
    suelo.rotation.x = -Math.PI / 2;
    grupo.add(suelo);
    var rejilla = new THREE.GridHelper(360, 72, 0x1b3a7a, 0x0e1c36);
    rejilla.material.transparent = true; rejilla.material.opacity = 0.3;
    rejilla.position.y = 0.02;
    grupo.add(rejilla);

    // Volúmenes
    bloque(grupo, 84, 11, 46, 0, 0, 0, 11, 0.5);             // podio
    var torre = bloque(grupo, 36, 48, 22, 4, 11, -4, 23, 0.58);
    bloque(grupo, 26, 26, 22, -40, 0, -6, 37, 0.48);
    bloque(grupo, 24, 34, 20, 42, 0, -8, 51, 0.55);
    bloque(grupo, 20, 16, 16, -22, 11, 8, 67, 0.42);
    aletas(grupo, torre.position.x - 18, torre.position.x + 18, 11, 48, 7.5);

    // Puente peatonal acristalado entre la torre y el ala este
    var puente = new THREE.Mesh(new THREE.BoxGeometry(12, 3.2, 5),
      new THREE.MeshStandardMaterial({ color: 0x1b3f7a, metalness: 0.4, roughness: 0.15, transparent: true, opacity: 0.55,
        emissive: C.cian, emissiveIntensity: 0.18 }));
    puente.position.set(27, 27, -6);
    grupo.add(puente);

    // Equipos en las azoteas
    var matEquipo = new THREE.MeshStandardMaterial({ color: 0x1a2740, metalness: 0.6, roughness: 0.5 });
    [[-6, -10], [10, -10], [16, 0], [-10, 2]].forEach(function (p) {
      var e = new THREE.Mesh(new THREE.BoxGeometry(5, 2.2, 4), matEquipo);
      e.position.set(torre.position.x + p[0], 60.2, p[1]);
      grupo.add(e);
    });

    // Marquesina de urgencias con franja de luz
    var marquesina = new THREE.Mesh(new THREE.BoxGeometry(30, 0.8, 9),
      new THREE.MeshStandardMaterial({ color: 0x111c2d, metalness: 0.6, roughness: 0.3 }));
    marquesina.position.set(18, 8, 27);
    grupo.add(marquesina);
    var franja = new THREE.Mesh(new THREE.BoxGeometry(30, 0.18, 0.3), new THREE.MeshBasicMaterial({ color: C.cian }));
    franja.position.set(18, 7.55, 31.4);
    grupo.add(franja);
    var rotulo = new THREE.Mesh(new THREE.BoxGeometry(12, 1.4, 0.2), new THREE.MeshBasicMaterial({ color: 0xff4d5e }));
    rotulo.position.set(18, 9.4, 31.3);
    grupo.add(rotulo);

    // Ambulancia en la bahía, con luces intermitentes
    var ambulancia = new THREE.Group();
    var cuerpo = new THREE.Mesh(new THREE.BoxGeometry(3.2, 2.6, 6.4), new THREE.MeshStandardMaterial({ color: 0xe9eef6, roughness: 0.4 }));
    cuerpo.position.y = 1.6; ambulancia.add(cuerpo);
    var raya = new THREE.Mesh(new THREE.BoxGeometry(3.25, 0.4, 6.45), new THREE.MeshBasicMaterial({ color: 0xff4d5e }));
    raya.position.y = 1.4; ambulancia.add(raya);
    var luzA = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.3, 0.5), new THREE.MeshBasicMaterial({ color: 0xff4d5e }));
    var luzB = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.3, 0.5), new THREE.MeshBasicMaterial({ color: 0x4d8dff }));
    luzA.position.set(-0.7, 3.05, 2.4); luzB.position.set(0.7, 3.05, 2.4);
    ambulancia.add(luzA); ambulancia.add(luzB);
    ambulancia.position.set(24, 0, 36);
    ambulancia.rotation.y = 0.2;
    grupo.add(ambulancia);
    var destello = new THREE.PointLight(0xff4d5e, 0, 26, 2);
    destello.position.set(24, 4, 38);
    grupo.add(destello);

    // Cruz en la fachada de la torre
    var cruzMat = new THREE.MeshBasicMaterial({ color: 0xff4d5e });
    [new THREE.BoxGeometry(5.4, 1.6, 0.3), new THREE.BoxGeometry(1.6, 5.4, 0.3)].forEach(function (g) {
      var m = new THREE.Mesh(g, cruzMat); m.position.set(torre.position.x + 12, 54, 8.2); grupo.add(m);
    });
    var luzCruz = new THREE.PointLight(0xff4d5e, 1.6, 44, 2);
    luzCruz.position.set(torre.position.x + 12, 54, 11);
    grupo.add(luzCruz);

    // Helipuerto
    var heli = new THREE.Mesh(new THREE.RingGeometry(5.2, 6, 48),
      new THREE.MeshBasicMaterial({ color: C.cian, transparent: true, opacity: 0.75, side: THREE.DoubleSide }));
    heli.rotation.x = -Math.PI / 2;
    heli.position.set(torre.position.x, 59.1, -4);
    grupo.add(heli);

    // Plano de "escaneo" del gemelo digital que recorre la torre
    var escaneo = new THREE.Mesh(new THREE.PlaneGeometry(44, 30),
      new THREE.MeshBasicMaterial({ color: C.cian, transparent: true, opacity: 0.07, side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending, depthWrite: false }));
    escaneo.rotation.x = -Math.PI / 2;
    escaneo.position.set(torre.position.x, 12, -4);
    grupo.add(escaneo);

    // Árboles y faroles de la plaza (instancias)
    var rnd = H.aleatorio(9);
    var nArb = 34;
    var copas = new THREE.InstancedMesh(new THREE.ConeGeometry(1.6, 5, 7),
      new THREE.MeshStandardMaterial({ color: 0x0f2a33, roughness: 0.9 }), nArb);
    var troncos = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.18, 0.22, 1.6, 6),
      new THREE.MeshStandardMaterial({ color: 0x1a2232 }), nArb);
    var m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3();
    for (var a = 0; a < nArb; a++) {
      var ax = -80 + a * 5 + (rnd() - 0.5) * 2, az = a % 2 ? 44 : 30 + rnd() * 2;
      if (ax > 2 && ax < 34 && az < 40) az = 46;              // no tapar la bahía de urgencias
      var esc = 0.75 + rnd() * 0.6;
      copas.setMatrixAt(a, m4.compose(p.set(ax, 1.6 + 2.5 * esc, az), q, s.set(esc, esc, esc)));
      troncos.setMatrixAt(a, m4.compose(p.set(ax, 0.8, az), q, s.set(1, 1, 1)));
    }
    grupo.add(copas); grupo.add(troncos);
    var nFar = 12;
    var postes = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.1, 0.12, 5, 6),
      new THREE.MeshStandardMaterial({ color: 0x2a3a58, metalness: 0.7 }), nFar);
    var bombillas = new THREE.InstancedMesh(new THREE.SphereGeometry(0.35, 10, 8),
      new THREE.MeshBasicMaterial({ color: 0xbfe6ff }), nFar);
    for (var f = 0; f < nFar; f++) {
      var fx = -60 + f * 11, fz = 38;
      postes.setMatrixAt(f, m4.makeTranslation(fx, 2.5, fz));
      bombillas.setMatrixAt(f, m4.makeTranslation(fx, 5.1, fz));
    }
    grupo.add(postes); grupo.add(bombillas);

    // Vía de acceso con luces que circulan (llegadas)
    var curva = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-150, 0.2, 64), new THREE.Vector3(-40, 0.2, 54), new THREE.Vector3(18, 0.2, 42),
      new THREE.Vector3(70, 0.2, 50), new THREE.Vector3(160, 0.2, 76)
    ]);
    grupo.add(new THREE.Mesh(new THREE.TubeGeometry(curva, 100, 0.14, 6, false), new THREE.MeshBasicMaterial({ color: 0x1b3a7a })));
    var nLuces = 16;
    var luces = new THREE.InstancedMesh(new THREE.SphereGeometry(0.55, 10, 8), new THREE.MeshBasicMaterial({ color: 0xffffff }), nLuces);
    var colorLuz = new THREE.Color();
    for (var i = 0; i < nLuces; i++) luces.setColorAt(i, colorLuz.set(i % 3 === 0 ? 0xff4d5e : 0xbfe6ff));
    grupo.add(luces);

    // Partículas ambientales
    var n = 800, pos = new Float32Array(n * 3);
    for (var k = 0; k < n; k++) {
      pos[k * 3] = (rnd() - 0.5) * 340; pos[k * 3 + 1] = rnd() * 120; pos[k * 3 + 2] = (rnd() - 0.5) * 340;
    }
    var gp = new THREE.BufferGeometry();
    gp.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    var particulas = new THREE.Points(gp, new THREE.PointsMaterial({
      color: 0x7fb4ff, size: 0.5, transparent: true, opacity: 0.5, depthWrite: false, blending: THREE.AdditiveBlending
    }));
    grupo.add(particulas);

    var mL = new THREE.Matrix4();
    return {
      grupo: grupo,
      actualizar: function (t) {
        escaneo.position.y = 11 + ((t * 6) % 50);
        escaneo.material.opacity = 0.05 + 0.04 * Math.sin(t * 2);
        for (var j = 0; j < nLuces; j++) {
          var u = ((t * 0.03) + j / nLuces) % 1;
          mL.makeTranslation(0, 0, 0).setPosition(curva.getPointAt(u));
          mL.elements[13] += 0.45;
          luces.setMatrixAt(j, mL);
        }
        luces.instanceMatrix.needsUpdate = true;
        var parpadeo = Math.sin(t * 9) > 0;
        luzA.visible = parpadeo; luzB.visible = !parpadeo;
        destello.intensity = parpadeo ? 1.6 : 0.4;
        particulas.rotation.y = t * 0.006;
        heli.material.opacity = 0.55 + 0.25 * Math.sin(t * 1.6);
      }
    };
  };

  /* Resplandor: compositor con UnrealBloomPass a resolución reducida (si los scripts cargaron) */
  H.crearBloom = function (renderer, escena, camara, opciones) {
    if (!THREE.EffectComposer || !THREE.UnrealBloomPass || !THREE.RenderPass) return null;
    var comp = new THREE.EffectComposer(renderer);
    comp.addPass(new THREE.RenderPass(escena, camara));
    var bloom = new THREE.UnrealBloomPass(new THREE.Vector2(256, 256), opciones.fuerza, opciones.radio, opciones.umbral);
    comp.addPass(bloom);
    return {
      render: function () { comp.render(); },
      ajustar: function (w, h) {
        comp.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.25));
        comp.setSize(w, h);
        bloom.resolution.set(w / 2, h / 2);
      }
    };
  };

  /* Escena exterior: modo "hero" (la cámara se acerca) o "cierre" (vista panorámica) */
  H.EscenaExterior = function (contenedor, modo) {
    if (!H.webgl()) { contenedor.classList.add("sin-webgl"); if (H.listo) H.listo(modo); return; }
    var renderer = H.crearRenderer(contenedor, { maxRatio: 1.5, exposicion: 1.1 });
    renderer.setClearColor(C.fondo, 1);
    var escena = new THREE.Scene();
    escena.fog = new THREE.FogExp2(0x060b16, 0.0046);
    var camara = new THREE.PerspectiveCamera(36, 1, 0.5, 1400);

    escena.add(new THREE.HemisphereLight(0x6fa8ff, 0x05070d, 0.5));
    var sol = new THREE.DirectionalLight(0xbcd6ff, 0.6);
    sol.position.set(80, 120, 60);
    escena.add(sol);
    var relleno = new THREE.PointLight(C.azul, 0.7, 180, 2);
    relleno.position.set(-30, 20, 60);
    escena.add(relleno);

    var campus = H.crearCampus(escena);
    var movil = window.innerWidth < 760;
    var bloom = H.crearBloom(renderer, escena, camara, { fuerza: movil ? 0.6 : 0.85, radio: 0.55, umbral: 0.5 });
    var mira = new THREE.Vector3(0, 18, 0);
    var raton = { x: 0, y: 0, sx: 0, sy: 0 };
    var inicio = performance.now();
    var visible = true, primerCuadro = true;

    function ajustar() {
      var w = contenedor.clientWidth || 1, h = contenedor.clientHeight || 1;
      renderer.setSize(w, h, false);
      if (bloom) bloom.ajustar(w, h);
      camara.aspect = w / h;
      camara.fov = w < 700 ? 50 : 36;
      camara.updateProjectionMatrix();
    }
    if ("ResizeObserver" in window) new ResizeObserver(ajustar).observe(contenedor); else window.addEventListener("resize", ajustar);
    ajustar();

    window.addEventListener("pointermove", function (e) {
      raton.x = (e.clientX / window.innerWidth - 0.5) * 2;
      raton.y = (e.clientY / window.innerHeight - 0.5) * 2;
    }, { passive: true });

    function progresoScroll() {
      var r = contenedor.getBoundingClientRect(), vh = window.innerHeight;
      if (modo === "hero") return H.limitar(-r.top / Math.max(r.height, 1), 0, 1);
      return H.limitar((vh - r.top) / (vh + r.height), 0, 1);
    }

    function posicionCamara(t, p) {
      if (modo === "hero") {
        var intro = H.reducido ? 1 : H.suavizar(H.limitar(t / 6, 0, 1));
        var deriva = H.reducido ? 0 : Math.sin(t * 0.08) * 6;
        var x = 90 - 50 * intro - 30 * p + deriva, y = 60 - 22 * intro - 8 * p, z = 270 - 112 * intro - 40 * p;
        // En pantallas anchas el edificio queda a la derecha y el titular a la izquierda
        var desvio = contenedor.clientWidth > 900 ? -34 : 0;
        mira.set(desvio + 4 - 6 * p, 18 + 4 * intro - 6 * p, 0);
        return [x, y, z];
      }
      var ang = -0.9 + p * 1.7 + (H.reducido ? 0 : t * 0.015);
      var radio = 200 - 46 * p;
      mira.set(0, 18, 0);
      return [Math.sin(ang) * radio, 96 - 40 * p, Math.cos(ang) * radio];
    }

    function cuadro() {
      requestAnimationFrame(cuadro);
      if (!visible || document.hidden) return;
      var t = (performance.now() - inicio) / 1000;
      raton.sx += (raton.x - raton.sx) * 0.035;
      raton.sy += (raton.y - raton.sy) * 0.035;
      var pc = posicionCamara(t, progresoScroll());
      camara.position.set(pc[0] + raton.sx * 7, pc[1] - raton.sy * 3.5, pc[2]);
      camara.lookAt(mira);
      campus.actualizar(H.reducido ? 0 : t);
      if (bloom) bloom.render(); else renderer.render(escena, camara);
      if (primerCuadro) { primerCuadro = false; if (H.listo) H.listo(modo); }
    }
    H.alVer(contenedor, function (v) { visible = v; });
    // El recorrido de entrada empieza cuando se retira la pantalla de carga
    if (modo === "hero") document.addEventListener("hun:cargado", function () { inicio = performance.now(); });
    cuadro();
  };

  H.esperar("#escena-hero", function (el) { new H.EscenaExterior(el, "hero"); });
  // El cierre se crea solo cuando el usuario se acerca: no compite con la carga inicial
  H.esperar("#escena-cierre", function (el) {
    var creada = false;
    H.alVer(el, function (v) { if (v && !creada) { creada = true; new H.EscenaExterior(el, "cierre"); } }, "900px");
  });
})(window.HUN);
