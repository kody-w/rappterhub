---
name: WeatherPoet
version: 1.0.0
description: Fetches live weather for any city and composes a haiku about the conditions. Demonstrates data_slush for agent-to-agent signal chaining.
author: kody-w
runtime: python
tags: [weather, poetry, haiku, data-slush, demo]
---

# WeatherPoet 🌦️✍️

An openrappter agent that fetches **live weather data** from [wttr.in](https://wttr.in) for any city, then composes a **haiku** inspired by the conditions.

Also serves as the reference example for **data slush** — the agent-to-agent signal pipeline. WeatherPoet returns curated `data_slush` signals (temperature, condition, mood) that downstream agents can consume without an LLM interpreting in between.

## Usage

```bash
openrappter --exec WeatherPoet "Smyrna GA"
openrappter --exec WeatherPoet "Tokyo"
openrappter --exec WeatherPoet "Reykjavik"
```

## Example Output

```json
{
  "status": "success",
  "city": "Smyrna GA",
  "weather": {
    "condition": "Partly cloudy",
    "temp_f": "65",
    "temp_c": "18",
    "feels_like_f": "65",
    "humidity": "65%",
    "wind_mph": "12"
  },
  "haiku": "Gray clouds drift along\nshapes dissolve and reappear\nthe world waits below",
  "observed_at": "afternoon",
  "data_slush": {
    "source_agent": "WeatherPoet",
    "city": "Smyrna GA",
    "condition": "partly cloudy",
    "temp_f": 65,
    "humidity_pct": 65,
    "mood": "clouds"
  }
}
```

## Data Slush Output

WeatherPoet curates these signals for downstream agents:

| Key | Type | Description |
|-----|------|-------------|
| `source_agent` | string | Always `"WeatherPoet"` |
| `city` | string | The queried city |
| `condition` | string | Weather condition (lowercase) |
| `temp_f` | int | Temperature in Fahrenheit |
| `humidity_pct` | int | Humidity percentage |
| `mood` | string | Mapped mood: `clear`, `clouds`, `rain`, `snow`, `fog` |

### Chaining Example

```python
# WeatherPoet → any downstream agent
poet = WeatherPoetAgent()
result = poet.execute(query="Smyrna GA")

# Feed curated signals into the next agent
advisor = ClothingAdvisorAgent()
result2 = advisor.execute(
    query="what should I wear?",
    upstream_slush=poet.last_data_slush
)
# advisor.context['upstream_slush'] == {"temp_f": 65, "mood": "clouds", ...}
```

## Weather Conditions & Haiku Moods

| Condition | Mood | Sample Line 1 |
|-----------|------|---------------|
| Clear/Sunny | `clear` | "Blue sky stretches wide" |
| Cloudy/Overcast | `clouds` | "Gray clouds drift along" |
| Rain/Drizzle | `rain` | "Raindrops tap the roof" |
| Snow/Sleet | `snow` | "Snowflakes softly fall" |
| Fog/Mist | `fog` | "Fog swallows the road" |

## Requirements

- Python 3.10+
- No external dependencies (uses `urllib` from stdlib)
- Internet access for wttr.in API

## Features

- 🌍 Works with any city, state, or country
- 🎲 Randomized haiku lines for variety
- 🕐 Time-aware via data sloshing (`observed_at` uses temporal context)
- 🧊 Data slush output for agent-to-agent chaining
- 📦 Zero dependencies — stdlib only
