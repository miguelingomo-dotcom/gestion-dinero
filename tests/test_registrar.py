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


# ── Rediseño: sugerencia del comercio, importe, tipo, logos y momento de éxito ──
CAT_CAFE = "38621c54013f819eb838ff6f8332fbc6"


def seleccionada(p):
    return p.locator("#catGrid .cat-item.selected").get_attribute("data-cat")


def test_el_comercio_sugiere_su_categoria_aunque_tenga_una_errata(app):
    p = app.page
    app.ir("registrar")
    p.locator("#inputName").fill("mercadna")
    expect(p.locator("#regSugerencia")).to_contain_text("Mercadona · Supermercado")
    expect(p.locator("#regSugerencia .kficha.logo")).to_have_count(1)
    assert seleccionada(p) == datos.CAT_SUPER
    p.locator("#inputName").fill("café en starbucks")
    expect(p.locator("#regSugerencia")).to_contain_text("Starbucks")
    assert seleccionada(p) == CAT_CAFE


def test_la_sugerencia_no_pisa_una_categoria_elegida_a_mano(app):
    p = app.page
    app.ir("registrar")
    p.locator('#catGrid .cat-item[data-cat="%s"]' % datos.CAT_OCIO).click()
    p.locator("#inputName").fill("spotify")
    expect(p.locator("#regSugerencia")).to_contain_text("Spotify")  # se enseña igual
    assert seleccionada(p) == datos.CAT_OCIO


def test_el_euro_va_pegado_al_importe_y_el_tipo_cambia_su_color(app):
    p = app.page
    app.ir("registrar")
    for valor in ["", "7", "1234,56"]:
        p.locator("#inputAmt").fill(valor)
        hueco = p.evaluate("()=>document.querySelector('.importe-eur').getBoundingClientRect().left-document.getElementById('inputAmt').getBoundingClientRect().right")
        assert -2 <= hueco <= 14, (valor, hueco)
    p.locator("#btnI").click()
    expect(p.locator("#regTipo")).to_have_class("type-toggle der")
    expect(p.locator("#inputAmt")).to_have_class("amount-in ing")
    expect(p.locator("#submitBtn")).to_have_class("submit-btn ing")


def test_pagos_con_logo_y_formato_espanol(app):
    p = app.page
    app.ir("registrar")
    spotify = p.locator(".sus-card-wrap", has=p.locator(".sus-name", has_text="Spotify"))
    expect(spotify.locator(".sus-icon .kficha.marca svg")).to_have_count(1)
    expect(spotify.locator(".sus-amount")).to_have_text("-20,99 €")
    letra = p.locator(".sus-card-wrap", has=p.locator(".sus-name", has_text="Letra Coche"))
    expect(letra.locator(".sus-icon .kficha.cat")).to_have_count(1)
    # Cuentas con su logo, sin emojis
    expect(p.locator("#accountChips .chip", has_text="Ibercaja").locator(".kficha.logo")).to_have_count(1)


def test_el_exito_lleva_la_ficha_del_comercio(app):
    p = app.page
    app.ir("registrar")
    rellenar(p, "3,20", "Starbucks")
    p.locator("#submitBtn").click()
    expect(app.toast()).to_contain_text("Gasto registrado")
    expect(p.locator("#successBadgeEmo .kficha.marca")).to_have_count(1)


@pytest.mark.parametrize("ancho", [390, 320], ids=["iphone", "estrecho"])
def test_el_importe_grande_nunca_se_corta(app, ancho):
    p = app.page
    p.set_viewport_size({"width": ancho, "height": 800})
    app.ir("registrar")
    for valor in ["123456,78", "98765432,10"]:
        p.locator("#inputAmt").fill(valor)
        r = p.evaluate("""()=>{const i=document.getElementById('inputAmt'),e=document.querySelector('.importe-eur');
          const a=i.getBoundingClientRect(),b=e.getBoundingClientRect();
          return {cabe:i.scrollWidth<=i.clientWidth+1,dentro:a.left>=0&&b.right<=innerWidth}}""")
        assert r["cabe"] and r["dentro"], (valor, r)
