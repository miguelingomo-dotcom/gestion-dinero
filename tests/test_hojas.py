"""Todas las hojas caben en la pantalla de un iPhone SE (390 × 667) sin desplazarse, con los botones a la vista."""
import pytest
from playwright.sync_api import expect

import datos

CABE = """(id)=>{const ov=document.getElementById(id),m=ov.querySelector('.modal'),b=m.querySelector('.modal-btns');
  const r=m.getBoundingClientRect(),rb=b?b.getBoundingClientRect():null;
  return {desborda:m.scrollHeight-m.clientHeight,arriba:r.top,botones:rb?rb.bottom<=innerHeight+1&&rb.top>=r.top:true,alto:Math.round(r.height)}}"""


def abrir_hoja(app, como):
    p = app.page
    if como == "editar_gasto":
        app.ir("movimientos")
        app.fila_mov("Mercadona").locator(".mov-info").click()
        return "editOverlay"
    if como == "editar_ingreso":
        app.ir("movimientos")
        app.fila_mov("Nómina noviembre").locator(".mov-info").click()
        return "editOverlay"
    if como == "editar_transferencia":
        app.ir("movimientos")
        app.fila_mov("Ibercaja → Revolut Personal").locator(".mov-icon").click()
        return "trEditOverlay"
    if como == "mover":
        p.evaluate("([a,b])=>showTransfer(a,'Ibercaja',b,150)", [datos.IBERCAJA, datos.REMUNERADA])
        return "transferOverlay"
    if como == "aportacion":
        app.ir("inversion")
        p.evaluate("()=>openInvModal('Aportación')")
        return "invOverlay"
    if como == "valor":
        app.ir("inversion")
        p.evaluate("()=>openInvModal('Valor Cartera')")
        return "invOverlay"
    if como == "confirmar":
        p.evaluate("()=>{hojaAccion({titulo:'¿Desactivar Ibercaja?',texto:'Dejará de aparecer en tus cuentas. Podrás reactivarla desde «Ver cuentas inactivas».',confirmar:'Desactivar',peligro:true})}")
        return "accionOverlay"
    if como == "ajustes":
        app.abrir_ajustes()
        return "ajustesOverlay"
    raise ValueError(como)


@pytest.mark.parametrize("como", ["editar_gasto", "editar_ingreso", "editar_transferencia", "mover", "aportacion", "valor",
                                  "confirmar", "ajustes"])
def test_la_hoja_cabe_en_un_iphone_se(app, como):
    p = app.page
    p.set_viewport_size({"width": 390, "height": 667})
    hoja = abrir_hoja(app, como)
    expect(p.locator("#" + hoja)).to_have_class(__import__("re").compile(r"\bshow\b"))
    p.wait_for_timeout(450)  # la hoja termina de subir
    r = p.evaluate(CABE, hoja)
    assert r["desborda"] <= 1 and r["arriba"] >= 0 and r["botones"], (como, r)


def test_editar_movimiento_compacto_con_logos(app):
    p = app.page
    app.ir("movimientos")
    app.fila_mov("Mercadona").locator(".mov-info").click()
    expect(p.locator("#editAmt")).to_have_value("84,50")
    expect(p.locator("#editAccChips .chip.selected .kficha.logo")).to_have_count(1)
    expect(p.locator("#editCatGrid .cat-item.selected")).to_contain_text("Supermercado")
    # Elegir otra categoría y guardar sigue funcionando
    p.locator('#editCatGrid .cat-item[data-cat="%s"]' % datos.CAT_RESTAURANTES).click()
    p.locator("#editOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Movimiento actualizado")
    w = app.escrituras("PATCH")[-1]["cuerpo"]["properties"]
    assert w["Fuente de Gasto"]["relation"][0]["id"] == datos.CAT_RESTAURANTES
