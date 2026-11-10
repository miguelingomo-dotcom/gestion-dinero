"""Interruptor de notificaciones y botón de prueba, con Notification, PushManager y service worker simulados."""
import json
import re

from playwright.sync_api import expect

import datos

# Navegador con Web Push simulado. window.__push lleva el estado; __push.respuesta es lo que contesta al permiso
SIMULADO = """(()=>{
  const st=window.__push={permiso:%s,pedidos:0,respuesta:'granted',sub:%s,suscritas:0,bajas:0,clave:0,oyente:null};
  const nueva=ep=>({endpoint:ep,toJSON(){return{endpoint:this.endpoint,keys:{p256dh:'p256',auth:'auth'}}},
    unsubscribe(){st.bajas++;st.sub=null;return Promise.resolve(true)}});
  if(st.sub)st.sub=nueva(st.sub);
  window.Notification=class{static get permission(){return st.permiso}
    static requestPermission(){st.pedidos++;st.permiso=st.respuesta;return Promise.resolve(st.permiso)}};
  window.PushManager=function(){};
  const reg={pushManager:{getSubscription:()=>Promise.resolve(st.sub),
    subscribe:o=>{st.suscritas++;st.clave=o.applicationServerKey.length;st.userVisible=o.userVisibleOnly;st.sub=nueva('https://push.example/nueva');return Promise.resolve(st.sub)}}};
  Object.defineProperty(navigator,'serviceWorker',{configurable:true,value:{register:u=>{st.registrado=u;return Promise.resolve(reg)},
    ready:Promise.resolve(reg),addEventListener:(t,f)=>{if(t==='message')st.oyente=f}}});
})();"""


def con_push(permiso="default", sub=None):
    return lambda page: page.add_init_script(SIMULADO % (json.dumps(permiso), json.dumps(sub)))


def interruptor(app):
    return app.page.locator("#notifSwitch")


def estado(app):
    return app.page.evaluate("()=>{const s=window.__push;return {permiso:s.permiso,pedidos:s.pedidos,suscritas:s.suscritas,bajas:s.bajas,clave:s.clave,userVisible:s.userVisible,registrado:s.registrado}}")


def test_al_abrir_no_pide_permiso_y_esta_apagado(abrir):
    app = abrir(antes=con_push())
    app.ir("cuentas")
    expect(interruptor(app)).to_have_attribute("aria-checked", "false")
    expect(app.page.locator("#notifPrueba")).to_be_disabled()
    expect(app.page.locator("#notifMeta")).to_have_text("Entre las 9:00 y las 9:59, si vence algo")
    e = estado(app)
    assert e["pedidos"] == 0 and e["registrado"] == "/sw.js"


def test_activar_pide_permiso_suscribe_y_guarda(abrir):
    app = abrir(antes=con_push())
    app.ir("cuentas")
    interruptor(app).click()
    expect(app.toast()).to_contain_text("Notificaciones activadas")
    expect(interruptor(app)).to_have_attribute("aria-checked", "true")
    expect(app.page.locator("#notifPrueba")).to_be_enabled()
    e = estado(app)
    assert e["pedidos"] == 1 and e["suscritas"] == 1 and e["clave"] == 65 and e["userVisible"] is True
    assert app.push["suscripcion"]["endpoint"] == "https://push.example/nueva"
    assert app.push["suscripcion"]["keys"] == {"p256dh": "p256", "auth": "auth"}


def test_permiso_denegado_no_suscribe(abrir):
    app = abrir(antes=con_push())
    app.page.evaluate("()=>{window.__push.respuesta='denied'}")
    app.ir("cuentas")
    interruptor(app).click()
    expect(app.toast()).to_contain_text("Ajustes › Notificaciones")
    expect(interruptor(app)).to_have_attribute("aria-checked", "false")
    assert estado(app)["suscritas"] == 0 and app.push["suscripcion"] is None


def test_desactivar_da_de_baja_en_el_iphone_y_en_el_servidor(abrir):
    app = abrir(antes=con_push("granted", "https://push.example/vieja"))
    app.push["suscripcion"] = {"endpoint": "https://push.example/vieja"}
    app.ir("cuentas")
    expect(interruptor(app)).to_have_attribute("aria-checked", "true")
    interruptor(app).click()
    expect(app.toast()).to_contain_text("Notificaciones desactivadas")
    expect(interruptor(app)).to_have_attribute("aria-checked", "false")
    assert estado(app)["bajas"] == 1 and app.push["suscripcion"] is None


