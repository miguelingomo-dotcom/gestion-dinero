"""Capturas de referencia de cada pestaña en los dos temas.
Compararlas: se ejecutan con el resto de la suite. Tras un cambio visual deliberado: pytest tests -k capturas --update-baseline"""
import pytest

from visual import comparar


@pytest.mark.parametrize("seccion", ["inicio", "movimientos", "registrar", "stats", "cuentas", "inversion"])
def test_capturas(app, seccion, tema, request):
    app.ir(seccion)
    p = app.page
    # Tareas diferidas del arranque (carrusel, chips de color): hasta 1,4 s
    p.wait_for_timeout(1700)
    p.wait_for_load_state("networkidle")
    p.evaluate("()=>{document.activeElement&&document.activeElement.blur();window.scrollTo(0,0)}")
    # Ventana tan alta como la página: la barra inferior, que es fija, queda abajo y no tapa contenido
    alto = p.evaluate("()=>document.documentElement.scrollHeight")
    p.set_viewport_size({"width": 390, "height": alto})
    p.wait_for_timeout(100)
    png = p.screenshot(animations="disabled", caret="hide")
    error = comparar("%s-%s" % (seccion, "claro" if tema == "light" else "oscuro"), png, request.config.getoption("--update-baseline"))
    assert error is None, error


def test_capturas_pantalla_de_clave(abrir, tema, request):
    p = abrir(clave=None).page
    p.wait_for_timeout(300)
    png = p.screenshot(animations="disabled", caret="hide")
    error = comparar("clave-%s" % ("claro" if tema == "light" else "oscuro"), png, request.config.getoption("--update-baseline"))
    assert error is None, error
