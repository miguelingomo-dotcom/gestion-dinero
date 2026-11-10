"""Movimientos: buscador (nombre, categoría o cuenta, combinable con los filtros) y logos de comercios en las filas."""
from playwright.sync_api import expect

import datos


def nombres(app):
    return app.page.locator("#recentMovs .mov-name")


def buscar(app, texto):
    app.page.locator("#movBuscar").fill(texto)


def test_buscar_por_nombre(app):
    app.ir("movimientos")
    expect(app.fila_mov("Repsol")).to_be_visible()
    buscar(app, "merca")
    expect(nombres(app)).to_have_text(["Mercadona"])
    # Sin distinguir mayúsculas
    buscar(app, "NÓMINA")
    expect(nombres(app)).to_have_text(["Nómina noviembre", "Nómina octubre"])


def test_buscar_por_categoria(app):
    app.ir("movimientos")
    buscar(app, "restaurante")
    expect(nombres(app)).to_have_text(["Cena con amigos", "Pizza"])


def test_buscar_por_cuenta_incluye_sus_transferencias(app):
    app.ir("movimientos")
    buscar(app, "revolut")
    expect(nombres(app)).to_have_text(["Repsol", "Ibercaja → Revolut Personal"])


def test_buscar_se_combina_con_los_filtros(app):
    p = app.page
    app.ir("movimientos")
    p.locator("#movTipoChips .chip", has_text="Gastos").click()
    buscar(app, "revolut")
    expect(nombres(app)).to_have_text(["Repsol"])


def test_sin_resultados_y_borrar_la_busqueda(app):
    p = app.page
    app.ir("movimientos")
    buscar(app, "zzz")
    expect(p.locator("#recentMovs")).to_contain_text("Sin resultados")
    expect(p.locator("#recentMovs")).to_contain_text("«zzz»")
    p.locator("#movBuscarX").click()
    expect(app.fila_mov("Repsol")).to_be_visible()
    expect(p.locator("#movBuscar")).to_have_value("")
    expect(p.locator("#movBuscarX")).to_be_hidden()


def _comercios(notion):
    datos.gasto(notion, "🎵 Spotify", "2026-11-13", 10.99, cat=datos.CAT_SUSCRIPCIONES)
    datos.gasto(notion, "macdonalds", "2026-11-13", 9.5, cat=datos.CAT_RESTAURANTES)


def test_logos_de_comercios_y_categorias_en_las_filas(abrir):
    app = abrir(mas=_comercios)
    app.ir("movimientos")
    # Logo oficial (imagen incluida en la app) para Mercadona
    expect(app.fila_mov("Mercadona").locator(".mov-icon .kficha.logo img")).to_have_count(1)
    # Logo de Simple Icons; el emoji del nombre en Notion no se enseña
    spotify = app.fila_mov("Spotify")
    expect(spotify.locator(".mov-icon .kficha.marca svg")).to_have_count(1)
    expect(spotify.locator(".mov-name")).to_have_text("Spotify")
    # Una errata también se reconoce
    expect(app.fila_mov("macdonalds").locator(".mov-icon .kficha.marca")).to_have_count(1)
    # Sin comercio conocido: el icono de su categoría, y debajo la categoría y la cuenta
    repsol = app.fila_mov("Repsol")
    expect(repsol.locator(".mov-icon .kficha.cat")).to_have_count(1)
    expect(repsol.locator(".mov-date")).to_have_text("Gasolina · Revolut Personal")
    # Transferencia: icono morado y sin categoría
    tr = app.fila_mov("Ibercaja → Revolut Personal")
    expect(tr.locator(".mov-date")).to_have_text("Transferencia")
    expect(tr.locator(".mov-amount")).to_have_class("mov-amount transfer")


def test_chips_sin_emojis(app):
    p = app.page
    app.ir("movimientos")
    textos = p.locator("#sec-movimientos .chip").all_inner_texts()
    assert textos and not [t for t in textos if any(ord(c) > 0x2190 for c in t)], textos
    expect(p.locator("#movFilterChips .chip", has_text="Ibercaja").locator(".kficha.logo")).to_have_count(1)
    expect(p.locator("#movCatChips .chip", has_text="Restaurantes").locator(".kficha.cat")).to_have_count(1)
