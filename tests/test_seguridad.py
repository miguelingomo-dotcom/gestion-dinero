"""La garantía de que las pruebas no tocan datos reales."""
import pytest
from notion_mock import APP_ORIGIN


def test_la_app_corre_en_un_origen_inexistente(app):
    assert app.page.url.startswith(APP_ORIGIN)


@pytest.mark.parametrize("url", [
    "https://api.notion.com/v1/databases/x/query",
    "https://gestion-dinero-dusky.vercel.app/api/query?dbId=x",
])
def test_una_llamada_real_se_bloquea(app, url):
    resultado = app.page.evaluate(
        "u=>fetch(u,{method:'POST',mode:'no-cors',body:'{}'}).then(()=>'salió').catch(()=>'bloqueada')", url)
    assert resultado == "bloqueada"
    assert url in app.externos
    app.externos.remove(url)  # este intento es provocado por la prueba


def test_abrir_y_navegar_no_sale_a_la_red(app):
    for seccion in ("movimientos", "cuentas", "inversion", "registrar", "stats", "inicio"):
        app.ir(seccion)
    app.page.wait_for_load_state("networkidle")
    assert all("fonts.g" in u for u in app.externos), app.externos
