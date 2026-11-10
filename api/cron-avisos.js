// Aviso diario (Vercel Cron, ver vercel.json). Dos crons, a las 07:00 y 08:00 UTC: Vercel Hobby los lanza en algún
// momento de esa hora, y solo envía el que cae entre las 9:00 y las 9:59 en Madrid (en verano el de las 07, en
// invierno el de las 08). Calcula lo que vence con kashy-vencimientos.js, la misma lógica que el aviso de Inicio.
// Solo Vercel lo llama: protegido con CRON_SECRET, que Vercel envía como «Authorization: Bearer …».
import { createHash, timingSafeEqual } from 'crypto';
import '../kashy-vencimientos.js';
import { consultarNotion } from './_notion.js';
import { leerAjustes, guardarAjustes } from './_ajustes.js';
import { enviarPush, vapidListo, suscripcionCaducada } from './_push.js';

export const HORA_AVISO = 9;
const huella = v => createHash('sha256').update(String(v)).digest();

// Fecha y hora de Madrid (con su horario de verano) para un instante dado
export function enMadrid(fecha) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23',
  }).formatToParts(fecha).map(x => [x.type, x.value]));
  return { hoy: `${p.year}-${p.month}-${p.day}`, hora: Number(p.hour) };
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  const secreto = process.env.CRON_SECRET;
  if (!secreto) { res.status(500).json({ error: 'CRON_SECRET sin configurar en Vercel' }); return; }
  if (!timingSafeEqual(huella(req.headers.authorization || ''), huella('Bearer ' + secreto))) {
    res.status(401).json({ error: 'No autorizado' });
    return;
  }
  const { hoy, hora } = enMadrid(new Date());
  if (hora !== HORA_AVISO) { res.status(200).json({ enviado: false, motivo: 'fuera de la franja', hoy, hora }); return; }
  if (!vapidListo()) { res.status(500).json({ error: 'Claves VAPID sin configurar en Vercel' }); return; }

  try {
    const ajustes = await leerAjustes();
    if (!ajustes.suscripcion) { res.status(200).json({ enviado: false, motivo: 'sin suscripción' }); return; }
    if (ajustes.ultimoEnvio === hoy) { res.status(200).json({ enviado: false, motivo: 'ya enviado hoy' }); return; }
    const K = globalThis.KashyVencimientos;
    const vence = await K.vencenHoy(hoy, consultarNotion);
    // Recordatorio de la cartera: una sola vez por cada valor registrado (si falla la consulta, sin recordatorio)
    let cartera = null;
    try {
      const c = await K.recordatorioCartera(hoy, consultarNotion);
      if (c.debeAvisar && ajustes.carteraAvisada !== c.clave) cartera = c;
    } catch (e) {}
    const aviso = K.textoNotificacion({ ...vence, cartera });
    if (!aviso) { res.status(200).json({ enviado: false, motivo: 'nada vence hoy' }); return; }

    const estado = await enviarPush(ajustes.suscripcion, { title: aviso.titulo, body: aviso.cuerpo, url: '/index-nuevo.html' });
    if (suscripcionCaducada(estado)) {
      await guardarAjustes(ajustes, { suscripcion: null });
      res.status(200).json({ enviado: false, motivo: 'suscripción caducada: borrada' });
      return;
    }
    if (estado < 200 || estado >= 300) { res.status(502).json({ error: 'El servicio push respondió ' + estado }); return; }
    await guardarAjustes(ajustes, { ultimoEnvio: hoy, ...(cartera ? { carteraAvisada: cartera.clave } : {}) });
    res.status(200).json({ enviado: true, hoy });
  } catch (e) {
    res.status(502).json({ error: String(e.message || e) });
  }
}
