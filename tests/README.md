# Tests de Ka$hy

Primera vez (crea `.venv` y `.browsers`, ignorados en git): `tests/setup.sh`

Ejecutar, desde la raíz del proyecto:

```
tests/.venv/bin/pytest tests                 # todo, en los dos temas (~1 min 10 s)
tests/.venv/bin/pytest tests -k claro        # solo tema claro (~35 s)
tests/.venv/bin/pytest tests/test_inicio.py  # un solo archivo
tests/.venv/bin/pytest tests -k capturas --update-baseline   # acepta un cambio visual deliberado
```

- **Datos:** `notion_mock.py` simula Notion en memoria y `datos.py` trae datos inventados. Toda petición se intercepta en el navegador; si la app intenta salir a la red, salvo las fuentes de Google (que se bloquean), la prueba falla.
- **Clave:** el servidor simulado exige `X-Kashy-Key` como el real, con una clave de prueba inventada. `test_api_clave.py` ejecuta el código real de `api/` con Node y `fetch` simulado.
- **Fecha:** el reloj está fijo (15/11/2026 salvo que la prueba indique otra), así que los resultados no dependen del día.
- **Capturas:** referencia en `screenshots/baseline/`; las últimas y las diferencias (`-diff.png`), en `screenshots/current/`. Son propias de este Mac (Chromium y emojis del sistema) y sin la fuente Inter, porque no se descarga.
- **`xfail`:** fallos conocidos de la app. Cuando se arreglen, la prueba avisará: entonces se quita la marca.

## Refactorizar CSS

`comparar_estilos.py` es una comprobación opcional, fuera de pytest, para cambios de CSS que no deben alterar nada. Compara los estilos calculados de todos los elementos con los de una versión de git, en muchos estados que las capturas no ven: modales, `:active`, modo privado, movimiento normal y reducido.

```
tests/.venv/bin/python tests/comparar_estilos.py            # HEAD contra tu index-nuevo.html (~5 min)
tests/.venv/bin/python tests/comparar_estilos.py --rapido   # solo 2 de las 6 combinaciones (~2 min)
tests/.venv/bin/python tests/comparar_estilos.py main~3     # contra otra versión
```

Sale con código 0 si no hay diferencias y 1 si las hay. No compara `@keyframes` ni barras de desplazamiento, y usa Chromium, no Safari.
