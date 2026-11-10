// Envío de notificaciones Web Push con VAPID. web-push cifra y firma (generateRequestDetails) y el envío se hace con
// fetch, así los tests pueden interceptarlo. TTL de 24 h: si el iPhone está apagado, llega al encenderlo.
// Sin «Topic»: cada aviso es una notificación nueva y no sustituye a las anteriores en el Centro de notificaciones.
import webpush from 'web-push';

export const TTL_SEGUNDOS = 24 * 60 * 60;

// Las claves se limpian antes de usarlas: al copiarlas a Vercel se cuelan espacios, saltos de línea o un «=» final,
// y web-push solo acepta Base64 URL-safe sin relleno. Son los mismos bytes, así que las suscripciones siguen valiendo
export const limpiarClave = v => String(v || '').replace(/\s+/g, '').replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');
export const clavePublica = () => limpiarClave(process.env.VAPID_PUBLIC_KEY);

export function vapidListo() {
  return !!(clavePublica() && limpiarClave(process.env.VAPID_PRIVATE_KEY) && String(process.env.VAPID_SUBJECT || '').trim());
}

// Devuelve el código HTTP del servicio push (201 = aceptado; 404/410 = la suscripción ya no existe)
export async function enviarPush(suscripcion, aviso) {
  const d = webpush.generateRequestDetails(suscripcion, JSON.stringify(aviso), {
    vapidDetails: {
      subject: String(process.env.VAPID_SUBJECT).trim(),
      publicKey: clavePublica(),
      privateKey: limpiarClave(process.env.VAPID_PRIVATE_KEY),
    },
    TTL: TTL_SEGUNDOS,
    urgency: 'high',
  });
  const r = await fetch(d.endpoint, { method: d.method || 'POST', headers: d.headers, body: d.body });
  return r.status;
}

export const suscripcionCaducada = estado => estado === 404 || estado === 410;
