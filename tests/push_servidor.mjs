// Notificaciones en el servidor y el service worker, con el código real. Notion se simula en memoria y fetch está
// interceptado: nada sale a la red. Las notificaciones salen cifradas por web-push y aquí se descifran para leerlas.
// Uso: node push_servidor.mjs <carpeta con api/, kashy-vencimientos.js, sw.js y node_modules>
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createECDH, randomBytes } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const dir = process.argv[2];
const require = createRequire(join(dir, 'api', 'x.js'));
const webpush = require('web-push');
const ece = require('http_ece');
let pruebas = 0;
const ok = (nombre, fn) => fn().then(() => { pruebas++; }, e => { console.error('FALLA: ' + nombre); throw e; });

// ── Notion simulado ──
const AJUSTES = '60fa0f60f1874c64bbcd3f5f659c7439';
const IDS = { IB: '31621c54013f811ebd49f65e2776d28e', REM: '3d821c54013f81eab324f5174d95ade2', REV: '31621c54013f817f9f00fc6acc160c26', MYI: '3b821c54013f817088e9fe2e7a0a3707' };
const DB = { MOVS: '25e21c54013f817481d6cd37b0daa2b5', TR: '25e21c54013f813faceae0152856368e', CU: '25e21c54013f817e959ee75351072a94' };
let notion, envios, estadoPush, notionCaido;
function reiniciar() {
  notion = { [DB.MOVS]: [], [DB.TR]: [], [DB.CU]: [], [AJUSTES]: [] };
  envios = []; estadoPush = 201; notionCaido = false;
}
const txt = p => (p && (p.title || p.rich_text) || []).map(x => x.plain_text ?? x.text?.content).join('');
function cumple(pg, f) {
  if (f.and) return f.and.every(x => cumple(pg, x));
  const v = pg.properties[f.property] || {};
  if (f.title) return txt(v) === f.title.equals;
  if (f.select) return (v.select || {}).name === f.select.equals;
  if (f.number) return v.number === f.number.equals;
  if (f.relation) return (v.relation || []).some(r => r.id.replace(/-/g, '') === f.relation.contains);
  if (f.date) { const d = (v.date || {}).start; return d && (f.date.on_or_after ? d >= f.date.on_or_after : d <= f.date.on_or_before); }
  throw new Error('filtro no simulado ' + JSON.stringify(f));
}
const normal = props => { const o = JSON.parse(JSON.stringify(props)); for (const v of Object.values(o)) for (const k of ['title', 'rich_text']) (v[k] || []).forEach(x => { x.plain_text = x.text.content; }); return o; };
const fila = (db, props) => notion[db].push({ id: 'p' + Math.random().toString(16).slice(2), properties: normal(props) });
const gasto = (nombre, fecha, importe) => fila(DB.MOVS, { Nombre: { title: [{ text: { content: nombre } }] }, Fecha: { date: { start: fecha } }, Gasto: { number: importe } });
const transf = (de, a, monto, fecha) => fila(DB.TR, { 'Transferir Desde': { relation: [{ id: de }] }, 'Transferir a': { relation: [{ id: a }] }, Monto: { number: monto }, Fecha: { date: { start: fecha } } });
const valorCartera = fecha => fila(DB.CU, { InvTipo: { select: { name: 'Valor Cartera' } }, InvFecha: { date: { start: fecha } } });
const json = (status, data) => ({ status, ok: status < 300, json: async () => data, text: async () => JSON.stringify(data) });
globalThis.fetch = async (url, opts = {}) => {
  url = String(url);
  if (url.startsWith('https://api.notion.com/v1/')) {
    if (notionCaido) return json(500, { object: 'error' });
    assert.equal(opts.headers.Authorization, 'Bearer token-de-prueba');
    const ruta = url.slice(26), body = opts.body ? JSON.parse(opts.body) : {};
    let m;
    if ((m = ruta.match(/^databases\/(\w+)\/query$/))) {
      let filas = (notion[m[1]] || []).filter(p => !body.filter || cumple(p, body.filter));
      if (body.sorts) filas = [...filas].sort((a, b) => ((b.properties.InvFecha || {}).date || {}).start > ((a.properties.InvFecha || {}).date || {}).start ? 1 : -1);
      return json(200, { results: filas.slice(0, body.page_size || 100), has_more: false });
    }
    if (ruta === 'pages' && opts.method === 'POST') { fila(body.parent.database_id, body.properties); return json(200, notion[body.parent.database_id].at(-1)); }
    if ((m = ruta.match(/^pages\/(\w+)$/)) && opts.method === 'PATCH') {
      const p = Object.values(notion).flat().find(x => x.id === m[1]);
      Object.assign(p.properties, normal(body.properties));
      return json(200, p);
    }
    throw new Error('Notion no simulado: ' + opts.method + ' ' + ruta);
  }
  if (url.startsWith('https://push.example/')) { envios.push({ url, headers: opts.headers, body: opts.body }); return json(estadoPush, {}); }
  throw new Error('Petición real bloqueada: ' + url);
};

