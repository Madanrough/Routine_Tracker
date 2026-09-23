# Erumaa's Daily

Erumaa's Daily is a private, mobile-first personal routine and wellness tracker. It records sleep, exercise, food habits, water, stress-management behavior, mood, and optional daily notes. It is intentionally **not** a medical, diagnostic, fertility, menstrual-cycle, or treatment application.

## Features

- Private email/password sign-in with Supabase Authentication
- One duplicate-safe record per user per India-local date
- Exact 100-point daily scoring with completion as 10% of the score
- Today/yesterday editing; older records are read-only in both UI and database
- Weekly and monthly progress, streaks, factual insights, and mobile-friendly Plotly charts
- 80%+ celebration only after seven complete Monday–Sunday entries
- Locally generated, downloadable PNG achievement card
- CSV export, graceful empty states, and a focused About view
- Dark-purple, touch-friendly Streamlit interface

## Tech stack

Python, Streamlit, Pandas, Plotly, Pillow, Supabase PostgreSQL, and Supabase Authentication. No paid or AI APIs are used. Persistent data lives in Supabase, so the deployed app works while the developer's computer is off.

## Project structure

```text
app.py                      Authentication and four-item navigation
pages/                      Home, Today, History, Progress screens
src/auth.py                 Supabase auth and session handling
src/database.py             Authenticated CRUD and app-layer edit checks
src/scoring.py              All daily/weekly scoring rules
src/timezone_utils.py       Asia/Kolkata date boundaries
src/daily_form.py           Reusable today/yesterday editor
src/history.py              History presentation helpers
src/progress.py             Weekly/monthly aggregation
src/insights.py             Descriptive non-medical insights
src/celebrations.py         Local Pillow PNG generation
src/ui.py                   Shared responsive UI and Settings
src/validators.py           Server-side input validation
supabase/schema.sql         Schema, constraints, indexes, RLS, immutability
tests/                      Scoring, date, validation, streak tests
```

## Supabase setup

1. Create a free Supabase project.
2. Open **SQL Editor**, paste `supabase/schema.sql`, and run the complete script.
3. In **Authentication → Providers**, keep Email enabled. For a private single-user deployment, disable public sign-ups after creating the intended account.
4. Create the user in **Authentication → Users → Add user**. Do not put the email or password in source code.
5. From **Project Settings → API**, copy the project URL and the anon/public key. Never use the service-role key in this app.

The SQL enables and forces Row Level Security. Authenticated users can select only their own rows, insert only their own current/recent rows, and update only their own today/yesterday rows. There is deliberately no delete policy. A database trigger separately prevents changing an entry owner/date and rejects updates older than yesterday using `Asia/Kolkata`.

## Local installation

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_ANON_KEY"
```

Then run:

```powershell
streamlit run app.py
```

The same values may instead be provided as `SUPABASE_URL` and `SUPABASE_ANON_KEY` environment variables. `.streamlit/secrets.toml` and `.env` are ignored by Git.

## Tests

```powershell
pytest
```

The suite covers all specified sleep/exercise/water examples, food semantics, stress and mood neutrality, celebration thresholds, India-local date behavior, edit permissions, validation, and streaks.

## Free deployment (Streamlit Community Cloud)

1. Complete the Supabase steps above and test locally.
2. Create a private or public GitHub repository and push this project. Confirm no real secret file is staged.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and create an app from the repository.
4. Set the entry point to `app.py`.
5. In the deployment's **Secrets** panel, add `SUPABASE_URL` and `SUPABASE_ANON_KEY` in the same TOML format shown above.
6. Deploy, sign in with the private Supabase account, and save a test entry.
7. Confirm the entry appears in Supabase Table Editor, refresh the app, and confirm it persists.
8. Test at roughly 360 px width or on the target Android phone: navigation, every form choice, save/update, history, charts, CSV export, and card download.

The hosted Streamlit process talks directly to Supabase; the developer PC is not part of production runtime.

## Security notes

- Never commit passwords, `.env`, `.streamlit/secrets.toml`, access tokens, or the Supabase service-role key.
- The anon key is expected in the server-side app configuration; authorization is enforced by the signed-in user's JWT plus PostgreSQL RLS.
- UI restrictions are convenience only. RLS and the update trigger enforce ownership and the edit window at the database layer.
- Daily records should never be copied into GitHub issues, logs, fixtures, or source code.
- Before sharing the app URL, disable public sign-up in Supabase if only one account should exist.

## Scoring

The implementation is documented in `src/scoring.py`: Sleep 20%, Exercise 20%, Food 25%, Water 15%, Stress-management action 10%, and completion 10%. Food already includes 80% meal quality and 20% junk/sugary-food control, so junk food is not double-counted. Mood and stress level never change the score.

## Production checklist

- Supabase schema ran without errors; RLS is enabled and policies are visible.
- Only the intended account can authenticate; public sign-up is disabled if desired.
- Today saves once and repeated saves update the same row.
- Yesterday updates; a two-days-old update is rejected.
- India-local midnight, Monday–Sunday boundaries, streaks, and charts are correct.
- Celebration stays locked for six days and for a seven-day average below 80%.
- CSV includes only the signed-in user's rows.
- No credentials are tracked by Git.
- Login and all four pages work at mobile and desktop widths.

