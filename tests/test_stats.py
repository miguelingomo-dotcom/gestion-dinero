"""Estadísticas: cifras del periodo, categorías con su icono y color, comparativa, histórico y extracto.
Datos base (15/11/2026): noviembre gasta 144,50 (Mercadona 84,50 + Repsol 60) e ingresa 2000; octubre gasta 45,50."""
import re

from playwright.sync_api import expect

import datos


def abrir_stats(app):
    app.ir("stats")
    expect(app.page.locator("#statGasto")).to_have_text("-144,50 €")


def test_cifras_del_mes(app):
    p = app.page
    abrir_stats(app)
    expect(p.locator("#statBalance")).to_have_text("+1855,50 €")
    expect(p.locator("#statBalance .dec")).to_have_text(",50 €")
    expect(p.locator("#statIngreso")).to_have_text("+2000,00 €")
    expect(p.locator("#rateNum")).to_have_text("92,8 %")
    expect(p.locator("#statSub")).to_have_text("Estás ahorrando bien")  # sin emoji
    expect(p.locator("#actCount")).to_have_text("3")
    expect(p.locator("#actAvg")).to_have_text("72,25 €")
    expect(p.locator("#actMax")).to_have_text("84,50 €")
    expect(p.locator("#sec-stats .header h1")).to_have_text("Estadísticas")


def test_categorias_con_su_icono_y_su_color(app):
    p = app.page
    abrir_stats(app)
    expect(p.locator("#pieLegend .leg-item")).to_have_count(2)
    expect(p.locator("#pieLegend .leg-item").first).to_contain_text("Supermercado")
    expect(p.locator("#pieLegend .leg-item").first).to_contain_text("58 %")
    color = p.locator("#pieLegend .leg-dot").first.evaluate("e=>getComputedStyle(e).backgroundColor")
    assert color == "rgb(47, 158, 91)", color  # Supermercado #2F9E5B
    top = p.locator("#topList .top-item")
    expect(top).to_have_count(2)
    expect(top.first.locator(".kficha.cat")).to_have_count(1)
    expect(top.first.locator(".top-amount")).to_have_text("84,50 €")
    ing = p.locator("#incomeChartWrap .chart-row")
    expect(ing).to_have_count(1)
    expect(ing.first).to_contain_text("Nómina")
    expect(ing.first.locator(".kficha.cat")).to_have_count(1)


def test_comparativa_con_el_mes_anterior(app):
    p = app.page
    abrir_stats(app)
    filas = p.locator("#comparList .compar-row")
    expect(filas).to_have_count(3)
    rest = p.locator("#comparList .compar-row", has_text="Restaurantes")
    expect(rest).to_contain_text("45,50 € → 0,00 €")
    expect(rest.locator(".compar-pct")).to_have_text("100 %")
    expect(p.locator("#comparList")).not_to_contain_text("▲")


def test_mes_anterior_oculta_proyeccion_y_comparativa(app):
    p = app.page
    abrir_stats(app)
    p.locator('#sec-stats .period-btn[onclick*="-1"]').click()
    expect(p.locator("#statGasto")).to_have_text("-45,50 €")
    expect(p.locator("#projCard")).to_be_hidden()
    expect(p.locator("#comparCard")).to_be_hidden()
    # La marca del periodo se mueve al elegido
    marca = p.locator("#sec-stats .period-marca").bounding_box()
    boton = p.locator('#sec-stats .period-btn[onclick*="-1"]').bounding_box()
    assert abs(marca["x"] - boton["x"]) <= 2, (marca, boton)


def test_historico_y_extracto(app):
    p = app.page
    abrir_stats(app)
    expect(p.locator("#monthChips .chip")).to_have_count(12)
    expect(p.locator("#histGasto")).to_have_text("-144,50 €")
    p.locator("#monthChips .chip").nth(1).click()
    expect(p.locator("#histGasto")).to_have_text("-45,50 €")
    with p.expect_download() as d:
        p.locator("#sec-stats .export-btn").click()
    texto = open(d.value.path(), encoding="utf-8-sig").read()
    assert "Cena con amigos" in texto and "-45,50" in texto, texto
    expect(app.toast()).to_contain_text("Extracto descargado")
