import re

import pytest
from playwright.sync_api import expect

import datos


def tarjeta(app, nombre):
    return app.page.locator(".sus-card-wrap", has=app.page.locator(".sus-name", has_text=nombre))


def alerta(app):
    return app.page.locator("#alertBanner")


def aviso_de(app):
    return app.page.locator("#alertItems")


def registrados(n, nombre, fechas, importe):
    for f in fechas:
        datos.pago_registrado(n, nombre, f, importe)


def test_registrar_pago_simple(app):
    app.ir("registrar")
    tarjeta(app, "Spotify").locator(".sus-btn").click()
    expect(app.toast()).to_contain_text("Spotify registrada")
    w = app.escrituras("POST")[-1]["cuerpo"]["properties"]
    assert w["Nombre"]["title"][0]["text"]["content"] == "🎵 Spotify"
    assert w["Gasto"]["number"] == 20.99 and w["Fecha"]["date"]["start"] == datos.HOY


def test_cuotas_cuentan_movimientos_reales_por_nombre_exacto(abrir):
    def mas(n):
        registrados(n, "🛋️ Mueble Ikea", ["2026-10-27"], 28.93)
        registrados(n, "Mueble Ikea", ["2026-10-28"], 28.93)  # sin emoji: no es de este pago
    app = abrir(mas=mas)
    app.ir("registrar")
    t = tarjeta(app, "Mueble Ikea")
    expect(t).to_contain_text("1/3 cuotas")
    expect(t).to_contain_text("Pagado 28,93 €")


def test_cuotas_iniciales_se_suman(app):
    app.ir("registrar")
    expect(tarjeta(app, "Letra Coche")).to_contain_text("3/24 cuotas")


def test_movimientos_anteriores_al_inicio_no_cuentan(abrir):
    app = abrir(mas=lambda n: registrados(n, "🛋️ Mueble Ikea", ["2026-09-01"], 28.93))
    app.ir("registrar")
    expect(tarjeta(app, "Mueble Ikea")).to_contain_text("0/3 cuotas")


def test_vinilos_usa_el_importe_de_cada_cuota(abrir):
    app = abrir(mas=lambda n: registrados(n, "💿 Vinilos", ["2026-10-29"], 28.85))
    app.ir("registrar")
    t = tarjeta(app, "Vinilos")
    expect(t).to_contain_text("1/3 cuotas")
    expect(t.locator(".sus-amount")).to_have_text("-28.86 €")
    t.locator(".sus-btn").click()
    expect(app.toast()).to_contain_text("Vinilos registrada")
    assert app.escrituras("POST")[-1]["cuerpo"]["properties"]["Gasto"]["number"] == 28.86


def test_pago_terminado_desaparece(abrir):
    app = abrir(mas=lambda n: registrados(n, "🛋️ Mueble Ikea", ["2026-10-27", "2026-11-01", "2026-11-02"], 28.93))
    app.ir("registrar")
    expect(tarjeta(app, "Vinilos")).to_be_visible()
    expect(tarjeta(app, "Mueble Ikea")).to_have_count(0)


def test_registrar_la_ultima_cuota_retira_la_tarjeta(abrir):
    app = abrir(mas=lambda n: registrados(n, "🛋️ Mueble Ikea", ["2026-10-27", "2026-11-01"], 28.93))
    app.ir("registrar")
    t = tarjeta(app, "Mueble Ikea")
    expect(t).to_contain_text("2/3 cuotas")
    t.locator(".sus-btn").click()
    expect(t).to_have_count(0)


def test_error_de_notion_no_da_el_pago_por_terminado(abrir):
    app = abrir(mas=lambda n: n.fallar_consultas.add(datos.BASES["movs"]))
    app.ir("registrar")
    expect(tarjeta(app, "Letra Coche")).to_contain_text("3/24")


# ── Revisiones Coche ──
def test_revisiones_antes_de_empezar(app):
    app.ir("registrar")
    t = tarjeta(app, "Revisiones Coche")
    expect(t).to_contain_text("0/12 cuotas")
    expect(t).to_contain_text("Próximo pago 05/12/2026")
    expect(t).to_contain_text("660,00 €")
    expect(t).to_contain_text("Ibercaja")
    expect(t.locator(".sus-btn")).to_be_disabled()


