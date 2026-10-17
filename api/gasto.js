// Registrar un gasto desde un atajo de iOS (p. ej. con Toque posterior), sin abrir la app.
//   GET  → { categorias: [...], cuentas: [...] } para las listas del atajo (categorías de más a menos usadas
//          en los últimos 90 días; Revolut la primera cuenta).
//   POST { importe, concepto, categoria?, cuenta? } → crea el gasto con la fecha de hoy (hora de España)
//        y responde un texto corto para mostrarlo como notificación.
// Usa /api/query y /api/page de este mismo despliegue, así que no necesita su propio token.
const DB_MOVS = '25e21c54013f817481d6cd37b0daa2b5';
const DB_CUENTAS = '25e21c54013f817e959ee75351072a94';
const DB_CATEGORIAS = '25e21c54013f811abbffea0726c1d250';
const REVOLUT = '31621c54013f817f9f00fc6acc160c26'; // cuenta por defecto
const AUTO = '✨ Automática'; // ya no sale en la lista; se acepta por compatibilidad con atajos antiguos
const DIAS_USO = 90; // ventana para ordenar las categorías por uso
// Las mismas palabras que reconoce el registro de la app (PALABRAS_EMOJI), apuntando a su categoría
const PALABRAS = [
  ['mercadona', 'supermercado'], ['restaurante', 'restaurantes'], ['gasolina', 'gasolina'],
  ['coche', 'coche'], ['letra', 'coche'], ['farmacia', 'farmacia'], ['bizum', 'bizum'],
];

const sinGuiones = x => x.replace(/-/g, '');
const sinEmoji = s => (s || '').replace(/[\p{Extended_Pictographic}️‍]/gu, '').trim();
const norm = s => sinEmoji(String(s || '')).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
const espera = ms => new Promise(r => setTimeout(r, ms));

// Igual que parseAmt de la app: acepta 12,5 · 12.5 · 1.234,56 · 1,234.56
function leerImporte(v) {
  if (typeof v === 'number') return v;
  let s = String(v || '').trim().replace(/[^0-9,.\-]/g, '');
  if (s.includes(',') && s.includes('.')) {
    s = s.lastIndexOf(',') > s.lastIndexOf('.') ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
  } else s = s.replace(',', '.');
  return parseFloat(s);
}