// ── Claves de prueba ──
const vapid = webpush.generateVAPIDKeys();
Object.assign(process.env, { VAPID_PUBLIC_KEY: vapid.publicKey, VAPID_PRIVATE_KEY: vapid.privateKey, VAPID_SUBJECT: 'mailto:prueba@example.com',
  CRON_SECRET: 'secreto-cron', KASHY_KEY: 'clave-kashy', NOTION_TOKEN: 'token-de-prueba' });
const ecdh = createECDH('prime256v1'); ecdh.generateKeys();
const auth = randomBytes(16);
const SUB = { endpoint: 'https://push.example/dispositivo', keys: { p256dh: ecdh.getPublicKey('base64url'), auth: auth.toString('base64url') } };
const leer = e => JSON.parse(ece.decrypt(e.body, { version: 'aes128gcm', privateKey: ecdh, authSecret: auth.toString('base64url') }).toString());
const suscribir = () => fila(AJUSTES, { Nombre: { title: [{ text: { content: 'Push' } }] }, Suscripcion: { rich_text: [{ text: { content: JSON.stringify(SUB) } }] } });
const ajuste = k => txt((notion[AJUSTES][0] || { properties: {} }).properties[k]);

// ── Reloj ──
const DateReal = Date;
function ahora(iso) {
  const t = DateReal.parse(iso);
  globalThis.Date = class extends DateReal { constructor(...a) { a.length ? super(...a) : super(t); } static now() { return t; } };
}
function respuesta() {
  const r = { codigo: 200, cabeceras: {}, status(c) { r.codigo = c; return r; }, json(b) { r.cuerpo = b; return r; }, end() { return r; }, setHeader(k, v) { r.cabeceras[k.toLowerCase()] = v; } };
  return r;
}
const imp = f => import(pathToFileURL(join(dir, f)).href);
const cron = (await imp('api/cron-avisos.js')).default;
const push = (await imp('api/push.js')).default;
const llamarCron = async (auth = 'Bearer secreto-cron') => { const r = respuesta(); await cron({ method: 'GET', headers: auth ? { authorization: auth } : {}, query: {} }, r); return r; };
const llamarPush = async (method, { query = {}, body, clave = 'clave-kashy' } = {}) => {
  const r = respuesta(); await push({ method, headers: { 'x-kashy-key': clave }, query, body }, r); return r;
};

// ── Módulo compartido ──
const K = globalThis.KashyVencimientos;
await ok('mes de febrero bisiesto y no bisiesto', async () => {
  assert.deepEqual(K.mesDe('2028-02-10'), { ini: '2028-02-01', fin: '2028-02-29' });
  assert.deepEqual(K.mesDe('2026-02-10'), { ini: '2026-02-01', fin: '2026-02-28' });
});
await ok('texto de la notificación', async () => {
  assert.equal(K.textoNotificacion({ pagos: [], transferencias: [] }), null);
  const n = K.textoNotificacion({ pagos: [{ s: { emoji: '🎵', name: 'Spotify' }, importe: 20.99 }],
    transferencias: [{ destino: 'Revolut Personal', importe: null }, { aportacion: true, importe: 150 }], cartera: { dias: 40 } });
  assert.equal(n.titulo, 'Ka$hy · Hoy vence');
  assert.equal(n.cuerpo, '🎵 Spotify 20,99 €\n⇄ Revolut Personal\n📈 Aportación mensual 150,00 €\n📊 Actualiza el valor de la cartera (40 días)');
  assert.equal(K.textoNotificacion({ pagos: [], transferencias: [], cartera: { dias: null } }).titulo, 'Ka$hy · Recordatorio');
});

