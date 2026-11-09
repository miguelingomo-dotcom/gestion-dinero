import pytest
from playwright.sync_api import expect

import datos


def rellenar(p, importe, nombre):
    p.locator("#inputAmt").fill(importe)
    p.locator("#inputName").fill(nombre)


def elegir(p, cuenta_txt, cat_id):
    p.locator("#accountChips .chip", has_text=cuenta_txt).click()
    p.locator('#catGrid .cat-item[data-cat="%s"]' % cat_id).click()


def test_registrar_gasto_y_deshacer(app):
    p = app.page
    app.ir("registrar")
    rellenar(p, "12,34", "Churros")
    elegir(p, "Ibercaja", datos.CAT_RESTAURANTES)
    p.locator("#submitBtn").click()
    expect(app.toast()).to_contain_text("Gasto registrado")
    w = app.escrituras("POST")[-1]["cuerpo"]["properties"]
    assert w["Nombre"]["title"][0]["text"]["content"] == "Churros"
    assert w["Gasto"]["number"] == 12.34 and "Ingreso" not in w
    assert w["Tipo"]["select"]["name"] == "Expense"
    assert w["Fecha"]["date"]["start"] == datos.HOY
    assert w["Cuenta"]["relation"][0]["id"] == datos.IBERCAJA
    assert w["Fuente de Gasto"]["relation"][0]["id"] == datos.CAT_RESTAURANTES
    expect(p.locator("#inputAmt")).to_have_value("")
    assert len(app.notion.filas("movs")) == 9
    # Deshacer archiva la página y devuelve lo escrito al formulario
    app.deshacer()
    expect(app.toast()).to_contain_text("Registro deshecho")
    assert len(app.notion.filas("movs")) == 8
    expect(p.locator("#inputAmt")).to_have_value("12,34")
    expect(p.locator("#inputName")).to_have_value("Churros")


def test_registrar_ingreso_y_deshacer(app):
    p = app.page
    app.ir("registrar")
    p.locator("#btnI").click()
    rellenar(p, "50", "Venta")
    elegir(p, "Revolut Personal", datos.CAT_NOMINA)
    p.locator("#submitBtn").click()
    expect(app.toast()).to_contain_text("Ingreso registrado")
    w = app.escrituras("POST")[-1]["cuerpo"]["properties"]
    assert w["Ingreso"]["number"] == 50 and "Gasto" not in w
    assert w["Tipo"]["select"]["name"] == "Income"
    assert w["Fuente de Ingreso"]["relation"][0]["id"] == datos.CAT_NOMINA
    assert w["Cuenta"]["relation"][0]["id"] == datos.REVOLUT
    app.deshacer()
    expect(app.toast()).to_contain_text("Registro deshecho")
    assert len(app.notion.filas("movs")) == 8


def test_con_fecha_de_ayer(app):
    p = app.page
    app.ir("registrar")
    rellenar(p, "5", "Café")
    p.locator('.chip[data-fecha="ayer"]').click()
    p.locator("#submitBtn").click()
    expect(app.toast()).to_contain_text("Gasto registrado")
    assert app.escrituras("POST")[-1]["cuerpo"]["properties"]["Fecha"]["date"]["start"] == "2026-11-14"


@pytest.mark.parametrize("importe,nombre,mensaje", [
    ("", "Algo", "Importe inválido"),
    ("0", "Algo", "Importe inválido"),
    ("10", "", "Introduce un nombre"),
])
def test_validacion_no_escribe_nada(app, importe, nombre, mensaje):
    p = app.page
    app.ir("registrar")
    rellenar(p, importe, nombre)
    p.locator("#submitBtn").click()
    expect(app.toast()).to_contain_text(mensaje)
    assert not app.escrituras()


def test_registrado_aparece_en_movimientos_e_inicio(app):
    p = app.page
    app.ir("registrar")
    rellenar(p, "10", "Churros")
    p.locator("#submitBtn").click()
    expect(app.toast()).to_contain_text("Gasto registrado")
    app.ir("movimientos")
    expect(app.fila_mov("Churros")).to_be_visible()
    app.ir("inicio")
    expect(p.locator("#resGasto")).to_have_text("-154,50 €")
