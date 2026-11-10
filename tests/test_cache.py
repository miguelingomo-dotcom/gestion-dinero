"""Pestañas con los últimos datos al instante, refresco silencioso y datos al día tras cualquier escritura."""
import re

from playwright.sync_api import expect

import datos

# Las llamadas a /api/ quedan pendientes mientras window.__sinRed sea true: así se ve qué hay antes de que responda Notion
SIN_RED = """(()=>{const f=window.fetch;window.__peticiones=0;window.__maxAVez=0;let enCurso=0;
  window.fetch=async(u,o)=>{
    if(String(u).startsWith('/api/')){
      if(window.__sinRed||sessionStorage.getItem('sin-red'))return new Promise(()=>{});
      window.__peticiones++;enCurso++;window.__maxAVez=Math.max(window.__maxAVez,enCurso);
      try{return await f(u,o);}finally{enCurso--;}
    }
    return f(u,o);};})();"""


def con_red_controlada(page):
    page.add_init_script(SIN_RED)


def sin_red(app):
    app.page.evaluate("()=>{window.__sinRed=true}")


def test_volver_a_una_pestana_muestra_lo_ultimo_sin_esqueleto(abrir):
    app = abrir(antes=con_red_controlada)
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    app.ir("inicio")
    sin_red(app)
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    assert p.locator("#recentMovs .skeleton").count() == 0


def test_sin_nada_guardado_sale_el_esqueleto(abrir):
    app = abrir(antes=con_red_controlada)
    sin_red(app)
    app.ir("movimientos")
    expect(app.page.locator("#recentMovs .skeleton").first).to_be_visible()


def test_al_abrir_la_app_se_ve_lo_guardado_antes_de_que_responda_notion(abrir):
    app = abrir(antes=con_red_controlada)
    p = app.page
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    expect(p.locator("#quickAccounts .qa-card")).to_have_count(5)
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    app.ir("cuentas")
    expect(app.cuenta("Ibercaja").locator(".account-balance")).to_have_text("2790,00 €")
    app.ir("inversion")
    expect(p.locator("#invHistList .mov-item")).to_have_count(5)
    p.wait_for_timeout(600)  # la caché se escribe en localStorage con un pequeño retardo
    p.evaluate("()=>sessionStorage.setItem('sin-red','1')")
    p.reload()
    # Sin red el logo se va a los 1,2 s, y debajo ya están los datos guardados
    expect(p.locator("#splashScreen")).to_have_class(re.compile(r"\bhide\b"), timeout=2000)
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    expect(p.locator("#resGasto")).to_have_text("-144,50 €")
    expect(p.locator("#quickAccounts .qa-card", has_text="Ibercaja")).to_contain_text("2790,00 €")
    expect(p.locator("#chartWrap .chart-row")).to_have_count(2)
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    app.ir("cuentas")
    expect(app.cuenta("Ibercaja").locator(".account-balance")).to_have_text("2790,00 €")
    app.ir("inversion")
    expect(p.locator("#invHistList .mov-item")).to_have_count(5)
    expect(p.locator("#invValorActual")).to_have_text("1900,00 €")
    assert p.locator(".skeleton").count() == 0


def test_sin_cambios_no_se_repinta(abrir):
    app = abrir(reducir=False)
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    p.evaluate("()=>{window.__fila=document.querySelector('#recentMovs .mov-item')}")
    app.ir("inicio")
    app.ir("movimientos")
    p.wait_for_load_state("networkidle")
    p.wait_for_timeout(300)
    assert p.evaluate("()=>document.querySelector('#recentMovs .mov-item')===window.__fila")


def test_si_cambia_algo_se_repinta_en_silencio(abrir):
    app = abrir(antes=con_red_controlada)
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    app.ir("inicio")
    datos.gasto(app.notion, "Hecho en otro dispositivo", "2026-11-15", 7)
    app.ir("movimientos")
    assert p.locator("#recentMovs .skeleton").count() == 0
    expect(app.fila_mov("Hecho en otro dispositivo")).to_be_visible()