// ── Cron: autenticación ──
await ok('cron sin CRON_SECRET, sin cabecera o con otra: rechazado sin tocar Notion', async () => {
  reiniciar(); suscribir(); ahora('2026-07-23T07:30:00Z');
  delete process.env.CRON_SECRET;
  assert.equal((await llamarCron()).codigo, 500);
  process.env.CRON_SECRET = 'secreto-cron';
  for (const a of [null, 'Bearer otro', 'secreto-cron', 'Bearer secreto-cron2']) assert.equal((await llamarCron(a)).codigo, 401);
  assert.equal(envios.length, 0);
});

// ── Cron: horario de Madrid ──
const casos = [
  ['verano: el de las 07 UTC envía', '2026-07-23T07:30:00Z', true],
  ['verano: el de las 08 UTC no', '2026-07-23T08:30:00Z', false],
  ['invierno: el de las 08 UTC envía', '2026-01-23T08:59:00Z', true],
  ['invierno: el de las 07 UTC no', '2026-01-23T07:59:00Z', false],
  ['día del cambio a verano (29/03)', '2026-03-29T07:10:00Z', true],
  ['día del cambio a invierno (25/10): 08 UTC', '2026-10-25T08:10:00Z', true],
  ['día del cambio a invierno (25/10): 07 UTC no', '2026-10-25T07:10:00Z', false],
];
for (const [nombre, iso, envia] of casos) {
  await ok(nombre, async () => {
    reiniciar(); suscribir(); valorCartera(iso.slice(0, 10)); ahora(iso);
    // Siempre vence algo: el pago de iCloud es el 30, así que se fuerza con la transferencia del 23 cuando toca
    gasto('☁️ iCloud', iso.slice(0, 8) + '01', 1.5);
    const dia = Number(iso.slice(8, 10));
    const r = await llamarCron();
    assert.equal(r.codigo, 200, JSON.stringify(r.cuerpo));
    if (!envia) { assert.equal(r.cuerpo.motivo, 'fuera de la franja'); assert.equal(envios.length, 0); return; }
    if (dia === 23) { assert.equal(r.cuerpo.enviado, true, JSON.stringify(r.cuerpo)); assert.equal(envios.length, 1); }
    else assert.equal(r.cuerpo.motivo, 'nada vence hoy');
  });
}

await ok('envío: contenido, TTL de 24 h, urgencia alta y sin Topic (no sustituye avisos anteriores)', async () => {
  reiniciar(); suscribir(); valorCartera('2026-07-20'); ahora('2026-07-23T07:30:00Z');
  const r = await llamarCron();
  assert.equal(r.cuerpo.enviado, true);
  const e = envios[0];
  assert.equal(e.url, SUB.endpoint);
  assert.equal(String(e.headers.TTL), '86400');
  assert.equal(e.headers.Urgency, 'high');
  assert.ok(!('Topic' in e.headers) && !('topic' in e.headers));
  assert.match(e.headers.Authorization, /^vapid t=/);
  assert.equal(e.headers['Content-Encoding'], 'aes128gcm');
  assert.deepEqual(leer(e), { title: 'Ka$hy · Hoy vence', body: '⇄ MyInvestor Remunerada 150,00 €', url: '/index-nuevo.html' });
  assert.equal(ajuste('UltimoEnvio'), '2026-07-23');
});

await ok('un solo envío por día aunque el cron se repita', async () => {
  reiniciar(); suscribir(); valorCartera('2026-07-20'); ahora('2026-07-23T07:10:00Z');
  await llamarCron(); ahora('2026-07-23T07:55:00Z');
  const r = await llamarCron();
  assert.equal(r.cuerpo.motivo, 'ya enviado hoy');
  assert.equal(envios.length, 1);
});

