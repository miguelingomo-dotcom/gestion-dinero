import re

from playwright.sync_api import expect

import datos


def fila(app, texto):
    return app.page.locator("#invHistList .mov-item", has_text=texto).first


def fila_por_id(app, id):
    """Las filas no llevan su id a la vista: se localiza el botón por su onclick."""
    return app.page.locator("#invHistList .mov-item:has(.del-btn[onclick*='%s'])" % id)


def test_historial_y_valor_de_cartera(app):
    p = app.page
    app.ir("inversion")
    expect(p.locator("#invHistList .mov-item")).to_have_count(5)
    expect(p.locator("#invFondos .fondo-row").first).to_contain_text("S&P 500")
    expect(p.locator("#invFondos")).to_contain_text("1082,50 €")  # 1000 + 55 % de los 150 aportados después


def test_aportacion_mensual_crea_transferencia_y_aportacion_enlazadas(app):
    p = app.page
    app.ir("inversion")
    expect(p.locator("#invHistList .mov-item")).to_have_count(5)
    p.locator("#sec-inversion .sus-btn", has_text="Registrar").click()
    expect(app.toast()).to_contain_text("Aportación de 150€")
    t = app.notion.filas("transfers")[-1]
    assert t["properties"]["Nombre"]["title"][0]["plain_text"] == "MyInvestor Remunerada → MyInvestor"
    assert t["properties"]["Monto"]["number"] == 150
    assert t["properties"]["Transferir Desde"]["relation"][0]["id"] == datos.REMUNERADA
    assert t["properties"]["Transferir a"]["relation"][0]["id"] == datos.MYINVESTOR
    ap = [f for f in app.notion.filas("cuentas") if f["properties"].get("Nombre", {}).get("title", [{}])[0].get("plain_text", "").startswith("Aportación mensual")]
    assert len(ap) == 1
    assert ap[0]["properties"]["InvImporte"]["number"] == 150
    assert ap[0]["properties"]["InvFecha"]["date"]["start"] == datos.HOY
    assert ap[0]["properties"]["InvTransferId"]["rich_text"][0]["plain_text"] == t["id"]
    expect(p.locator("#invHistList .mov-item")).to_have_count(6)


def test_nueva_aportacion_manual(app):
    p = app.page
    app.ir("inversion")
    p.locator('#sec-inversion .submit-btn[onclick*="Aportación"]').click()
    p.locator("#invAmt").fill("33")
    p.locator("#invOverlay .modal-confirm").click()
    expect(app.toast()).to_have_class(re.compile(r"\bsuccess\b"))
    assert app.escrituras("POST")[-1]["cuerpo"]["properties"]["InvImporte"]["number"] == 33


def test_actualizar_valor_guarda_solo_los_fondos_cambiados(app):
    p = app.page
    app.ir("inversion")
    expect(p.locator("#invHistList .mov-item")).to_have_count(5)
    p.locator('#sec-inversion .submit-btn[onclick*="Valor Cartera"]').click()
    p.locator("#invAmtF1").fill("600")
    p.locator("#invOverlay .modal-confirm").click()
    expect(app.toast()).to_have_class(re.compile(r"\bsuccess\b"))
    posts = app.escrituras("POST")
    assert len(posts) == 1
    assert posts[0]["cuerpo"]["properties"]["InvFondo"]["select"]["name"] == "MSCI World"
    assert posts[0]["cuerpo"]["properties"]["InvImporte"]["number"] == 600


def test_borrar_aportacion_enlazada_borra_la_transferencia_y_deshacer_restaura(app):
    app.ir("inversion")
    app.borrar_fila(fila_por_id(app, datos.AP_ENLAZADA))
    expect(app.toast()).to_contain_text("Aportación y transferencia eliminadas")
    assert not app.notion.activa(datos.AP_ENLAZADA) and not app.notion.activa(datos.TR_APORTACION)
    app.deshacer()
    expect(app.toast()).to_contain_text("Restaurado")
    assert app.notion.activa(datos.AP_ENLAZADA) and app.notion.activa(datos.TR_APORTACION)


