"""Notion falso en memoria. Sustituye a los proxies /api/* interceptando las peticiones dentro del navegador:
ninguna petición sale de la máquina y los datos reales no se tocan nunca.

Reproduce lo que la app usa de la API de Notion: filtros, orden, paginación, formato de propiedades,
archivado y sus errores (editar una página archivada da 400 validation_error; una inexistente, 404)."""
import json
from datetime import date, timedelta
from urllib.parse import parse_qs, urlparse

APP_ORIGIN = "http://kashy.test"


def _sin_guiones(valor):
    return (valor or "").replace("-", "")


def _texto(items):
    return "".join(x.get("plain_text", "") for x in items or [])


def _normalizar(propiedades):
    """Pasa las propiedades del formato de escritura de Notion al de lectura."""
    salida = {}
    for nombre, valor in propiedades.items():
        valor = json.loads(json.dumps(valor))
        for clave in ("title", "rich_text"):
            if clave in valor:
                for item in valor[clave]:
                    item["plain_text"] = item.get("plain_text") or item.get("text", {}).get("content", "")
        salida[nombre] = valor
    return salida


def _cumple(pagina, filtro):
    if "and" in filtro:
        return all(_cumple(pagina, f) for f in filtro["and"])
    if "or" in filtro:
        return any(_cumple(pagina, f) for f in filtro["or"])
    valor = pagina["properties"].get(filtro["property"], {})
    if "title" in filtro:
        if "contains" in filtro["title"]:  # como Notion: sin distinguir mayúsculas
            return filtro["title"]["contains"].lower() in _texto(valor.get("title")).lower()
        return _texto(valor.get("title")) == filtro["title"]["equals"]
    if "rich_text" in filtro:
        return _texto(valor.get("rich_text")) == filtro["rich_text"]["equals"]
    if "select" in filtro:
        nombre = (valor.get("select") or {}).get("name")
        cond = filtro["select"]
        if "equals" in cond:
            return nombre == cond["equals"]
        if cond.get("is_empty"):
            return nombre is None
        if cond.get("is_not_empty"):
            return nombre is not None
    if "number" in filtro:
        numero = valor.get("number")
        cond = filtro["number"]
        if numero is None:
            return False
        if "equals" in cond:
            return numero == cond["equals"]
        if "greater_than" in cond:
            return numero > cond["greater_than"]
    if "relation" in filtro:
        buscado = _sin_guiones(filtro["relation"]["contains"])
        return any(_sin_guiones(r["id"]) == buscado for r in valor.get("relation") or [])
    if "date" in filtro:
        fecha = (valor.get("date") or {}).get("start")
        cond = filtro["date"]
        if fecha is None:
            return False
        if "on_or_after" in cond:
            return fecha >= cond["on_or_after"]
        if "on_or_before" in cond:
            return fecha <= cond["on_or_before"]
    raise AssertionError("Filtro no soportado por el mock: " + json.dumps(filtro))


