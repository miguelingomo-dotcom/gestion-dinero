// Llamadas a la API de Notion con el token de la variable NOTION_TOKEN (solo en Vercel, nunca en el código).
// Un fallo del token no se devuelve como 401: la app lo tomaría por una clave X-Kashy-Key incorrecta y la volvería a pedir.
export async function responderDeNotion(res, ruta, { method = 'GET', body } = {}) {
  const token = process.env.NOTION_TOKEN;
  if (!token) {
    res.status(500).json({ error: 'NOTION_TOKEN sin configurar en Vercel' });
    return;
  }
  const headers = { 'Authorization': 'Bearer ' + token, 'Notion-Version': '2022-06-28' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const response = await fetch(`https://api.notion.com/v1/${ruta}`, {
    method,
    headers,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  const data = await response.json();
  if (response.status === 401) {
    res.status(502).json({ error: 'Notion rechaza NOTION_TOKEN', message: 'Notion rechaza NOTION_TOKEN' });
    return;
  }
  res.status(response.status).json(data);
}
