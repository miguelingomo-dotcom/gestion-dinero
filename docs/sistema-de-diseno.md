# Ka$hy · Sistema de diseño (fase 1: propuesta)

Propuesta para que Ka$hy se sienta como una app de finanzas nativa del nivel de Revolut o Trade Republic, sin copiar su marca. El demo `rediseno-demo.html` (no enlazado desde la app, con datos de ejemplo) aplica todo esto a Inicio y Movimientos. Nada de esto está aún en `index-nuevo.html`.

## 1. Qué hace que Revolut y Trade Republic se sientan premium

| Aspecto | Qué hacen | Principio para Ka$hy |
|---|---|---|
| Tipografía | Fuente de sistema o propia muy cuidada, pocos tamaños, jerarquía por peso | SF Pro (fuente del sistema) con 7 tamaños fijos; jerarquía con peso y color, no con tamaño |
| Números | Cifra principal enorme, decimales más pequeños, cifras de ancho fijo | Patrimonio a 48 pt con los decimales a 28 pt en gris; `tabular-nums` en todas las cantidades |
| Color | Base neutra casi monocroma; el color solo significa algo | Fondo y superficies neutras; un único acento (morado Ka$hy) para lo pulsable y lo seleccionado; verde solo para ingresos y subidas; rojo solo para errores, borrar y saldos negativos. **Los gastos van en el color del texto, no en rojo** |
| Espacio | Mucho aire, márgenes constantes, nada pegado | Escala de 4 px; márgenes laterales de 16 y 20 px |
| Tarjetas | Pocas, grandes, radio generoso; agrupan, no decoran | Listas agrupadas (estilo iOS) con separadores finos sangrados; sombras casi nulas en claro y ninguna en oscuro |
| Listas | Filas de 60-64 pt con icono en ficha, título, subtítulo e importe a la derecha | Fila estándar: ficha de 40 pt, título 16 pt, subtítulo 13 pt en gris, importe 16 pt alineado a la derecha |
| Transiciones | Cortas, sin rebote gratuito; las hojas siguen al dedo | Interacción en 120-240 ms con curvas propias; la hoja sigue al dedo 1:1 y se cierra con un gesto rápido |
| Hojas | Hojas desde abajo con asa, fondo oscurecido, arrastrar para cerrar | Hoja con asa, velo y arrastre con resistencia hacia arriba |
| Vacíos y carga | Esqueletos con la forma real; vacíos con una frase útil | Esqueleto solo sin datos guardados; vacío con icono, una línea y qué hacer |

## 2. Tokens

### Color
| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--bg` | `#F4F4F7` | `#0B0B0E` | Fondo de pantalla |
| `--surface` | `#FFFFFF` | `#17171C` | Tarjetas, grupos, hojas |
| `--surface-2` | `#F0F0F4` | `#202027` | Bloques dentro de una hoja |
| `--fill` | gris al 12 % | gris al 24 % | Botones secundarios, chips, buscador, ficha neutra |
| `--text` / `--text-2` / `--text-3` | `#0B0B0F` / `#62626E` / `#8E8E99` | `#F4F4F6` / `#A1A1AC` / `#73737E` | Texto principal, secundario y terciario |
| `--separator` | gris al 16 % | gris al 42 % | Separadores de 0,5 px |
| `--accent` | `#5B4CEB` | `#A197FF` | Acción principal, selección, gráfica |
| `--positive` | `#0A8A4A` | `#3DD68C` | Ingresos, subidas |
| `--negative` | `#D0342C` | `#FF7A70` | Borrar, errores, saldo negativo |
| `--warning` | `#B26B00` | `#FFC247` | Avisos («Hoy vence») |

Las barras superior e inferior usan un material translúcido (`backdrop-filter`) con el fondo debajo; con «Reducir transparencia» pasan a ser opacas.

### Tipografía (SF Pro por `-apple-system`; números grandes en SF Pro Rounded)
| Estilo | Tamaño / peso | Interletraje |
|---|---|---|
| Cifra principal | 48 / 700, decimales 28 / 600 | −0,035 em |
| Título grande | 34 / 700 | −0,025 em |
| Título de sección | 20 / 700 | −0,02 em |
| Cuerpo y botones | 17 / 400-600 | −0,01 em |
| Fila (título / importe) | 16 / 500-600 | −0,01 em |
| Secundario | 15 / 500 | 0 |
| Pie y subtítulos | 13 / 500 | 0; en mayúsculas +0,04 em |

### Espaciado, radios y elevación
- **Espaciado:** 4, 8, 12, 16, 20, 24 y 32 px. Margen lateral de 20 px en textos y 16 px en grupos.
- **Radios:** 10 (ficha pequeña), 14 (ficha, buscador, botón), 20 (tarjeta y grupo), 28 (hoja) y píldora (chips, selector de periodo).
- **Elevación:** en claro, una sombra mínima solo en tarjetas; en oscuro, sin sombras y con superficies más claras cuanto más arriba están.

### Movimiento
| Token | Valor | Uso |
|---|---|---|
| `--d-press` | 120 ms, `ease-out` | Pulsación (`scale(.97)`) |
| `--d-fast` | 180 ms | Color de chips y pestañas |
| `--d-base` | 240 ms | Cambio de pantalla, selector de periodo |
| `--d-sheet` | 420 ms, `cubic-bezier(.32,.72,0,1)` | Abrir y cerrar hojas |
| Contador | 900 ms, ease-out | Patrimonio desde 0 al entrar |
| Iconos | 320-700 ms | Las 7 familias (abajo) |

