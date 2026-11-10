"""Datos ficticios de las pruebas. Los ids son los de las constantes públicas de la app; los importes y
nombres son inventados. Fecha de referencia: 15/11/2026."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HTML = (RAIZ / "index-nuevo.html").read_text(encoding="utf-8")


def _constante(nombre):
    return re.search(r"const %s='([0-9a-f]{32})'" % nombre, HTML).group(1)


BASES = {"movs": _constante("DB_ID"), "cuentas": _constante("CUENTAS_DB"),
         "transfers": _constante("TRANSFER_DB")}

REVOLUT = "31621c54013f817f9f00fc6acc160c26"
IBERCAJA = "31621c54013f811ebd49f65e2776d28e"
SABADELL = "3b821c54013f81d1abfafae8f2fd00e4"
MYINVESTOR = "3b821c54013f817088e9fe2e7a0a3707"
REMUNERADA = "3d821c54013f81eab324f5174d95ade2"
EFECTIVO = "31621c54013f813483ded3bbd77a5e10"

CAT_SUPER = "31621c54013f815cbebbf321cd287ac9"
CAT_RESTAURANTES = "31621c54013f815794d0e6ee1cae8af4"
CAT_GASOLINA = "31621c54013f8119a964c44adbb84017"
CAT_COCHE = "31621c54013f81689c53c344e9ce8987"
CAT_HOGAR = "31621c54013f816d85afc5277c4e2c08"
CAT_OCIO = "31621c54013f8196b8d4dc7c51c738b2"
CAT_SUSCRIPCIONES = "31621c54013f8130bd7ddbf775f0f1bd"
CAT_NOMINA = "31621c54013f81d69e4af11bee366830"

HOY = "2026-11-15"

# Ids fijos de filas a las que las pruebas se refieren por su nombre
MOV_MERCADONA = "a0000000000000000000000000000001"
MOV_NOMINA = "a0000000000000000000000000000002"
TR_REVOLUT = "b0000000000000000000000000000001"
TR_APORTACION = "b0000000000000000000000000000002"
TR_ANTIGUA = "b0000000000000000000000000000003"
AP_ENLAZADA = "c0000000000000000000000000000001"
AP_ANTIGUA = "c0000000000000000000000000000002"
VAL_SP500 = "d0000000000000000000000000000001"


def titulo(texto):
    return {"title": [{"plain_text": texto}]}


def relacion(id):
    return {"relation": [{"id": id}]}


def gasto(notion, nombre, fecha, importe, cuenta=IBERCAJA, cat=CAT_SUPER, id=None):
    return notion.anadir("movs", {"Nombre": titulo(nombre), "Fecha": {"date": {"start": fecha}},
                                  "Tipo": {"select": {"name": "Expense"}}, "Gasto": {"number": importe},
                                  "Cuenta": relacion(cuenta), "Fuente de Gasto": relacion(cat)}, id=id)


def ingreso(notion, nombre, fecha, importe, cuenta=IBERCAJA, cat=CAT_NOMINA, id=None):
    return notion.anadir("movs", {"Nombre": titulo(nombre), "Fecha": {"date": {"start": fecha}},
                                  "Tipo": {"select": {"name": "Income"}}, "Ingreso": {"number": importe},
                                  "Cuenta": relacion(cuenta), "Fuente de Ingreso": relacion(cat)}, id=id)


def transferencia(notion, desde, hacia, importe, fecha, nombre="Transferencia", id=None):
    return notion.anadir("transfers", {"Nombre": titulo(nombre), "Monto": {"number": importe},
                                       "Fecha": {"date": {"start": fecha}},
                                       "Transferir Desde": relacion(desde), "Transferir a": relacion(hacia)}, id=id)


def cuenta(notion, nombre, id, saldo, estado="🟢 Activo"):
    return notion.anadir("cuentas", {"Nombre": titulo(nombre), "Cuenta o Meta": {"select": {"name": "Cuenta"}},
                                     "Estado": {"select": {"name": estado}}, "Balance Inicial": {"number": saldo}}, id=id)


def aportacion(notion, importe, fecha, transfer_id=None, id=None):
    props = {"Nombre": titulo("Aportación"), "InvTipo": {"select": {"name": "Aportación"}},
             "InvImporte": {"number": importe}, "InvFecha": {"date": {"start": fecha}}}
    if transfer_id:
        props["InvTransferId"] = {"rich_text": [{"plain_text": transfer_id}]}
    return notion.anadir("cuentas", props, id=id)


def valor_cartera(notion, fondo, importe, fecha, id=None):
    return notion.anadir("cuentas", {"Nombre": titulo("Valor Cartera"), "InvTipo": {"select": {"name": "Valor Cartera"}},
                                     "InvFondo": {"select": {"name": fondo}}, "InvImporte": {"number": importe},
                                     "InvFecha": {"date": {"start": fecha}}}, id=id)


def pago_registrado(notion, nombre, fecha, importe):
    """Movimiento con el nombre exacto que crea «Registrar» en un pago recurrente (emoji + nombre)."""
    return gasto(notion, nombre, fecha, importe, cat=CAT_SUSCRIPCIONES)


def sembrar(notion):
    """Conjunto base. Totales a 15/11/2026:
    1M (mes en curso): gastado 144,50 · ingresado 2000,00 · balance +1855,50
    3M: 220,00 · 4000,00 · +3780,00  |  6M: 520,00 · 4000,00 · +3480,00  |  Todo: 1520,00 · 4000,00 · +2480,00
    Saldos: Ibercaja 2790 · Revolut 290 · Remunerada 850 · Efectivo 20 · Sabadell (inactiva) 75; cartera 1900;
    patrimonio 5925 (la app suma también las cuentas inactivas)."""
    cuenta(notion, "Revolut Personal", REVOLUT, 100)
    cuenta(notion, "💳 Ibercaja", IBERCAJA, 500)
    cuenta(notion, "📈 MyInvestor", MYINVESTOR, 0)
    cuenta(notion, "MyInvestor Remunerada (2,50%)", REMUNERADA, 1000)
    cuenta(notion, "💵 Efectivo", EFECTIVO, 20)
    cuenta(notion, "🟦 Sabadell", SABADELL, 75, estado="🔴 Inactivo")

    ingreso(notion, "Nómina noviembre", "2026-11-01", 2000, id=MOV_NOMINA)
    gasto(notion, "Mercadona", "2026-11-10", 84.5, id=MOV_MERCADONA)
    gasto(notion, "Repsol", "2026-11-14", 60, cuenta=REVOLUT, cat=CAT_GASOLINA)
    ingreso(notion, "Nómina octubre", "2026-10-01", 2000)
    gasto(notion, "Cena con amigos", "2026-10-20", 45.5, cat=CAT_RESTAURANTES)
    gasto(notion, "Pizza", "2026-09-10", 30, cat=CAT_RESTAURANTES)
    gasto(notion, "Seguro", "2026-06-01", 300, cat=CAT_COCHE)
    gasto(notion, "Sofá viejo", "2026-01-15", 1000, cat=CAT_HOGAR)

    transferencia(notion, IBERCAJA, REVOLUT, 250, "2026-11-02", nombre="Ibercaja → Revolut Personal", id=TR_REVOLUT)
    transferencia(notion, REMUNERADA, MYINVESTOR, 150, "2026-10-23", nombre="MyInvestor Remunerada → MyInvestor", id=TR_APORTACION)
    aportacion(notion, 150, "2026-10-23", transfer_id=TR_APORTACION, id=AP_ENLAZADA)
    aportacion(notion, 100, "2026-01-23", id=AP_ANTIGUA)
    valor_cartera(notion, "S&P 500", 1000, "2026-10-01", id=VAL_SP500)
    valor_cartera(notion, "MSCI World", 500, "2026-10-01")
    valor_cartera(notion, "Emergentes", 250, "2026-10-01")
