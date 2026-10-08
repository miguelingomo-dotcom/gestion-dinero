// Historial diario del patrimonio en cuentas, reconstruido a partir de los movimientos y transferencias.
// Usa /api/query de este mismo despliegue (con paginación), así que no necesita su propio token.
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const { movs, cuentas, transfers, excluir = '', hasta } = req.query;
  if (!movs || !cuentas || !transfers || !/^\d{4}-\d{2}-\d{2}$/.test(hasta || '')) {
    res.status(400).json({ error: 'Faltan parámetros' });
    return;
  }
  const proto = req.headers['x-forwarded-proto'] || 'https';
  const origin = `${proto}://${req.headers.host}`;

  async function todas(dbId, filter) {
    const out = [];
    let cursor = null;
    do {
      const r = await fetch(`${origin}/api/query?dbId=${dbId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ page_size: 100, ...(filter ? { filter } : {}), ...(cursor ? { start_cursor: cursor } : {}) }),
      });
      const j = await r.json();
      if (!j.results) throw new Error(j.message || 'Error al consultar Notion');
      out.push(...j.results);
      cursor = j.has_more ? j.next_cursor : null;
    } while (cursor);
    return out;
  }

  try {
    const [cuentasPags, invPags, movPags, trPags] = await Promise.all([
      todas(cuentas, { property: 'Cuenta o Meta', select: { equals: 'Cuenta' } }),
      todas(cuentas, { property: 'InvTipo', select: { is_not_empty: true } }),
      todas(movs),
      todas(transfers),
    ]);
    const id = x => x.replace(/-/g, '');
    const excluidas = new Set(excluir.split(',').filter(Boolean).map(id));
    const cuenta = rel => (rel || []).map(r => id(r.id)).filter(k => !excluidas.has(k));
    const dia = f => (f > hasta ? hasta : f); // lo fechado en el futuro ya cuenta en el balance de hoy

    // Balance = Balance Inicial + Ingresos − Gastos + Transferencias recibidas − Transferencias enviadas
    let inicial = 0, hoy = 0;
    for (const p of cuentasPags) {
      if (excluidas.has(id(p.id))) continue;
      inicial += p.properties?.['Balance Inicial']?.number || 0;
      hoy += p.properties?.Balance?.formula?.number || 0;
    }
    const cambios = {};
    const sumar = (f, v) => { if (f && v) cambios[dia(f.slice(0, 10))] = (cambios[dia(f.slice(0, 10))] || 0) + v; };
    for (const m of movPags) {
      const p = m.properties || {};
      const neto = (p.Ingreso?.number || 0) - (p.Gasto?.number || 0);
      for (const _ of cuenta(p.Cuenta?.relation)) sumar(p.Fecha?.date?.start, neto);
    }
    for (const t of trPags) {
      const p = t.properties || {};
      const monto = p.Monto?.number || 0;
      const neto = cuenta(p['Transferir a']?.relation).length * monto - cuenta(p['Transferir Desde']?.relation).length * monto;
      sumar(p.Fecha?.date?.start, neto);
    }

    const fechas = Object.keys(cambios).sort();
    const desde = fechas[0] && fechas[0] < hasta ? fechas[0] : hasta;
    const serie = [];
    let acumulado = inicial;
    for (let d = new Date(desde + 'T12:00:00Z'); ; d.setUTCDate(d.getUTCDate() + 1)) {
      const f = d.toISOString().slice(0, 10);
      acumulado += cambios[f] || 0;
      serie.push(Math.round(acumulado * 100) / 100);
      if (f >= hasta) break;
    }

    const inv = invPags.map(r => ({
      tipo: r.properties?.InvTipo?.select?.name || '',
      fondo: r.properties?.InvFondo?.select?.name || '',
      importe: r.properties?.InvImporte?.number || 0,
      fecha: r.properties?.InvFecha?.date?.start || '',
      creado: r.created_time,
    })).filter(r => r.fecha);

    res.status(200).json({ desde, hasta, cuentas: serie, cuentasHoy: Math.round(hoy * 100) / 100, inv });
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
}
