# Ka$hy · Sistema de diseño

Ka$hy aplica este sistema en todas sus pantallas desde el rediseño (fase 2, terminada en noviembre de 2026). El objetivo es que se sienta como una app de finanzas nativa del nivel de Revolut o Trade Republic, sin copiar su marca. `rediseno-demo.html` es la demo con datos falsos que sirvió de referencia; no está enlazada desde la app.

El rediseño cambió el aspecto, no lo que hace la app: se mantuvieron todas sus funciones y todas las categorías de Notion, salvo las que se quitaron a propósito (sección 6).

## 1. Principios

| Aspecto | Principio en Ka$hy |
|---|---|
| Tipografía | La del sistema (SF Pro en el iPhone), pocos tamaños, jerarquía con peso y color |
| Números | Cifra principal grande con los céntimos más pequeños; `tabular-nums` en todas las cantidades; formato español («84,50 €», espacio antes de € y %) |
| Color | Base neutra; el color solo significa algo: **gastos en rojo, ingresos en verde y transferencias en morado**. El morado es también lo pulsable y lo seleccionado |
| Espacio | Escala de 4 px; márgenes laterales de 16 y 20 px |
| Tarjetas | Listas agrupadas al estilo iOS, con separadores finos sangrados; sombra mínima en claro y ninguna en oscuro |
| Filas | Ficha de 40 px, título 16, subtítulo 13 en gris, importe 16 a la derecha |
| Movimiento | Interacciones de 120-240 ms con curvas propias; las hojas siguen al dedo |
| Vacíos y carga | Esqueleto solo si no hay nada guardado; vacío con icono, una frase y qué hacer |
| Importes | **Ninguno se corta nunca**: se reduce la letra hasta la mitad y, si aún no cabe, pasa de línea |

## 2. Tokens

### Color (en `index-nuevo.html`: `:root` es el oscuro y `[data-theme="light"]` el claro)
| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--bg` / `--page` | `#F4F4F7` | `#0B0B0E` | Fondo de pantalla |
| `--surface` / `--sheet` | `#FFFFFF` | `#17171C` / `#1C1C22` | Tarjetas, grupos y hojas |
| `--surface2` / `--surface3` | `#F0F0F4` / `#E6E6EC` | `#202027` / `#2A2A32` | Bloques dentro de una superficie |
| `--fill` | gris al 12 % | gris al 24 % | Botones secundarios, chips, buscador, campos de las hojas |
| `--text` / `--muted` / `--muted2` | `#0B0B0F` / `#62626E` / `#8E8E99` | `#F4F4F6` / `#A1A1AC` / `#73737E` | Texto principal, secundario y terciario |
| `--separator` | gris al 16 % | gris al 42 % | Separadores de 0,5 px |
| `--accent` | `#5B4CEB` | `#A197FF` | Acción principal, selección, gráficas, transferencias |
| `--green` / `--positive` | `#0A8A4A` | `#3DD68C` | Ingresos, subidas |
| `--red` / `--negative` | `#D0342C` | `#FF7A70` | Gastos, borrar, errores |
| `--yellow` / `--warning-soft` | `#B26B00` | `#FFC247` | Avisos («Hoy vence») |

Las barras superior e inferior son translúcidas (`backdrop-filter`); con «Reducir transparencia» pasan a ser opacas.

### Tipografía
La del sistema (`--font`, SF Pro); las cifras grandes usan `--font-round` (SF Pro Rounded en el iPhone). No se carga ninguna fuente web.

| Estilo | Tamaño / peso |
|---|---|
| Cifra principal | 48 / 700, céntimos al 58 % en gris |
| Título de pantalla | 27-34 / 700 (se ajusta en pantallas estrechas) |
| Título de sección | 20 / 700 |
| Cuerpo, campos y botones | 16-17 / 400-600 |
| Fila (título / importe) | 16 / 500-600 |
| Subtítulos y pies | 12-13 / 500 |

