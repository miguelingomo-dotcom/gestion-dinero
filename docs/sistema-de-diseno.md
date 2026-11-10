# Ka$hy · Sistema de diseño (fase 1: propuesta)

Propuesta para que Ka$hy se sienta como una app de finanzas nativa del nivel de Revolut o Trade Republic, sin copiar su marca. El demo `rediseno-demo.html` (no enlazado desde la app, con datos de ejemplo) aplica todo esto a Inicio y Movimientos. Nada de esto está aún en `index-nuevo.html`.

## 1. Qué hace que Revolut y Trade Republic se sientan premium

| Aspecto | Qué hacen | Principio para Ka$hy |
|---|---|---|
| Tipografía | Fuente de sistema o propia muy cuidada, pocos tamaños, jerarquía por peso | SF Pro (fuente del sistema) con 7 tamaños fijos; jerarquía con peso y color, no con tamaño |
| Números | Cifra principal enorme, decimales más pequeños, cifras de ancho fijo | Patrimonio a 48 pt con los decimales a 28 pt en gris; `tabular-nums` en todas las cantidades |
| Color | Base neutra casi monocroma; el color solo significa algo | Fondo y superficies neutras. Importes como en la app actual: **gastos en rojo, ingresos en verde y transferencias en morado Ka$hy**. El morado es también el color de lo pulsable y lo seleccionado |
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
| `--accent` | `#5B4CEB` | `#A197FF` | Acción principal, selección, gráfica, importes de transferencias |
| `--positive` | `#0A8A4A` | `#3DD68C` | Ingresos, subidas |
| `--negative` | `#D0342C` | `#FF7A70` | Gastos, borrar, errores, saldo negativo |
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
- **Cabecera:** el nombre de la pantalla a la izquierda y, a la derecha, el ojo (ocultar saldos) y el botón de tema (luna o sol), como en la app actual. Al hacer scroll se pliega y muestra el título pequeño (en Inicio, el patrimonio redondeado).
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

### Logos de comercios y bancos

**Regla:** si el nombre de un movimiento contiene un comercio conocido, la ficha muestra su logo; si no, el icono de su categoría. La lista va **dentro de la app**: no se consulta ninguna API de logos ni se carga nada externo, así que nadie sabe qué comercios usas.

**Cómo se reconoce el comercio:**
- Se ignoran mayúsculas, tildes, emojis y signos («McDonald’s» = «mcdonalds»).
- Se buscan palabras enteras, así que «desayunike» no es Nike.
- Si aparecen dos comercios, gana el primero: «mercadona nike» es Mercadona.
- Las marcas de una palabra admiten **una errata**: «mercadoan», «spotfy», «vintde». En marcas de menos de 7 letras solo cuenta una letra cambiada o dos intercambiadas, para que «consumo» no sea Consum.

**Comercios encontrados en tus movimientos de Notion** (solo lectura) y su logo:

| Comercio | Cómo lo escribes | Logo |
|---|---|---|
| Vinted | vinted, vintedada, «zapas vinted»… | Simple Icons |
| Mercadona | mercadona, «compra mercadona»… | Web oficial (favicon) |
| DAZN | dazn, dazn fútbol, dazn basket | Simple Icons |
| McDonald's | mcdonalds, mcdonald, mcdonald’s, macdonalds, mcdon, macdon, mcdo, mcd, mackies, mc | Simple Icons |
| Spotify · iCloud · Claude · IKEA | igual que su nombre | Simple Icons |
| AliExpress | aliexpress, ali express | Simple Icons |
| Nike | nike (palabra entera) | Simple Icons |
| Funko | funko, funkos | Web oficial (favicon) |
| EA Play | ea play, ea play pro | Simple Icons (EA) |
| Alcampo | alcampo | Web oficial (favicon) |
| KFC · Zara · Starbucks · PayPal · Klarna · Airbnb | igual que su nombre | Simple Icons |
| Google (AI Pro) | google | Simple Icons |
| Winamax | winamax | Web oficial (icono de app) |
| Consum | consum | Web oficial (favicon) |
| Muerde la Pasta | muerde la pasta | Web oficial (icono de app) |
| Panini | panini | Web oficial (favicon) |
| Decathlon · Primark · Amazon | igual que su nombre | **Sin logo: inicial.** Sus webs bloquearon la descarga (403) |

Sin comercio, con icono de categoría: «pan», «gasolina», «desayuno», «sushi», «gym», «awela», «nómina», «boca te lía», «aires burger», «wina», etc. Bares y restaurantes locales no tienen logo público, y «wina» o «bet» no se asocian a ninguna casa de apuestas porque no siempre lo son.

**Bancos y cuentas (logo oficial descargado de su propia web, guardado dentro de la app):**

| Cuenta | Fuente |
|---|---|
| Ibercaja | Icono de www.ibercaja.es (`/favicon.ico`, 128 px) |
| Sabadell | Icono de app de www.bancsabadell.com (`apple-icon-180x180.png`) |
| MyInvestor y MyInvestor Remunerada | Icono de app de myinvestor.es (`myinvestor_apple-touch-icon` de cdn.myinvestor.es) |
| Openbank (Corriente y Ahorro) | Símbolo (la llave) recortado del logo oficial de www.openbank.es (`Logo_Web_8_0.svg`), sin redibujar |
| Pluxee | Icono de app de www.pluxee.es (`apple-touch-icon-152x152.png`) |
| Revolut (Personal y Compartida) | Simple Icons |
| Efectivo | Icono Lucide `banknote` |

