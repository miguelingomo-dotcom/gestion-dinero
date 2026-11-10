"""Ejecuta tests/push_servidor.mjs con Node sobre una copia del código: sin red real ni notificaciones reales."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(not shutil.which("node"), reason="Hace falta Node")
@pytest.mark.skipif(not (RAIZ / "node_modules" / "web-push").exists(), reason="Ejecuta «npm install» en la raíz del proyecto")
def test_notificaciones_en_el_servidor():
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        shutil.copytree(RAIZ / "api", t / "api")
        for f in ("kashy-vencimientos.js", "sw.js"):
            shutil.copy(RAIZ / f, t / f)
        (t / "package.json").write_text('{"type":"module"}')
        os.symlink(RAIZ / "node_modules", t / "node_modules")
        r = subprocess.run(["node", str(RAIZ / "tests" / "push_servidor.mjs"), str(t)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "pruebas: 21" in r.stdout, r.stdout
