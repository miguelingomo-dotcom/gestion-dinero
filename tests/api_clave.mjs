// Comprueba cada archivo de api/ (cualquiera que se añada entra solo). fetch está simulado: nada sale a la red.
import { readdirSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const dir = process.argv[2];
const CLAVE = 'clave-de-prueba-larga';
const METODOS = ['GET', 'POST', 'PATCH', 'DELETE'];
let llamadas = [];
globalThis.fetch = async (url, opts = {}) => {
  llamadas.push({ url: String(url), headers: opts.headers || {} });
  return { status: 200, json: async () => ({ results: [], has_more: false, id: 'x' }) };
};

function respuesta() {
  const r = { codigo: 200, cabeceras: {}, status(c) { r.codigo = c; return r; }, json(b) { r.cuerpo = b; return r; },
    send(b) { r.cuerpo = b; return r; }, end() { return r; }, setHeader(k, v) { r.cabeceras[k.toLowerCase()] = v; } };
  return r;
}
function peticion(method, clave) {
  const headers = { host: 'kashy.test', 'x-forwarded-proto': 'https' };
  if (clave !== undefined) headers['x-kashy-key'] = clave;
  return { method, headers, body: { importe: 5, concepto: 'Prueba' },
    query: { dbId: 'db', pageId: 'pg', movs: 'm', cuentas: 'c', transfers: 't', hasta: '2026-11-15' } };
}
async function llamar(h, method, clave) {
  llamadas = [];
  const res = respuesta();
  await h(peticion(method, clave), res);
  return res;
}

const archivos = readdirSync(dir).filter(f => f.endsWith('.js') && !f.startsWith('_'));
for (const archivo of archivos) {
  const h = (await import(pathToFileURL(join(dir, archivo)).href)).default;
  process.env.KASHY_KEY = CLAVE;
  for (const m of METODOS) {
    for (const [caso, clave] of [['sin clave', undefined], ['vacía', ''], ['incorrecta', 'x'], ['otra de igual longitud', CLAVE.replace(/.$/, '!')], ['con un prefijo correcto', CLAVE + 'x']]) {
      const r = await llamar(h, m, clave);
      assert.equal(r.codigo, 401, `${archivo} ${m} ${caso}`);
      assert.equal(llamadas.length, 0, `${archivo} ${m} ${caso}: no debe llegar a Notion`);
      assert.equal(r.cabeceras['cache-control'], 'no-store', `${archivo} ${m} ${caso}`);
    }
  }
  // Preflight: el navegador no envía la clave, pero debe poder preguntar si puede enviarla
  const pre = await llamar(h, 'OPTIONS');
  assert.equal(pre.codigo, 200, archivo);
  assert.match(pre.cabeceras['access-control-allow-headers'], /X-Kashy-Key/, archivo);
  // Con la clave correcta pasa, y las llamadas a este mismo despliegue la reenvían
  const metodoOk = { 'query.js': 'POST', 'delete.js': 'DELETE', 'page.js': 'GET' }[archivo] || 'GET';
  const ok = await llamar(h, metodoOk, CLAVE);
  assert.notEqual(ok.codigo, 401, `${archivo} con la clave correcta`);
  assert.ok(llamadas.length > 0, `${archivo} con la clave correcta debe trabajar`);
  for (const l of llamadas.filter(x => x.url.startsWith('https://kashy.test/'))) {
    assert.equal(l.headers['x-kashy-key'], CLAVE, `${archivo} reenvía la clave a ${l.url}`);
  }
  // La respuesta autenticada nunca se puede guardar en la CDN: se serviría sin comprobar la clave
  assert.doesNotMatch(String(ok.cabeceras['cache-control'] || ''), /public|s-maxage/, `${archivo} sin caché pública`);
  // Sin KASHY_KEY en Vercel se rechaza todo, también una clave vacía
  delete process.env.KASHY_KEY;
  for (const clave of [undefined, '', CLAVE]) {
    const r = await llamar(h, metodoOk, clave);
    assert.equal(r.codigo, 500, `${archivo} sin KASHY_KEY`);
    assert.equal(llamadas.length, 0, `${archivo} sin KASHY_KEY`);
  }
  process.env.KASHY_KEY = CLAVE;
}

// /api/gasto: la lista guardada en la instancia no se entrega sin clave y evita repetir las consultas
const gasto = (await import(pathToFileURL(join(dir, 'gasto.js')).href)).default;
await llamar(gasto, 'GET', CLAVE);
const repetida = await llamar(gasto, 'GET', CLAVE);
assert.equal(repetida.codigo, 200);
assert.equal(llamadas.length, 0, 'la lista sale de la instancia');
const sinClave = await llamar(gasto, 'GET');
assert.equal(sinClave.codigo, 401, 'la lista guardada exige la clave');
assert.equal(sinClave.cuerpo.categorias, undefined);
// El atajo: POST con la clave llega a /api/page con ella
const post = await llamar(gasto, 'POST', CLAVE);
assert.equal(post.codigo, 200);
console.log('endpoints: ' + archivos.length);
