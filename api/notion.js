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

  const notionPath = req.url.replace('/api/notion', '').split('?')[0];

  const body = req.method === 'POST' ? JSON.stringify(req.body) : undefined;

  const response = await fetch(`https://api.notion.com/v1${notionPath}`, {
    method: req.method,
    headers: {
      'Authorization': req.headers.authorization || '',
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body,
  });

  const data = await response.json();
  res.status(response.status).json(data);
}