await ok('nada pendiente: sin notificación', async () => {
  reiniciar(); suscribir(); valorCartera('2026-07-20'); transf(IDS.IB, IDS.REM, 150, '2026-07-02'); ahora('2026-07-23T07:30:00Z');
  const r = await llamarCron();
  assert.equal(r.cuerpo.motivo, 'nada vence hoy');
  assert.equal(envios.length, 0);
});

await ok('día 26: Revolut sin importe, aportación y pago, y la cuota con su importe', async () => {
  reiniciar(); suscribir(); valorCartera('2026-07-20'); ahora('2026-07-26T07:30:00Z');
  const r = await llamarCron();
  assert.equal(r.cuerpo.enviado, true);
  assert.equal(leer(envios[0]).body, '⇄ Revolut Personal\n📈 Aportación mensual 150,00 €');
});

await ok('la aportación cuenta como hecha con cualquier importe; Revolut con cualquier importe', async () => {
  reiniciar(); suscribir(); valorCartera('2026-07-20'); ahora('2026-07-26T07:30:00Z');
  transf(IDS.REM, IDS.MYI, 80, '2026-07-10'); transf(IDS.IB, IDS.REV, 37.2, '2026-07-01');
  assert.equal((await llamarCron()).cuerpo.motivo, 'nada vence hoy');
});

await ok('recordatorio de cartera: una sola vez por cada valor', async () => {
  reiniciar(); suscribir(); valorCartera('2026-06-01'); ahora('2026-07-14T07:30:00Z');
  let r = await llamarCron();
  assert.equal(r.cuerpo.enviado, true);
  assert.deepEqual(leer(envios[0]).body, '📊 Actualiza el valor de la cartera (43 días)');
  assert.equal(leer(envios[0]).title, 'Ka$hy · Recordatorio');
  assert.equal(ajuste('CarteraAvisada'), '2026-06-01');
  ahora('2026-07-15T07:30:00Z');
  r = await llamarCron();
  assert.equal(r.cuerpo.motivo, 'nada vence hoy');
  valorCartera('2026-05-01'); // un valor más antiguo no cambia el último
  ahora('2026-07-16T07:30:00Z');
  assert.equal((await llamarCron()).cuerpo.motivo, 'nada vence hoy');
});

await ok('suscripción caducada (410): se borra y no se marca como enviado', async () => {
  reiniciar(); suscribir(); valorCartera('2026-07-20'); ahora('2026-07-23T07:30:00Z'); estadoPush = 410;
  const r = await llamarCron();
  assert.match(r.cuerpo.motivo, /caducada/);
  assert.equal(ajuste('Suscripcion'), '');
  assert.equal(ajuste('UltimoEnvio'), '');
});

await ok('sin suscripción: nada; Notion caído: error sin enviar', async () => {
  reiniciar(); ahora('2026-07-23T07:30:00Z');
  assert.equal((await llamarCron()).cuerpo.motivo, 'sin suscripción');
  notionCaido = true;
  assert.equal((await llamarCron()).codigo, 502);
  assert.equal(envios.length, 0);
});

// ── /api/push ──
await ok('push: clave pública, guardar, probar, caducada y borrar', async () => {
  reiniciar(); ahora('2026-07-23T12:00:00Z');
  assert.equal((await llamarPush('GET', { clave: 'mala' })).codigo, 401);
  let r = await llamarPush('GET');
  assert.equal(r.cuerpo.publicKey, vapid.publicKey); assert.equal(r.cuerpo.suscrito, false);
  assert.equal((await llamarPush('POST', { query: { prueba: '1' } })).codigo, 409);
  assert.equal((await llamarPush('POST', { body: { subscription: { endpoint: 'http://inseguro' } } })).codigo, 400);
  assert.equal((await llamarPush('POST', { body: { subscription: SUB } })).codigo, 200);
  assert.equal(notion[AJUSTES].length, 1);
  assert.deepEqual(JSON.parse(ajuste('Suscripcion')), SUB);
  r = await llamarPush('GET'); assert.equal(r.cuerpo.endpoint, SUB.endpoint);
  r = await llamarPush('POST', { query: { prueba: '1' } });
  assert.equal(r.codigo, 200);
  assert.deepEqual(leer(envios[0]), { title: 'Ka$hy · Prueba', body: 'Las notificaciones funcionan ✓', url: '/index-nuevo.html' });
  assert.equal(String(envios[0].headers.TTL), '86400');
  estadoPush = 410;
  assert.equal((await llamarPush('POST', { query: { prueba: '1' } })).codigo, 410);
  assert.equal(ajuste('Suscripcion'), '');
  await llamarPush('POST', { body: { subscription: SUB } });
  assert.equal((await llamarPush('DELETE')).codigo, 200);
  assert.equal(ajuste('Suscripcion'), '');
  delete process.env.VAPID_PRIVATE_KEY;
  assert.equal((await llamarPush('GET')).codigo, 500);
  process.env.VAPID_PRIVATE_KEY = vapid.privateKey;
});

