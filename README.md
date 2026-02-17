# EdTech Digest Agent - Setup & Usage

## Quick Start - Phase 2 (Email Enabled)

### 1. Install Dependencies
```bash
python3 -m pip install anthropic requests
```

### 2. Set Your API Keys
```bash
export ANTHROPIC_API_KEY=your-anthropic-key-here
export GMAIL_APP_PASSWORD=your-16-char-app-password
```

**Getting Gmail App Password:**
1. Go to: https://myaccount.google.com/apppasswords
2. Create new app password for "Mail"
3. Copy the 16-character password
4. Use it in the export command above

(On Windows: use `set` instead of `export`)

### 3. Edit Article URLs
Open `edtech_digest.py` and replace the example URLs in `ARTICLE_URLS` with real articles from this week.

### 4. Run It
```bash
python3 edtech_digest.py
```

---

## What Happens Now

1. **Fetches articles** - Downloads content from each URL
2. **Synthesizes digest** - Claude analyzes all articles and writes ~500 word narrative
3. **Quality checks** - Verifies word count, citations, no placeholders
4. **Extracts theme** - Claude identifies the key theme for subject line
5. **Sends email** - Emails digest from serenaetang@gmail.com to serenatang@microsoft.com

**Important**: If quality checks fail, email is NOT sent. You'll see the digest in terminal instead.

---

## Email Details

- **From:** serenaetang@gmail.com
- **To:** serenatang@microsoft.com
- **Subject:** "Weekly EdTech Digest: [Key Theme]" (auto-generated)
- **Format:** HTML email, nicely formatted
- **Frequency:** Manual for now (Phase 3 adds weekly scheduling)

---

## For This Week's Test

Find 5-8 recent EdTech articles from:
- EdSurge
- Education Week  
- TechCrunch (education tag)
- The74Million

Copy their URLs into the `ARTICLE_URLS` list in the script.

---

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
- Run the export command above in your terminal
- Or add it to your script: `API_KEY = "sk-..."`

**"Failed to fetch" errors**
- Paywalls: Normal, digest will note missing articles
- Timeouts: Try again or remove that URL
- 403 errors: Site blocking bots, remove that URL

**Digest quality issues**
- Too short: Might need more/longer articles
- Too few citations: Model might be paraphrasing too much
- We'll iterate on the prompt if needed

---

## Next Steps After Phase 1

Once you see a good digest:
- Phase 2: Add email sending (10 min)
- Phase 3: Add weekly scheduling (15 min)
- Total: ~60 minutes to fully working agent
