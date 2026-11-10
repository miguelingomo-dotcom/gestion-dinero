// Notificaciones desde la app (con X-Kashy-Key):
//   GET              → { publicKey, suscrito, endpoint }
//   POST {subscription} → guarda la suscripción del iPhone
//   POST ?prueba=1   → envía una notificación de prueba
//   DELETE           → borra la suscripción
import { autorizado } from './_auth.js';
import { leerAjustes, guardarAjustes } from './_ajustes.js';
import { enviarPush, vapidListo, suscripcionCaducada } from './_push.js';

export const config = { api: { bodyParser: true } };

function suscripcionValida(s) {
  return !!(s && typeof s.endpoint === 'string' && s.endpoint.startsWith('https://') && s.keys && s.keys.p256dh && s.keys.auth);
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Kashy-Key');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }
  if (!autorizado(req, res)) return;
  if (!vapidListo()) { res.status(500).json({ error: 'Claves VAPID sin configurar en Vercel' }); return; }

  try {
    const ajustes = await leerAjustes();
    if (req.method === 'GET') {
      res.status(200).json({ publicKey: process.env.VAPID_PUBLIC_KEY, suscrito: !!ajustes.suscripcion,
        endpoint: ajustes.suscripcion ? ajustes.suscripcion.endpoint : null });
      return;
    }
    if (req.method === 'DELETE') {
      await guardarAjustes(ajustes, { suscripcion: null });
      res.status(200).json({ ok: true });
      return;
    }
    if (req.method !== 'POST') { res.status(405).json({ error: 'Usa GET, POST o DELETE' }); return; }

    if (req.query.prueba) {
      if (!ajustes.suscripcion) { res.status(409).json({ error: 'Sin suscripción' }); return; }
      const estado = await enviarPush(ajustes.suscripcion, {
        title: 'Ka$hy · Prueba', body: 'Las notificaciones funcionan ✓', url: '/index-nuevo.html',
      });
      if (suscripcionCaducada(estado)) {
        await guardarAjustes(ajustes, { suscripcion: null });
        res.status(410).json({ error: 'La suscripción ya no es válida' });
        return;
      }
      if (estado < 200 || estado >= 300) {
        console.error('push de prueba rechazado:', estado);
        res.status(502).json({ error: 'El servicio push respondió ' + estado });
        return;
      }
      res.status(200).json({ ok: true });
      return;
    }

    const s = req.body && req.body.subscription;
    if (!suscripcionValida(s)) { res.status(400).json({ error: 'Suscripción no válida' }); return; }
    await guardarAjustes(ajustes, { suscripcion: { endpoint: s.endpoint, keys: { p256dh: s.keys.p256dh, auth: s.keys.auth } } });
    res.status(200).json({ ok: true });
  } catch (e) {
    console.error('api/push:', e.message || e);
    res.status(502).json({ error: String(e.message || e) });
  }
}
