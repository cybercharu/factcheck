# 🔍 FactCheck AI — Automated PDF Fact-Checking

A Streamlit web app that extracts factual claims from any PDF and verifies them against **live Google Search data** using **Gemini 1.5 Flash**.

## 🚀 Live Demo
> Deploy to Streamlit Cloud and paste your URL here.

---

## ✨ Features
- **Extract** Identifies stats, dates, financial figures, and technical claims from PDFs
- **Verify** Uses Gemini's Google Search grounding to cross-reference each claim in real time
- **Report** Labels every claim as Verified / Inaccurate / False with evidence
- **Download** Export the full report as JSON

---

## 🛠 Tech Stack
| Layer | Tool |
|-------|------|
| Frontend | Streamlit |
| AI Model | Gemini 1.5 Flash (Google) |
| Web Search | Google Search grounding (built into Gemini) |
| PDF Parsing | pdfplumber |
| Env Management | python-dotenv |

---

##  Local Installation

```bash
git clone https://github.com/cybercharu/factcheck.git
cd factcheck-ai

pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Edit .env and paste your GOOGLE_API_KEY

streamlit run app.py
```

---

## 🔑 API Key Setup

Get a **free** Google Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — no credit card required.

### Option A — `.env` file (local dev)
```
GOOGLE_API_KEY=AIza_your_key_here
```

### Option B — Streamlit Cloud Secrets (deployment)
In Streamlit Cloud dashboard → App Settings → Secrets:
```toml
GOOGLE_API_KEY = "AIza_your_key_here"
```

### Option C — Enter in UI
If no env/secret is set, the app shows a password input at runtime.

---

## ☁️ Deploy to Streamlit Cloud (Free)

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New App** → select repo → set `app.py` as entry point
4. Under **Advanced Settings → Secrets**, add your `GOOGLE_API_KEY`
5. Click **Deploy** 🎉

---

## 📁 Project Structure
```
factcheck-ai/
├── app.py            # Main Streamlit application
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
├── .gitignore        # Excludes .env from git
└── README.md
```


