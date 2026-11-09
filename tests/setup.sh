#!/bin/sh
# Crea el entorno local de los tests (tests/.venv y tests/.browsers, ignorados en git). Ocupa unos 355 MB.
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -q --disable-pip-version-check -r requirements.txt
PLAYWRIGHT_BROWSERS_PATH="$PWD/.browsers" .venv/bin/playwright install --only-shell chromium
echo "Listo. Ejecuta desde la raíz del proyecto: tests/.venv/bin/pytest tests"
