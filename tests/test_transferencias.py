import re

from playwright.sync_api import expect

import datos


def enviar(p, importe):
    p.locator("#transferAmt").fill(importe)
    p.locator("#transferOverlay .modal-confirm").click()


def aportaciones(app):
    return [f for f in app.notion.filas("cuentas") if (f["properties"].get("InvTipo", {}).get("select") or {}).get("name") == "Aportación"]


def test_crear_transferencia_desde_una_cuenta(app):
    p = app.page
    app.ir("cuentas")
    app.desplegar_cuenta("Ibercaja").locator(".acc-action", has_text="Mover").click()
    expect(p.locator("#transferFrom")).to_have_text("Ibercaja")
    p.locator("#transferToChips .chip", has_text="Efectivo").click()
    enviar(p, "40,50")
    expect(app.toast()).to_contain_text("Transferencia registrada")
    t = app.notion.filas("transfers")[-1]["properties"]
    assert t["Monto"]["number"] == 40.5
    assert t["Transferir Desde"]["relation"][0]["id"] == datos.IBERCAJA
    assert t["Transferir a"]["relation"][0]["id"] == datos.EFECTIVO
    assert t["Fecha"]["date"]["start"] == datos.HOY
    assert t["Nombre"]["title"][0]["plain_text"] == "Ibercaja → Efectivo"
    assert len(aportaciones(app)) == 2  # no va a MyInvestor: sin aportación
    # Los saldos siguen a la transferencia
    expect(app.cuenta("Efectivo").locator(".account-balance")).to_have_text("60,50 €")


def test_transferir_a_myinvestor_crea_aportacion_enlazada(app):
    p = app.page
    app.ir("cuentas")
    app.desplegar_cuenta("Ibercaja").locator(".acc-action", has_text="Mover").click()
    p.locator("#transferToChips .chip", has_text="MyInvestor").first.click()
    enviar(p, "75")
    expect(app.toast()).to_contain_text("Transferencia registrada")
    t = app.notion.filas("transfers")[-1]
    ap = aportaciones(app)[-1]["properties"]
    assert ap["InvImporte"]["number"] == 75
    assert ap["InvFecha"]["date"]["start"] == datos.HOY
    assert ap["InvTransferId"]["rich_text"][0]["plain_text"] == t["id"].replace("-", "")


def test_importe_invalido_no_escribe(app):
    p = app.page
    app.ir("cuentas")
    app.desplegar_cuenta("Ibercaja").locator(".acc-action", has_text="Mover").click()
    enviar(p, "")
    expect(app.toast()).to_have_class(re.compile(r"\berror\b"))
    assert not app.escrituras()


def abrir_edicion(app, nombre):
    app.ir("movimientos")
    app.fila_mov(nombre).locator(".mov-icon").click()
    expect(app.page.locator("#trEditOverlay")).to_have_class("modal-overlay show")


def guardar_edicion(app):
    app.page.locator("#trEditOverlay .modal-confirm").click()


def test_editar_transferencia(app):
    p = app.page
    abrir_edicion(app, "Ibercaja → Revolut Personal")
    expect(p.locator("#trEditAmt")).to_have_value("250")
    p.locator("#trEditAmt").fill("260,25")
    p.locator("#trEditDate").fill("2026-11-03")
    guardar_edicion(app)
    expect(app.toast()).to_contain_text("Transferencia actualizada")
    t = app.notion.pagina(datos.TR_REVOLUT)["properties"]
    assert t["Monto"]["number"] == 260.25 and t["Fecha"]["date"]["start"] == "2026-11-03"


def test_editar_transferencia_enlazada_actualiza_la_aportacion(app):
    p = app.page
    abrir_edicion(app, "Remunerada (2,50%) → MyInvestor")
    p.locator("#trEditAmt").fill("175")
    p.locator("#trEditDate").fill("2026-10-24")
    guardar_edicion(app)
    expect(app.toast()).to_contain_text("Transferencia actualizada")
    ap = app.notion.pagina(datos.AP_ENLAZADA)["properties"]
    assert ap["InvImporte"]["number"] == 175 and ap["InvFecha"]["date"]["start"] == "2026-10-24"


def test_cambiar_destino_fuera_de_myinvestor_borra_la_aportacion_con_deshacer(app):
    p = app.page
    abrir_edicion(app, "Remunerada (2,50%) → MyInvestor")
    p.locator("#trEditToChips .chip", has_text="Efectivo").click()
    guardar_edicion(app)
    expect(app.toast()).to_contain_text("aportación eliminada")
    assert not app.notion.activa(datos.AP_ENLAZADA)
    app.deshacer()
    expect(app.toast()).to_contain_text("Restaurado")
    assert app.notion.activa(datos.AP_ENLAZADA)


def test_cambiar_destino_a_myinvestor_crea_aportacion_enlazada(app):
    p = app.page
    abrir_edicion(app, "Ibercaja → Revolut Personal")
    p.locator("#trEditToChips .chip").filter(has_text="MyInvestor").first.click()
    guardar_edicion(app)
    expect(app.toast()).to_contain_text("Transferencia actualizada")
    ap = aportaciones(app)[-1]["properties"]
    assert ap["InvImporte"]["number"] == 250
    assert ap["InvTransferId"]["rich_text"][0]["plain_text"] == datos.TR_REVOLUT


def test_borrar_transferencia_y_deshacer(app):
    app.ir("movimientos")
    app.borrar_fila(app.fila_mov("Ibercaja → Revolut Personal"))
    expect(app.toast()).to_contain_text("Transferencia eliminada")
    assert not app.notion.activa(datos.TR_REVOLUT)
    expect(app.fila_mov("Ibercaja → Revolut Personal")).to_have_count(0)
    app.deshacer()
    expect(app.toast()).to_contain_text("Restaurado")
    assert app.notion.activa(datos.TR_REVOLUT)
    expect(app.fila_mov("Ibercaja → Revolut Personal")).to_be_visible()


def test_borrar_transferencia_enlazada_borra_y_restaura_las_dos(app):
    app.ir("movimientos")
    app.borrar_fila(app.fila_mov("Remunerada (2,50%) → MyInvestor"))
    expect(app.toast()).to_contain_text("Transferencia y aportación eliminadas")
    assert not app.notion.activa(datos.TR_APORTACION) and not app.notion.activa(datos.AP_ENLAZADA)
    app.deshacer()
    expect(app.toast()).to_contain_text("Restaurado")
    assert app.notion.activa(datos.TR_APORTACION) and app.notion.activa(datos.AP_ENLAZADA)


def test_transferencia_antigua_a_myinvestor_avisa_sin_tocar_aportaciones(abrir):
    app = abrir(mas=lambda n: datos.transferencia(n, datos.IBERCAJA, datos.MYINVESTOR, 80, "2026-09-01", id=datos.TR_ANTIGUA))
    p = app.page
    abrir_edicion(app, "Ibercaja → MyInvestor")
    expect(p.locator("#trEditAviso")).to_be_visible()
    p.locator("#trEditOverlay .modal-cancel").click()
    app.borrar_fila(app.fila_mov("Ibercaja → MyInvestor"))
    expect(app.toast()).to_contain_text("revisa la aportación en Inversión")
    assert app.notion.activa(datos.AP_ANTIGUA)