function texto(res, msg) {
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.status(200).send(msg);
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const proto = req.headers['x-forwarded-proto'] || 'https';
  const origin = `${proto}://${req.headers.host}`;

  // Consulta paginada; ante un 429 de Notion espera y reintenta
  async function consulta(dbId, filter) {
    const out = [];
    let cursor = null;
    do {
      let j;
      for (let intento = 0; intento < 3; intento++) {
        const r = await fetch(`${origin}/api/query?dbId=${dbId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ page_size: 100, filter, ...(cursor ? { start_cursor: cursor } : {}) }),
        });
        j = await r.json();
        if (r.status !== 429) break;
        await espera(600 * (intento + 1));
      }
      if (!j.results) throw new Error(j.message || 'Error al consultar Notion');
      out.push(...j.results);
      cursor = j.has_more ? j.next_cursor : null;
    } while (cursor);
    return out;
  }

  async function listas(conUso) {
    const hoyMadrid = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Madrid' }).format(new Date());
    const desde = new Date(hoyMadrid + 'T12:00:00Z');
    desde.setUTCDate(desde.getUTCDate() - DIAS_USO);
    const [cats, ctas, usados] = await Promise.all([
      consulta(DB_CATEGORIAS, { property: 'Tipo', multi_select: { contains: 'Gasto' } }),
      consulta(DB_CUENTAS, { and: [
        { property: 'Cuenta o Meta', select: { equals: 'Cuenta' } },
        { property: 'Estado', select: { equals: '🟢 Activo' } },
      ] }),
      conUso ? consulta(DB_MOVS, { and: [
        { property: 'Gasto', number: { greater_than: 0 } },
        { property: 'Fecha', date: { on_or_after: desde.toISOString().slice(0, 10) } },
      ] }) : Promise.resolve([]),
    ]);
    // Cuántas veces se ha usado cada categoría en la ventana
    const usos = {};
    for (const m of usados) {
      const rel = m.properties?.['Fuente de Gasto']?.relation?.[0]?.id;
      if (rel) usos[sinGuiones(rel)] = (usos[sinGuiones(rel)] || 0) + 1;
    }
    const titulo = p => (p.properties?.Nombre?.title || []).map(t => t.plain_text).join('').trim();
    const categorias = cats.map(p => ({ id: sinGuiones(p.id), nombre: titulo(p) }))
      .filter(c => c.nombre)
      .sort((a, b) => (usos[b.id] || 0) - (usos[a.id] || 0) || sinEmoji(a.nombre).localeCompare(sinEmoji(b.nombre), 'es'));
    const cuentas = ctas.map(p => ({ id: sinGuiones(p.id), nombre: sinEmoji(titulo(p)) }))
      .filter(c => c.nombre)
      .sort((a, b) => (b.id === REVOLUT) - (a.id === REVOLUT) || a.nombre.localeCompare(b.nombre, 'es'));
    return { categorias, cuentas };
  }

  try {
    if (req.method === 'GET') {
      const l = await listas(true);
      res.status(200).json({ categorias: l.categorias.map(c => c.nombre), cuentas: l.cuentas.map(c => c.nombre) });
      return;
    }
    if (req.method !== 'POST') { res.status(405).json({ error: 'Usa GET o POST' }); return; }

    // El cuerpo puede llegar como JSON, formulario o texto sin cabecera de tipo
    let b = req.body;
    if (Buffer.isBuffer(b)) b = b.toString('utf8');
    if (typeof b === 'string') {
      try { b = JSON.parse(b); } catch (e) { b = Object.fromEntries(new URLSearchParams(b)); }
    }
    if (!b || typeof b !== 'object') b = {};
    // Claves sin distinguir mayúsculas ni tildes: el teclado de iOS escribe «Importe» o «Categoría»
    const campos = {};
    for (const [k, v] of Object.entries(b)) campos[norm(k)] = v;
    const recibido = JSON.stringify(b).slice(0, 160);
    const importe = leerImporte(campos.importe);
    const concepto = String(campos.concepto || '').trim();
    if (!(importe > 0)) return texto(res, `❌ Importe no válido. Recibido: ${recibido}`);
    if (!concepto) return texto(res, `❌ Falta el concepto. Recibido: ${recibido}`);

    const l = await listas();

    // Cuenta: la elegida por nombre; si no viene o no se reconoce, Revolut
    const cn = norm(campos.cuenta);
    const cuenta = (cn && (l.cuentas.find(c => norm(c.nombre) === cn)
        || l.cuentas.find(c => norm(c.nombre).includes(cn) || cn.includes(norm(c.nombre)))))
      || l.cuentas.find(c => c.id === REVOLUT) || l.cuentas[0];
    if (!cuenta) return texto(res, '❌ No hay cuentas activas');

    // Categoría: la elegida; sin categoría (o «Automática» de un atajo antiguo) se deduce del concepto
    const catN = norm(campos.categoria);
    let cat = null;
    if (catN && catN !== norm(AUTO)) {
      cat = l.categorias.find(c => norm(c.nombre) === catN) || l.categorias.find(c => norm(c.nombre).includes(catN));
      if (!cat) return texto(res, `❌ No existe la categoría «${campos.categoria}»`);
    } else {
      const con = norm(concepto);
      cat = l.categorias.find(c => con.includes(norm(c.nombre)));
      if (!cat) {
        const p = PALABRAS.find(([k]) => con.includes(k));
        if (p) cat = l.categorias.find(c => norm(c.nombre) === p[1]);
      }
      if (!cat) return texto(res, `❓ No sé de qué categoría es «${concepto}». No se ha guardado: vuelve a lanzarlo y elígela.`);
    }

    const hoy = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Madrid' }).format(new Date());
    const r = await fetch(`${origin}/api/page`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parent: { database_id: DB_MOVS }, properties: {
        Nombre: { title: [{ text: { content: concepto } }] },
        Fecha: { date: { start: hoy } },
        Tipo: { select: { name: 'Expense' } },
        Cuenta: { relation: [{ id: cuenta.id }] },
        Gasto: { number: importe },
        'Fuente de Gasto': { relation: [{ id: cat.id }] },
      } }),
    });
    const d = await r.json();
    if (!d.id) return texto(res, '❌ No se pudo guardar: ' + (d.message || 'error de Notion'));
    const euros = importe.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    texto(res, `✓ ${euros} € · ${concepto} · ${sinEmoji(cat.nombre)} · ${cuenta.nombre}`);
  } catch (e) {
    texto(res, '❌ ' + (e.message || 'Error'));
  }
}
