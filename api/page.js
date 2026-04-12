export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Notion-Version, Content-Type');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const response = await fetch(`https://api.notion.com/v1/pages`, {
    method: 'POST',
    headers: {
      'Authorization': req.headers.authorization,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(req.body),
  });
  const data = await response.json();
  res.status(response.status).json(data);
}
