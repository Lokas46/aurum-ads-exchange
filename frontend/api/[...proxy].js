const NGROK_BASE = 'https://recount-preheated-runt.ngrok-free.dev';

export default async function handler(req, res) {
  const path = (req.query.proxy || []).join('/');
  if (!path) {
    return res.status(400).json({ error: 'No API path specified' });
  }

  const qIndex = req.url.indexOf('?');
  const query = qIndex >= 0 ? req.url.slice(qIndex) : '';
  const targetUrl = `${NGROK_BASE}/api/${path}${query}`;

  const headers = { 'User-Agent': 'VercelProxy/1.0' };
  if (req.headers['content-type']) {
    headers['Content-Type'] = req.headers['content-type'];
  }

  let body;
  if (req.method !== 'GET' && req.method !== 'HEAD' && req.body != null) {
    body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
  }

  try {
    const response = await fetch(targetUrl, { method: req.method, headers, body });
    const text = await response.text();
    const contentType = response.headers.get('content-type') || 'application/json';
    res.status(response.status).setHeader('Content-Type', contentType).send(text);
  } catch (error) {
    res.status(502).json({ error: 'Proxy error', detail: error.message });
  }
}
