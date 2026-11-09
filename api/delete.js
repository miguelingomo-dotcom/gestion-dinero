import { autorizado } from './_auth.js';
import { responderDeNotion } from './_notion.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type, X-Kashy-Key');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }
  if (!autorizado(req, res)) return;

  const { pageId } = req.query;
  await responderDeNotion(res, `pages/${pageId}`, { method: 'PATCH', body: { archived: true } });
}
