# Optional: Deploy Against Real PostgreSQL

The main app (`../app.py`) needs zero setup — it bundles its own data.
This folder is an **optional upgrade** for a stronger resume/interview
story: "I also deployed it against a real managed Postgres database,"
instead of only an in-memory demo.

This is a separate, read-only app (`app_postgres.py`) — it doesn't
replace the main one. Deploy both if you like; they're independent.

## Step 1 — Create a free Postgres database (Supabase)

1. Go to [supabase.com](https://supabase.com) and sign up (free tier).
2. Click **New Project**. Pick any name/region, set a database
   password (save it somewhere), wait ~2 minutes for it to provision.
3. Once ready, click **SQL Editor** in the left sidebar.

## Step 2 — Create the schema and load the data

1. In the SQL Editor, click **New Query**.
2. Open `schema.sql` from this folder, copy its contents, paste into
   the editor, click **Run**.
3. New query again, this time paste in `seed_data.sql` (the 500-row
   dataset), click **Run**. This may take a few seconds.
4. Sanity check: new query, run `SELECT COUNT(*) FROM trips;` — should
   return 500.

## Step 3 — Get your connection string

1. In Supabase, go to **Project Settings → Database**.
2. Under **Connection string**, choose the **URI** tab, copy it. It
   looks like:
   `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres`
3. Replace `[YOUR-PASSWORD]` with the database password from Step 1.

## Step 4 — Deploy the Postgres-backed app

1. Create a new GitHub repo (e.g. `ride-sharing-dashboard-postgres`).
2. Upload `app_postgres.py` and `requirements.txt` from this folder to
   the repo root via the GitHub web UI.
3. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
   → point it at your repo, main file path `app_postgres.py`.
4. **Before or after deploying**, go to your app's **Settings → Secrets**
   in Streamlit Cloud and paste:
   ```
   DATABASE_URL = "postgresql://postgres:your-password@db.xxxxx.supabase.co:5432/postgres"
   ```
5. Save, and the app will restart and connect automatically.

## Notes

- This app is **read-only** on purpose — editing production data
  through a public app URL is bad practice. Use Supabase's SQL Editor
  to change data instead.
- If the app shows a connection error, double check: password has no
  typos, no extra brackets left in the URL, and the Supabase project
  is fully provisioned (not still spinning up).
- Free-tier Supabase projects pause after a week of inactivity — if
  your app suddenly can't connect, log into Supabase once to wake it
  back up.
