# AreaPulse 🗺️
**Civic Issue Tracker for Delhi**

> Live: [problem-map.onrender.com](https://problem-map.onrender.com)

Report potholes, garbage, broken streetlights, sewage leaks and more — see them on a live heatmap, earn points, and escalate to NGOs.

---

## Features
- 🗺️ **Live Heatmap** — issue density across 50+ Delhi areas
- 📍 **Report Issues** — with GPS auto-detection and keyword auto-tagging
- ⬆️ **Upvote · Verify · Resolve** — community moderation with points
- 🏛️ **NGO Escalation** — each issue type matched to a real Delhi NGO
- 🏆 **Leaderboard** — top civic contributors
- 🎁 **Rewards** — redeem points for Metro top-ups, Paytm cashback, vouchers

## Stack
`Python` `Flask` `SQLite` `Leaflet.js` `Vanilla JS`

## Run Locally
```bash
pip install flask
python app.py
# → http://127.0.0.1:5000
```

## Project Structure
```
├── app.py          # Routes & logic
├── database.py     # SQLite helpers
├── classifier.py   # Keyword auto-tagger
├── static/
│   └── style.css
└── templates/
    ├── index.html        # Heatmap + report
    ├── issues.html       # Browse & filter
    ├── leaderboard.html  # Top contributors
    └── redeem.html       # Rewards
```

## Deploy on Render
1. Add `gunicorn` to `requirements.txt`
2. Set start command: `gunicorn app:app`
3. Note: SQLite resets on redeploy — use a Render Disk for persistence

---
MIT License