def test_revisiones_el_primer_dia(abrir):
    app = abrir(hoy="2026-12-05")
    app.ir("registrar")
    t = tarjeta(app, "Revisiones Coche")
    expect(t.locator(".sus-btn")).to_be_enabled()
    expect(t).not_to_contain_text("Próximo pago")
    t.locator(".sus-btn").click()
    expect(t).to_contain_text("1/12 cuotas")
    w = app.escrituras("POST")[-1]["cuerpo"]["properties"]
    assert w["Nombre"]["title"][0]["text"]["content"] == "🔧 Revisiones Coche"
    assert w["Gasto"]["number"] == 55
    assert w["Cuenta"]["relation"][0]["id"] == datos.IBERCAJA
    assert w["Fuente de Gasto"]["relation"][0]["id"] == datos.CAT_COCHE


def test_revisiones_terminadas_desaparecen(abrir):
    fechas = ["2026-12-05"] + ["2027-%02d-05" % m for m in range(1, 12)]
    app = abrir(hoy="2027-11-05", mas=lambda n: registrados(n, "🔧 Revisiones Coche", fechas, 55))
    app.ir("registrar")
    expect(tarjeta(app, "Letra Coche")).to_be_visible()
    expect(tarjeta(app, "Revisiones Coche")).to_have_count(0)
    expect(aviso_de(app)).not_to_contain_text("Revisiones")


# ── Avisos en Inicio ──
def test_aviso_el_dia_del_pago(abrir):
    app = abrir(hoy="2026-11-11")
    expect(alerta(app)).to_have_class(re.compile(r"\bshow\b"))
    expect(aviso_de(app)).to_have_text("🤖 Claude Pro · -21.78 €")


def test_sin_aviso_otro_dia(app):
    app.avisos_listos()
    expect(alerta(app)).not_to_have_class(re.compile(r"\bshow\b"))


def test_sin_aviso_si_ya_esta_registrado_este_mes(abrir):
    app = abrir(hoy="2026-11-11", mas=lambda n: registrados(n, "🤖 Claude Pro", ["2026-11-10"], 21.78))
    app.avisos_listos()
    expect(alerta(app)).not_to_have_class(re.compile(r"\bshow\b"))


def test_aviso_si_lo_registrado_es_del_mes_pasado(abrir):
    app = abrir(hoy="2026-11-11", mas=lambda n: registrados(n, "🤖 Claude Pro", ["2026-10-11"], 21.78))
    expect(alerta(app)).to_have_class(re.compile(r"\bshow\b"))


def test_aviso_suma_los_pagos_del_dia_y_omite_cuotas_que_no_tocan(abrir):
    app = abrir(hoy="2026-11-05")
    expect(aviso_de(app)).to_have_text("🚗 Letra Coche · -432.35 €")  # Revisiones aún no ha empezado


def test_aviso_de_revisiones_desde_el_primer_dia(abrir):
    app = abrir(hoy="2026-12-05")
    expect(aviso_de(app)).to_contain_text("🔧 Revisiones Coche")
    expect(aviso_de(app)).to_contain_text("487.35 €")  # con Letra Coche


def test_sin_aviso_de_un_pago_terminado(abrir):
    app = abrir(hoy="2026-11-27", mas=lambda n: registrados(n, "🛋️ Mueble Ikea", ["2026-10-27", "2026-11-01", "2026-11-02"], 28.93))
    app.avisos_listos()
    expect(aviso_de(app)).to_contain_text("DAZN Basket")
    expect(aviso_de(app)).not_to_contain_text("Mueble Ikea")


# ── Transferencias recurrentes ──
def rec(app, i):
    return app.page.locator("#transfRecList .sus-card").nth(i)


