# AI Policy Daily Digest 📰

A lightweight Python automation that scrapes curated AI policy RSS feeds, ranks the top 3 stories by relevance and recency, and delivers them to your email every morning.

Built as part of pre-HKS MPP preparation for specialising in AI/Tech Policy.

---

## How it works

```
GitHub Actions (cron: 7 AM IST)
        ↓
src/fetch_news.py  — fetches 10 RSS feeds, scores by keyword relevance + recency
        ↓
src/email_template.py — renders a clean HTML email
        ↓
src/main.py — sends via Gmail SMTP
        ↓
Your inbox ✓
```

No web scraping, no API keys, no rate limiting. All sources expose public RSS feeds.

---

## Sources monitored

| Source | Type |
|---|---|
| Tech Policy Press | Think tank |
| CSIS AI & Security | Think tank |
| Brookings Technology | Think tank |
| RAND AI | Research |
| Stanford HAI | Research |
| MIT Technology Review | Journalism |
| The Verge (AI) | Journalism |
| Wired (AI) | Journalism |
| EU Digital Strategy | Government |
| Hard Fork (NYT) | Podcast |

---

## Setup (takes ~15 minutes)

### Step 1 — Fork or clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/ai-news-digest.git
cd ai-news-digest
```

### Step 2 — Create a Gmail App Password

You need a **Gmail App Password** (not your regular Gmail password) to let the script send email on your behalf.

1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** (required)
3. Go to **Security → App Passwords**
4. Select app: **Mail** → Select device: **Other** → type `ai-digest` → click **Generate**
5. Copy the 16-character password shown (e.g. `abcd efgh ijkl mnop`) — you won't see it again
6. Remove the spaces when saving: `abcdefghijklmnop`

> **Note:** If you don't see "App Passwords", your account may have Advanced Protection enabled. In that case, create a new plain Gmail account just for sending this digest.

### Step 3 — Add GitHub Secrets

In your GitHub repository:
1. Go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret** for each of the following:

| Secret name | Value |
|---|---|
| `SENDER_EMAIL` | Your Gmail address (e.g. `yourname@gmail.com`) |
| `SENDER_PASSWORD` | The 16-char App Password from Step 2 |
| `RECIPIENT_EMAIL` | Where to deliver the digest (can be same Gmail, or any email) |
| `GITHUB_USERNAME` | Your GitHub username |

### Step 4 — Adjust the send time

Open `.github/workflows/daily_digest.yml` and check the cron line:

```yaml
- cron: "30 1 * * *"   # 1:30 AM UTC = 7:00 AM IST
```

Common alternatives:
- `"30 1 * * *"` → 7:00 AM IST (Delhi, pre-departure)
- `"00 13 * * *"` → 7:00 AM EST (Boston, after Aug 24)
- `"30 0 * * *"` → 6:00 AM IST if you want it earlier

Cron format: `minute hour day month weekday`

### Step 5 — Test it manually

1. Go to your repo → **Actions** tab
2. Click **AI Policy Daily Digest** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Watch the logs — you should receive an email within 60 seconds

### Step 6 — Enable scheduled runs

GitHub Actions workflows with `schedule:` triggers are enabled by default on public repos. On private repos, make sure Actions are enabled under **Settings → Actions → General → Allow all actions**.

> **Note:** GitHub may disable scheduled workflows if the repo has no activity for 60 days. Just re-enable from the Actions tab if this happens.

---

## Customising sources

Edit `src/fetch_news.py` — the `RSS_SOURCES` list at the top. Each entry has:
- `name` — display name in the email
- `url` — RSS feed URL
- `weight` — multiplier for scoring (1.3 = prioritise this source)

To find an RSS feed for any website: try appending `/feed`, `/rss`, or `/feed.xml` to the homepage URL. Or search `site:example.com RSS`.

---

## Folder structure

```
ai-news-digest/
├── .github/
│   └── workflows/
│       └── daily_digest.yml   ← GitHub Actions cron job
├── src/
│   ├── main.py                ← Entry point
│   ├── fetch_news.py          ← RSS fetcher + ranker
│   └── email_template.py      ← HTML email renderer
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Troubleshooting

**Email not arriving?**
- Check GitHub Actions logs for errors (Actions tab → click the run)
- Verify secrets are set correctly (names must match exactly, no extra spaces)
- Check your spam folder
- Make sure 2FA is enabled on Gmail before generating the App Password

**`SMTPAuthenticationError`?**
- Your App Password is wrong or has extra spaces — regenerate it
- Check that `SENDER_EMAIL` is the Gmail account you generated the password for

**No stories in email?**
- All RSS sources returned items older than 48 hours (unlikely on weekdays)
- Run manually and check the Actions log output

---

## Switching to Boston time (after Aug 24)

Update the cron line in `daily_digest.yml`:
```yaml
- cron: "00 13 * * *"   # 7:00 AM EST (UTC-5, Boston winter)
```
Or `"00 12 * * *"` for EDT (UTC-4, Boston summer through November).
