import re

import pytest
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


NOMBRE_LARGO = "Compra larguísima en una tienda con un nombre que no cabe de ninguna manera en la fila"


def largos(n):
    datos.gasto(n, NOMBRE_LARGO, "2026-11-12", 12345.67, cuenta=datos.REVOLUT)


def importe_visible(fila, importe, ancho, nombre=".mov-name"):
    """El importe se ve entero dentro de la pantalla y, si el nombre no cabe, es el nombre el que se recorta."""
    expect(fila.locator(importe)).to_be_visible()
    caja = fila.locator(importe).bounding_box()
    assert caja["x"] + caja["width"] <= ancho, caja
    return fila.locator(nombre).evaluate("e=>[e.scrollWidth>e.clientWidth,getComputedStyle(e).textOverflow]")


@pytest.mark.parametrize("ancho", [390, 320], ids=["iphone", "estrecho"])
@pytest.mark.parametrize("nombre", ["Remunerada (2,50%) → MyInvestor", NOMBRE_LARGO], ids=["transferencia", "movimiento"])
def test_nombre_largo_se_recorta_y_el_importe_se_ve(abrir, ancho, nombre):
    app = abrir(mas=largos)
    app.page.set_viewport_size({"width": ancho, "height": 844})
    app.ir("movimientos")
    fila = app.fila_mov(nombre)
    fila.wait_for()
    assert importe_visible(fila, ".mov-amount", ancho) == [True, "ellipsis"]
    # La fila ocupa justo el carril: no hay que deslizar para ver el importe
    rail = fila.locator("xpath=ancestor::div[contains(@class,'swipe')][1]")
    assert fila.bounding_box()["width"] <= rail.bounding_box()["width"]


@pytest.mark.parametrize("ancho", [390, 320], ids=["iphone", "estrecho"])
def test_nombre_largo_en_la_vista_de_cuenta(abrir, ancho):
    app = abrir(mas=largos)
    app.page.set_viewport_size({"width": ancho, "height": 844})
    app.ir("cuentas")
    t = app.desplegar_cuenta("Revolut Personal")
    fila = t.locator(".acc-mov-row", has_text=NOMBRE_LARGO)
    fila.wait_for()
    assert importe_visible(fila, ".amn-amt", ancho, ".amn-name") == [True, "ellipsis"]


def test_filas_de_inversion_dentro_de_la_pantalla(app):
    app.ir("inversion")
    filas = app.page.locator("#invHistList .mov-item")
    expect(filas).to_have_count(5)
    for i in range(5):
        caja = filas.nth(i).locator(".mov-amount").bounding_box()
        assert caja["x"] + caja["width"] <= 390, caja


def test_las_acciones_de_deslizar_siguen_fuera_hasta_deslizar(abrir):
    app = abrir(mas=largos)
    app.ir("movimientos")
    fila = app.fila_mov(NOMBRE_LARGO)
    fila.wait_for()
    assert fila.locator("xpath=ancestor::div[contains(@class,'swipe')][1]").evaluate("e=>e.scrollWidth>e.clientWidth")
