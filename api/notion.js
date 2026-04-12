export default async function handler(req, res) {
  // Extraer el path de Notion desde la query
  const notionPath = req.url.replace('/api/notion', '').split('?')[0];
  
  const response = await fetch(`https://api.notion.com/v1${notionPath}`, {
    method: req.method,
    headers: {
      'Authorization': req.headers.authorization || '',
      'Notion-Version': req.headers['notion-version'] || '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: req.method === 'POST' ? JSON.stringify(req.body) : undefined,
  });

  const data = await response.json();
  
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Notion-Version, Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  res.status(response.status).json(data);
}
