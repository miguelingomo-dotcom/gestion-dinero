"""La clave de la API en la app. La parte del servidor está en test_api_clave.py."""
import re

from playwright.sync_api import expect

from conftest import CLAVE


def pantalla(app):
    return app.page.locator("#claveScreen")


def introducir(app, clave):
    app.page.locator("#claveInput").fill(clave)
    app.page.locator("#claveBtn").click()


def test_primer_arranque_pide_la_clave_y_no_llama_a_la_api_sin_ella(abrir):
    app = abrir(clave=None)
    p = app.page
    expect(pantalla(app)).to_be_visible()
    expect(p.locator("#claveTitulo")).to_have_text("Introduce tu clave")
    p.wait_for_timeout(300)
    assert not app.peticiones_api
    expect(p.locator("#totalAmount")).to_have_text("0,00 €")
    introducir(app, CLAVE)
    expect(pantalla(app)).to_be_hidden()
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    assert p.evaluate("()=>localStorage.getItem('kashy-key')") == CLAVE
    assert not app.rechazos


def test_con_la_clave_guardada_no_la_vuelve_a_pedir(abrir):
    app = abrir(clave=None)
    p = app.page
    introducir(app, CLAVE)
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    p.reload()
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    expect(pantalla(app)).to_be_hidden()


def test_clave_vacia_no_se_envia(abrir):
    app = abrir(clave=None)
    introducir(app, "   ")
    expect(pantalla(app)).to_be_visible()
    assert not app.peticiones_api


def test_clave_incorrecta_da_401_y_la_vuelve_a_pedir(abrir):
    app = abrir(clave=None)
    p = app.page
    introducir(app, "mala")
    expect(p.locator("#claveError")).to_have_text("Clave incorrecta. Vuelve a introducirla.")
    expect(pantalla(app)).to_be_visible()
    assert app.rechazos
    assert p.evaluate("()=>localStorage.getItem('kashy-key')") is None
    assert not app.notion.escrituras
    introducir(app, CLAVE)
    expect(pantalla(app)).to_be_hidden()
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")


def test_clave_guardada_que_ya_no_vale_la_pide_al_abrir(abrir):
    app = abrir(clave="antigua")
    expect(pantalla(app)).to_be_visible()
    expect(app.page.locator("#claveError")).to_contain_text("Clave incorrecta")
    introducir(app, CLAVE)
    expect(app.page.locator("#totalAmount")).to_have_text("5925,00 €")


def test_401_a_mitad_de_uso_pide_la_clave_y_completa_la_escritura_una_sola_vez(app):
    p = app.page
    app.ir("registrar")
    p.locator("#inputAmt").fill("12,34")
    p.locator("#inputName").fill("Churros")
    app.clave_valida = "clave-nueva"  # la clave cambia en Vercel con la app abierta
    p.locator("#submitBtn").click()
    expect(pantalla(app)).to_be_visible()
    assert not app.escrituras()
    introducir(app, "clave-nueva")
    expect(app.toast()).to_contain_text("Gasto registrado")
    assert len(app.escrituras("POST")) == 1


def test_todas_las_llamadas_llevan_la_clave_y_ninguna_el_token_de_notion(app):
    for seccion in ("movimientos", "cuentas", "inversion", "registrar", "stats", "inicio"):
        app.ir(seccion)
    app.page.wait_for_load_state("networkidle")
    assert app.peticiones_api
    assert all(h.get("x-kashy-key") == CLAVE for h in app.peticiones_api)
    assert not any("authorization" in h for h in app.peticiones_api)


def test_la_clave_no_viaja_en_la_url(app):
    app.page.wait_for_load_state("networkidle")
    assert not any(CLAVE in r for r in app.rechazos)
    assert CLAVE not in app.page.url


def test_ningun_archivo_incluye_un_token_de_notion():
    from datos import RAIZ
    patron = re.compile(r"(ntn|secret)_[A-Za-z0-9]{20,}")
    archivos = list(RAIZ.glob("*.html")) + list((RAIZ / "api").glob("*.js"))
    assert len(archivos) >= 6
    assert not [str(f) for f in archivos if patron.search(f.read_text(encoding="utf-8"))]
