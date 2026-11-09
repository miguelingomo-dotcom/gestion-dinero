import re

import pytest
from playwright.sync_api import expect

import datos


@pytest.mark.parametrize("periodo,gastado,ingresado,balance,etiqueta", [
    ("1M", "-144,50 €", "+2000,00 €", "+1855,50 €", "Este mes"),
    ("3M", "-220,00 €", "+4000,00 €", "+3780,00 €", None),
    ("6M", "-520,00 €", "+4000,00 €", "+3480,00 €", None),
    ("Todo", "-1520,00 €", "+4000,00 €", "+2480,00 €", None),
])
def test_cifras_por_periodo(app, periodo, gastado, ingresado, balance, etiqueta):
    p = app.page
    p.locator('.pat-period[data-p="%s"]' % periodo).click()
    expect(p.locator("#resGasto")).to_have_text(gastado)
    expect(p.locator("#resIngreso")).to_have_text(ingresado)
    expect(p.locator("#resBalance")).to_have_text(balance)
    expect(p.locator('.pat-period[data-p="%s"]' % periodo)).to_have_class(re.compile(r"\bactive\b"))
    if etiqueta:
        expect(p.locator("#resPeriodoLbl")).to_have_text(etiqueta)


def test_abre_en_un_mes_y_vuelve_a_el(app):
    p = app.page
    expect(p.locator('.pat-period[data-p="1M"]')).to_have_class(re.compile(r"\bactive\b"))
    expect(p.locator("#resGasto")).to_have_text("-144,50 €")
    p.locator('.pat-period[data-p="Todo"]').click()
    expect(p.locator("#resGasto")).to_have_text("-1520,00 €")
    p.locator('.pat-period[data-p="1M"]').click()
    expect(p.locator("#resGasto")).to_have_text("-144,50 €")


def test_balance_negativo_con_signo_y_en_rojo(abrir):
    def poco(n):
        datos.cuenta(n, "💳 Ibercaja", datos.IBERCAJA, 500)
        datos.ingreso(n, "Nómina", "2026-11-01", 100)
        datos.gasto(n, "Compra", "2026-11-02", 296.17)
    p = abrir(sembrar=poco).page
    expect(p.locator("#resBalance")).to_have_text("-196,17 €")
    assert p.locator("#resBalance").evaluate("e=>e.style.color") == "var(--red)"


def test_patrimonio_total_y_desglose(app):
    p = app.page
    # Cuentas 3950 + inactiva 75 + cartera 1900. La cuenta MyInvestor no suma su saldo en bruto
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    p.locator("#patHeroCard .hero-label").click()
    desglose = p.locator("#patBreakdown .pat-item")
    expect(desglose).to_have_count(6)
    expect(desglose.first).to_contain_text("Ibercaja")
    expect(desglose.first).to_contain_text("2790,00 €")
    expect(p.locator("#patBreakdown")).to_contain_text("MyInvestor")
    expect(p.locator("#patBreakdown")).to_contain_text("1900,00 €")


def test_grafica_y_variacion_del_patrimonio(app):
    p = app.page
    expect(p.locator(".pat-chart-line")).to_have_attribute("d", re.compile(r"^M"))
    expect(p.locator("#patVariation .var-badge")).to_be_visible()


def test_gastos_por_categoria_del_mes(app):
    filas = app.page.locator("#chartWrap .chart-row")
    expect(filas).to_have_count(2)
    expect(filas.first).to_contain_text("Supermercado")
    expect(filas.first).to_contain_text("84,50 €")
    expect(filas.nth(1)).to_contain_text("Gasolina")


def test_ojo_oculta_los_saldos(app):
    p = app.page
    p.locator("#kashyEyeBtn").click()
    expect(p.locator("body")).to_have_class(re.compile(r"kashy-privado"))
    p.locator("#kashyEyeBtn").click()
    expect(p.locator("body")).not_to_have_class(re.compile(r"kashy-privado"))
