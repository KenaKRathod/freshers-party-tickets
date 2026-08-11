# 🎉 Freshers' ZENITH — QR Ticket & Check-in System

A complete QR-based entry pass and check-in system for college freshers' events.
Each pass has a unique QR code that links to a check-in URL. Volunteers scan QR codes
with their phone camera and tap "Grant Entry" — no extra app needed.

## Features

- **250 unique QR passes** generated as a printable PDF
- **Instant check-in** — scan QR → tap "Grant Entry" → done
- **Duplicate detection** — blocks re-entry with timestamp
- **Live dashboard** — real-time stats (checked in / remaining)
- **Staff-only access** — session-based auth, public page for attendees
- **Mobile-first** — optimized for phone screens (that's what volunteers use)
- **Deploy-ready** — `render.yaml` for one-click Render deployment

## Quick Start

### 1. Setup

```bash
# Clone and install
git clone <your-repo-url>
cd freshers-party-tickets
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env: set STAFF_PASSWORD and BASE_URL
```

### 2. Generate Passes

```bash
# Place your pass template at:
#   static/template/pass_template.png

# Preview QR placement (generates 1 sample)
python generate.py --preview

# Adjust QR_POSITION and QR_SIZE in generate.py if needed

# Generate all 250 passes + PDF
python generate.py
```

### 3. Run Locally

```bash
python app.py
# → Open http://localhost:5000
```

### 4. Deploy to Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your repo
4. Set environment variables:
   - `STAFF_PASSWORD` — shared volunteer password
   - `BASE_URL` — your Render URL (e.g., `https://freshers-zenith.onrender.com`)
5. Deploy

> **Important:** Set `BASE_URL` *before* running `generate.py` — it's baked into every QR code.

## Event Day Workflow

1. **Before the event:** Print `output/all_passes.pdf` and distribute passes
2. **Volunteers:** Open the app URL on their phone → Login with staff password
3. **At the gate:** Point phone camera at each pass → tap the link → tap "Grant Entry"
4. **Monitor:** Check the Dashboard for live attendance stats

## Tech Stack

- **Backend:** Python Flask + SQLite
- **QR Generation:** `qrcode` + Pillow
- **PDF Assembly:** `img2pdf` (lossless)
- **Frontend:** Plain HTML/CSS (no framework needed)
- **Hosting:** Render free tier

## Project Structure

```
├── app.py              # Flask routes + auth
├── config.py           # Environment config
├── database.py         # SQLite helpers
├── generate.py         # Token → QR → Pass → PDF pipeline
├── requirements.txt
├── render.yaml         # Render deploy config
├── Procfile
├── templates/          # Jinja2 HTML templates
├── static/css/         # Styling
├── static/template/    # Your pass template image
├── static/qr_codes/    # Generated QR images
├── static/passes/      # Generated pass images
└── output/             # Printable PDF
```
