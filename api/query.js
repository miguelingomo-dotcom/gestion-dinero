import { autorizado } from './_auth.js';
import { responderDeNotion } from './_notion.js';

export const config = { api: { bodyParser: true } };

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Notion-Version, Content-Type, X-Kashy-Key');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }
  if (!autorizado(req, res)) return;

  const { dbId } = req.query;
  await responderDeNotion(res, `databases/${dbId}/query`, { method: 'POST', body: req.body || {} });
}
