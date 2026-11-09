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


@pytest.mark.xfail(strict=True, reason="FALLO CONOCIDO: el movimiento no está en movsCache y openEditMovement lo pide con "
                                       "nFetch('/pages/id','GET'), que hace un POST vacío a /api/page y Notion lo rechaza")
def test_editar_movimiento_desde_la_vista_de_cuenta(app):
    app.ir("cuentas")
    t = app.desplegar_cuenta("Revolut Personal")
    t.locator(".acc-mov-row").first.click()
    expect(app.page.locator("#editOverlay")).to_have_class("modal-overlay show", timeout=1500)