class FakeNotion:
    """Estado de una prueba. `escrituras` guarda cada petición de escritura para poder comprobarla."""

    def __init__(self, ids):
        self.ids = ids  # {"movs": id, "cuentas": id, "transfers": id}
        self.bases = {k: [] for k in ids.values()}
        self.escrituras = []  # {"metodo": "POST|PATCH|DELETE", "id": ..., "cuerpo": ...}
        self.fallos = {}  # id de página -> (status, code): fuerza un error al escribir en esa página
        self.fallar_consultas = set()  # bases cuyas consultas responden con error
        self._secuencia = 0

    # ── Datos ──
    def _nuevo_id(self):
        self._secuencia += 1
        return "%032x" % (0xF0000000 + self._secuencia)

    def _creado(self):
        return "2026-01-01T00:00:00.000Z" if self._secuencia == 0 else "2026-01-01T%02d:%02d:%02d.000Z" % (
            self._secuencia // 3600 % 24, self._secuencia // 60 % 60, self._secuencia % 60)

    def anadir(self, base, propiedades, id=None):
        pagina = {
            "object": "page",
            "id": id or self._nuevo_id(),
            "created_time": self._creado(),
            "archived": False,
            "in_trash": False,
            "properties": _normalizar(propiedades),
        }
        if id:
            self._secuencia += 1
        self.bases[self.ids[base] if base in self.ids else base].append(pagina)
        return pagina

    def pagina(self, id):
        id = _sin_guiones(id)
        for filas in self.bases.values():
            for fila in filas:
                if _sin_guiones(fila["id"]) == id:
                    return fila
        return None

    def filas(self, base, archivadas=False):
        return [p for p in self.bases[self.ids[base]] if archivadas or not p["archived"]]

    def activa(self, id):
        """True si la página existe y no está archivada."""
        p = self.pagina(id)
        return bool(p) and not p["archived"]

    def _con_balance(self, pagina):
        """La columna Balance es una fórmula en Notion: saldo inicial + movimientos y transferencias vigentes."""
        props = pagina["properties"]
        if "Balance Inicial" not in props:
            return pagina
        cid = _sin_guiones(pagina["id"])
        saldo = props["Balance Inicial"]["number"]
        for m in self.filas("movs"):
            if any(_sin_guiones(r["id"]) == cid for r in m["properties"].get("Cuenta", {}).get("relation", [])):
                saldo += m["properties"].get("Ingreso", {}).get("number") or 0
                saldo -= m["properties"].get("Gasto", {}).get("number") or 0
        for t in self.filas("transfers"):
            monto = t["properties"].get("Monto", {}).get("number") or 0
            if any(_sin_guiones(r["id"]) == cid for r in t["properties"].get("Transferir a", {}).get("relation", [])):
                saldo += monto
            if any(_sin_guiones(r["id"]) == cid for r in t["properties"].get("Transferir Desde", {}).get("relation", [])):
                saldo -= monto
        copia = json.loads(json.dumps(pagina))
        copia["properties"]["Balance"] = {"type": "formula", "formula": {"number": round(saldo, 2)}}
        return copia

    # ── API ──
    def _consulta(self, db, cuerpo):
        if db in self.fallar_consultas:
            return 400, {"object": "error", "code": "validation_error", "message": "fallo simulado"}
        if db not in self.bases:
            return 404, {"object": "error", "code": "object_not_found"}
        filas = [p for p in self.bases[db] if not p["archived"]]
        if cuerpo.get("filter"):
            filas = [p for p in filas if _cumple(p, cuerpo["filter"])]
        for orden in reversed(cuerpo.get("sorts") or []):
            desc = orden.get("direction") == "descending"
            if "timestamp" in orden:
                filas = sorted(filas, key=lambda p: p["created_time"], reverse=desc)
            else:
                filas = sorted(filas, key=lambda p: (p["properties"].get(orden["property"], {}).get("date") or {}).get("start") or "", reverse=desc)
        inicio = int(cuerpo.get("start_cursor") or 0)
        tam = min(int(cuerpo.get("page_size") or 100), 100)
        trozo = filas[inicio:inicio + tam]
        hay_mas = inicio + tam < len(filas)
        return 200, {"object": "list", "results": [self._con_balance(p) for p in trozo], "has_more": hay_mas,
                     "next_cursor": str(inicio + tam) if hay_mas else None}

    def _error_de(self, id):
        if id in self.fallos:
            status, code = self.fallos[id]
            return status, {"object": "error", "code": code, "message": "fallo simulado"}
        return None

    def _crear(self, cuerpo):
        self.escrituras.append({"metodo": "POST", "id": None, "cuerpo": cuerpo})
        db = _sin_guiones((cuerpo.get("parent") or {}).get("database_id"))
        if not db or db not in self.bases:
            return 400, {"object": "error", "code": "validation_error", "message": "body.parent should be defined"}
        return 200, self.anadir(db, cuerpo.get("properties") or {})

    def _leer(self, id):
        forzado = self._error_de(id)
        if forzado:
            return forzado
        p = self.pagina(id)
        if not p:
            return 404, {"object": "error", "code": "object_not_found"}
        return 200, self._con_balance(p)

    def _editar(self, id, cuerpo):
        self.escrituras.append({"metodo": "PATCH", "id": id, "cuerpo": cuerpo})
        forzado = self._error_de(id)
        if forzado:
            return forzado
        p = self.pagina(id)
        if not p:
            return 404, {"object": "error", "code": "object_not_found"}
        if p["archived"] and cuerpo.get("archived") is not False:
            return 400, {"object": "error", "code": "validation_error", "message": "Can't edit block that is archived."}
        if "archived" in cuerpo:
            p["archived"] = p["in_trash"] = bool(cuerpo["archived"])
        p["properties"].update(_normalizar(cuerpo.get("properties") or {}))
        return 200, p

    def _borrar(self, id):
        self.escrituras.append({"metodo": "DELETE", "id": id, "cuerpo": None})
        forzado = self._error_de(id)
        if forzado:
            return forzado
        p = self.pagina(id)
        if not p:
            return 404, {"object": "error", "code": "object_not_found"}
        if p["archived"]:
            return 400, {"object": "error", "code": "validation_error", "message": "Can't edit block that is archived."}
        p["archived"] = p["in_trash"] = True
        return 200, p

    def _historial(self, consulta):
        """Lo mínimo de /api/history: una serie diaria estable de los últimos 200 días y las filas de inversión."""
        hasta = date.fromisoformat(consulta["hasta"][0])
        dias = 200
        inv = []
        for p in self.filas("cuentas"):
            tipo = (p["properties"].get("InvTipo", {}).get("select") or {}).get("name")
            if tipo:
                inv.append({
                    "tipo": tipo,
                    "importe": p["properties"]["InvImporte"]["number"],
                    "fecha": p["properties"]["InvFecha"]["date"]["start"],
                    "fondo": (p["properties"].get("InvFondo", {}).get("select") or {}).get("name"),
                    "creado": p["created_time"],
                })
        serie = [round(2000 + i * 8 + (i % 7) * 15, 2) for i in range(dias)]
        return 200, {"desde": (hasta - timedelta(days=dias - 1)).isoformat(), "hasta": consulta["hasta"][0],
                     "cuentas": serie, "cuentasHoy": serie[-1], "inv": inv}

    def responder(self, metodo, url, cuerpo):
        """Devuelve (status, json) o None si la ruta no existe en la app."""
        u = urlparse(url)
        consulta = parse_qs(u.query)
        if u.path == "/api/query" and metodo == "POST":
            return self._consulta(consulta["dbId"][0], cuerpo or {})
        if u.path == "/api/page" and metodo == "GET":
            return self._leer(consulta["pageId"][0])
        if u.path == "/api/page" and metodo == "POST":
            return self._crear(cuerpo or {})
        if u.path == "/api/page" and metodo == "PATCH":
            return self._editar(consulta["pageId"][0], cuerpo or {})
        if u.path == "/api/delete" and metodo == "DELETE":
            return self._borrar(consulta["pageId"][0])
        if u.path == "/api/history" and metodo == "GET":
            return self._historial(consulta)
        return None
