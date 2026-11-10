// Estado de las notificaciones en la base «Ajustes Kashy» de Notion (una sola fila): la suscripción push del
// iPhone, la fecha del último aviso diario y el último valor de cartera por el que ya se avisó.
import { pedirNotion } from './_notion.js';

export const AJUSTES_DB = '60fa0f60f1874c64bbcd3f5f659c7439';
const texto = p => ((p && p.rich_text) || []).map(x => x.plain_text).join('');
// Notion limita cada trozo de texto a 2000 caracteres
const enTrozos = s => {
  const out = [];
  for (let i = 0; i < s.length; i += 1900) out.push({ text: { content: s.slice(i, i + 1900) } });
  return out;
};

export async function leerAjustes() {
  const r = await pedirNotion(`databases/${AJUSTES_DB}/query`, { method: 'POST', body: { page_size: 1 } });
  if (r.status !== 200 || !r.data.results) throw new Error('No se puede leer «Ajustes Kashy» (' + r.status + ')');
  const p = r.data.results[0];
  if (!p) return { id: null, suscripcion: null, ultimoEnvio: '', carteraAvisada: '' };
  let suscripcion = null;
  try { suscripcion = JSON.parse(texto(p.properties.Suscripcion)); } catch (e) {}
  return { id: p.id, suscripcion, ultimoEnvio: texto(p.properties.UltimoEnvio), carteraAvisada: texto(p.properties.CarteraAvisada) };
}

// cambios: {suscripcion?, ultimoEnvio?, carteraAvisada?}. Crea la fila la primera vez
export async function guardarAjustes(ajustes, cambios) {
  const props = {};
  if ('suscripcion' in cambios) props.Suscripcion = { rich_text: cambios.suscripcion ? enTrozos(JSON.stringify(cambios.suscripcion)) : [] };
  if ('ultimoEnvio' in cambios) props.UltimoEnvio = { rich_text: enTrozos(cambios.ultimoEnvio || '') };
  if ('carteraAvisada' in cambios) props.CarteraAvisada = { rich_text: enTrozos(cambios.carteraAvisada || '') };
  const r = ajustes.id
    ? await pedirNotion(`pages/${ajustes.id}`, { method: 'PATCH', body: { properties: props } })
    : await pedirNotion('pages', { method: 'POST', body: {
        parent: { database_id: AJUSTES_DB },
        properties: { Nombre: { title: [{ text: { content: 'Push' } }] }, ...props },
      } });
  if (r.status !== 200) throw new Error('No se puede guardar en «Ajustes Kashy» (' + r.status + ')');
  return { ...ajustes, ...cambios, id: r.data.id };
}
