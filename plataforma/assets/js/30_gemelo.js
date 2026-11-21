/* Gemelo digital del flujo hospitalario (sección 04).

   DATOS REALES (de /api/gemelo, ver plataforma/datos/gemelo.py):
     - ocupación media por día × hora de hospitalización y urgencias/observación
     - llegadas medias por día × hora de ambulatorio e ingreso a urgencias
     - probabilidades de transición entre servicios
     - tasas por 100 de los escenarios A (θ = 0,5) y B (θ* por servicio), prueba M7.2
   ILUSTRATIVO:
     - el plano, la posición de cada cama y las trayectorias de los pacientes
     - qué paciente concreto tiene estancia larga o alerta: se sortea con las tasas reales

   Una semana típica (168 h) se recorre a 2,5 s por hora con velocidad 1×. */
(function (H) {
  "use strict";
  if (!window.THREE) return;
  var C = H.COLOR;
  var SEG_POR_HORA = 2.5;
  var ESCALA_LLEGADAS = 1 / 20;      // 1 punto ≈ 20 visitas
  var CORREDOR_Z = 4;
  var MAX_AGENTES = 240;
  var DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

  /* ---------------------------- Plano ilustrativo ---------------------------- */
  var ZONAS = {
    ambulatorio: { nombre: "Ambulatorio", x: -24, z: 14, w: 24, d: 14, puerta: [-24, 7], color: 0x5b6f91 },
    urgencias_ingreso: { nombre: "Ingreso a urgencias", x: 22, z: 14.5, w: 22, d: 13, puerta: [22, 8], color: 0x9b8cff },
    urgencias_observacion: { nombre: "Urgencias · observación", x: 22, z: -9, w: 26, d: 20, puerta: [22, 1], color: C.cian },
    hospitalizacion: { nombre: "Hospitalización", x: -18, z: -12, w: 36, d: 20, puerta: [-18, -2], color: C.azul }
  };
  var ENTRADA = { x: 0, z: 31, puerta: [0, 24] };
  var ENTRADA_URG = { x: 36, z: 31 };
  var EGRESO = { x: -44, z: CORREDOR_Z, puerta: [-38, CORREDOR_Z] };

  function v3(x, z, y) { return new THREE.Vector3(x, y === undefined ? 0.55 : y, z); }

  /* Ruta ortogonal por el corredor central: punto → puerta → corredor → puerta → punto */
  function ruta(desde, puertaA, puertaB, hasta) {
    var pts = [v3(desde[0], desde[1])];
    if (puertaA) { pts.push(v3(puertaA[0], puertaA[1])); pts.push(v3(puertaA[0], CORREDOR_Z)); }
    if (puertaB) { pts.push(v3(puertaB[0], CORREDOR_Z)); pts.push(v3(puertaB[0], puertaB[1])); }
    pts.push(v3(hasta[0], hasta[1]));
    return pts.filter(function (p, i) { return i === 0 || p.distanceToSquared(pts[i - 1]) > 0.01; });
  }

  function Gemelo(contenedor, datos) {
    this.el = contenedor;
    this.datos = datos;
    this.escenario = "B";
    this.velocidad = 1;
    this.corriendo = false;
    this.horaSim = 0;
    this.rnd = H.aleatorio(2026);
    this.seleccion = null;
    this.acumulado = { ambulatorio: 0, urgencias_ingreso: 0 };
    this.enfriamiento = { hospitalizacion: 0, urgencias_observacion: 0 };
    this.webgl = H.webgl();
    this.construirControles();
    this.pintarIdentidad();
    this.pintarMetricas();
    if (!this.webgl) { contenedor.classList.add("sin-webgl", "listo"); return; }
    try {
      this.iniciar3D();
    } catch (e) {
      console.error("Gemelo 3D:", e);
      contenedor.classList.add("sin-webgl", "listo");
    }
  }

  /* ------------------------------ Escena 3D ------------------------------ */
  Gemelo.prototype.iniciar3D = function () {
    var self = this;
    this.renderer = H.crearRenderer(this.el, { sombras: true, exposicion: 0.95 });
    this.el.insertBefore(this.renderer.domElement, this.el.firstChild);
    this.escena = new THREE.Scene();
    this.escena.background = new THREE.Color(0x0a1220);
    this.renderer.setClearColor(0x0a1220, 1);
    this.escena.fog = new THREE.Fog(0x0a1220, 120, 230);
    this.camara = new THREE.PerspectiveCamera(40, 1, 0.5, 500);
    this.camara.position.set(0, 62, 76);

    this.controles = new THREE.OrbitControls(this.camara, this.renderer.domElement);
    this.controles.target.set(-3, 0, 3);
    this.controles.enableDamping = true;
    this.controles.dampingFactor = 0.08;
    this.controles.enableZoom = false;        // la rueda del ratón sigue desplazando la página
    this.controles.enablePan = false;
    this.controles.maxPolarAngle = 1.32;
    this.controles.minPolarAngle = 0.0;

    this.escena.add(new THREE.HemisphereLight(0x9cc3ff, 0x0a0f1c, 0.55));
    var sol = new THREE.DirectionalLight(0xdde9ff, 0.9);
    sol.position.set(-30, 70, 40);
    sol.castShadow = true;
    sol.shadow.mapSize.set(1024, 1024);
    var sc = sol.shadow.camera; sc.left = -60; sc.right = 60; sc.top = 50; sc.bottom = -50; sc.near = 10; sc.far = 180;
    sol.shadow.bias = -0.0008;
    this.escena.add(sol);
    var azul = new THREE.PointLight(C.azul, 0.9, 90, 2); azul.position.set(-18, 14, -12); this.escena.add(azul);
    var cian = new THREE.PointLight(C.cian, 0.8, 80, 2); cian.position.set(22, 14, -9); this.escena.add(cian);

    this.construirPlanta();
    this.construirCamas();
    this.construirAgentes();
    this.construirEtiquetas();

    this.reiniciar();

    this.raycaster = new THREE.Raycaster();
    var abajo = null;
    var dom = this.renderer.domElement;
    dom.addEventListener("pointerdown", function (e) { abajo = [e.clientX, e.clientY]; });
    var ultimoHover = 0;
    dom.addEventListener("pointermove", function (e) {
      var ahora = performance.now();
      if (ahora - ultimoHover < 60 || abajo) return;
      ultimoHover = ahora;
      self.sobrevolar(e);
    });
    dom.addEventListener("pointerleave", function () { self.anilloHover.visible = false; dom.style.cursor = ""; });
    dom.addEventListener("pointerup", function (e) {
      if (abajo && Math.abs(e.clientX - abajo[0]) + Math.abs(e.clientY - abajo[1]) < 6) self.elegir(e);
      abajo = null;
    });

    this.bloom = H.crearBloom ? H.crearBloom(this.renderer, this.escena, this.camara, { fuerza: 0.4, radio: 0.35, umbral: 0.9 }) : null;
    var ajustar = function () {
      var w = self.el.clientWidth || 1, h = self.el.clientHeight || 1;
      self.renderer.setSize(w, h, false);
      if (self.bloom) self.bloom.ajustar(w, h);
      self.camara.aspect = w / h;
      self.camara.fov = w < 640 ? 52 : 40;
      self.camara.updateProjectionMatrix();
    };
    if ("ResizeObserver" in window) new ResizeObserver(ajustar).observe(this.el); else window.addEventListener("resize", ajustar);
    ajustar();

    this.visible = false;
    H.alVer(this.el, function (v) {
      self.visible = v;
      if (v && !self.presentado) { self.presentado = true; self.presentar(); }
    });
    this.ultimo = performance.now();
    var cuadro = function (ahora) {
      requestAnimationFrame(cuadro);
      var dt = Math.min(0.25, (ahora - self.ultimo) / 1000);   // tolera equipos lentos sin congelar la semana
      self.ultimo = ahora;
      if (!self.visible || document.hidden) return;
      self.actualizar(dt);
      self.controles.update();
      if (self.bloom) self.bloom.render(); else self.renderer.render(self.escena, self.camara);
      self.moverEtiquetas();
    };
    requestAnimationFrame(cuadro);
    this.el.classList.add("listo");
  };

  Gemelo.prototype.construirPlanta = function () {
    var esc = this.escena;
    var losa = new THREE.Mesh(new THREE.BoxGeometry(92, 1, 66),
      new THREE.MeshStandardMaterial({ color: 0x0b1424, metalness: 0.15, roughness: 0.85 }));
    losa.position.set(-3, -0.5, 4);
    losa.receiveShadow = true;
    esc.add(losa);
    var rejilla = new THREE.GridHelper(92, 46, 0x16284a, 0x111f38);
    rejilla.position.set(-3, 0.01, 4);
    rejilla.material.transparent = true; rejilla.material.opacity = 0.5;
    esc.add(rejilla);

    // Corredores: franjas luminosas por donde circulan los pacientes
    var matCorredor = new THREE.MeshBasicMaterial({ color: 0x1a3566, transparent: true, opacity: 0.55 });
    var c1 = new THREE.Mesh(new THREE.PlaneGeometry(82, 4.6), matCorredor);
    c1.rotation.x = -Math.PI / 2; c1.position.set(-4, 0.03, CORREDOR_Z); esc.add(c1);
    var c2 = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 26), matCorredor);
    c2.rotation.x = -Math.PI / 2; c2.position.set(0, 0.03, 18); esc.add(c2);
    var matFlecha = new THREE.MeshBasicMaterial({ color: C.cian, transparent: true, opacity: 0.35 });
    this.flechas = [];
    for (var i = 0; i < 16; i++) {
      var f = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.18), matFlecha);
      f.rotation.x = -Math.PI / 2; f.position.set(-40 + i * 5, 0.05, CORREDOR_Z); esc.add(f); this.flechas.push(f);
    }

    var matMuro = new THREE.MeshStandardMaterial({ color: 0x1c2c48, metalness: 0.3, roughness: 0.4, transparent: true, opacity: 0.82 });
    var matBorde = new THREE.LineBasicMaterial({ color: C.cian, transparent: true, opacity: 0.45 });
    var self = this;
    this.contornos = {};
    Object.keys(ZONAS).forEach(function (k) {
      var z = ZONAS[k];
      var piso = new THREE.Mesh(new THREE.PlaneGeometry(z.w, z.d),
        new THREE.MeshStandardMaterial({ color: z.color, transparent: true, opacity: 0.08, metalness: 0, roughness: 1 }));
      piso.rotation.x = -Math.PI / 2; piso.position.set(z.x, 0.04, z.z); piso.receiveShadow = true;
      esc.add(piso);
      // Contorno que cambia de color si el servicio supera su umbral de saturación
      var pts = [[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]].map(function (p) {
        return new THREE.Vector3(z.x + p[0] * z.w / 2, 0.08, z.z + p[1] * z.d / 2);
      });
      var contorno = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
        new THREE.LineBasicMaterial({ color: z.color, transparent: true, opacity: 0.9 }));
      esc.add(contorno);
      self.contornos[k] = { linea: contorno, piso: piso, base: new THREE.Color(z.color) };
      self.muros(z, matMuro, matBorde);
    });

    // Mobiliario ilustrativo
    var matMueble = new THREE.MeshStandardMaterial({ color: 0x24375a, metalness: 0.4, roughness: 0.5 });
    function caja(w, h, d, x, z, mat) {
      var m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat || matMueble);
      m.position.set(x, h / 2, z); m.castShadow = true; m.receiveShadow = true; esc.add(m); return m;
    }
    caja(6, 1.1, 1.4, 0, 22);                    // recepción principal
    caja(7, 1.1, 1.2, -18, -15.55);              // estación de enfermería hospitalización (entre filas)
    caja(5, 1.1, 1.4, 27, 18);                   // registro de urgencias
    // Consultorios ambulatorios: registro puntual, sin estancia (gris)
    var matConsulta = new THREE.MeshStandardMaterial({ color: 0x93a3b8, metalness: 0.2, roughness: 0.6, transparent: true, opacity: 0.9 });
    this.consultorios = [];
    for (var cx = 0; cx < 4; cx++) {
      for (var cz = 0; cz < 2; cz++) {
        var x = -33 + cx * 6, zz = 11 + cz * 6;
        caja(4.4, 0.9, 3.6, x, zz, matConsulta);
        this.consultorios.push([x, zz - 2.6]);
      }
    }
    // Sala de espera de urgencias
    this.asientos = [];
    var matSilla = new THREE.MeshStandardMaterial({ color: 0x33496f, roughness: 0.6 });
    for (var sx = 0; sx < 6; sx++) {
      for (var sz = 0; sz < 3; sz++) {
        var px = 13 + sx * 2.2, pz = 11 + sz * 2.6;
        caja(1.5, 0.5, 0.9, px, pz, matSilla);
        this.asientos.push([px, pz + 0.9]);
      }
    }
    // Bahía de ambulancias y marcas de entrada / egreso
    var anillo = function (x, z, r, color) {
      var m = new THREE.Mesh(new THREE.RingGeometry(r * 0.82, r, 40),
        new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.8, side: THREE.DoubleSide }));
      m.rotation.x = -Math.PI / 2; m.position.set(x, 0.06, z); esc.add(m); return m;
    };
    this.anillos = [anillo(ENTRADA_URG.x, ENTRADA_URG.z, 2.6, C.rojo), anillo(ENTRADA.x, ENTRADA.z, 2.4, C.texto),
      anillo(EGRESO.x, EGRESO.z, 2.4, C.verde)];
  };

  /* Muros bajos con una abertura en la puerta de cada zona */
  Gemelo.prototype.muros = function (z, mat, matBorde) {
    var alto = 1.5, grosor = 0.3, hueco = 4.2;
    var esc = this.escena;
    function tramo(x1, z1, x2, z2) {
      var largo = Math.hypot(x2 - x1, z2 - z1);
      if (largo < 0.2) return;
      var geo = new THREE.BoxGeometry(largo, alto, grosor);
      var m = new THREE.Mesh(geo, mat);
      m.position.set((x1 + x2) / 2, alto / 2, (z1 + z2) / 2);
      m.rotation.y = -Math.atan2(z2 - z1, x2 - x1);
      m.castShadow = true;
      esc.add(m);
      var b = new THREE.LineSegments(new THREE.EdgesGeometry(geo), matBorde);
      b.position.copy(m.position); b.rotation.copy(m.rotation);
      esc.add(b);
    }
    var x0 = z.x - z.w / 2, x1 = z.x + z.w / 2, z0 = z.z - z.d / 2, z1 = z.z + z.d / 2;
    var px = z.puerta[0], pz = z.puerta[1];
    // Lado de la puerta (el que da al corredor)
    var ladoPuerta = Math.abs(pz - z0) < Math.abs(pz - z1) ? z0 : z1;
    var otroLado = ladoPuerta === z0 ? z1 : z0;
    tramo(x0, ladoPuerta, px - hueco / 2, ladoPuerta);
    tramo(px + hueco / 2, ladoPuerta, x1, ladoPuerta);
    if (z.nombre === "Ingreso a urgencias") {         // abierto a la entrada de urgencias
      tramo(x0, otroLado, x1 - 7, otroLado);
    } else {
      tramo(x0, otroLado, x1, otroLado);
    }
    tramo(x0, z0, x0, z1);
    tramo(x1, z0, x1, z1);
  };

  Gemelo.prototype.construirCamas = function () {
    var camas = [];
    var add = function (zona, prefijo, columnas, filas, dx, dz, cx, cz) {
      var n = 0;
      for (var f = 0; f < filas; f++) {
        for (var c = 0; c < columnas; c++) {
          n++;
          camas.push({
            id: prefijo + "-" + (n < 10 ? "0" : "") + n, zona: zona,
            x: cx + (c - (columnas - 1) / 2) * dx, z: cz + (f - (filas - 1) / 2) * dz, estado: "libre"
          });
        }
      }
    };
    var sh = this.datos.servicios;
    var nh = sh.hospitalizacion.camas_dibujadas, nu = sh.urgencias_observacion.camas_dibujadas;
    add("hospitalizacion", "H", 12, Math.ceil(nh / 12), 2.7, 6.5, ZONAS.hospitalizacion.x, ZONAS.hospitalizacion.z - 0.3);
    add("urgencias_observacion", "U", 6, Math.ceil(nu / 6), 3.8, 3.5, ZONAS.urgencias_observacion.x, ZONAS.urgencias_observacion.z - 0.5);
    this.camas = camas;

    var n = camas.length;
    this.mallaMarco = new THREE.InstancedMesh(new THREE.BoxGeometry(1.15, 0.42, 2.15),
      new THREE.MeshStandardMaterial({ color: 0x2a3a58, metalness: 0.5, roughness: 0.4 }), n);
    this.mallaColchon = new THREE.InstancedMesh(new THREE.BoxGeometry(0.98, 0.18, 1.95),
      new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false }), n);   // sin iluminación: el color del estado se lee igual desde cualquier ángulo
    this.mallaBrillo = new THREE.InstancedMesh(new THREE.PlaneGeometry(2.6, 3.4),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }), n);
    this.mallaPaciente = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.17, 0.17, 0.9, 8),
      new THREE.MeshStandardMaterial({ color: 0xe8eef8, roughness: 0.6 }), n);
    this.mallaMarco.castShadow = true; this.mallaMarco.receiveShadow = true;
    this.mallaColchon.receiveShadow = true;
    var m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(1, 1, 1), p = new THREE.Vector3();
    var plano = new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0));
    var tumbado = new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0));
    var blanco = new THREE.Color(0xffffff);
    for (var i = 0; i < n; i++) {
      var c = camas[i];
      this.mallaMarco.setMatrixAt(i, m.compose(p.set(c.x, 0.21, c.z), q, s));
      this.mallaColchon.setMatrixAt(i, m.compose(p.set(c.x, 0.5, c.z), q, s));
      this.mallaBrillo.setMatrixAt(i, m.compose(p.set(c.x, 0.07, c.z), plano, s));
      this.mallaPaciente.setMatrixAt(i, m.compose(p.set(c.x, 0.86, c.z + 0.15), tumbado, s));
      this.mallaColchon.setColorAt(i, blanco);
      this.mallaBrillo.setColorAt(i, blanco);
    }
    this.tumbado = tumbado;
    [this.mallaMarco, this.mallaColchon, this.mallaBrillo, this.mallaPaciente].forEach(function (x) { this.escena.add(x); }, this);

    // Anillo de selección
    this.anilloSel = new THREE.Mesh(new THREE.RingGeometry(1.55, 1.8, 40),
      new THREE.MeshBasicMaterial({ color: C.texto, transparent: true, opacity: 0.9, side: THREE.DoubleSide }));
    this.anilloSel.rotation.x = -Math.PI / 2;
    this.anilloSel.visible = false;
    this.escena.add(this.anilloSel);
    this.anilloHover = new THREE.Mesh(new THREE.RingGeometry(1.5, 1.62, 40),
      new THREE.MeshBasicMaterial({ color: C.cian, transparent: true, opacity: 0.7, side: THREE.DoubleSide }));
    this.anilloHover.rotation.x = -Math.PI / 2;
    this.anilloHover.visible = false;
    this.escena.add(this.anilloHover);
  };

  Gemelo.prototype.construirAgentes = function () {
    this.agentes = [];
    this.mallaAgentes = new THREE.InstancedMesh(new THREE.SphereGeometry(0.42, 14, 10),
      new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false }), MAX_AGENTES);
    var cero = new THREE.Matrix4().makeScale(0, 0, 0);
    var col = new THREE.Color(C.cian);
    for (var i = 0; i < MAX_AGENTES; i++) {
      this.mallaAgentes.setMatrixAt(i, cero);
      this.mallaAgentes.setColorAt(i, col);
      this.agentes.push({ activo: false, indice: i });
    }
    this.mallaAgentes.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.escena.add(this.mallaAgentes);
  };

  Gemelo.prototype.construirEtiquetas = function () {
    var capa = document.getElementById("gemelo-etiquetas");
    this.etiquetas = {};
    var self = this;
    var anclas = {
      hospitalizacion: [ZONAS.hospitalizacion.x, 3.2, ZONAS.hospitalizacion.z - ZONAS.hospitalizacion.d / 2],
      urgencias_observacion: [ZONAS.urgencias_observacion.x, 3.2, ZONAS.urgencias_observacion.z - ZONAS.urgencias_observacion.d / 2],
      urgencias_ingreso: [ZONAS.urgencias_ingreso.x + 4, 3.2, ZONAS.urgencias_ingreso.z + ZONAS.urgencias_ingreso.d / 2],
      ambulatorio: [ZONAS.ambulatorio.x, 3.2, ZONAS.ambulatorio.z + ZONAS.ambulatorio.d / 2],
      egreso: [EGRESO.x + 2, 2.6, EGRESO.z - 2]
    };
    Object.keys(anclas).forEach(function (k) {
      var div = document.createElement("div");
      div.className = "zona-etiqueta";
      capa.appendChild(div);
      self.etiquetas[k] = { el: div, pos: new THREE.Vector3(anclas[k][0], anclas[k][1], anclas[k][2]) };
    });
    this.etiquetas.egreso.el.innerHTML = "<b>Egreso</b>alta o traslado";
  };

  /* ------------------------------ Simulación ------------------------------ */
  Gemelo.prototype.horaIndice = function () { return Math.floor(this.horaSim) % 168; };

  Gemelo.prototype.ocupacionObjetivo = function (servicio) {
    var s = this.datos.servicios[servicio], h = this.horaIndice();
    var occ = s.ocupacion[Math.floor(h / 24)][h % 24];
    return { ocupacion: occ, camas: Math.round(Math.min(occ, 1) * s.camas_dibujadas), saturado: occ >= s.umbral_saturacion,
      fracSaturada: s.frac_saturada[Math.floor(h / 24)][h % 24] };
  };

  /* Paciente con resultado sorteado según la prevalencia real y la política de cada escenario */
  Gemelo.prototype.nuevoPaciente = function (cama) {
    cama.u1 = this.rnd(); cama.u2 = this.rnd();
    cama.desde = this.horaSim;
  };

  Gemelo.prototype.resultado = function (cama, esc) {
    var e = this.datos.servicios[cama.zona].escenarios;
    var larga = cama.u1 < e.prevalencia;
    var alerta = larga ? cama.u2 < e[esc].sensibilidad : cama.u2 < (1 - e[esc].especificidad);
    return { larga: larga, alerta: alerta };
  };

  Gemelo.prototype.reiniciar = function () {
    this.horaSim = 0;
    this.rnd = H.aleatorio(2026);
    var self = this;
    this.agentes.forEach(function (a) { a.activo = false; });
    this.camas.forEach(function (c) { c.estado = "libre"; });
    ["hospitalizacion", "urgencias_observacion"].forEach(function (k) {
      var obj = self.ocupacionObjetivo(k).camas;
      var libres = self.camas.filter(function (c) { return c.zona === k; });
      for (var i = 0; i < obj && i < libres.length; i++) {
        var c = libres[Math.floor(self.rnd() * libres.length)];
        if (c.estado === "ocupada") { i--; continue; }
        c.estado = "ocupada"; self.nuevoPaciente(c); c.desde = -self.rnd() * 48;
      }
    });
    this.horaMostrada = -1;
    this.pintarCamas();
    this.pintarAgentes();
    this.actualizarHora(true);
  };

  Gemelo.prototype.crearAgente = function (puntos, opciones) {
    var a = null;
    for (var i = 0; i < this.agentes.length; i++) { if (!this.agentes[i].activo) { a = this.agentes[i]; break; } }
    if (!a) return null;                                   // grupo lleno: se omite el punto
    a.activo = true; a.puntos = puntos; a.tramo = 0; a.avance = 0;
    a.pos = puntos[0].clone();
    a.espera = 0; a.esperas = opciones.esperas || {};
    a.alLlegar = opciones.alLlegar || null;
    a.color = opciones.color || C.cian;
    a.desc = opciones.desc || "";
    a.vel = 7 + this.rnd() * 2;
    a.alpha = 1;
    this.mallaAgentes.setColorAt(a.indice, new THREE.Color(a.color));
    this.mallaAgentes.instanceColor.needsUpdate = true;
    return a;
  };

  Gemelo.prototype.llegadaAmbiente = function (servicio, dtHoras) {
    var h = this.horaIndice();
    var lam = this.datos.servicios[servicio].llegadas[Math.floor(h / 24)][h % 24];
    this.acumulado[servicio] += lam * ESCALA_LLEGADAS * dtHoras;
    var self = this;
    while (this.acumulado[servicio] >= 1) {
      this.acumulado[servicio] -= 1;
      if (servicio === "ambulatorio") {
        var c = this.consultorios[Math.floor(this.rnd() * this.consultorios.length)];
        var pts = ruta([ENTRADA.x, ENTRADA.z], ENTRADA.puerta, ZONAS.ambulatorio.puerta, c)
          .concat(ruta(c, ZONAS.ambulatorio.puerta, EGRESO.puerta, [EGRESO.x, EGRESO.z]).slice(1));
        this.crearAgente(pts, { color: 0xb8c6dc, desc: "Visita ambulatoria → consulta → egreso (sin estancia)",
          esperas: (function () { var o = {}; o[ruta([ENTRADA.x, ENTRADA.z], ENTRADA.puerta, ZONAS.ambulatorio.puerta, c).length - 1] = 1.2; return o; })() });
      } else {
        var t = this.datos.transiciones.urgencias_ingreso;
        var asiento = this.asientos[Math.floor(this.rnd() * this.asientos.length)];
        var pObs = t.urgencias_observacion / (t.urgencias_observacion + t["(egreso)"] + t.hospitalizacion);
        var aObs = this.rnd() < pObs;
        var tramo1 = [v3(ENTRADA_URG.x, ENTRADA_URG.z), v3(31, 21.5), v3(asiento[0], asiento[1])];
        var tramo2 = aObs
          ? ruta(asiento, ZONAS.urgencias_ingreso.puerta, ZONAS.urgencias_observacion.puerta,
            [ZONAS.urgencias_observacion.puerta[0], ZONAS.urgencias_observacion.puerta[1] - 1.5]).slice(1)
          : ruta(asiento, ZONAS.urgencias_ingreso.puerta, EGRESO.puerta, [EGRESO.x, EGRESO.z]).slice(1);
        var esperas = {}; esperas[2] = 1.6 + self.rnd() * 1.4;
        this.crearAgente(tramo1.concat(tramo2), {
          color: 0x9b8cff, esperas: esperas,
          desc: aObs ? "Ingreso a urgencias → sala de espera → observación (" + H.fmt(pObs * 100, 0) + " % de los casos)"
            : "Ingreso a urgencias → sala de espera → egreso"
        });
      }
    }
  };

  /* Ajusta las camas ocupadas a la ocupación real de la hora: ingresos y altas animados */
  Gemelo.prototype.balancearCamas = function (servicio, dt) {
    this.enfriamiento[servicio] -= dt * Math.max(1, this.velocidad);
    if (this.enfriamiento[servicio] > 0) return;
    var objetivo = this.ocupacionObjetivo(servicio).camas;
    var propias = this.camas.filter(function (c) { return c.zona === servicio; });
    var ocupadas = propias.filter(function (c) { return c.estado === "ocupada" || c.estado === "reservada"; });
    var self = this;
    var z = ZONAS[servicio];
    if (ocupadas.length < objetivo) {
      var libres = propias.filter(function (c) { return c.estado === "libre"; });
      if (!libres.length) return;
      var cama = libres[Math.floor(this.rnd() * libres.length)];
      cama.estado = "reservada";
      var origen = servicio === "hospitalizacion" ? ZONAS.urgencias_observacion.puerta : ZONAS.urgencias_ingreso.puerta;
      var desc = servicio === "hospitalizacion" ? "Traslado de urgencias a hospitalización (97 % de los ingresos vienen de urgencias)"
        : "Ingreso a observación desde la sala de espera";
      var pts = ruta([origen[0], origen[1] + (servicio === "hospitalizacion" ? -1 : 1)], origen, z.puerta, [cama.x, cama.z + 1.4]);
      var a = this.crearAgente(pts, { color: C.cian, desc: desc, alLlegar: function () { cama.estado = "ocupada"; self.nuevoPaciente(cama); self.pintarCamas(); } });
      if (!a) { cama.estado = "ocupada"; this.nuevoPaciente(cama); }
      cama.agente = a;
      this.enfriamiento[servicio] = 0.35;
      this.pintarCamas();
    } else if (propias.filter(function (c) { return c.estado === "ocupada"; }).length > objetivo) {
      // Alta: las estancias normales salen antes que las largas
      var cand = propias.filter(function (c) { return c.estado === "ocupada"; });
      cand.sort(function (a, b) { return (self.resultado(a, "B").larga - self.resultado(b, "B").larga) || (a.desde - b.desde); });
      var sale = cand[Math.floor(this.rnd() * Math.min(cand.length, 6))];
      sale.estado = "saliendo";
      var t = this.datos.transiciones[servicio];
      var aHosp = servicio === "urgencias_observacion" && this.rnd() < t.hospitalizacion / (t.hospitalizacion + t["(egreso)"]);
      var destino = aHosp ? ruta([sale.x, sale.z + 1.4], z.puerta, ZONAS.hospitalizacion.puerta, [ZONAS.hospitalizacion.puerta[0], ZONAS.hospitalizacion.puerta[1] - 1.5])
        : ruta([sale.x, sale.z + 1.4], z.puerta, EGRESO.puerta, [EGRESO.x, EGRESO.z]);
      var b = this.crearAgente(destino, { color: aHosp ? C.azul : C.verde,
        desc: aHosp ? "Observación → hospitalización (" + H.fmt(t.hospitalizacion * 100, 1) + " % de las transiciones)" : "Alta: " + z.nombre.toLowerCase() + " → egreso" });
      setTimeout(function () { sale.estado = "libre"; self.pintarCamas(); }, 450);
      this.enfriamiento[servicio] = 0.35;
      this.pintarCamas();
    }
  };

  Gemelo.prototype.actualizar = function (dt) {
    var t = performance.now() / 1000;
    if (this.ola) {
      this.pintarCamas();
      if (performance.now() - this.ola.inicio > 1000) { this.ola = null; this.pintarCamas(); }
    }
    if (this.corriendo) {
      var dtHoras = dt * this.velocidad / SEG_POR_HORA;
      this.horaSim = (this.horaSim + dtHoras) % 168;
      this.llegadaAmbiente("ambulatorio", dtHoras);
      this.llegadaAmbiente("urgencias_ingreso", dtHoras);
      this.balancearCamas("hospitalizacion", dt);
      this.balancearCamas("urgencias_observacion", dt);
      this.actualizarHora(false);
    }
    this.moverAgentes(this.corriendo ? dt * Math.min(2.5, Math.max(1, this.velocidad)) : 0);
    // Brillo y contornos de saturación
    var self = this;
    ["hospitalizacion", "urgencias_observacion"].forEach(function (k) {
      var o = self.estadoHora[k];
      var c = self.contornos[k];
      if (o && o.saturado) {
        c.linea.material.color.setHex(C.naranja);
        c.piso.material.color.setHex(C.naranja);
        c.piso.material.opacity = 0.09 + 0.05 * Math.sin(t * 4);
      } else {
        c.linea.material.color.copy(c.base);
        c.piso.material.color.copy(c.base);
        c.piso.material.opacity = 0.08;
      }
    });
    for (var i = 0; i < this.flechas.length; i++) {
      this.flechas[i].position.x = -40 + ((i * 5 + t * (this.corriendo ? 3 * this.velocidad : 0.6)) % 80);
    }
    if (this.seleccion && this.seleccion.tipo === "agente") {
      var a = this.seleccion.obj;
      if (a.activo) this.anilloSel.position.set(a.pos.x, 0.08, a.pos.z); else this.anilloSel.visible = false;
    }
  };

  Gemelo.prototype.moverAgentes = function (dt) {
    var m = new THREE.Matrix4(), s = new THREE.Vector3(), q = new THREE.Quaternion();
    var cero = new THREE.Matrix4().makeScale(0, 0, 0);
    for (var i = 0; i < this.agentes.length; i++) {
      var a = this.agentes[i];
      if (!a.activo) { this.mallaAgentes.setMatrixAt(i, cero); continue; }
      if (dt > 0) {
        if (a.espera > 0) { a.espera -= dt; }
        else {
          var paso = a.vel * dt;
          while (paso > 0 && a.tramo < a.puntos.length - 1) {
            var destino = a.puntos[a.tramo + 1];
            var dist = a.pos.distanceTo(destino);
            if (dist <= paso) {
              a.pos.copy(destino); paso -= dist; a.tramo++;
              if (a.esperas[a.tramo]) { a.espera = a.esperas[a.tramo]; break; }
            } else {
              a.pos.lerp(destino, paso / dist); paso = 0;
            }
          }
          if (a.tramo >= a.puntos.length - 1) {
            a.activo = false;
            if (a.alLlegar) a.alLlegar();
            this.mallaAgentes.setMatrixAt(i, cero);
            continue;
          }
        }
      }
      var bote = 0.55 + Math.abs(Math.sin((a.pos.x + a.pos.z) * 1.4)) * 0.12;
      m.compose(s.set(a.pos.x, bote, a.pos.z), q, new THREE.Vector3(1, 1, 1));
      this.mallaAgentes.setMatrixAt(i, m);
    }
    this.mallaAgentes.instanceMatrix.needsUpdate = true;
  };

  Gemelo.prototype.escenarioDeCama = function (c) {
    if (!this.ola) return this.escenario;
    var retraso = (c.x + 40) / 80 * 0.9;
    return (performance.now() - this.ola.inicio) / 1000 < retraso ? this.ola.desde : this.escenario;
  };

  Gemelo.prototype.colorCama = function (c) {
    if (c.estado === "libre") return C.verde;
    if (c.estado === "reservada" || c.estado === "saliendo") return C.cian;
    var r = this.resultado(c, this.escenarioDeCama(c));
    if (r.alerta) return C.naranja;
    if (r.larga) return C.rojo;
    return C.azul;
  };

  Gemelo.prototype.pintarCamas = function () {
    if (!this.mallaColchon) return;
    var col = new THREE.Color(), m = new THREE.Matrix4(), p = new THREE.Vector3(), uno = new THREE.Vector3(1, 1, 1), cero = new THREE.Vector3(0, 0, 0);
    var q = new THREE.Quaternion();
    for (var i = 0; i < this.camas.length; i++) {
      var c = this.camas[i];
      col.setHex(this.colorCama(c));
      this.mallaColchon.setColorAt(i, col);
      this.mallaBrillo.setColorAt(i, col);
      var ocupada = c.estado === "ocupada" || c.estado === "saliendo";
      this.mallaPaciente.setMatrixAt(i, m.compose(p.set(c.x, 0.86, c.z + 0.15), this.tumbado, ocupada ? uno : cero));
    }
    this.mallaColchon.instanceColor.needsUpdate = true;
    this.mallaBrillo.instanceColor.needsUpdate = true;
    this.mallaPaciente.instanceMatrix.needsUpdate = true;
    this.pintarConteo();
    if (this.seleccion && this.seleccion.tipo === "cama") this.pintarInspector();
  };

  Gemelo.prototype.pintarAgentes = function () {
    if (this.mallaAgentes) this.moverAgentes(0);
  };

  Gemelo.prototype.actualizarHora = function (forzar) {
    var h = this.horaIndice();
    if (!forzar && h === this.horaMostrada) return;
    this.horaMostrada = h;
    var dia = Math.floor(h / 24), hora = h % 24;
    var reloj = document.getElementById("gemelo-reloj");
    if (reloj) reloj.textContent = DIAS[dia] + " " + (hora < 10 ? "0" : "") + hora + ":00";
    if (this.barra && document.activeElement !== this.barra) this.barra.value = h;
    var self = this;
    this.estadoHora = {};
    ["hospitalizacion", "urgencias_observacion"].forEach(function (k) { self.estadoHora[k] = self.ocupacionObjetivo(k); });
    if (!this.etiquetas) return;
    var sv = this.datos.servicios;
    ["hospitalizacion", "urgencias_observacion"].forEach(function (k) {
      var o = self.estadoHora[k], et = self.etiquetas[k].el;
      et.classList.toggle("saturada", o.saturado);
      et.innerHTML = "<b>" + ZONAS[k].nombre + "</b>Ocupación <span class='valor'>" + H.fmt(o.ocupacion * 100, 0) + " %</span>" +
        (o.saturado ? " · sobre el umbral de " + H.fmt(sv[k].umbral_saturacion * 100, 0) + " %" : "") +
        "<span class='extra'><br>Esta franja estuvo saturada el " + H.fmt(o.fracSaturada * 100, 0) + " % de las semanas</span>";
    });
    ["ambulatorio", "urgencias_ingreso"].forEach(function (k) {
      var lam = sv[k].llegadas[dia][hora];
      self.etiquetas[k].el.innerHTML = "<b>" + ZONAS[k].nombre + "</b>Llegadas <span class='valor'>" + H.fmt(lam, lam < 10 ? 1 : 0) + "/h</span>";
    });
  };

  Gemelo.prototype.moverEtiquetas = function () {
    var w = this.el.clientWidth, h = this.el.clientHeight, v = new THREE.Vector3();
    for (var k in this.etiquetas) {
      var e = this.etiquetas[k];
      v.copy(e.pos).project(this.camara);
      if (v.z > 1) { e.el.style.display = "none"; continue; }
      e.el.style.display = "";
      e.el.style.transform = "translate(-50%,-100%) translate(" + ((v.x + 1) / 2 * w).toFixed(1) + "px," + ((1 - v.y) / 2 * h).toFixed(1) + "px)";
    }
  };

  /* ------------------------------ Interacción ------------------------------ */
  Gemelo.prototype.elegir = function (e) {
    var r = this.renderer.domElement.getBoundingClientRect();
    var ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    this.raycaster.setFromCamera(ndc, this.camara);
    var golpeAgente = this.raycaster.intersectObject(this.mallaAgentes);
    var golpeCama = this.raycaster.intersectObjects([this.mallaColchon, this.mallaMarco]);
    var activo = golpeAgente.filter(function (g) { return this.agentes[g.instanceId].activo; }, this)[0];
    if (activo && (!golpeCama[0] || activo.distance < golpeCama[0].distance + 2)) {
      this.seleccion = { tipo: "agente", obj: this.agentes[activo.instanceId] };
    } else if (golpeCama[0]) {
      var c = this.camas[golpeCama[0].instanceId];
      this.seleccion = { tipo: "cama", obj: c };
      this.anilloSel.position.set(c.x, 0.08, c.z);
    } else {
      this.seleccion = null;
    }
    this.anilloSel.visible = !!this.seleccion;
    this.pintarInspector();
  };

  Gemelo.prototype.sobrevolar = function (e) {
    var r = this.renderer.domElement.getBoundingClientRect();
    var ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    this.raycaster.setFromCamera(ndc, this.camara);
    var g = this.raycaster.intersectObjects([this.mallaColchon, this.mallaMarco])[0];
    if (g) {
      var c = this.camas[g.instanceId];
      this.anilloHover.position.set(c.x, 0.09, c.z);
      this.anilloHover.visible = true;
      this.renderer.domElement.style.cursor = "pointer";
    } else {
      this.anilloHover.visible = false;
      this.renderer.domElement.style.cursor = "";
    }
  };

  Gemelo.prototype.pintarInspector = function () {
    var div = document.getElementById("inspector");
    if (!div) return;
    var s = this.seleccion;
    if (!s) { div.innerHTML = "<p class='vacio'>Haz clic en una cama o en un paciente para ver su estado.</p>"; return; }
    var fila = function (k, v) { return "<dt>" + k + "</dt><dd>" + v + "</dd>"; };
    var chipEstado = function (texto, color) {
      return "<span class='estado-chip' style='color:" + color + ";background:color-mix(in srgb," + color + " 14%, transparent)'>" + texto + "</span>";
    };
    var escActivo = this.escenario === "A" ? "A · regla actual (θ = 0,5)" : "B · política óptima (θ*)";
    if (s.tipo === "agente") {
      div.innerHTML = "<div class='inspector-cabecera'><b>Paciente simulado</b>" + chipEstado(s.obj.espera > 0 ? "En espera" : "En tránsito", "var(--cian)") + "</div>" +
        "<dl>" + fila("Recorrido", s.obj.desc) + "</dl>" +
        "<p class='nota-pie' style='margin-top:10px'>Punto ilustrativo: la tasa de llegadas y la ruta salen de datos reales; la persona no existe.</p>";
      return;
    }
    var c = s.obj, sv = this.datos.servicios[c.zona];
    var nombres = { libre: ["Disponible", "var(--verde)"], reservada: ["Paciente en camino", "var(--cian)"],
      saliendo: ["Liberándose", "var(--cian)"], ocupada: ["Ocupada", "var(--azul)"] };
    var html = "<div class='inspector-cabecera'><b>" + c.id + "</b>" + chipEstado(nombres[c.estado][0], nombres[c.estado][1]) + "</div><dl>" +
      fila("Servicio", ZONAS[c.zona].nombre) + fila("Política activa", escActivo) +
      fila("Representa", "≈ " + H.fmt(sv.lugares_por_cama, 1) + " lugares de la capacidad estimada");
    var nota = "";
    if (c.estado === "ocupada" || c.estado === "saliendo") {
      var r = this.resultado(c, this.escenario), ra = this.resultado(c, "A"), rb = this.resultado(c, "B");
      var alerta = r.alerta ? chipEstado("Con alerta", "var(--naranja)") : (r.larga ? chipEstado("Sin alerta · estancia larga", "var(--rojo)") : chipEstado("Sin alerta", "var(--gris-claro)"));
      html += fila("Alerta ahora", alerta) +
        fila("Estancia (simulada)", r.larga ? "Larga: supera el P75 del servicio" : "Dentro de lo normal") +
        fila("En A / en B", (ra.alerta ? "alerta" : "sin alerta") + " / " + (rb.alerta ? "alerta" : "sin alerta"));
      nota = "<p class='nota-pie' style='margin-top:10px'>Paciente simulado: su estancia y su alerta se sortean con la prevalencia real (" +
        H.fmt(sv.escenarios.prevalencia * 100, 0) + " %) y la sensibilidad / especificidad de cada política en la prueba. Es el mismo paciente en A y en B.</p>";
    }
    div.innerHTML = html + "</dl>" + nota;
  };

  Gemelo.prototype.pintarConteo = function () {
    var span = document.getElementById("conteo-pantalla");
    if (!span || !this.camas) return;
    var self = this, alertas = 0, perdidas = 0, ocup = 0;
    this.camas.forEach(function (c) {
      if (c.zona !== "hospitalizacion" || c.estado !== "ocupada") return;
      ocup++;
      var r = self.resultado(c, self.escenario);
      if (r.alerta) alertas++; else if (r.larga) perdidas++;
    });
    span.textContent = "En pantalla, hospitalización: " + alertas + " con alerta y " + perdidas +
      " estancias largas sin alerta de " + ocup + " camas ocupadas.";
  };

  Gemelo.prototype.pintarMetricas = function () {
    var e = this.datos.servicios.hospitalizacion.escenarios, x = e[this.escenario];
    var u = this.datos.servicios.urgencias_observacion.escenarios[this.escenario];
    var met = document.getElementById("metricas-escenario");
    var o = e[this.escenario === "A" ? "B" : "A"];
    // Diferencia frente al otro escenario; "mejor" según si la métrica debe subir o bajar
    var delta = function (v, ref, sube, pp) {
      var d = v - ref;
      if (Math.abs(d) < 0.05) return "";
      var mejor = sube ? d > 0 : d < 0;
      return "<small class='" + (mejor ? "mejor" : "peor") + "'>" + (d > 0 ? "+" : "−") + H.fmt(Math.abs(d), 1) + (pp ? " pp" : "") + "</small>";
    };
    if (met) {
      met.innerHTML = [
        [H.fmt(x.sensibilidad * 100, 1) + " %" + delta(x.sensibilidad * 100, o.sensibilidad * 100, true, true), "estancias largas con alerta"],
        [H.fmt(x.fn_100, 1) + delta(x.fn_100, o.fn_100, false), "estancias largas sin alerta por 100"],
        [H.fmt(x.alertas_100, 1) + delta(x.alertas_100, o.alertas_100, false), "alertas por cada 100 pacientes"],
        [H.fmt(x.costo_100, 1) + delta(x.costo_100, o.costo_100, false), "costo esperado por 100 (5:1)"]
      ].map(function (p) { return "<div><b>" + p[0] + "</b><span>" + p[1] + "</span></div>"; }).join("");
    }
    var qc = document.getElementById("que-cambia");
    if (qc) {
      var th = this.datos.servicios.hospitalizacion.escenarios.B.umbral, tu = this.datos.servicios.urgencias_observacion.escenarios.B.umbral;
      qc.innerHTML = this.escenario === "A"
        ? "<b>Regla actual:</b> solo alerta cuando el modelo estima ≥ 50 %. Con 1 de cada 4 estancias largas en hospitalización, casi nadie llega a ese valor: la mayoría de las estancias largas queda en rojo."
        : "<b>Política óptima:</b> alerta desde " + H.fmt(th * 100, 0) + " % en hospitalización y " + H.fmt(tu * 100, 0) +
          " % en urgencias, porque no avisar cuesta 5 veces más que avisar de más. Aparecen más alertas (naranja) y casi desaparece el rojo.";
    }
    var nota = document.getElementById("nota-escenario");
    if (nota) {
      nota.innerHTML = "Hospitalización, prueba temporal única (n = " + H.fmt(e.n, 0) + "). Urgencias: el escenario " +
        this.escenario + " alerta al " + H.fmt(u.alertas_100, 0) + " % de los pacientes." +
        "<br><span id='conteo-pantalla'></span>";
    }
    this.pintarConteo();
  };

  Gemelo.prototype.ponerEscenario = function (esc) {
    if (esc !== this.escenario && !H.reducido) this.ola = { inicio: performance.now(), desde: this.escenario };
    this.escenario = esc;
    this.pintarIdentidad();
    document.getElementById("esc-a").setAttribute("aria-pressed", esc === "A");
    document.getElementById("esc-b").setAttribute("aria-pressed", esc === "B");
    this.pintarMetricas();
    this.pintarCamas();
  };

  /* Identidad de cada escenario: color del marco y rótulo dentro del lienzo */
  Gemelo.prototype.pintarIdentidad = function () {
    this.el.setAttribute("data-escenario", this.escenario);
    var r = document.getElementById("gemelo-escenario");
    if (r) r.textContent = this.escenario === "A" ? "Escenario A · regla actual θ = 0,5" : "Escenario B · política óptima θ*";
  };

  Gemelo.prototype.ponerCamara = function (modo) {
    document.getElementById("cam-perspectiva").setAttribute("aria-pressed", modo === "perspectiva");
    document.getElementById("cam-cenital").setAttribute("aria-pressed", modo === "cenital");
    if (!this.camara) return;
    var destino = modo === "cenital" ? { x: -2, y: 92, z: 6 } : { x: 0, y: 62, z: 76 };
    if (window.gsap && !H.reducido) gsap.to(this.camara.position, { duration: 1.4, ease: "power3.inOut", x: destino.x, y: destino.y, z: destino.z });
    else this.camara.position.set(destino.x, destino.y, destino.z);
  };

  /* Entrada de cámara la primera vez que el gemelo aparece en pantalla */
  Gemelo.prototype.presentar = function () {
    if (!window.gsap || H.reducido) return;
    var p = this.camara.position;
    gsap.fromTo(p, { x: -70, y: 110, z: 130 }, { x: 0, y: 62, z: 76, duration: 2.4, ease: "power3.out" });
  };

  Gemelo.prototype.construirControles = function () {
    var self = this;
    var $ = function (id) { return document.getElementById(id); };
    var iniciar = $("sim-iniciar"), pausar = $("sim-pausar"), reiniciar = $("sim-reiniciar");
    var contenedor = $("sim-hora-contenedor");
    if (contenedor) {
      contenedor.innerHTML = "<label class='solo-lector' for='sim-hora'>Hora de la semana</label>" +
        "<input id='sim-hora' class='barra-tiempo' type='range' min='0' max='167' step='1' value='0'>";
      this.barra = $("sim-hora");
      this.barra.addEventListener("input", function () {
        self.horaSim = Number(self.barra.value) + 0.001;
        self.actualizarHora(true);
      });
    }
    var estado = function () {
      iniciar.textContent = self.corriendo ? "En marcha" : (self.horaSim > 0.01 ? "Reanudar" : "Iniciar");
      iniciar.disabled = self.corriendo;
      pausar.disabled = !self.corriendo;
    };
    iniciar.addEventListener("click", function () { self.corriendo = true; estado(); });
    pausar.addEventListener("click", function () { self.corriendo = false; estado(); });
    reiniciar.addEventListener("click", function () { self.corriendo = false; if (self.camas) self.reiniciar(); else self.horaSim = 0; estado(); });
    $("esc-a").addEventListener("click", function () { self.ponerEscenario("A"); });
    $("esc-b").addEventListener("click", function () { self.ponerEscenario("B"); });
    $("cam-perspectiva").addEventListener("click", function () { self.ponerCamara("perspectiva"); });
    $("cam-cenital").addEventListener("click", function () { self.ponerCamara("cenital"); });
    Array.prototype.forEach.call(document.querySelectorAll("[data-velocidad]"), function (b) {
      b.addEventListener("click", function () {
        self.velocidad = Number(b.getAttribute("data-velocidad"));
        Array.prototype.forEach.call(document.querySelectorAll("[data-velocidad]"), function (o) { o.setAttribute("aria-pressed", o === b); });
      });
    });
    estado();
  };

  H.esperar("#gemelo-lienzo", function (el) {
    H.esperar("#sim-hora-contenedor", function () {
      fetch("/api/gemelo").then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      }).then(function (datos) {
        H.gemelo = new Gemelo(el, datos);
      }).catch(function (err) {
        console.error("No se pudieron cargar los datos del gemelo:", err);
        el.classList.add("sin-webgl", "listo");
        var aviso = el.querySelector(".gemelo-sin-webgl");
        if (aviso) aviso.innerHTML = "<p>No se pudieron cargar los datos del gemelo (/api/gemelo).</p>";
      });
    });
  });
})(window.HUN);
