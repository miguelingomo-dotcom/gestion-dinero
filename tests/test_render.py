"""Lo que pinta un render está completo en ese mismo instante: sin temporizadores ni observadores que lo retoquen."""
import re

from playwright.sync_api import expect

import datos


def registrar_temporizadores(page):
    page.add_init_script("""
      window.__intervalos=[];const si=window.setInterval;window.setInterval=(f,t,...a)=>{window.__intervalos.push(t);return si(f,t,...a);};
      window.__observados=[];const O=window.MutationObserver;
      window.MutationObserver=class extends O{observe(n,o){window.__observados.push(n.id||n.nodeName);return super.observe(n,o);}};
    """)


def test_no_hay_intervalos_ni_observadores_de_parches(abrir):
    app = abrir(antes=registrar_temporizadores)
    app.ir("movimientos")
    app.page.wait_for_timeout(1500)
    assert app.page.evaluate("()=>window.__intervalos") == []
    observados = app.page.evaluate("()=>window.__observados")
    for id in ("recentMovs", "invHistList", "accountCards", "accountChips", "movFilterChips"):
        assert id not in observados


CHIPS_INICIALES = "()=>{renderChips();return [...document.querySelectorAll('#accountChips .chip')].map(c=>[c.textContent,!!c.querySelector('.kficha.logo img')])}"


def test_chips_con_su_logo_en_el_mismo_render(app):
    # Rediseño: el chip de Registrar lleva el logo del banco (antes, su color). Se lee en la misma tarea que el render:
    # un observador o temporizador aún no habría podido actuar
    chips = app.page.evaluate(CHIPS_INICIALES)
    ibercaja = [c for c in chips if "Ibercaja" in c[0]][0]
    assert ibercaja[1]


def test_todas_las_listas_de_chips_con_color_al_abrir(app):
    p = app.page
    color = p.evaluate("""([ib,rem])=>{showTransfer(ib,'Ibercaja',rem,150);
      return document.querySelector('#transferToChips .chip.selected').style.background}""", [datos.IBERCAJA, datos.REMUNERADA])
    assert color


def test_filtro_todas_sin_color_de_banco(app):
    p = app.page
    r = p.evaluate("()=>{renderMovFilterChips();const c=document.querySelector('#movFilterChips .chip');return [c.style.background,c.dataset.bank||null]}")
    assert r == ["", None]


def test_movimientos_agrupados_y_con_carril_al_terminar_el_render(app):
    r = app.page.evaluate("""async()=>{await loadMovs();const l=document.getElementById('recentMovs');
      return {sueltas:l.querySelectorAll(':scope > .mov-item').length,
              sinCarril:[...l.querySelectorAll('.mov-item')].filter(f=>!f.parentElement.classList.contains('swipe')).length,
              grupos:l.querySelectorAll('.mov-group').length,cabeceras:l.querySelectorAll('.mov-daygroup').length,
              balance:l.querySelector('.mov-daygroup .mov-day-bal')?.textContent}}""")
    assert r["sueltas"] == 0 and r["sinCarril"] == 0
    assert r["grupos"] == r["cabeceras"] > 0
    assert r["balance"] == "-60,00 €"


FILAS_MOVIDAS = """async(id)=>{
  const l=document.getElementById(id);l.innerHTML='';delete l.dataset.clave;
  let movidas=0;
  const o=new MutationObserver(ms=>ms.forEach(m=>m.removedNodes.forEach(n=>{
    if(n.nodeType===1&&(n.matches('.mov-item')||n.querySelector('.mov-item')))movidas++;})));
  o.observe(l,{childList:true,subtree:true});
  await (id==='recentMovs'?loadMovs(true):loadInversion());
  await new Promise(r=>setTimeout(r,1300));
  o.disconnect();
  return {filas:l.querySelectorAll('.mov-item').length,movidas}}"""


def test_las_filas_de_movimientos_no_se_recolocan(abrir):
    """Mover un nodo reinicia su animación de entrada: cada fila debe nacer ya en su grupo y su carril."""
    r = abrir(reducir=False).page.evaluate(FILAS_MOVIDAS, "recentMovs")
    assert r["filas"] == 10 and r["movidas"] == 0, r


def test_las_filas_de_inversion_no_se_recolocan(abrir):
    r = abrir(reducir=False).page.evaluate(FILAS_MOVIDAS, "invHistList")
    assert r["filas"] == 5 and r["movidas"] == 0, r


