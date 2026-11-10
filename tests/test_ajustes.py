"""Hoja de Ajustes (engranaje de Inicio): tema, privacidad, notificaciones y cambiar la clave."""
import re

from playwright.sync_api import expect

from conftest import CLAVE


def test_el_engranaje_abre_ajustes_con_todo(app):
    app.abrir_ajustes()
    hoja = app.page.locator("#ajustesOverlay")
    for texto in ["Tema", "Ocultar importes", "Aviso diario", "Enviar notificación de prueba", "Cambiar clave"]:
        expect(hoja).to_contain_text(texto)
    # Las notificaciones ya no están en Cuentas
    expect(app.page.locator("#sec-cuentas #notifSwitch")).to_have_count(0)
    app.page.locator("#ajustesOverlay .modal-cancel").click()
    expect(hoja).not_to_have_class(re.compile(r"\bshow\b"))


def test_tema_claro_y_oscuro_desde_ajustes(app, tema):
    p = app.page
    app.abrir_ajustes()
    actual = p.evaluate("()=>document.documentElement.dataset.theme")
    assert actual == tema
    marcado = "#temaOscuro" if tema == "dark" else "#temaClaro"
    expect(p.locator(marcado)).to_have_attribute("aria-pressed", "true")
    otro, valor = ("#temaClaro", "light") if tema == "dark" else ("#temaOscuro", "dark")
    p.locator(otro).click()
    assert p.evaluate("()=>document.documentElement.dataset.theme") == valor
    assert p.evaluate("()=>localStorage.getItem('kashy-theme')") == valor
    expect(p.locator(otro)).to_have_attribute("aria-pressed", "true")
    # Tocar el que ya está elegido no cambia nada
    p.locator(otro).click()
    assert p.evaluate("()=>document.documentElement.dataset.theme") == valor


def test_privacidad_en_ajustes_va_a_la_par_que_el_ojo(app):
    p = app.page
    app.abrir_ajustes()
    sw = p.locator("#privSwitch")
    expect(sw).to_have_attribute("aria-checked", "false")
    sw.click()
    expect(sw).to_have_attribute("aria-checked", "true")
    expect(p.locator("body")).to_have_class(re.compile(r"\bkashy-privado\b"))
    p.locator("#ajustesOverlay .modal-cancel").click()
    p.locator("#kashyEyeBtn").click()  # el ojo lo vuelve a mostrar, y el interruptor lo sigue
    expect(p.locator("body")).not_to_have_class(re.compile(r"\bkashy-privado\b"))
    expect(sw).to_have_attribute("aria-checked", "false")


def test_cambiar_clave_y_cancelar_no_toca_la_guardada(app):
    p = app.page
    app.abrir_ajustes()
    p.locator("#btnCambiarClave").click()
    expect(p.locator("#claveScreen")).to_be_visible()
    expect(p.locator("#claveTitulo")).to_have_text("Cambiar clave")
    p.locator("#claveCancelar").click()
    expect(p.locator("#claveScreen")).to_be_hidden()
    assert p.evaluate("()=>localStorage.getItem('kashy-key')") == CLAVE
    # La pantalla vuelve a ser la de siempre para la próxima vez que haga falta
    expect(p.locator("#claveTitulo")).to_have_text("Introduce tu clave")
    expect(p.locator("#claveCancelar")).to_be_hidden()


def test_cambiar_clave_por_la_nueva_de_vercel(app):
    p = app.page
    app.clave_valida = "clave-nueva"  # se cambió en Vercel
    app.abrir_ajustes()
    p.locator("#btnCambiarClave").click()
    p.locator("#claveInput").fill("clave-nueva")
    p.locator("#claveBtn").click()
    expect(app.toast()).to_contain_text("Clave cambiada")
    expect(p.locator("#claveScreen")).to_be_hidden()
    assert p.evaluate("()=>localStorage.getItem('kashy-key')") == "clave-nueva"
    expect(p.locator("#totalAmount")).to_have_text("5925,00 €")


def test_cambiar_a_una_clave_incorrecta_la_vuelve_a_pedir(app):
    p = app.page
    app.abrir_ajustes()
    p.locator("#btnCambiarClave").click()
    p.locator("#claveInput").fill("equivocada")
    p.locator("#claveBtn").click()
    # Al refrescar, el servidor la rechaza y la app la pide como siempre, con el aviso
    expect(p.locator("#claveError")).to_have_text("Clave incorrecta. Vuelve a introducirla.")
    expect(p.locator("#claveTitulo")).to_have_text("Introduce tu clave")
    p.locator("#claveInput").fill(CLAVE)
    p.locator("#claveBtn").click()
    expect(p.locator("#claveScreen")).to_be_hidden()
    assert p.evaluate("()=>localStorage.getItem('kashy-key')") == CLAVE
