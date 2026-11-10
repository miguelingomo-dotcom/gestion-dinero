/* Ka$hy · service worker: solo notificaciones push.
   - Sin manejador «fetch»: nunca sirve una versión guardada de la app ni toca su caché de pantalla.
   - Cada aviso es una notificación nueva (sin «tag»): no sustituye a las anteriores.
   - No cierra notificaciones: se quedan en el Centro de notificaciones hasta que las borres tú. */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = { body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || 'Ka$hy', {
    body: d.body || '',
    icon: '/icon-192.png',
    data: { url: d.url || '/index-nuevo.html' },
  }));
});

/* Al tocarla: Ka$hy en Inicio (si ya está abierta, se trae al frente y vuelve a Inicio) */
self.addEventListener('notificationclick', e => {
  const url = (e.notification.data && e.notification.data.url) || '/index-nuevo.html';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(ventanas => {
    const abierta = ventanas.find(v => v.url.includes('/index-nuevo.html'));
    if (abierta) {
      abierta.postMessage({ tipo: 'ir-inicio' });
      return abierta.focus();
    }
    return self.clients.openWindow(url);
  }));
});
