# 🚖 Ride-Sharing Analytics — Streamlit Dashboard

Interactive version of the SQL project. No database setup needed — it
runs on an in-memory SQLite database seeded with the same 500-trip
dataset as `ride_sharing_analytics.sql`.

## What's inside
- `app.py` — the app
- `riders_data.csv`, `drivers_data.csv`, `trips_data.csv` — the default
  dataset (500 trips / 40 riders / 18 drivers) it loads on startup
- `requirements.txt` — the two packages it needs

Want to run this against a **real Postgres database** instead of the
bundled demo data, as a resume talking point? See `postgres_deploy/` —
it's a self-contained optional add-on, the main app above still works
standalone with zero setup.

## Deploy on Streamlit Community Cloud

1. Create a new GitHub repo (e.g. `ride-sharing-dashboard`)
2. Upload `app.py` and `requirements.txt` to the repo root via the
   GitHub web UI (drag both in at once, same as you did for `voyager`)
3. Go to [share.streamlit.io](https://share.streamlit.io), sign in,
   click **New app**
4. Point it at your repo, branch `main`, main file path `app.py`
5. Click **Deploy** — it'll be live in a minute or two

## Run locally (optional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## What it shows
- Headline KPI row (total trips, completed, cancellation rate, revenue, fare/km)
- **Edit Data** — spreadsheet-style grids to add/change riders, drivers,
  trips; everything below updates live, no button needed
- **Revenue, Drivers, Riders, Peak Times, Routes** — the core KPI breakdowns
- **Trends** — monthly revenue/volume, month-over-month growth, weekly
  cancellation rate, new rider signups
- **Insights** — plain-English findings (cancellation gap by vehicle,
  revenue concentration, surge-hour premium, revenue trend), computed
  live from SQL, not hardcoded
- **Ask the Data** — a chatbot (powered by Groq) that explains the
  current KPIs/insights in plain English, or answers follow-up
  questions about them. Requires a free Groq API key — see below.
- **Raw SQL** — type and run your own query against the current data

## Setting up the "Ask the Data" chatbot (optional)

The rest of the app works with zero configuration. This one tab needs
a free API key:

1. Go to [console.groq.com](https://console.groq.com), sign up, and
   create an API key (Groq's free tier is generous and plenty for a
   demo app).
2. In your deployed app on [share.streamlit.io](https://share.streamlit.io),
   go to **Settings → Secrets** and add:
   ```
   GROQ_API_KEY = "your-key-here"
   ```
3. Save — the app restarts automatically and the chat tab starts working.

Running locally instead? Create a `.streamlit/secrets.toml` file next
to `app.py` with the same line.

If you see a "model not found" type error in the chat tab, Groq may
have retired the model this app uses — open `app.py`, find the
`GROQ_MODEL` constant near the top, and swap in a current model name
from [console.groq.com/docs/models](https://console.groq.com/docs/models).
