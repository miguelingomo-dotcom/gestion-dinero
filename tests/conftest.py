import json
import os
import re
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
# Navegador dentro del proyecto (ignorado en git), no en la caché global de Playwright
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(AQUI / ".browsers"))

from playwright.sync_api import expect, sync_playwright  # noqa: E402

import datos  # noqa: E402
from notion_mock import APP_ORIGIN, FakeNotion  # noqa: E402

expect.set_options(timeout=5000)
# Las únicas peticiones externas que la app intenta son las fuentes de Google: se bloquean, y cualquier otra hace fallar la prueba
EXTERNOS_ESPERADOS = ("https://fonts.googleapis.com/", "https://fonts.gstatic.com/")
ESTATICOS = {"/icon.png": "image/png", "/icon-192.png": "image/png", "/kashy-vencimientos.js": "text/javascript",
             "/manifest.webmanifest": "application/manifest+json", "/sw.js": "text/javascript"}
CLAVE = "clave-de-prueba"  # inventada: la real solo está en Vercel y en el dispositivo


def pytest_addoption(parser):
    parser.addoption("--update-baseline", action="store_true", help="Reescribe las capturas de referencia")


class App:
    """La app abierta en un móvil simulado, con Notion falso."""

    NAV = {"inicio": 0, "movimientos": 1, "cuentas": 2, "inversion": 3}

    def __init__(self, page, notion):
        self.page = page
        self.notion = notion
        self.errores_js = []
        self.externos = []
        self.rutas_desconocidas = []
        self.clave_valida = CLAVE  # la que acepta el servidor simulado
        self.rechazos = []  # peticiones respondidas con 401
        self.peticiones_api = []  # cabeceras de cada llamada a /api/
        # /api/push simulado: suscripción guardada, pruebas enviadas y el código que devolverá la prueba
        self.push = {"suscripcion": None, "pruebas": 0, "codigo_prueba": 200, "guardados": 0, "borrados": 0}

    def ir(self, seccion):
        if seccion in self.NAV:
            self.page.locator("#nav%d" % self.NAV[seccion]).click()
        elif seccion == "registrar":
            self.page.locator(".nav-add").click()
        elif seccion == "stats":
            self.ir("inicio")
            self.page.locator('#sec-inicio .icon-btn[aria-label="Stats"]').click()
        else:
            raise ValueError(seccion)
        expect(self.page.locator("#sec-" + seccion)).to_have_class(re.compile(r"\bactive\b"))

    def toast(self):
        return self.page.locator("#toast")

    def deshacer(self):
        self.page.locator("#toast .toast-accion").click()

    def fila_mov(self, nombre):
        return self.page.locator("#recentMovs .mov-item", has_text=nombre)

    def borrar_fila(self, fila):
        """Borra con el botón «Eliminar» del carril de deslizar, el camino real en el iPhone."""
        fila.locator("xpath=ancestor::div[contains(@class,'swipe')][1]").locator(".swipe-del").click()

    def cuenta(self, nombre):
        return self.page.locator('#accountCards .account-card:has(.account-name[data-plain="%s"])' % nombre)

    def desplegar_cuenta(self, nombre):
        """Las acciones (Mover, Desactivar...) y los movimientos solo se ven con la tarjeta desplegada."""
        t = self.cuenta(nombre)
        t.locator(".account-card-head").click()
        expect(t).to_have_class(re.compile(r"\bexpanded\b"))
        return t

    def avisos_listos(self):
        """Espera a que termine la comprobación de avisos, para que afirmar «no hay aviso» no pase antes de tiempo."""
        self.page.evaluate("()=>checkAlerts()")

    def escrituras(self, metodo=None):
        return [e for e in self.notion.escrituras if not metodo or e["metodo"] == metodo]


# Clave pública VAPID de prueba (65 bytes, como las reales)
CLAVE_VAPID = "BPWgDWfYVxXkAHU4xN7O2t2h3hkr8tlqmDqzvwDYiwq8bWEgDDJptNqtsukaBePvXa2rzvxLfVKH87sezIfBnd0"


def responder_push(app, metodo, url, cuerpo):
    p = app.push
    if metodo == "GET":
        return 200, {"publicKey": CLAVE_VAPID, "suscrito": bool(p["suscripcion"]),
                     "endpoint": p["suscripcion"]["endpoint"] if p["suscripcion"] else None}
    if metodo == "DELETE":
        p["suscripcion"] = None
        p["borrados"] += 1
        return 200, {"ok": True}
    if "prueba=" in url:
        if not p["suscripcion"]:
            return 409, {"error": "Sin suscripción"}
        p["pruebas"] += 1
        return p["codigo_prueba"], {}
    p["suscripcion"] = cuerpo["subscription"]
    p["guardados"] += 1
    return 200, {"ok": True}


