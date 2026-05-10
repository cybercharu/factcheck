# 🔍 FactCheck AI — Automated PDF Fact-Checking

A Streamlit web app that extracts factual claims from any PDF and verifies them against **live Google Search data** using **Gemini 1.5 Flash**.

## 🚀 Live Demo
> https://factcheck-efszvgwmcda5zjtwyzvx2n.streamlit.app/

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
## 📁 Project Structure
```
factcheck-ai/
├── app.py            # Main Streamlit application
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
├── .gitignore        # Excludes .env from git
└── README.md
```


