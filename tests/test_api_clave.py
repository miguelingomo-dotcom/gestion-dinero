"""Ejecuta el código real de api/ con Node y fetch simulado: sin red, sin Notion."""
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
        r = subprocess.run(["node", str(RAIZ / "tests" / "api_clave.mjs"), str(destino)],
                           capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "endpoints: 5" in r.stdout, r.stdout
