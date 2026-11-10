"""Ningún importe se corta: con cifras enormes, cada importe cabe en su caja (se reduce la letra o pasa de línea)."""
from playwright.sync_api import expect

import datos

CORTADAS = """(sel)=>[...document.querySelectorAll(sel)].filter(e=>e.offsetParent!==null&&e.textContent.trim()).map(e=>{
  const caja=e.closest('.hero-mini,.qa-card,.chart-row,.pat-item,.hero-card,.alert-banner')||e.parentElement;
  const r=e.getBoundingClientRect(),c=caja.getBoundingClientRect();
  const cortada=e.scrollWidth>e.clientWidth+1||r.right>c.right+1||r.left<c.left-1||r.bottom>c.bottom+1||r.top<c.top-1
    ||(getComputedStyle(caja).overflow!=='visible'&&caja.scrollHeight>caja.clientHeight+1);  // el carrusel se desliza: cada cifra se mide en su tarjeta
  return cortada?e.id+' '+e.className+' «'+e.textContent+'» '+e.scrollWidth+'/'+e.clientWidth:null}).filter(Boolean)"""

SEL = "#sec-inicio .hero-amount,#sec-inicio .hero-mini-val,#sec-inicio .qa-bal,#sec-inicio .chart-val,#sec-inicio .pat-item-val"


def _enormes(notion):
    datos.cuenta(notion, "Openbank Corriente", "31621c54013f8195b826ed3873c898ea", 98765432.1)
    datos.ingreso(notion, "Premio", "2026-11-03", 12345678.9)
    datos.gasto(notion, "Casa", "2026-11-04", 9876543.21, cat=datos.CAT_HOGAR)


def _ninguna_cortada(p):
    p.wait_for_timeout(200)
    cortadas = p.evaluate(CORTADAS, SEL)
    assert not cortadas, cortadas
    assert p.evaluate("()=>document.documentElement.scrollWidth<=innerWidth"), "la página se desliza de lado"


def test_ningun_importe_de_inicio_se_corta_con_cifras_enormes(abrir):
    app = abrir(mas=_enormes)
    p = app.page
    expect(p.locator("#totalAmount")).to_contain_text("€")
    p.wait_for_function("()=>document.getElementById('totalAmount').dataset.rawVal>1e8", timeout=4000)
    expect(p.locator("#resIngreso")).to_have_text("+12.347.678,90 €")
    expect(p.locator("#quickAccounts .qa-card", has_text="Openbank")).to_contain_text("98.765.432,10 €")
    _ninguna_cortada(p)
    p.locator("#patHeroCard .hero-label").click()  # el desglose también
    expect(p.locator("#patBreakdown")).to_contain_text("98.765.432,10 €")
    _ninguna_cortada(p)
    # En un móvil estrecho, igual
    p.set_viewport_size({"width": 320, "height": 700})
    p.wait_for_timeout(300)
    _ninguna_cortada(p)


def test_la_cifra_grande_lleva_los_centimos_mas_pequenos(app):
    p = app.page
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    expect(p.locator("#totalAmount .ent")).to_have_text("5925")
    expect(p.locator("#totalAmount .dec")).to_have_text(",00 €")


def _carrusel_largo(notion):
    """Varias cuentas con saldos largos: el carrusel entero, no solo una tarjeta."""
    for nombre, id, saldo in [("Openbank Corriente", "31621c54013f8195b826ed3873c898ea", 98765432.1),
                              ("Openbank Ahorro", "31621c54013f812089b8f9667f4743b0", 1234567.89),
                              ("Pluxee", "31621c54013f815ba96bde36edc89cb2", 123456.78)]:
        datos.cuenta(notion, nombre, id, saldo)


def test_los_saldos_del_carrusel_nunca_se_cortan(abrir):
    app = abrir(mas=_carrusel_largo)
    p = app.page
    tarjetas = p.locator("#quickAccounts .qa-card")
    expect(tarjetas).to_have_count(8)
    expect(p.locator("#quickAccounts .qa-card", has_text="Openbank Corriente")).to_contain_text("98.765.432,10 €")
    sel = "#quickAccounts .qa-bal"
    for ancho in [390, 320]:
        p.set_viewport_size({"width": ancho, "height": 760})
        p.wait_for_timeout(300)
        for i in range(tarjetas.count()):  # cada tarjeta a la vista, como al deslizar el carrusel
            tarjetas.nth(i).scroll_into_view_if_needed()
            cortadas = p.evaluate(CORTADAS, sel)
            assert not cortadas, (ancho, cortadas)
        # Y el saldo se ve entero: la tarjeta no lo tapa por abajo
        tapados = p.evaluate("""()=>[...document.querySelectorAll('#quickAccounts .qa-card')].filter(c=>{
          const b=c.querySelector('.qa-bal').getBoundingClientRect(),r=c.getBoundingClientRect();
          return b.bottom>r.bottom-4||b.height<10}).length""")
        assert tapados == 0, (ancho, tapados)
        # Todas las tarjetas miden lo mismo: un nombre largo no las estira
        anchos = p.evaluate("()=>[...document.querySelectorAll('#quickAccounts .qa-card')].map(c=>Math.round(c.getBoundingClientRect().width))")
        assert len(set(anchos)) == 1, anchos
