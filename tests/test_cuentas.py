import re

import pytest
from playwright.sync_api import expect

import datos


def test_saldos_de_las_cuentas(app):
    app.ir("cuentas")
    p = app.page
    expect(p.locator("#accountCards .account-card")).to_have_count(5)
    for nombre, saldo in [("Ibercaja", "2790,00 €"), ("Revolut Personal", "290,00 €"), ("Efectivo", "20,00 €")]:
        expect(app.cuenta(nombre).locator(".account-balance")).to_have_text(saldo)


def test_myinvestor_muestra_el_valor_de_cartera(app):
    app.ir("cuentas")
    expect(app.cuenta("MyInvestor").locator(".account-balance")).to_have_text("1900,00 €")


def test_cuenta_inactiva_oculta_y_visible_bajo_demanda(app):
    p = app.page
    app.ir("cuentas")
    expect(p.locator("#accountCards")).not_to_contain_text("Sabadell")
    p.locator("#btnInactivas").click()
    expect(p.locator("#accountCardsInactive")).to_contain_text("Sabadell")


def test_desplegar_una_cuenta_muestra_sus_movimientos(app):
    p = app.page
    app.ir("cuentas")
    t = app.desplegar_cuenta("Revolut Personal")
    filas = t.locator(".acc-mov-row")
    expect(filas).to_have_count(1)
    expect(filas.first).to_contain_text("Repsol")
    expect(filas.first).to_contain_text("-60,00 €")
    # Solo una desplegada a la vez
    app.desplegar_cuenta("Ibercaja")
    expect(t).not_to_have_class(re.compile(r"\bexpanded\b"))


def test_cuenta_sin_movimientos(app):
    app.ir("cuentas")
    t = app.desplegar_cuenta("Efectivo")
    expect(t).to_contain_text("Sin movimientos registrados")


def test_carrusel_de_inicio_abre_la_cuenta(app):
    p = app.page
    app.ir("cuentas")
    expect(app.cuenta("Ibercaja").locator(".account-balance")).to_have_text("2790,00 €")
    app.ir("inicio")
    p.locator("#quickAccounts .qa-card", has_text="Ibercaja").click()
    expect(p.locator("#sec-cuentas")).to_have_class(re.compile(r"\bactive\b"))
    expect(app.cuenta("Ibercaja")).to_have_class(re.compile(r"\bexpanded\b"))


def test_desactivar_cuenta(app):
    p = app.page
    app.ir("cuentas")
    app.desplegar_cuenta("Efectivo").locator(".acc-action", has_text="Desactivar").click()
    p.locator("#accionConfirmar").click()
    expect(app.toast()).to_contain_text("Efectivo")
    assert app.notion.pagina(datos.EFECTIVO)["properties"]["Estado"]["select"]["name"] == "🔴 Inactivo"
    expect(p.locator("#accountCards")).not_to_contain_text("Efectivo")


def abrir_fila(app, cuenta, texto):
    t = app.desplegar_cuenta(cuenta)
    t.locator(".acc-mov-row", has_text=texto).click()
    return t


def test_editar_movimiento_desde_la_vista_de_cuenta(app):
    p = app.page
    app.ir("cuentas")
    abrir_fila(app, "Ibercaja", "Mercadona")
    expect(p.locator("#editOverlay")).to_have_class("modal-overlay show")
    expect(p.locator("#editAmt")).to_have_value("84.5")
    expect(p.locator("#editName")).to_have_value("Mercadona")
    assert not app.escrituras("POST")  # leer una página no escribe nada
    p.locator("#editAmt").fill("100")
    p.locator("#editOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Movimiento actualizado")
    assert app.notion.pagina(datos.MOV_MERCADONA)["properties"]["Gasto"]["number"] == 100
    # Al guardar se ven el importe y el saldo nuevos, con la cuenta aún desplegada
    expect(app.cuenta("Ibercaja")).to_have_class(re.compile(r"\bexpanded\b"))
    expect(app.cuenta("Ibercaja").locator(".acc-mov-row", has_text="Mercadona")).to_contain_text("-100,00 €")
    expect(app.cuenta("Ibercaja").locator(".account-balance")).to_have_text("2774,50 €")


def test_editar_ingreso_desde_la_vista_de_cuenta(app):
    p = app.page
    app.ir("cuentas")
    abrir_fila(app, "Ibercaja", "Nómina noviembre")
    expect(p.locator("#editTitle")).to_contain_text("Ingreso")
    expect(p.locator("#editAmt")).to_have_value("2000")


def test_mover_el_movimiento_a_otra_cuenta_lo_saca_de_la_lista(app):
    p = app.page
    app.ir("cuentas")
    abrir_fila(app, "Ibercaja", "Mercadona")
    p.locator("#editAccChips .chip", has_text="Efectivo").click()
    p.locator("#editOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Movimiento actualizado")
    expect(app.cuenta("Ibercaja").locator(".acc-mov-row", has_text="Nómina noviembre")).to_be_visible()
    expect(app.cuenta("Ibercaja").locator(".acc-mov-row", has_text="Mercadona")).to_have_count(0)
    expect(app.cuenta("Efectivo").locator(".account-balance")).to_have_text("-64,50 €")


@pytest.mark.parametrize("fallo", [(500, "internal_server_error"), (404, "object_not_found")], ids=["error", "no_existe"])
def test_si_no_se_puede_leer_avisa_y_no_escribe(app, fallo):
    p = app.page
    app.ir("cuentas")
    app.notion.fallos[datos.MOV_MERCADONA] = fallo
    abrir_fila(app, "Ibercaja", "Mercadona")
    expect(app.toast()).to_have_class(re.compile(r"\berror\b"))
    expect(p.locator("#editOverlay")).not_to_have_class(re.compile(r"\bshow\b"))
    assert not app.escrituras("POST")


def test_movimiento_borrado_en_otro_sitio_no_se_abre(app):
    p = app.page
    app.ir("cuentas")
    t = app.desplegar_cuenta("Ibercaja")
    t.locator(".acc-mov-row", has_text="Mercadona").wait_for()
    app.notion.pagina(datos.MOV_MERCADONA)["archived"] = True
    t.locator(".acc-mov-row", has_text="Mercadona").click()
    expect(app.toast()).to_have_class(re.compile(r"\berror\b"))
    expect(p.locator("#editOverlay")).not_to_have_class(re.compile(r"\bshow\b"))


def test_desde_movimientos_no_hace_falta_leer_ni_recarga_cuentas(app):
    p = app.page
    app.ir("movimientos")
    app.fila_mov("Mercadona").locator(".mov-icon").click()
    expect(p.locator("#editOverlay")).to_have_class("modal-overlay show")
    p.locator("#editOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Movimiento actualizado")
    expect(p.locator("#sec-movimientos")).to_have_class(re.compile(r"\bactive\b"))
