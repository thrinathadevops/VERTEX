# AI Interview App

Standalone AI interview platform for VAREX.

## Interview Modes

- `Free Mock`: First mock interview is free (one-time per email).
- `Paid Mock`: From second mock onwards, each attempt is `Rs 50`.
- `Real Company Interview`: Package billing at `Rs 500` per interview with volume discount:
  - `2+` interviews: `5%`
  - `5+` interviews: `10%`
  - `10+` interviews: `30%`
  - `20+` interviews: `50%`

## Run

```bash
docker compose up -d --build
```

Open: `http://localhost:3010`

Get a Gemini API key (free): https://aistudio.google.com/apikey
Add to your .env

AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...your-key
Rebuild: docker compose up --build -d

Graceful fallback: If no API key is set or LLM is unavailable, the app automatically falls back to static questions + word-count scoring — it never crashes.

