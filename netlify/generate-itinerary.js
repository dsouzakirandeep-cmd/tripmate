exports.handler = async function(event) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method not allowed' };
  }

  try {
    const { destination, start_date, end_date, prefs } = JSON.parse(event.body);

    const prompt = `List 6 travel activities for ${destination} from ${start_date} to ${end_date}.
Group: ${prefs.ageGroups || 'adults'}
Style: ${prefs.travelStyle || 'balanced'}
Budget: ${prefs.budget || 'moderate'}
Transport: ${prefs.transport || 'mixed'}

Return ONLY a JSON array. Keep all strings short.
Format: [{"title":"string","event_date":"YYYY-MM-DD","event_time":"HH:MM","location":"string","notes":"string"}]
Maximum 6 items. No markdown. No explanation.`;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.REACT_APP_CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-6',
        max_tokens: 1000,
        messages: [{ role: 'user', content: prompt }]
      })
    });

    const data = await response.json();
    const text = data.content[0].text;
    const start = text.indexOf('[');
    const end = text.lastIndexOf(']');
    const jsonStr = text.slice(start, end + 1);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: jsonStr
    };
  } catch (err) {
    return { statusCode: 500, body: JSON.stringify({ error: err.message }) };
  }
};