def test_tarjetas_de_transferencias_recurrentes(app):
    app.ir("cuentas")
    expect(app.page.locator("#transfRecList .sus-card")).to_have_count(2)
    expect(rec(app, 0)).to_contain_text("Ibercaja → MyInvestor Remunerada (2,50%)")
    expect(rec(app, 0)).to_contain_text("Día 23")
    expect(rec(app, 0).locator(".sus-amount")).to_have_text("150.00 €")
    expect(rec(app, 1)).to_contain_text("Ibercaja → Revolut Personal")
    expect(rec(app, 1)).to_contain_text("Día 26")
    expect(rec(app, 1)).to_contain_text("importe a elegir")
    expect(rec(app, 1).locator(".sus-amount")).to_have_count(0)


def test_remunerada_precargada_editable_y_sin_aportacion(app):
    p = app.page
    app.ir("cuentas")
    rec(app, 0).locator(".sus-btn").click()
    expect(p.locator("#transferAmt")).to_have_value("150,00")
    expect(p.locator("#transferFrom")).to_have_text("Ibercaja")
    expect(p.locator("#transferToChips .chip.selected")).to_contain_text("Remunerada")
    p.locator("#transferAmt").fill("175,50")
    p.locator("#transferOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Transferencia registrada")
    posts = app.escrituras("POST")
    assert len(posts) == 1  # sin aportación
    assert posts[0]["cuerpo"]["properties"]["Monto"]["number"] == 175.5
    assert posts[0]["cuerpo"]["properties"]["Transferir a"]["relation"][0]["id"] == datos.REMUNERADA


def test_revolut_con_importe_vacio(app):
    p = app.page
    app.ir("cuentas")
    rec(app, 1).locator(".sus-btn").click()
    expect(p.locator("#transferAmt")).to_have_value("")
    expect(p.locator("#transferToChips .chip.selected")).to_contain_text("Revolut Personal")
    p.locator("#transferAmt").fill("312")
    p.locator("#transferOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Transferencia registrada")
    posts = app.escrituras("POST")
    assert len(posts) == 1 and posts[0]["cuerpo"]["properties"]["Monto"]["number"] == 312


def test_aviso_transferencia_dia_23(abrir):
    app = abrir(hoy="2026-11-23")
    expect(alerta(app).locator(".alert-title")).to_have_text("⇄ Transferencias hoy")
    expect(aviso_de(app)).to_have_text("MyInvestor Remunerada · 150.00 €")


def test_aviso_transferencia_dia_26_sin_importe_y_se_retira_al_registrar(abrir):
    app = abrir(hoy="2026-12-26")  # diciembre: los datos base ya traen la de noviembre
    expect(aviso_de(app)).to_have_text("Revolut Personal, Aportación mensual · 150.00 €")
    app.ir("cuentas")
    rec(app, 1).locator(".sus-btn").click()
    app.page.locator("#transferAmt").fill("90")
    app.page.locator("#transferOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Transferencia registrada")
    # Solo queda la aportación, que vence el mismo día
    expect(aviso_de(app)).to_have_text("Aportación mensual · 150.00 €")


@pytest.mark.parametrize("hoy,desde,hacia,importe,fecha,avisa", [
    ("2026-11-23", datos.IBERCAJA, datos.REMUNERADA, 150, "2026-11-03", False),  # ya registrada
    ("2026-11-23", datos.IBERCAJA, datos.REMUNERADA, 200, "2026-11-03", True),   # otro importe no cuenta
    ("2026-11-23", datos.IBERCAJA, datos.REMUNERADA, 150, "2026-10-23", True),   # es del mes pasado
    ("2026-11-23", datos.REVOLUT, datos.REMUNERADA, 150, "2026-11-03", True),    # otro origen
    ("2026-11-26", datos.IBERCAJA, datos.REVOLUT, 37.2, "2026-11-20", False),    # cualquier importe vale
    ("2026-11-26", datos.IBERCAJA, datos.EFECTIVO, 37.2, "2026-11-20", True),    # otro destino
])
def test_ya_registrada_este_mes(abrir, hoy, desde, hacia, importe, fecha, avisa):
    def semilla(n):
        datos.cuenta(n, "💳 Ibercaja", datos.IBERCAJA, 500)
        datos.transferencia(n, desde, hacia, importe, fecha)
        # El día 26 también vence la aportación: ya hecha, para que solo cuente la transferencia probada
        datos.transferencia(n, datos.REMUNERADA, datos.MYINVESTOR, 150, hoy[:8] + "02")
    app = abrir(hoy=hoy, sembrar=semilla)
    app.avisos_listos()
    if avisa:
        expect(alerta(app)).to_have_class(re.compile(r"\bshow\b"))
    else:
        expect(alerta(app)).not_to_have_class(re.compile(r"\bshow\b"))