def test_un_fallo_al_refrescar_no_borra_lo_que_se_ve(app):
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    app.ir("inicio")
    app.notion.fallar_consultas.add(datos.BASES["movs"])
    app.ir("movimientos")
    app.page.wait_for_load_state("networkidle")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    expect(app.page.locator("#recentMovs")).not_to_contain_text("Error")


def registrar_gasto(app, importe, nombre):
    p = app.page
    app.ir("registrar")
    p.locator("#inputAmt").fill(importe)
    p.locator("#inputName").fill(nombre)
    p.locator("#accountChips .chip", has_text="Ibercaja").click()
    p.locator("#submitBtn").click()
    expect(app.toast()).to_contain_text("Gasto registrado")


def test_tras_registrar_todo_al_dia_incluido_el_carrusel(app):
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    app.ir("cuentas")
    expect(app.cuenta("Ibercaja").locator(".account-balance")).to_have_text("2790,00 €")
    registrar_gasto(app, "10", "Churros")
    app.ir("inicio")
    expect(p.locator("#quickAccounts .qa-card", has_text="Ibercaja")).to_contain_text("2780,00 €")
    expect(p.locator("#resGasto")).to_have_text("-154,50 €")
    expect(p.locator("#totalAmount")).to_have_text("5915,00 €")
    app.ir("cuentas")
    expect(app.cuenta("Ibercaja").locator(".account-balance")).to_have_text("2780,00 €")
    app.ir("movimientos")
    expect(app.fila_mov("Churros")).to_be_visible()


def test_el_refresco_llega_sin_cambiar_de_pestana(app):
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_be_visible()
    app.fila_mov("Mercadona").locator(".mov-icon").click()
    p.locator("#editAmt").fill("90")
    p.locator("#editOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Movimiento actualizado")
    # El carrusel de Inicio (oculto) ya está al día antes de volver
    expect(p.locator("#quickAccounts .qa-card", has_text="Ibercaja")).to_contain_text("2784,50 €")


def test_los_periodos_de_inicio_se_recalculan_tras_escribir(app):
    p = app.page
    p.locator('.pat-period[data-p="3M"]').click()
    expect(p.locator("#resGasto")).to_have_text("-220,00 €")
    registrar_gasto(app, "10", "Churros")
    app.ir("inicio")
    expect(p.locator("#resGasto")).to_have_text("-230,00 €")
    p.locator('.pat-period[data-p="Todo"]').click()
    expect(p.locator("#resGasto")).to_have_text("-1530,00 €")
    p.locator('.pat-period[data-p="1M"]').click()
    expect(p.locator("#resGasto")).to_have_text("-154,50 €")


def test_un_periodo_ya_visto_sale_al_momento_sin_atenuar(abrir):
    app = abrir(antes=con_red_controlada)
    p = app.page
    p.locator('.pat-period[data-p="3M"]').click()
    expect(p.locator("#resGasto")).to_have_text("-220,00 €")
    p.locator('.pat-period[data-p="1M"]').click()
    expect(p.locator("#resGasto")).to_have_text("-144,50 €")
    sin_red(app)
    p.locator('.pat-period[data-p="3M"]').click()
    expect(p.locator("#resGasto")).to_have_text("-220,00 €")
    expect(p.locator("#sec-inicio .hero-card .hero-row")).not_to_have_class(re.compile(r"cargando"))


def test_borrar_y_deshacer_se_mantienen_al_cambiar_de_pestana(app):
    p = app.page
    app.ir("movimientos")
    app.borrar_fila(app.fila_mov("Mercadona"))
    expect(app.toast()).to_contain_text("Movimiento eliminado")
    app.ir("inicio")
    app.ir("movimientos")
    expect(app.fila_mov("Mercadona")).to_have_count(0)
    p.evaluate("()=>{const b=document.querySelector('#toast .toast-accion');if(b)b.click()}")
    expect(app.fila_mov("Mercadona")).to_be_visible()


