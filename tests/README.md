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
- **Fecha:** el reloj está fijo (15/11/2026 salvo que la prueba indique otra), así que los resultados no dependen del día.
- **Capturas:** referencia en `screenshots/baseline/`; las últimas y las diferencias (`-diff.png`), en `screenshots/current/`. Son propias de este Mac (Chromium y emojis del sistema) y sin la fuente Inter, porque no se descarga.
- **`xfail`:** fallos conocidos de la app. Cuando se arreglen, la prueba avisará: entonces se quita la marca.