### Espaciado, radios y movimiento
- **Espaciado:** 4, 8, 12, 16, 20, 24 y 32 px.
- **Radios:** 10, 14, 20, 28 (hoja) y píldora (chips, selectores).
- **Movimiento:** pulsación 120 ms (`scale(.97)`), color 150-180 ms, cambios 240 ms, hojas con `cubic-bezier(.32,.72,0,1)`. Las cifras cuentan desde 0 en 600 ms al entrar en una pestaña (Inicio, Cuentas, Inversión, Estadísticas) y el patrimonio al abrir la app. Con «Reducir movimiento» nada cuenta ni se anima.

## 3. Componentes
- **Cabecera:** título grande a la izquierda y botones redondos a la derecha. Inicio: ojo, engranaje (Ajustes), Estadísticas y tema. El resto: ojo y tema (el tema muestra luna o sol según el tema actual). Estadísticas lleva la flecha de volver junto al título.
- **Ficha:** de categoría (icono sobre su color al 12 %), de marca (logo sobre su color oficial) o de banco (su logo). Ver la sección 4.
- **Filas y grupos:** listas agrupadas, por día en Movimientos con el balance del día a la derecha. Deslizar a la izquierda muestra Editar (morado) y Eliminar (rojo).
- **Chips:** píldoras grises; el elegido se invierte o lleva un aro morado. Las cuentas con su logo y las categorías con su icono, sin emojis.
- **Control segmentado:** Gasto/Ingreso y los periodos, con una marca que se desliza.
- **Avisos en tarjeta:** «Hoy vence» (amarillo) y MyInvestor (morado), con icono y el texto entero.
- **Hojas:** asa, velo, arrastre para cerrar. **Siempre caben** en una pantalla de 390 × 667 sin desplazarse, con Cancelar/Guardar fijos abajo, y **nunca se mueven de lado**: solo las filas de chips se deslizan, dentro de sí mismas. Los campos de fecha son idénticos al campo de al lado.
- **Aviso inferior:** píldora oscura encima de la barra, con «Deshacer» cuando se puede deshacer.
- **Barra inferior:** Inicio, Movimientos, «+» (Registrar) en el morado, Cuentas e Inversión, con iconos del sistema.
- **Gráficas:** línea morada con degradado suave; en Inicio se lee con el dedo. En Estadísticas, «Este mes» acumula el gasto día a día y compara en gris con el mes anterior hasta el mismo día.
- **Icono de la app y pantalla de inicio:** la palabra «Ka$hy» en blanco sobre el morado `#5B4CEB`, con el $ en lila; solo tipografía y color, sin mascota.

## 4. Iconos y logos

Todo va **dentro de la app**: no se consulta ninguna API de logos ni se carga nada externo, así que nadie sabe qué comercios usas. Los tests fallan si la app pide algo fuera.

### Categorías: Lucide (licencia ISC), con su color y su familia de animación
| Categoría | Icono | Familia |
|---|---|---|
| Supermercado | `shopping-cart` | avance |
| Restaurantes | `utensils` | balanceo |
| Café | `coffee` | flote |
| Helados | `ice-cream-cone` | salto |
| Comida Rápida | `sandwich` | latido |
| Gasolina | `fuel` | latido |
| Coche | **logo de Hyundai** (Simple Icons, `#002C5E`) | avance |
| Ropa | `shirt` | balanceo |
| Apuestas | `dices` | giro |
| Farmacia | `pill` | balanceo |
| Ocio | `gamepad-2` | zumbido |
| Regalos | `gift` | salto |
| Bizum | `smartphone` | zumbido |
| Viajes | `plane` | avance |
| Hogar | `house` | latido |
| Suscripciones | `repeat` | giro |
| Peluquería | `scissors` | zumbido |
| Salud | `heart-pulse` | latido |
| Educación | `graduation-cap` | salto |
| Libros | `book-open` | flote |
| Nómina / Nómina Pluxee | `briefcase-business` / `utensils` | salto / balanceo |
| Transf. Mamá | `hand-heart` | latido |
| Remuneración / Wins / Otros Ingresos | `hand-coins` / `trophy` / `wallet` | salto / latido / flote |
| Transferencia | `arrow-left-right` (morado) | avance |