def test_al_abrir_reenvia_la_suscripcion_si_el_servidor_no_la_tiene(abrir):
    app = abrir(antes=con_push("granted", "https://push.example/movil"))
    app.ir("cuentas")
    expect(interruptor(app)).to_have_attribute("aria-checked", "true")
    app.page.wait_for_load_state("networkidle")
    assert app.push["suscripcion"]["endpoint"] == "https://push.example/movil"
    assert app.push["guardados"] == 1


def test_al_abrir_no_reescribe_si_ya_coincide(abrir):
    def antes(page):
        con_push("granted", "https://push.example/movil")(page)
    app = abrir(antes=antes)
    app.page.wait_for_load_state("networkidle")
    app.push["suscripcion"] = {"endpoint": "https://push.example/movil"}
    app.push["guardados"] = 0
    app.page.reload()
    app.page.wait_for_load_state("networkidle")
    app.page.wait_for_timeout(300)
    assert app.push["guardados"] == 0


def test_boton_de_prueba(abrir):
    app = abrir(antes=con_push("granted", "https://push.example/movil"))
    app.push["suscripcion"] = {"endpoint": "https://push.example/movil"}
    app.ir("cuentas")
    expect(app.page.locator("#notifPrueba")).to_be_enabled()
    app.page.locator("#notifPrueba").click()
    expect(app.toast()).to_contain_text("Enviada")
    assert app.push["pruebas"] == 1


def test_prueba_con_suscripcion_caducada_apaga_el_interruptor(abrir):
    app = abrir(antes=con_push("granted", "https://push.example/movil"))
    app.push["suscripcion"] = {"endpoint": "https://push.example/movil"}
    app.push["codigo_prueba"] = 410
    app.ir("cuentas")
    app.page.locator("#notifPrueba").click()
    expect(app.toast()).to_contain_text("vuelve a activarlas")
    expect(interruptor(app)).to_have_attribute("aria-checked", "false")
    expect(app.page.locator("#notifPrueba")).to_be_disabled()


def test_sin_soporte_explica_que_hay_que_instalarla(abrir):
    app = abrir(antes=lambda page: page.add_init_script("delete window.PushManager"))
    app.ir("cuentas")
    expect(interruptor(app)).to_be_disabled()
    expect(app.page.locator("#notifMeta")).to_contain_text("pantalla de inicio")


def test_tocar_la_notificacion_con_la_app_abierta_vuelve_a_inicio(abrir):
    app = abrir(antes=con_push("granted", "https://push.example/movil"))
    app.ir("cuentas")
    app.page.evaluate("()=>window.__push.oyente({data:{tipo:'ir-inicio'}})")
    expect(app.page.locator("#sec-inicio")).to_have_class(re.compile(r"\bactive\b"))


def test_manifest_para_instalar_en_el_iphone():
    m = json.loads((datos.RAIZ / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert m["start_url"] == "/index-nuevo.html" and m["display"] == "standalone" and m["scope"] == "/"
    for icono in m["icons"]:
        assert (datos.RAIZ / icono["src"].lstrip("/")).exists()
    assert '<link rel="manifest" href="/manifest.webmanifest">' in datos.HTML


def test_vercel_cron_en_la_franja_de_las_9_en_madrid():
    v = json.loads((datos.RAIZ / "vercel.json").read_text(encoding="utf-8"))
    horas = sorted(c["schedule"] for c in v["crons"])
    assert horas == ["0 7 * * *", "0 8 * * *"]  # 9:00 en Madrid: 07 UTC en verano, 08 UTC en invierno
    assert all(c["path"].startswith("/api/cron-avisos") for c in v["crons"])


def test_si_la_prueba_falla_muestra_el_motivo(abrir):
    app = abrir(antes=con_push("granted", "https://push.example/movil"))
    app.push["suscripcion"] = {"endpoint": "https://push.example/movil"}
    app.push["codigo_prueba"] = 502
    app.ir("cuentas")
    app.page.locator("#notifPrueba").click()
    expect(app.toast()).to_have_text("No se pudo enviar: El servicio push respondió 403")
    expect(interruptor(app)).to_have_attribute("aria-checked", "true")
