exports.handler = async function(event) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method not allowed' };
  }

  try {
    const { destination, start_date, end_date, prefs } = JSON.parse(event.body);

    const prompt = `Create travel activities for a trip to ${destination} from ${start_date} to ${end_date}.
Group: ${prefs.ageGroups || 'adults'}, ${prefs.travelStyle || 'balanced'} pace, ${prefs.budget || 'moderate'} budget, ${prefs.transport || 'mixed'} transport.
Special: ${prefs.restrictions || 'none'}

Return ONLY a JSON array with 8 items. No text before or after.
Each item: {"title":"string","event_date":"YYYY-MM-DD","event_time":"HH:MM","location":"string","notes":"string"}
Keep notes under 40 chars. No quotes or commas inside values.`;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.REACT_APP_CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-6',
        max_tokens: 1500,
        messages: [{ role: 'user', content: prompt }]
      })
    });

    const data = await response.json();
    if (!data.content || !data.content[0]) {
      return { statusCode: 500, body: JSON.stringify({ error: 'No response from Claude' }) };
    }

    const text = data.content[0].text;
    
    // Smart JSON repair - handles truncated responses
    function repairAndParseJSON(raw) {
      const start = raw.indexOf('[');
      if (start === -1) throw new Error('No JSON array found in response');
      
      let jsonStr = raw.slice(start);
      let lastCompleteEnd = -1;
      let depth = 0;
      let inString = false;
      let escaped = false;
      
      for (let i = 0; i < jsonStr.length; i++) {
        const ch = jsonStr[i];
        if (escaped) { escaped = false; continue; }
        if (ch === '\\' && inString) { escaped = true; continue; }
        if (ch === '"') { inString = !inString; continue; }
        if (inString) continue;
        if (ch === '{') depth++;
        if (ch === '}') {
          depth--;
          if (depth === 0) lastCompleteEnd = i;
        }
      }
      
      if (lastCompleteEnd === -1) throw new Error('No complete JSON objects found');
      
      const trimmed = jsonStr.slice(0, lastCompleteEnd + 1) + ']';
      const fixed = trimmed.replace(/,\s*\]/g, ']').replace(/,\s*}/g, '}');
      return JSON.parse(fixed);
    }

    const suggestions = repairAndParseJSON(text);

    if (!suggestions.length) {
      return { statusCode: 500, body: JSON.stringify({ error: 'No activities generated' }) };
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(suggestions)
    };

  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: err.message })
    };
  }
};