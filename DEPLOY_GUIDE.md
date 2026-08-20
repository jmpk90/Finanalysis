# EQUITEX PRO — Cloud Deployment Guide
**From local Python script → live website in ~45 minutes**

---

## What you'll set up
- **GitHub** — stores your code (free)
- **Supabase** — stores your data in the cloud (free, no credit card)
- **Streamlit Community Cloud** — runs your app and gives you a public URL (free)

Final result: `https://your-name-equitex.streamlit.app`

---

## Files you need (all in one folder)

```
equitex-pro/
├── FinAnalysis_Pro.py       ← main app
├── finance_advisor.py       ← finance module
├── mf_module.py             ← mutual funds module
├── equitex_store.py         ← NEW: cloud storage (provided)
├── requirements.txt         ← NEW: dependencies (provided)
└── .streamlit/
    ├── secrets.toml         ← NEW: your API keys (provided template)
    └── config.toml          ← NEW: app config (provided)
```

---

## STEP 1 — Create a GitHub account & repository (10 min)

### 1a. Create GitHub account
1. Go to **github.com**
2. Click **Sign up** — use your email, create username and password
3. Verify your email

### 1b. Create a new repository
1. After login, click the **＋** button (top right) → **New repository**
2. Repository name: `equitex-pro`
3. Set to **Private** (so only you can see your code)
4. Click **Create repository**

### 1c. Upload your files
1. On the repository page, click **uploading an existing file**
2. Drag and drop ALL your files:
   - `FinAnalysis_Pro.py`
   - `finance_advisor.py`
   - `mf_module.py`
   - `equitex_store.py`
   - `requirements.txt`
3. Click **Commit changes**

### 1d. Upload the .streamlit folder
> GitHub doesn't show hidden folders (starting with `.`) in the drag-drop UI.
> Do this separately:

1. Click **Add file** → **Create new file**
2. In the filename box type: `.streamlit/config.toml`
3. Paste the contents of `config.toml` (provided)
4. Click **Commit new file**

> ⚠️ Do NOT upload `secrets.toml` to GitHub — it contains your private keys.
> You'll enter secrets directly in Streamlit Cloud's dashboard.

---

## STEP 2 — Set up Supabase (free database) (10 min)

### 2a. Create account
1. Go to **supabase.com**
2. Click **Start your project** → sign up with GitHub (easiest) or email
3. No credit card needed

### 2b. Create a project
1. Click **New project**
2. Name it: `equitex-pro`
3. Set a database password (save it somewhere)
4. Region: **Mumbai (ap-south-1)** — closest to India
5. Click **Create new project** — wait ~2 minutes

### 2c. Create the 3 tables

Go to **Table Editor** → **New table** and create these 3 tables:

**Table 1: `portfolios`**
| Column name | Type | Default | Primary |
|---|---|---|---|
| id | int8 | auto | ✅ |
| user_id | text | — | — |
| data | text | — | — |

Click **Save**.

**Table 2: `profiles`**
| Column name | Type | Default | Primary |
|---|---|---|---|
| id | int8 | auto | ✅ |
| user_id | text | — | — |
| data | text | — | — |

Click **Save**.

**Table 3: `mf_store`**
| Column name | Type | Default | Primary |
|---|---|---|---|
| id | int8 | auto | ✅ |
| user_id | text | — | — |
| data | text | — | — |

Click **Save**.

### 2d. Add unique constraint on user_id

For each of the 3 tables:
1. Go to **Database** → **Tables** → click the table name
2. Click **Add index** (or go to SQL Editor and run):

```sql
-- Run this in SQL Editor (Database → SQL Editor → New query)
ALTER TABLE portfolios ADD CONSTRAINT portfolios_user_id_key UNIQUE (user_id);
ALTER TABLE profiles   ADD CONSTRAINT profiles_user_id_key   UNIQUE (user_id);
ALTER TABLE mf_store   ADD CONSTRAINT mf_store_user_id_key   UNIQUE (user_id);
```

Click **Run** — you should see "Success".

