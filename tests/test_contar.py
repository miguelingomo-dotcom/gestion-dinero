"""Al entrar en una pestaña, sus cifras cuentan desde 0 hasta su valor; no al tocar la pestaña en la que ya estás, al
volver de una hoja ni con «Reducir movimiento»."""
import re

from playwright.sync_api import expect

OBSERVA = """(sel)=>{window.__vistos=[];const els=[...document.querySelectorAll(sel)];
  const ob=new MutationObserver(()=>els.forEach((e,i)=>{const t=e.textContent.trim();
    if(window.__vistos[window.__vistos.length-1]?.[1]!==t||window.__vistos[window.__vistos.length-1]?.[0]!==i)window.__vistos.push([i,t]);}));
  els.forEach(e=>ob.observe(e,{childList:true,subtree:true,characterData:true}));window.__ob=ob;}"""


def valores(p, i=0):
    out = []
    for j, t in p.evaluate("()=>window.__vistos"):
        m = re.search(r"(\d[\d.]*,\d+)", t)
        if j == i and m:
            out.append(float(m.group(1).replace(".", "").replace(",", ".")))
    return out


def test_inicio_cuenta_desde_cero_al_volver_a_la_pestana(abrir):
    app = abrir(reducir=False)
    p = app.page
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    p.wait_for_timeout(900)
    app.ir("cuentas")
    p.wait_for_timeout(300)
    p.evaluate(OBSERVA, "#totalAmount")
    app.ir("inicio")
    p.wait_for_timeout(900)
    v = valores(p)
    assert len(v) > 3 and v[0] < 1500 and v[-1] == 5925, v
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")


def test_cada_pestana_cuenta_sus_cifras(abrir):
    app = abrir(reducir=False)
    p = app.page
    for tab, sel, final in [("cuentas", "#accountCards .account-balance", None), ("stats", "#statGasto", "-144,50 €")]:
        app.ir(tab)
        p.wait_for_timeout(1200)  # primera visita: cargan los datos
        app.ir("inicio")
        p.wait_for_timeout(300)
        app.ir(tab)
        p.evaluate(OBSERVA, sel)
        p.wait_for_timeout(50)
        p.wait_for_timeout(900)
        v = valores(p)
        assert len(v) > 3 and v[0] < v[-1], (tab, v)
        if final:
            expect(p.locator(sel)).to_have_text(final)


def test_no_cuenta_al_tocar_la_misma_pestana_ni_al_cerrar_una_hoja(abrir):
    app = abrir(reducir=False)
    p = app.page
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    p.wait_for_timeout(900)
    p.evaluate(OBSERVA, "#totalAmount")
    app.ir("inicio")  # la pestaña en la que ya estás
    app.abrir_ajustes()
    p.locator("#ajustesOverlay .modal-cancel").click()
    p.wait_for_timeout(900)
    assert valores(p) == [], valores(p)


def test_con_reducir_movimiento_no_cuenta(app):
    p = app.page
    # Espera a que termine la cuenta del arranque (esa ya existía y no depende de esta función)
    p.wait_for_function("()=>document.getElementById('totalAmount').dataset.rawVal==='5925'", timeout=4000)
    app.ir("cuentas")
    p.evaluate(OBSERVA, "#totalAmount")
    app.ir("inicio")
    p.wait_for_timeout(700)
    assert all(x == 5925 for x in valores(p)), valores(p)