Con «Reducir movimiento», todo pasa a ser instantáneo o a un simple fundido.

## 3. Componentes
- **Cabecera:** se pliega al hacer scroll y muestra el título pequeño (en Inicio, el patrimonio redondeado).
- **Fila de lista:** ficha, título y subtítulo, e importe. Los grupos se cabecean por día, con el balance del día a la derecha.
- **Ficha:** categoría (icono Lucide sobre su color al 12 %), marca (logo sobre su color oficial) o inicial (letra sobre el color del banco).
- **Chips de filtro:** píldoras grises; el seleccionado se invierte (texto sobre fondo de texto).
- **Botones:** primario (acento), secundario (`--fill`) y peligro (texto rojo). Siempre de 50 pt de alto en hojas.
- **Selector de periodo:** control segmentado con una marca que se desliza.
- **Hoja:** asa, velo, arrastre 1:1, resistencia hacia arriba y cierre al pasar del 30 % o con un gesto rápido.
- **Barra de pestañas:** 5 huecos, iconos de línea, botón «+» central en el color de acento.
- **Gráfica:** línea de 2,25 px con degradado suave; al deslizar el dedo muestra el valor de ese día en la cifra principal.

## 4. Iconos

### Categorías: Lucide (licencia ISC)
- Más de 1.500 iconos de línea en una retícula de 24 px y un solo grosor, y casi todos están hechos de varios trazos separados. Eso permite **animar por partes** (el vapor del café, por ejemplo) con las mismas 7 familias que ya usa Ka$hy.
- La licencia ISC permite usarlos en cualquier proyecto; solo exige conservar el aviso de copyright en el código, y el demo ya lo incluye.
- Alternativas descartadas: Phosphor (MIT, pero muchos iconos son un único trazado y no se pueden animar por partes) y Tabler (MIT, con un estilo más técnico).

| Categoría | Icono | Familia | Partes animadas |
|---|---|---|---|
| Supermercado | `shopping-cart` | avance | todo |
| Restaurantes | `utensils` | balanceo | todo |
| Café | `coffee` | flote | vapor (trazos 1, 2 y 4) |
| Helados | `ice-cream-cone` | salto | todo |
| Comida rápida | `sandwich` | latido | todo |
| Gasolina | `fuel` | latido | todo |
| Coche | `car` | avance | todo |
| Ropa | `shirt` | balanceo | todo |
| Apuestas | `dices` | giro | todo |
| Farmacia | `pill` | balanceo | todo |
| Ocio | `gamepad-2` | zumbido | todo |
| Regalos | `gift` | salto | todo |
| Bizum | `smartphone` | zumbido | todo |
| Viajes | `plane` | avance | todo |
| Hogar | `house` | latido | todo |
| Suscripciones | `repeat` | giro | todo |
| Peluquería | `scissors` | zumbido | todo |
| Salud | `heart-pulse` | latido | todo |
| Educación | `graduation-cap` | salto | todo |
| Libros | `book-open` | flote | todo |
| Nómina | `briefcase-business` | salto | todo |
| Remuneración / Wins / Otros | `hand-coins` / `trophy` / `wallet` | salto / latido / flote | todo |
| Transferencia | `arrow-left-right` | avance | todo |
| Efectivo | `banknote` | flote | todo |

### Marcas y bancos: Simple Icons (licencia CC0)
- **Hay logo oficial de:** Spotify, DAZN, IKEA, iCloud, Claude y Revolut. Cada uno va sobre su color oficial de Simple Icons.
- **No están** en Simple Icons: Ibercaja, Sabadell, MyInvestor, Openbank y Pluxee. Llevan su inicial sobre un color de la marca. Los del demo son **provisionales**: no los he comprobado en fuentes oficiales, y en la fase 2 se fijarán a partir del manual de marca de cada banco (o de los `BANK_COLORS` actuales de la app). No se dibuja ningún logo a mano.
- **Licencia:** los SVG de Simple Icons son de dominio público, pero las marcas siguen siendo de sus dueños. Se usan solo para identificar el servicio en una app personal y sin modificar su forma.

### Emojis guardados en Notion
- Los nombres de Notion se quedan como están («🎵 Spotify», «🤖 Claude Pro»), porque `kashy-vencimientos.js` y el registro de cuotas dependen del nombre exacto.
- La app quita el emoji solo al mostrar el nombre y elige el icono así: (1) si el nombre contiene una marca conocida, su logo; (2) si no, el icono de su categoría, según el id de la relación «Fuente de Gasto/Ingreso»; (3) si tampoco hay categoría, `wallet`.
- Las cuentas se identifican por su id, no por el emoji de su nombre.
- Los emojis de las constantes de la app (`GASTOS`, `INGRESOS`, `CUENTAS`) pasan a ser nombres de icono.

## 5. Fase 2 (cuando des el visto bueno)
Se migraría pantalla a pantalla para que los tests de regresión vayan detectando cambios: tokens y tipografía, luego Inicio, Movimientos, Registrar, Cuentas, Inversión y Estadísticas, y al final las hojas. Las capturas de referencia se renovarían en cada paso, revisándolas antes.
