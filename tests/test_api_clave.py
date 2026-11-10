"""Ejecuta el código real de api/ con Node y fetch simulado: sin red, sin Notion."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(not shutil.which("node"), reason="Hace falta Node para ejecutar api/")
def test_todos_los_endpoints_exigen_la_clave():
    with tempfile.TemporaryDirectory() as tmp:
        destino = Path(tmp) / "api"
        shutil.copytree(RAIZ / "api", destino)
        (Path(tmp) / "package.json").write_text('{"type":"module"}')
        shutil.copy(RAIZ / "kashy-vencimientos.js", Path(tmp) / "kashy-vencimientos.js")
        if (RAIZ / "node_modules").exists():
            os.symlink(RAIZ / "node_modules", Path(tmp) / "node_modules")
        r = subprocess.run(["node", str(RAIZ / "tests" / "api_clave.mjs"), str(destino)],
                           capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "endpoints: 6" in r.stdout, r.stdout