**Licencias:** Lucide (ISC) y Simple Icons (CC0). Los logos de las webs oficiales son marcas de sus dueños; se usan sin modificar (solo redimensionados, y en Openbank recortado el símbolo) y únicamente para identificar el comercio o el banco en una app personal.

### Emojis guardados en Notion
- Los nombres de Notion se quedan como están («🎵 Spotify», «🤖 Claude Pro»), porque `kashy-vencimientos.js` y el registro de cuotas dependen del nombre exacto.
- La app quita el emoji solo al mostrar el nombre y elige el icono así: (1) si el nombre contiene una marca conocida, su logo; (2) si no, el icono de su categoría, según el id de la relación «Fuente de Gasto/Ingreso»; (3) si tampoco hay categoría, `wallet`.
- Las cuentas se identifican por su id, no por el emoji de su nombre, y cada una lleva el logo de su banco.
- Los emojis de las constantes de la app (`GASTOS`, `INGRESOS`, `CUENTAS`) pasan a ser nombres de icono.

## 5. Lo que el rediseño no puede quitar
Es un rediseño, no una app nueva: **cambia el aspecto, no lo que hace**. La demo enseña el estilo y no lo trae todo; la versión final mantiene todas las funciones de `index-nuevo.html` y todas las categorías de Notion, con sus nombres y su orden. Antes de dar por terminada cada pantalla se repasa esta lista.

- **General**: pantalla de inicio con el logo, ojo de privacidad, tema claro/oscuro, solo español (el código de idiomas se queda), clave de acceso, **Ajustes** (engranaje de Inicio: tema, ocultar importes, notificaciones y cambiar clave), sin botones Recargar ni «tirar hacia abajo» (se quitó porque saltaba sin querer al desplazarse): los datos se refrescan solos al cambiar de pestaña y tras cualquier cambio, caché de pantallas (abre al momento y refresca detrás), «Deshacer» al borrar o registrar, avisos, esqueletos, estados vacíos y animación propia de cada categoría.
- **Inicio**: patrimonio que sube desde 0, desglose del patrimonio al tocarlo, variación y gráfica por periodos con lectura con el dedo, resumen del mes, aviso «Hoy vence» (pagos, cuotas, transferencias recurrentes y aportación), carrusel de cuentas que abre esa cuenta, aviso de MyInvestor y gastos por categoría. **Ningún importe se corta nunca**: se ajusta o pasa de línea.
- **Movimientos**: chips de tipo y de categoría, búsqueda (nueva), balance por día, **deslizar para Editar/Eliminar**, editar movimiento (importe, concepto, cuenta, categoría y fecha) y editar o borrar transferencias.
- **Registrar**: gasto/ingreso, ajuste del tamaño del importe, categoría sugerida por el concepto, chips de cuentas, Hoy/Ayer/otra fecha, momento de éxito, ingresos rápidos, y pagos recurrentes con **barra de cuotas**, sin los terminados.
- **Estadísticas**: periodos, gráfico circular, gastos fijos y variables, proyección del mes, actividad, gráfico de ingresos, comparativa, historial por meses, tendencia, más gastados, la frase de resumen y la **descarga del extracto**. Los presupuestos se han quitado.
- **Cuentas**: tarjetas que se despliegan con sus movimientos y sus transferencias (entrantes y salientes, en morado, mezcladas por fecha), Mover (transferir) y Desactivar (Añadir y Retirar ya estaban ocultos antes del rediseño y siguen así), transferencias recurrentes, desactivar, ver y reactivar cuentas inactivas. Metas de ahorro y lista de deseos se han quitado de la app (sus filas siguen en Notion y nunca salen como cuentas); las notificaciones están en Ajustes.
- **Inversión**: valor por fondo y total, copiar el ISIN, aportaciones enlazadas con su transferencia (editar o borrar una cambia la otra), aportación mensual rápida, actualizar valores por fondo, editar y borrar registros. Sin objetivo anual.
- **Fuera de la interfaz**: el atajo de iOS (`/api/gasto`), las notificaciones del cron y `kashy-vencimientos.js` no cambian.

**Categorías** (todas las de Notion; la demo ya las incluye):
- Gasto: Supermercado, Restaurantes, Café, Helados, Comida Rápida, Gasolina, Coche, Ropa, Apuestas, Farmacia, Ocio, Regalos, Bizum, Viajes, Hogar, Suscripciones, Peluquería, Salud, Educación y Libros.
- Ingreso: Nómina, Nómina Pluxee, Bizum, Transf. Mamá, Remuneración, Wins y Otros Ingresos.

## 6. Fase 2 (cuando des el visto bueno)
Se migraría pantalla a pantalla para que los tests de regresión vayan detectando cambios: tokens y tipografía, luego Inicio, Movimientos, Registrar, Cuentas, Inversión y Estadísticas, y al final las hojas. Las capturas de referencia se renovarían en cada paso, revisándolas antes.

**Hecho en el paso 8 (hojas y barra inferior):**
- La hoja de editar un movimiento cabe sin desplazarse: importe y fecha más pequeños, categorías en una fila que se desliza y Guardar/Cancelar siempre a la vista. Todas las hojas cumplen la misma regla, comprobada en 390 × 667 (iPhone SE) por `tests/test_hojas.py`.
- La barra inferior usa los iconos del sistema y las etiquetas en minúscula.