await ok('claves copiadas con espacios, saltos de línea o «=» final: se limpian y la prueba sale', async () => {
  reiniciar(); ahora('2026-07-23T12:00:00Z');
  const pub = process.env.VAPID_PUBLIC_KEY, priv = process.env.VAPID_PRIVATE_KEY;
  process.env.VAPID_PUBLIC_KEY = ' ' + pub + '=\n'; process.env.VAPID_PRIVATE_KEY = priv + ' \n'; process.env.VAPID_SUBJECT = ' https://kashy.test\n';
  try {
    assert.equal((await llamarPush('GET')).cuerpo.publicKey, pub);
    await llamarPush('POST', { body: { subscription: SUB } });
    const r = await llamarPush('POST', { query: { prueba: '1' } });
    assert.equal(r.codigo, 200, JSON.stringify(r.cuerpo));
    assert.equal(leer(envios[0]).title, 'Ka$hy · Prueba');
  } finally { process.env.VAPID_PUBLIC_KEY = pub; process.env.VAPID_PRIVATE_KEY = priv; process.env.VAPID_SUBJECT = 'mailto:prueba@example.com'; }
});

// ── Service worker ──
await ok('sw: muestra la notificación sin tag, no cierra nada, abre Inicio y no intercepta peticiones', async () => {
  const oyentes = {}, mostradas = [], abiertas = [], mensajes = [];
  let cerradas = 0, enfocadas = 0, ventanas = [];
  const self = {
    addEventListener: (t, f) => { oyentes[t] = f; }, skipWaiting() {},
    registration: { showNotification: (t, o) => { mostradas.push({ t, o }); return Promise.resolve(); } },
    clients: { claim: () => Promise.resolve(), matchAll: () => Promise.resolve(ventanas), openWindow: u => { abiertas.push(u); return Promise.resolve(); } },
  };
  new Function('self', readFileSync(join(dir, 'sw.js'), 'utf8'))(self);
  assert.ok(!oyentes.fetch, 'el service worker no debe interceptar peticiones');
  let espera;
  oyentes.push({ data: { json: () => ({ title: 'Ka$hy · Hoy vence', body: 'x', url: '/index-nuevo.html' }) }, waitUntil: p => { espera = p; } });
  await espera;
  assert.equal(mostradas[0].t, 'Ka$hy · Hoy vence');
  assert.equal(mostradas[0].o.body, 'x');
  assert.ok(!('tag' in mostradas[0].o) && !mostradas[0].o.renotify);
  const notif = { data: { url: '/index-nuevo.html' }, close: () => { cerradas++; } };
  oyentes.notificationclick({ notification: notif, waitUntil: p => { espera = p; } });
  await espera;
  assert.deepEqual(abiertas, ['/index-nuevo.html']);
  ventanas = [{ url: 'https://kashy.test/index-nuevo.html', postMessage: m => mensajes.push(m), focus: () => { enfocadas++; return Promise.resolve(); } }];
  oyentes.notificationclick({ notification: notif, waitUntil: p => { espera = p; } });
  await espera;
  assert.deepEqual(mensajes, [{ tipo: 'ir-inicio' }]);
  assert.equal(enfocadas, 1);
  assert.equal(cerradas, 0, 'no debe cerrar la notificación');
});

console.log('pruebas: ' + pruebas);
