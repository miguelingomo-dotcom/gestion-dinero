"""Comparación de capturas contra la referencia guardada en tests/screenshots/baseline."""
from pathlib import Path

from PIL import Image, ImageChops

AQUI = Path(__file__).resolve().parent
BASELINE = AQUI / "screenshots" / "baseline"
ACTUAL = AQUI / "screenshots" / "current"  # ignorada en git: últimas capturas y diferencias

UMBRAL_PIXEL = 16  # diferencia por canal por debajo de la cual un píxel se considera igual
MAX_CAMBIO = 0.00005  # proporción de píxeles distintos admitida (0,005 %): detecta el color de un solo importe


def comparar(nombre, png, actualizar):
    """Devuelve None si coincide; si no, el mensaje de error. Con actualizar=True reescribe la referencia."""
    ref = BASELINE / (nombre + ".png")
    if actualizar:
        BASELINE.mkdir(parents=True, exist_ok=True)
        ref.write_bytes(png)
        return None
    ACTUAL.mkdir(parents=True, exist_ok=True)
    actual = ACTUAL / (nombre + ".png")
    actual.write_bytes(png)
    if not ref.exists():
        return "Falta la referencia %s. Créala con --update-baseline" % ref.name
    a = Image.open(ref).convert("RGB")
    b = Image.open(actual).convert("RGB")
    if a.size != b.size:
        return "%s: tamaño distinto (referencia %s, actual %s). Actual: %s" % (nombre, a.size, b.size, actual)
    dif = ImageChops.difference(a, b)
    gris = dif.split()
    mascara = ImageChops.lighter(ImageChops.lighter(gris[0], gris[1]), gris[2]).point(lambda v: 255 if v > UMBRAL_PIXEL else 0)
    cambiados = mascara.histogram()[255]
    proporcion = cambiados / float(a.size[0] * a.size[1])
    if proporcion <= MAX_CAMBIO:
        return None
    mapa = ACTUAL / (nombre + "-diff.png")
    Image.composite(Image.new("RGB", a.size, (255, 0, 80)), b.point(lambda v: v // 3), mascara).save(mapa)
    return "%s: cambia el %.2f %% de los píxeles. Revisa %s" % (nombre, proporcion * 100, mapa)