@pytest.fixture(scope="session")
def navegador():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture(params=["light", "dark"], ids=["claro", "oscuro"])
def tema(request):
    return request.param


@pytest.fixture
def abrir(navegador, tema):
    """Devuelve abrir(hoy=..., sembrar=..., antes=...): abre la app en esa fecha con los datos indicados."""
    contextos = []
    apps = []

    def _abrir(hoy=datos.HOY, sembrar=datos.sembrar, antes=None, mas=None, reducir=True, clave=CLAVE):
        ctx = navegador.new_context(
            viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
            locale="es-ES", timezone_id="Europe/Madrid", service_workers="block",
            reduced_motion="reduce" if reducir else "no-preference",
        )
        contextos.append(ctx)
        page = ctx.new_page()
        page.set_default_timeout(5000)
        notion = FakeNotion(datos.BASES)
        if sembrar:
            sembrar(notion)
        if mas:
            mas(notion)
        app = App(page, notion)
        apps.append(app)
        html = datos.HTML

        def rutear(route):
            req = route.request
            if not req.url.startswith(APP_ORIGIN + "/"):
                app.externos.append(req.url)
                return route.abort()
            ruta = req.url[len(APP_ORIGIN):].split("?")[0]
            if ruta == "/":
                return route.fulfill(status=200, content_type="text/html; charset=utf-8", body=html)
            if ruta in ESTATICOS:
                return route.fulfill(status=200, content_type=ESTATICOS[ruta], path=str(datos.RAIZ / ruta[1:]))
            if ruta.startswith("/api/"):
                # Como el servidor real: sin la clave correcta no se ejecuta nada
                app.peticiones_api.append(req.headers)
                if req.headers.get("x-kashy-key") != app.clave_valida:
                    app.rechazos.append(req.method + " " + req.url)
                    return route.fulfill(status=401, content_type="application/json", body='{"error":"No autorizado"}')
                cuerpo = json.loads(req.post_data) if req.post_data else None
                if ruta == "/api/push":
                    r = responder_push(app, req.method, req.url, cuerpo)
                else:
                    r = notion.responder(req.method, req.url, cuerpo)
                if r is None:
                    app.rutas_desconocidas.append(req.method + " " + req.url)
                    return route.fulfill(status=500, content_type="application/json", body="{}")
                return route.fulfill(status=r[0], content_type="application/json", body=json.dumps(r[1]))
            app.rutas_desconocidas.append(req.method + " " + req.url)
            return route.fulfill(status=404, body="")

        # Todo pasa por aquí: lo que no sea la app simulada se bloquea y se anota
        ctx.route("**/*", rutear)
        page.on("pageerror", lambda e: app.errores_js.append(str(e)))
        page.clock.set_fixed_time(hoy + "T12:00:00+01:00")
        page.add_init_script(
            "try{localStorage.setItem('kashy-theme',%s);localStorage.setItem('kashy-lang','es')}catch(e){}" % json.dumps(tema))
        if clave:
            # Solo si aún no hay ninguna: una recarga no debe pisar la que haya guardado la app
            page.add_init_script(
                "try{if(!localStorage.getItem('kashy-key')&&!sessionStorage.getItem('sin-sembrar')){localStorage.setItem('kashy-key',%s);sessionStorage.setItem('sin-sembrar','1')}}catch(e){}" % json.dumps(clave))
        if antes:
            antes(page)
        page.goto(APP_ORIGIN + "/")
        expect(page.locator("#splashScreen")).to_have_class(re.compile(r"\bhide\b"))
        return app

    yield _abrir

    try:
        for app in apps:
            assert not app.errores_js, "Errores de JavaScript: %s" % app.errores_js
            assert not app.rutas_desconocidas, "Rutas sin simular: %s" % app.rutas_desconocidas
            raros = [u for u in app.externos if not u.startswith(EXTERNOS_ESPERADOS)]
            assert not raros, "La app intentó salir a la red: %s" % raros
    finally:
        for ctx in contextos:
            ctx.close()


@pytest.fixture
def app(abrir):
    return abrir()