Los colores y los ids de Notion están en `CAT_META`. Las barras de cada categoría (Inicio, Estadísticas, cuotas de Registrar) usan su color.

### Comercios
**Regla:** si el nombre de un movimiento menciona un comercio conocido, la ficha muestra su logo; si no, el icono de su categoría; y si tampoco hay categoría, `wallet`.

**Cómo se reconoce:** sin mayúsculas, tildes, emojis ni signos («McDonald’s» = «mcdonalds»); palabras enteras («desayunike» no es Nike); si hay dos, gana el primero; las marcas de una palabra admiten **una errata** (en las de menos de 7 letras, solo una letra cambiada o dos intercambiadas, para que «consumo» no sea Consum). Al escribir el concepto en Registrar, el comercio reconocido sugiere su categoría.

| Comercio | Cómo lo escribes | Logo |
|---|---|---|
| Mercadona · Alcampo · Consum · Funko · Panini | igual que su nombre (funkos también) | Web oficial |
| Winamax · Muerde la Pasta | winamax · muerde la pasta | Web oficial (icono de app) |
| McDonald's | mcdonalds, mcdonald, macdonalds, mcdon, macdon, mcdo, mcd, mackies, mc | Simple Icons |
| Vinted | vinted, vintedada | Simple Icons |
| Spotify · DAZN · iCloud · Claude · Google · IKEA | igual que su nombre | Simple Icons |
| AliExpress | aliexpress, ali express | Simple Icons |
| Nike · Zara · KFC · Starbucks · PayPal · Klarna · Airbnb | igual que su nombre | Simple Icons |
| EA Play | ea play, ea play pro | Simple Icons (EA) |
| Hyundai | hyundai | Simple Icons |
| Decathlon · Primark · Amazon | igual que su nombre | Inicial (sus webs bloquearon la descarga) |

Para añadir un comercio: su variante en `COMERCIOS`, cómo dibujarlo en `MARCA` y, si tiene categoría propia, `CAT_DE_COMERCIO`.

### Bancos y cuentas
| Cuenta | Fuente del logo |
|---|---|
| Ibercaja | Icono de www.ibercaja.es (128 px) |
| Sabadell | Icono de app de www.bancsabadell.com |
| MyInvestor y MyInvestor Remunerada | Icono de app de myinvestor.es |
| Openbank (Corriente y Ahorro) | Símbolo recortado del logo oficial de www.openbank.es, sin redibujar |
| Pluxee | Icono de app de www.pluxee.es |
| Revolut (Personal y Compartida) | Simple Icons |
| Efectivo | Lucide `banknote` |

**Licencias:** Lucide (ISC) y Simple Icons (CC0). Los logos de las webs oficiales son marcas de sus dueños; se usan sin modificar (solo redimensionados, y en Openbank recortado el símbolo) y únicamente para identificar el comercio o el banco en una app personal.

### Emojis guardados en Notion
- Los nombres de Notion se quedan como están («🎵 Spotify»): `kashy-vencimientos.js` y el registro de cuotas dependen del nombre exacto.
- La app quita el emoji solo al mostrarlo (`sinEmoji`). La interfaz no usa emojis; la notificación diaria sí los conserva.

