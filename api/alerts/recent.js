export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const alerts = [
    {
      id: 1,
      token_address: "7BgBvyjrZX1YKz4oh9mjb8ZScatkkwb8DzFx7LoiVkM3",
      alert_type: "phoenix_rising",
      message: "🚀 SLERF showing phoenix recovery potential",
      score_at_alert: 96.0,
      timestamp: new Date().toISOString()
    }
  ];

  res.status(200).json(alerts);
} 