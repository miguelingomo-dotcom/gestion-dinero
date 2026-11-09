import re

from playwright.sync_api import expect

import datos


def test_lista_ordenada_con_transferencias(app):
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_contain_text("-84,50 €")
    expect(app.fila_mov("Nómina noviembre")).to_contain_text("+2000,00 €")
    expect(app.fila_mov("Ibercaja → Revolut Personal")).to_contain_text("250,00 €")
    nombres = p.locator("#recentMovs .mov-name").all_inner_texts()
    assert nombres[:2] == ["Repsol", "Mercadona"], nombres  # lo más reciente primero
    expect(p.locator(".mov-daygroup").first).to_be_visible()


def test_editar_movimiento(app):
    p = app.page
    app.ir("movimientos")
    app.fila_mov("Mercadona").locator(".mov-info").click()
    expect(p.locator("#editOverlay")).to_have_class("modal-overlay show")
    expect(p.locator("#editAmt")).to_have_value("84.5")
    expect(p.locator("#editName")).to_have_value("Mercadona")
    p.locator("#editAmt").fill("90,10")
    p.locator("#editName").fill("Mercadona grande")
    p.locator("#editDate").fill("2026-11-11")
    p.locator("#editAccChips .chip", has_text="Revolut Personal").click()
    p.locator("#editOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Movimiento actualizado")
    props = app.notion.pagina(datos.MOV_MERCADONA)["properties"]
    assert props["Gasto"]["number"] == 90.1
    assert props["Nombre"]["title"][0]["plain_text"] == "Mercadona grande"
    assert props["Fecha"]["date"]["start"] == "2026-11-11"
    assert props["Cuenta"]["relation"][0]["id"] == datos.REVOLUT
    expect(app.fila_mov("Mercadona grande")).to_contain_text("-90,10 €")


def test_editar_ingreso_conserva_el_tipo(app):
    p = app.page
    app.ir("movimientos")
    app.fila_mov("Nómina noviembre").locator(".mov-info").click()
    p.locator("#editAmt").fill("2100")
    p.locator("#editOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Movimiento actualizado")
    props = app.notion.pagina(datos.MOV_NOMINA)["properties"]
    assert props["Ingreso"]["number"] == 2100 and "Gasto" not in props


def test_borrar_movimiento_y_deshacer(app):
    app.ir("movimientos")
    app.borrar_fila(app.fila_mov("Mercadona"))
    expect(app.toast()).to_contain_text("Movimiento eliminado")
    assert not app.notion.activa(datos.MOV_MERCADONA)
    expect(app.fila_mov("Mercadona")).to_have_count(0)
    app.deshacer()
    expect(app.toast()).to_contain_text("Restaurado")
    assert app.notion.activa(datos.MOV_MERCADONA)
    expect(app.fila_mov("Mercadona")).to_be_visible()


def test_error_al_borrar_conserva_la_fila(app):
    app.ir("movimientos")
    app.notion.fallos[datos.MOV_MERCADONA] = (500, "internal_server_error")
    app.borrar_fila(app.fila_mov("Mercadona"))
    expect(app.toast()).to_have_class(re.compile(r"\berror\b"))
    expect(app.fila_mov("Mercadona")).to_be_visible()


def filas_son(app, *nombres):
    """Espera a que la lista muestre exactamente esas filas, en ese orden."""
    expect(app.page.locator("#recentMovs .mov-name")).to_have_text(list(nombres))


def test_filtro_por_tipo(app):
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    p.locator("#movTipoChips .chip", has_text="Gastos").click()
    filas_son(app, "Repsol", "Mercadona", "Cena con amigos", "Pizza", "Seguro", "Sofá viejo")
    p.locator("#movTipoChips .chip", has_text="Ingresos").click()
    filas_son(app, "Nómina noviembre", "Nómina octubre")
    p.locator("#movTipoChips .chip", has_text="Transferencias").click()
    filas_son(app, "Ibercaja → Revolut Personal", "MyInvestor Remunerada (2,50%) → MyInvestor")
    p.locator("#movTipoChips .chip", has_text="Todos").click()
    expect(app.fila_mov("Mercadona")).to_be_visible()


def test_filtro_por_cuenta_incluye_transferencias_de_ambos_lados(app):
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    p.locator("#movFilterChips .chip", has_text="Revolut Personal").click()
    filas_son(app, "Repsol", "Ibercaja → Revolut Personal")


def test_filtro_por_categoria_oculta_transferencias(app):
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    p.locator("#movCatChips .chip", has_text="Restaurantes").click()
    filas_son(app, "Cena con amigos", "Pizza")


def test_filtros_combinados_y_estado_vacio(app):
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    p.locator("#movFilterChips .chip", has_text="Efectivo").click()
    expect(p.locator("#recentMovs")).to_contain_text("Sin movimientos")
    p.locator("#movFilterChips .chip", has_text="Ibercaja").click()
    p.locator("#movTipoChips .chip", has_text="Ingresos").click()
    filas_son(app, "Nómina noviembre", "Nómina octubre")


def test_fallo_en_transferencias_no_oculta_los_movimientos(app):
    app.notion.fallar_consultas.add(datos.BASES["transfers"])
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