## 5. Qué hace la app (estado final)
- **General:** pantalla de inicio con el logo, ojo para ocultar importes, tema claro/oscuro, solo español, clave de acceso, **Ajustes** (engranaje de Inicio: tema, ocultar importes, notificaciones y cambiar clave), caché de pantallas (abre al momento y refresca detrás), «Deshacer» al borrar o registrar, avisos, esqueletos y estados vacíos. Los datos se refrescan solos al cambiar de pestaña y tras cualquier cambio.
- **Inicio:** patrimonio que sube desde 0, desglose (desde el título, la cifra o «Desglose»), variación y gráfica por periodos con lectura con el dedo, resumen Gastado/Ingresado/Balance, avisos «Hoy vence» y de MyInvestor, carrusel de cuentas y gastos por categoría.
- **Movimientos:** buscador (por nombre, categoría o cuenta), chips de tipo, cuenta y categoría, balance por día, deslizar para Editar o Eliminar, editar movimientos y transferencias.
- **Registrar:** gasto o ingreso, importe con el € pegado, sugerencia del comercio, cuentas, categorías, Hoy/Ayer/Otra, momento de éxito, pagos recurrentes con barra de cuotas (los terminados no salen; orden: Letra Coche, Revisiones Coche, Claude Pro, DAZN Basket, DAZN Fútbol, Spotify, iCloud y el resto) e ingresos rápidos.
- **Cuentas:** cuentas con su logo; al desplegar una, Mover y Desactivar y sus movimientos y transferencias (entrantes y salientes, en morado) mezclados por fecha. Transferencias recurrentes y cuentas inactivas.
- **Inversión:** valor de la cartera, aportado, rendimiento y rentabilidad, fondos (copiar el ISIN), aportación mensual, nueva aportación, actualizar el valor por fondo e historial (todas las aportaciones y solo el valor actual de cada fondo; los anteriores siguen en Notion).
- **Estadísticas:** periodos, balance, tasa de ahorro, proyección, fijos y variables, evolución (acumulada y comparada en «Este mes»), categorías, fuentes de ingreso, top de gastos, comparativa, actividad, resumen, histórico por meses y descarga del extracto en CSV.
- **Fuera de la interfaz:** el atajo de iOS (`/api/gasto`), la notificación diaria y `kashy-vencimientos.js`.

**Categorías** (todas las de Notion): de gasto, Supermercado, Restaurantes, Café, Helados, Comida Rápida, Gasolina, Coche, Ropa, Apuestas, Farmacia, Ocio, Regalos, Bizum, Viajes, Hogar, Suscripciones, Peluquería, Salud, Educación y Libros; de ingreso, Nómina, Nómina Pluxee, Bizum, Transf. Mamá, Remuneración, Wins y Otros Ingresos.

## 6. Lo que se quitó a propósito
| Qué | Por qué | Qué queda |
|---|---|---|
| Presupuestos y su hoja | No se usaban | Nada |
| Metas de ahorro y Lista de deseos | Decisión del dueño | Sus filas siguen en Notion, sin tocar, y nunca salen como cuentas |
| Objetivo anual de Inversión | Decisión del dueño (solo estaba en la demo) | Nada |
| Botones Recargar | Sustituidos por el engranaje de Ajustes | El refresco al cambiar de pestaña y tras cada cambio |
| «Tirar hacia abajo para recargar» | Saltaba sin querer al desplazarse en Movimientos | Igual que arriba |
| Bloqueo con Face ID | Se quitó antes del rediseño | La app abre directamente en Inicio |
| Inglés | La app es solo en español | El diccionario `en` sigue en el código, sin mantener |

## 7. Cómo se comprueba
- La suite (`tests/.venv/bin/pytest tests`, unos 10 minutos) recorre la app a 390 × 844 en claro y oscuro con Notion simulado, y compara cada pantalla con su captura de referencia.
- Reglas del sistema con test propio: ningún importe se corta (`test_cifras.py`, con cifras enormes a 390 y 320 px), las hojas caben y no se mueven de lado (`test_hojas.py`), las cifras cuentan al entrar (`test_contar.py`), el buscador y los logos (`test_buscar.py`) y ninguna petición sale de la app.
- **Cada push a `main` se publica en la app instalada del iPhone** en cuanto Vercel termina (un minuto más o menos).