def test_borrar_aportacion_antigua_avisa_y_no_toca_transferencias(app):
    app.ir("inversion")
    transferencias = len(app.notion.filas("transfers"))
    app.borrar_fila(fila_por_id(app, datos.AP_ANTIGUA))
    expect(app.toast()).to_contain_text("Revisa la transferencia en Movimientos")
    assert not app.notion.activa(datos.AP_ANTIGUA)
    assert len(app.notion.filas("transfers")) == transferencias
    app.deshacer()
    expect(app.toast()).to_contain_text("Restaurado")
    assert app.notion.activa(datos.AP_ANTIGUA)


def test_borrar_aportacion_si_la_transferencia_ya_no_existe(app):
    app.ir("inversion")
    app.notion.pagina(datos.TR_APORTACION)["archived"] = True
    app.borrar_fila(fila_por_id(app, datos.AP_ENLAZADA))
    expect(app.toast()).to_have_text(re.compile(r"^Aportación eliminada"))
    app.deshacer()
    expect(app.toast()).to_contain_text("Restaurado")
    assert app.notion.activa(datos.AP_ENLAZADA)
    assert not app.notion.activa(datos.TR_APORTACION)  # no se resucita


def test_fallo_real_al_borrar_la_transferencia_revierte_la_aportacion(app):
    app.ir("inversion")
    app.notion.fallos[datos.TR_APORTACION] = (500, "internal_server_error")
    app.borrar_fila(fila_por_id(app, datos.AP_ENLAZADA))
    expect(app.toast()).to_have_class(re.compile(r"\berror\b"))
    assert app.notion.activa(datos.AP_ENLAZADA)


def test_borrar_valor_de_cartera_sigue_igual(app):
    app.ir("inversion")
    app.borrar_fila(fila_por_id(app, datos.VAL_SP500))
    expect(app.toast()).to_contain_text("Registro eliminado")


def editar(app, id, importe, fecha):
    p = app.page
    p.evaluate("id=>openEditInv(id)", id)
    p.locator("#invAmt").fill(importe)
    p.locator("#invDate").fill(fecha)
    p.locator("#invOverlay .modal-confirm").click()


def test_editar_aportacion_enlazada_actualiza_la_transferencia(app):
    app.ir("inversion")
    expect(app.page.locator("#invHistList .mov-item")).to_have_count(5)
    editar(app, datos.AP_ENLAZADA, "175", "2026-10-24")
    expect(app.toast()).to_have_class(re.compile(r"\bsuccess\b"))
    t = app.notion.pagina(datos.TR_APORTACION)["properties"]
    assert t["Monto"]["number"] == 175 and t["Fecha"]["date"]["start"] == "2026-10-24"
    assert app.notion.pagina(datos.AP_ENLAZADA)["properties"]["InvImporte"]["number"] == 175


def test_editar_aportacion_antigua_solo_toca_la_aportacion(app):
    app.ir("inversion")
    expect(app.page.locator("#invHistList .mov-item")).to_have_count(5)
    editar(app, datos.AP_ANTIGUA, "120", "2026-01-24")
    expect(app.toast()).to_have_class(re.compile(r"\bsuccess\b"))
    assert [e["id"] for e in app.escrituras("PATCH")] == [datos.AP_ANTIGUA]


def test_editar_aportacion_avisa_si_falla_la_transferencia(app):
    app.ir("inversion")
    expect(app.page.locator("#invHistList .mov-item")).to_have_count(5)
    app.notion.fallos[datos.TR_APORTACION] = (500, "internal_server_error")
    editar(app, datos.AP_ENLAZADA, "180", "2026-10-25")
    expect(app.toast()).to_contain_text("no se pudo actualizar la transferencia")
    assert app.notion.pagina(datos.AP_ENLAZADA)["properties"]["InvImporte"]["number"] == 180