def test_inversion_con_carril_al_terminar_el_render(app):
    r = app.page.evaluate("""async()=>{await loadInversion();const l=document.getElementById('invHistList');
      return [...l.querySelectorAll('.mov-item')].every(f=>f.parentElement.classList.contains('swipe'))&&l.querySelectorAll('.swipe-del').length}""")
    assert r == 5


def test_cuentas_con_color_icono_y_carrusel_al_terminar_el_render(app):
    r = app.page.evaluate("""async()=>{const q=document.getElementById('quickAccounts');q.innerHTML='';delete q.dataset.clave;await loadAccounts();
      const c=document.querySelector('#accountCards .account-card'),n=c.querySelector('.account-name');
      return {fondo:c.style.background,ico:n.querySelector('.acc-ico').textContent.length>0,plain:n.dataset.plain,
              carrusel:document.querySelectorAll('#quickAccounts .qa-card').length}}""")
    assert r["fondo"] and r["ico"] and r["plain"] == "Revolut Personal"
    assert r["carrusel"] == 5


def test_carrusel_visible_al_quitarse_el_splash(app):
    # abrir() espera a que el splash se retire: el carrusel debe estar ya, sin los 900 + 1200 ms de antes
    expect(app.page.locator("#quickAccounts .qa-card")).to_have_count(5, timeout=200)
    expect(app.page.locator("#quickAccounts .qa-card").first).to_contain_text("Revolut Personal")


def test_carrusel_se_actualiza_con_los_saldos_al_recargar_cuentas(app):
    p = app.page
    app.ir("cuentas")
    app.desplegar_cuenta("Ibercaja").locator(".acc-action", has_text="Mover").click()
    p.locator("#transferToChips .chip", has_text="Efectivo").click()
    p.locator("#transferAmt").fill("10")
    p.locator("#transferOverlay .modal-confirm").click()
    expect(p.locator("#quickAccounts .qa-card", has_text="Efectivo")).to_contain_text("30,00 €")


def test_deslizar_y_tocar_cierra_la_fila_sin_abrir_edicion(app):
    p = app.page
    app.ir("movimientos")
    fila = app.fila_mov("Mercadona")
    fila.wait_for()
    sw = "xpath=ancestor::div[contains(@class,'swipe')][1]"
    fila.locator(sw).evaluate("e=>{e.scrollLeft=168}")
    p.wait_for_function("()=>[...document.querySelectorAll('.swipe')].some(s=>s.scrollLeft>4)")
    fila.locator(".mov-icon").dispatch_event("click")
    expect(p.locator("#editOverlay")).not_to_have_class(re.compile(r"\bshow\b"))
    p.wait_for_function("()=>[...document.querySelectorAll('.swipe')].every(s=>s.scrollLeft===0)")


def test_deslizar_una_fila_cierra_la_otra(app):
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    r = p.evaluate("""async()=>{const [a,b]=document.querySelectorAll('.swipe');
      a.scrollLeft=168;await new Promise(r=>setTimeout(r,120));
      b.scrollLeft=168;await new Promise(r=>setTimeout(r,700));
      return [a.scrollLeft,b.scrollLeft]}""")
    # Se cierra la que estaba abierta y queda abierta la nueva
    assert r == [0, 168]


def test_una_fila_cerrada_se_puede_volver_a_abrir(app):
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    r = p.evaluate("""async()=>{const [a,b]=document.querySelectorAll('.swipe');
      a.scrollLeft=168;await new Promise(r=>setTimeout(r,120));
      b.scrollLeft=168;await new Promise(r=>setTimeout(r,700));
      a.scrollLeft=168;await new Promise(r=>setTimeout(r,700));
      return [a.scrollLeft,b.scrollLeft]}""")
    assert r == [168, 0]


def test_editar_desde_el_carril(app):
    p = app.page
    app.ir("movimientos")
    fila = app.fila_mov("Mercadona")
    fila.wait_for()
    fila.locator("xpath=ancestor::div[contains(@class,'swipe')][1]").locator(".swipe-edit").click()
    expect(p.locator("#editOverlay")).to_have_class(re.compile(r"\bshow\b"))
    expect(p.locator("#editName")).to_have_value("Mercadona")


def test_la_consulta_de_conteo_ya_no_existe(abrir):
    app = abrir()
    app.page.wait_for_timeout(1700)
    consultas = [e for e in app.peticiones_api]
    assert app.page.evaluate("()=>typeof cargarConteo") == "undefined"
    assert consultas