### 2e. Get your API keys

1. Go to **Settings** (gear icon, left sidebar) → **API**
2. Copy these two values — you'll need them in Step 4:
   - **Project URL** → looks like `https://abcdefgh.supabase.co`
   - **anon public** key → long string starting with `eyJ...`

---

## STEP 3 — Deploy on Streamlit Community Cloud (10 min)

### 3a. Create account
1. Go to **share.streamlit.io**
2. Click **Sign up** → **Continue with GitHub**
3. Authorize Streamlit to access GitHub

### 3b. Deploy your app
1. Click **New app**
2. **Repository**: select `your-username/equitex-pro`
3. **Branch**: `main`
4. **Main file path**: `FinAnalysis_Pro.py`
5. Click **Deploy!**

> The app will try to start — it will fail at first because the secrets aren't set yet. That's fine.

---

## STEP 4 — Add your secret keys (5 min)

### In Streamlit Cloud:
1. Go to your app → click **⋮** (three dots) → **Settings**
2. Click **Secrets** tab
3. Paste this (fill in YOUR values from Step 2e):

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "eyJ...your-anon-key..."
USER_ID = "rahul_equitex"
```

4. Click **Save**
5. Click **Reboot app**

---

## STEP 5 — Verify it works

1. Wait ~2 minutes for the app to boot
2. Open your app URL: `https://your-app-name.streamlit.app`
3. You should see EQUITEX PRO load with the Clean Light theme
4. Add a portfolio — it should save and persist even after refreshing

---

## STEP 6 — Migrate your existing data (optional)

If you already have data saved locally (`equitex_data.json`, `equitex_profile.json`):

1. Open your running app
2. Go to **Wealth** tab → **Import / Restore profile** → upload `equitex_profile.json`
3. Go to **Portfolio** tab → **Add Portfolio** → upload your broker CSV files again

---

## Troubleshooting

### App shows "Module not found" error
Make sure ALL .py files are uploaded to GitHub.

### Data not saving
1. Check Supabase → Table Editor → is the table empty or does it have a row?
2. Double-check your `SUPABASE_URL` and `SUPABASE_KEY` in Streamlit secrets — no extra spaces
3. Make sure the unique constraints were added (Step 2d)

### App crashes on startup
1. Go to Streamlit Cloud → your app → **Logs** tab
2. Read the error — it usually tells you exactly what's wrong

### yfinance not loading stock data
yfinance works fine on Streamlit Cloud. If a ticker fails, it's usually a network timeout — just retry.

---

## Keeping your app updated

Whenever you change a file:
1. Go to your GitHub repository
2. Click the file → **Edit** (pencil icon)
3. Make changes → **Commit changes**
4. Streamlit Cloud automatically detects the change and redeploys in ~1 minute

---

## Your app URLs

| What | Where |
|---|---|
| Your app | `https://your-app.streamlit.app` |
| GitHub repo | `https://github.com/your-username/equitex-pro` |
| Supabase dashboard | `https://supabase.com/dashboard` |
| Streamlit Cloud | `https://share.streamlit.io` |

---

## Cost summary

| Service | Free tier | Limits |
|---|---|---|
| GitHub | Free | Unlimited private repos |
| Supabase | Free | 500MB database, 2GB transfer/mo |
| Streamlit Cloud | Free | 1 app, sleeps after 7 days inactivity (wakes on visit) |
| Groq (AI Advisor) | Free | 14,400 req/day |

**Total cost: ₹0**

The only limitation is Streamlit Cloud's free tier puts the app to "sleep" after 7 days of no visits — it wakes up automatically when you open the URL, taking about 30 seconds.

---

## If you want a custom domain (optional)

Streamlit Cloud doesn't support custom domains on the free tier.
If you want `equitex.yourdomain.com`:
1. Upgrade to Streamlit Cloud Teams ($250/mo) — not worth it
2. Or migrate to **Railway** (~$5/mo) which supports custom domains

For personal use the `streamlit.app` URL is perfectly fine.
