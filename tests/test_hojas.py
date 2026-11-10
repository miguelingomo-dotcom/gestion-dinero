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


ANCHO = """(id)=>{const m=document.querySelector('#'+id+' .modal'),r=m.getBoundingClientRect(),cs=getComputedStyle(m);
  // Todo lo que no está dentro de una fila de chips queda dentro de la hoja; las filas, también (se deslizan por dentro)
  const fuera=[...m.querySelectorAll('*')].filter(e=>{
    if(e.closest('.chips-wrap,.fila-desliza')&&!e.matches('.chips-wrap,.fila-desliza'))return false;
    const b=e.getBoundingClientRect();return b.width&&(b.right>r.right+.5||b.left<r.left-.5)}).map(e=>e.id||e.className||e.tagName);
  const filas=[...m.querySelectorAll('.chips-wrap,.fila-desliza')].map(f=>getComputedStyle(f));
  return {ancho:m.scrollWidth-m.clientWidth,fuera,deLado:cs.overflowX,gesto:cs.touchAction,
    filasSeDeslizan:filas.every(f=>f.overflowX==='auto'&&f.touchAction.includes('pan-x')&&f.overscrollBehaviorX==='contain'),
    pagina:document.documentElement.scrollWidth-innerWidth,hojaAncho:Math.round(r.width),pantalla:innerWidth}}"""


@pytest.mark.parametrize("ancho", [390, 320], ids=["iphone", "estrecho"])
@pytest.mark.parametrize("como", ["editar_gasto", "editar_ingreso", "editar_transferencia", "mover", "aportacion", "valor",
                                  "confirmar", "ajustes"])
def test_ninguna_hoja_es_mas_ancha_que_la_pantalla_ni_se_mueve_de_lado(app, como, ancho):
    p = app.page
    p.set_viewport_size({"width": ancho, "height": 700})
    hoja = abrir_hoja(app, como)
    p.wait_for_timeout(450)
    r = p.evaluate(ANCHO, hoja)
    assert r["ancho"] <= 0 and not r["fuera"] and r["pagina"] <= 0 and r["hojaAncho"] <= r["pantalla"], (como, ancho, r)
    # La hoja solo se mueve en vertical; las filas de cuentas y categorías, de lado y sin arrastrar la hoja
    assert r["deLado"] == "hidden" and r["gesto"] == "pan-y" and r["filasSeDeslizan"], (como, r)


ESTILO = """([fecha,texto])=>{const f=document.getElementById(fecha),t=document.getElementById(texto);
  const cf=getComputedStyle(f),ct=getComputedStyle(t),bf=f.getBoundingClientRect(),bt=t.getBoundingClientRect(),caja=f.parentElement.getBoundingClientRect();
  const props=['height','paddingLeft','paddingRight','fontSize','fontWeight','borderTopLeftRadius','backgroundColor','color'];
  return {distintos:props.filter(k=>cf[k]!==ct[k]).map(k=>k+': '+cf[k]+' ≠ '+ct[k]),
    centrado:cf.lineHeight===cf.height,alineados:Math.abs(bf.top-bt.top)<=1||Math.abs(bf.bottom-bt.bottom)<=1||bf.top>=bt.bottom,
    dentro:bf.right<=caja.right+.5&&bf.left>=caja.left-.5&&bf.right<=innerWidth,
    // El texto de la fecha no informa de su ancho: se exige sitio para «11 nov 2026» o «11/10/2026» y el icono del calendario
    cortado:f.scrollWidth>f.clientWidth+1||f.clientWidth-parseFloat(cf.paddingLeft)-parseFloat(cf.paddingRight)<125}}"""


@pytest.mark.parametrize("ancho", [390, 320], ids=["iphone", "estrecho"])
@pytest.mark.parametrize("como,fecha,texto", [("editar_gasto", "editDate", "editName"), ("editar_transferencia", "trEditDate", "trEditAmt"),
                                              ("aportacion", "invDate", "invAmt")], ids=["movimiento", "transferencia", "inversion"])
def test_las_fechas_de_las_hojas_son_como_sus_campos_vecinos(app, como, fecha, texto, ancho):
    p = app.page
    p.set_viewport_size({"width": ancho, "height": 700})
    abrir_hoja(app, como)
    p.wait_for_timeout(450)
    r = p.evaluate(ESTILO, [fecha, texto])
    # Mismo alto, relleno, letra, caja y colores que «Nombre» (en las otras hojas, el importe solo difiere en la letra)
    distintos = [d for d in r["distintos"] if como == "editar_gasto" or not d.startswith(("fontSize", "fontWeight"))]
    assert not distintos and r["centrado"] and r["dentro"] and not r["cortado"], (como, ancho, r)
    if como == "editar_gasto":
        assert r["alineados"], r


@pytest.mark.parametrize("ancho", [390, 320], ids=["iphone", "estrecho"])
def test_la_fecha_otra_de_registrar_es_como_el_campo_nombre(app, ancho):
    p = app.page
    p.set_viewport_size({"width": ancho, "height": 760})
    app.ir("registrar")
    p.locator('#fechaChips [data-fecha="otra"]').click()
    expect(p.locator("#inputFecha")).to_be_visible()
    r = p.evaluate(ESTILO, ["inputFecha", "inputName"])
    assert not r["distintos"] and r["centrado"] and r["dentro"] and not r["cortado"], (ancho, r)