def test_el_scroll_de_cada_pestana_se_conserva(abrir):
    def muchos(n):
        for i in range(40):
            datos.gasto(n, "Compra %02d" % i, "2026-11-%02d" % (1 + i % 14), 1 + i)
    app = abrir(mas=muchos)
    p = app.page
    app.ir("movimientos")
    expect(app.fila_mov("Compra 39")).to_be_visible()
    p.evaluate("()=>window.scrollTo(0,900)")
    p.wait_for_timeout(100)
    app.ir("inicio")
    app.ir("movimientos")
    assert abs(p.evaluate("()=>scrollY") - 900) < 2
    p.wait_for_load_state("networkidle")
    p.wait_for_timeout(300)
    assert abs(p.evaluate("()=>scrollY") - 900) < 2


def test_como_mucho_cuatro_peticiones_a_la_vez(abrir):
    app = abrir(antes=con_red_controlada)
    p = app.page
    for seccion in ("movimientos", "cuentas", "inversion", "stats", "inicio"):
        app.ir(seccion)
    registrar_gasto(app, "3", "Café")
    p.wait_for_load_state("networkidle")
    p.wait_for_timeout(600)
    assert 1 <= p.evaluate("()=>window.__maxAVez") <= 4


def test_varias_escrituras_seguidas_dan_un_solo_refresco(app):
    p = app.page
    app.ir("cuentas")
    expect(app.cuenta("Ibercaja").locator(".account-balance")).to_have_text("2790,00 €")
    antes = len(app.peticiones_api)
    # Transferencia a MyInvestor: dos escrituras (transferencia y aportación)
    app.desplegar_cuenta("Ibercaja").locator(".acc-action", has_text="Mover").click()
    p.locator("#transferToChips .chip").filter(has_text="MyInvestor").first.click()
    p.locator("#transferAmt").fill("20")
    p.locator("#transferOverlay .modal-confirm").click()
    expect(app.toast()).to_contain_text("Transferencia registrada")
    p.wait_for_load_state("networkidle")
    p.wait_for_timeout(800)
    # Un refresco completo son ~20 consultas; dos refrescos (uno por escritura) serían el doble
    assert len(app.peticiones_api) - antes < 34, len(app.peticiones_api) - antes


def test_si_fallan_las_transferencias_no_se_guarda_una_lista_incompleta(app):
    app.ir("movimientos")
    expect(app.fila_mov("Ibercaja → Revolut Personal")).to_be_visible()
    app.ir("inicio")
    app.notion.fallar_consultas.add(datos.BASES["transfers"])
    app.ir("movimientos")
    app.page.wait_for_load_state("networkidle")
    app.page.wait_for_timeout(300)
    # Con datos guardados se conserva la lista completa, transferencias incluidas
    expect(app.fila_mov("Ibercaja → Revolut Personal")).to_be_visible()
    expect(app.fila_mov("Mercadona")).to_be_visible()


CONTADOR = """(()=>{window.__total=[];new MutationObserver(()=>{const e=document.getElementById('totalAmount');
  if(e&&window.__total[window.__total.length-1]!==e.textContent)window.__total.push(e.textContent);})
  .observe(document,{childList:true,subtree:true,characterData:true});})();"""


def valores_total(p):
    # La app escribe la cifra final un instante (para ajustar su tamaño) antes de contar: se espera al final de la cuenta
    p.wait_for_function("()=>document.getElementById('totalAmount').dataset.rawVal==='5925'", timeout=4000)
    return [float(x.replace(" €", "").replace(".", "").replace(",", ".")) for x in p.evaluate("()=>window.__total") if "€" in x]


def test_al_abrir_el_patrimonio_sube_desde_cero(abrir):
    app = abrir(antes=lambda page: page.add_init_script(CONTADOR))
    p = app.page
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    p.wait_for_timeout(300)
    p.evaluate("()=>{window.__total=[]}")
    p.reload()  # ya con caché: también debe subir desde 0
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    v = valores_total(p)
    assert v[0] < 1000 and v[-1] == 5925 and len(v) > 3, v


def test_si_notion_tarda_sube_hasta_el_guardado(abrir):
    def antes(page):
        page.add_init_script(CONTADOR)
        con_red_controlada(page)
    app = abrir(antes=antes)
    p = app.page
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")
    p.wait_for_timeout(600)
    p.evaluate("()=>sessionStorage.setItem('sin-red','1')")
    p.reload()
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €", timeout=4000)
    v = valores_total(p)
    assert v[0] < 1000 and v[-1] == 5925, v
