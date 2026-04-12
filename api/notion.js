export const config = {
  api: {
    bodyParser: true,
  },
};

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Notion-Version, Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // El rewrite de Vercel manda todo a /api/notion
  // El path real viene en req.query o en req.url
  const url = new URL(req.url, 'https://placeholder.com');
  const notionPath = url.pathname.replace('/api/notion', '');
  
  const notionUrl = `https://api.notion.com/v1${notionPath}`;

  const response = await fetch(notionUrl, {
    method: req.method,
    headers: {
      'Authorization': req.headers.authorization || '',
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: req.method === 'POST' ? JSON.stringify(req.body) : undefined,
  });

  const data = await response.json();
  res.status(response.status).json(data);
}