def test_si_notion_falla_se_avisa_igualmente(abrir):
    def semilla(n):
        n.fallar_consultas.add(datos.BASES["transfers"])
    app = abrir(hoy="2026-11-23", mas=semilla)
    expect(alerta(app)).to_have_class(re.compile(r"\bshow\b"))


# ── Aportación mensual (día 26) ──
def test_aviso_de_aportacion_el_26(abrir):
    def semilla(n):
        datos.cuenta(n, "💳 Ibercaja", datos.IBERCAJA, 500)
        datos.transferencia(n, datos.IBERCAJA, datos.REVOLUT, 50, "2026-11-03")
    app = abrir(hoy="2026-11-26", sembrar=semilla)
    expect(alerta(app).locator(".alert-title")).to_have_text("⇄ Transferencias hoy")
    expect(aviso_de(app)).to_have_text("Aportación mensual · 150.00 €")


def test_aportacion_de_cualquier_importe_cuenta_como_hecha(abrir):
    def semilla(n):
        datos.cuenta(n, "💳 Ibercaja", datos.IBERCAJA, 500)
        datos.transferencia(n, datos.IBERCAJA, datos.REVOLUT, 50, "2026-11-03")
        datos.transferencia(n, datos.REMUNERADA, datos.MYINVESTOR, 80, "2026-11-10")
    app = abrir(hoy="2026-11-26", sembrar=semilla)
    app.avisos_listos()
    expect(alerta(app)).not_to_have_class(re.compile(r"\bshow\b"))


def test_aportacion_de_otro_mes_no_cuenta(abrir):
    def semilla(n):
        datos.cuenta(n, "💳 Ibercaja", datos.IBERCAJA, 500)
        datos.transferencia(n, datos.IBERCAJA, datos.REVOLUT, 50, "2026-11-03")
        datos.transferencia(n, datos.REMUNERADA, datos.MYINVESTOR, 150, "2026-10-26")
    app = abrir(hoy="2026-11-26", sembrar=semilla)
    expect(aviso_de(app)).to_have_text("Aportación mensual · 150.00 €")


def test_registrar_la_aportacion_retira_el_aviso(abrir):
    def semilla(n):
        datos.cuenta(n, "💳 Ibercaja", datos.IBERCAJA, 500)
        datos.transferencia(n, datos.IBERCAJA, datos.REVOLUT, 50, "2026-11-03")
    app = abrir(hoy="2026-11-26", sembrar=semilla)
    expect(aviso_de(app)).to_have_text("Aportación mensual · 150.00 €")
    app.ir("inversion")
    app.page.locator("#sec-inversion .sus-btn", has_text="Registrar").click()
    expect(app.toast()).to_contain_text("Aportación de 150€")
    expect(alerta(app)).not_to_have_class(re.compile(r"\bshow\b"))


def test_pago_del_30_avisa_el_ultimo_dia_de_febrero(abrir):
    app = abrir(hoy="2027-02-28")
    expect(aviso_de(app)).to_contain_text("☁️ iCloud")
    app.ir("registrar")
    expect(app.page.locator(".sus-card-wrap", has=app.page.locator(".sus-name", has_text="iCloud")).locator(".sus-name")).to_contain_text("🔔")


def test_pago_del_30_no_avisa_antes_del_ultimo_dia(abrir):
    app = abrir(hoy="2027-02-27")
    app.avisos_listos()
    expect(aviso_de(app)).not_to_contain_text("iCloud")
