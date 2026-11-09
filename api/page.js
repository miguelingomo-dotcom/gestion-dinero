import { autorizado } from './_auth.js';
import { responderDeNotion } from './_notion.js';

export const config = { api: { bodyParser: true } };

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Notion-Version, Content-Type, X-Kashy-Key');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }
  if (!autorizado(req, res)) return;

  const { pageId } = req.query;
  if (req.method === 'GET') {
    await responderDeNotion(res, `pages/${pageId}`);
    return;
  }
  if (req.method === 'PATCH') {
    await responderDeNotion(res, `pages/${pageId}`, { method: 'PATCH', body: req.body || {} });
    return;
  }
  await responderDeNotion(res, 'pages', { method: 'POST', body: req.body || {} });
}
