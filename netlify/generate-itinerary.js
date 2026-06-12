exports.handler = async function(event) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method not allowed' };
  }

  try {
    const { destination, start_date, end_date, prefs } = JSON.parse(event.body);

    const prompt = `You are a travel planner. Create 6 activities for a trip to ${destination} from ${start_date} to ${end_date}.

Traveler info: ${prefs.ageGroups || 'adults'}, ${prefs.travelStyle || 'balanced'} pace, ${prefs.budget || 'moderate'} budget, using ${prefs.transport || 'mixed'} transport.

YOU MUST return ONLY valid JSON. Follow these strict rules:
1. No quotes inside string values - use spaces instead
2. No commas inside string values
3. Keep every string under 60 characters
4. No special characters except letters numbers spaces and basic punctuation

Return this exact structure with 6 items:
[
{"title":"Activity name here","event_date":"${start_date}","event_time":"09:00","location":"Place name here","notes":"Cost 15 USD takes 2 hours"},
{"title":"Activity name here","event_date":"${start_date}","event_time":"14:00","location":"Place name here","notes":"Free entry takes 1 hour"}
]

Only return the JSON array. Nothing before or after it.`;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.REACT_APP_CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-6',
        max_tokens: 800,
        messages: [{ role: 'user', content: prompt }]
      })
    });

    const data = await response.json();

    if (!data.content || !data.content[0]) {
      return { statusCode: 500, body: JSON.stringify({ error: 'No response from Claude' }) };
    }

    const text = data.content[0].text;
    const start = text.indexOf('[');
    const end = text.lastIndexOf(']');

    if (start === -1 || end === -1) {
      return { statusCode: 500, body: JSON.stringify({ error: 'No JSON found: ' + text.slice(0, 200) }) };
    }

    const jsonStr = text.slice(start, end + 1);

    // Validate JSON before returning
    JSON.parse(jsonStr);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: jsonStr
    };

  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: err.message })
    };
  }
};