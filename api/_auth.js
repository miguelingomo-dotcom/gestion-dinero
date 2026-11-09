// Clave compartida de la API. Se envía en la cabecera X-Kashy-Key y se compara con KASHY_KEY en tiempo constante:
// se comparan las huellas SHA-256, que siempre miden lo mismo, para no revelar ni la longitud de la clave.
// El prefijo _ evita que Vercel publique este archivo como un endpoint.
import { createHash, timingSafeEqual } from 'crypto';

export const CABECERA = 'x-kashy-key';
const huella = valor => createHash('sha256').update(String(valor)).digest();

// Responde el error y devuelve false si la petición no trae la clave correcta
export function autorizado(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  const esperada = process.env.KASHY_KEY;
  if (!esperada) {
    // Sin configurar no se abre la puerta: se rechaza todo, y no con 401 para no pedir una clave que nunca valdría
    res.status(500).json({ error: 'KASHY_KEY sin configurar en Vercel' });
    return false;
  }
  const recibida = req.headers[CABECERA];
  if (typeof recibida !== 'string' || !timingSafeEqual(huella(recibida), huella(esperada))) {
    res.status(401).json({ error: 'No autorizado' });
    return false;
  }
  return true;
}
