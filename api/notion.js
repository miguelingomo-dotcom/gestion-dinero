export default async function handler(req, res) {
  const path = req.url.replace('/api/notion', '');
  
  const response = await fetch(`https://api.notion.com${path}`, {
    method: req.method,
    headers: {
      'Authorization': req.headers.authorization,
      'Notion-Version': req.headers['notion-version'],
      'Content-Type': 'application/json',
    },
    body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined,
  });

  const data = await response.json();
  res.status(response.status).json(data);
}
