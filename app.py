import streamlit as st
import pdfplumber
import google.generativeai as genai
from googlesearch import search as google_search
import requests
from bs4 import BeautifulSoup
import json
import re
import io
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

#Page config 
st.set_page_config(
    page_title="FactCheck AI Truth Layer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.hero-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px; padding: 40px; margin-bottom: 32px;
    border: 1px solid #2a2a4a; text-align: center;
}
.hero-header h1 { font-size: 2.6rem; font-weight: 700; color: #e2e8f0; margin: 0; }
.hero-header p  { color: #94a3b8; font-size: 1.1rem; margin-top: 10px; }
.hero-accent    { color: #60a5fa; }
.stat-card {
    background: #1e293b; border-radius: 12px; padding: 20px;
    text-align: center; border: 1px solid #334155;
}
.stat-number { font-size: 2rem; font-weight: 700; }
.stat-label  { color: #94a3b8; font-size: 0.85rem; margin-top: 4px; }
.claim-card {
    background: #1e293b; border-radius: 12px; padding: 20px;
    margin-bottom: 16px; border: 1px solid #334155;
}
.claim-card.verified   { border-left: 4px solid #10b981; }
.claim-card.inaccurate { border-left: 4px solid #f59e0b; }
.claim-card.false      { border-left: 4px solid #ef4444; }
.badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
}
.badge-verified   { background: #064e3b; color: #34d399; }
.badge-inaccurate { background: #451a03; color: #fbbf24; }
.badge-false      { background: #450a0a; color: #f87171; }
.claim-text  { color: #e2e8f0; font-size: 1rem; font-weight: 500; margin: 12px 0 8px; }
.verdict-box { color: #94a3b8; font-size: 0.9rem; line-height: 1.6; }
.real-fact   { color: #60a5fa; font-size: 0.9rem; margin-top: 8px; }
.progress-step {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 16px; border-radius: 8px;
    background: #111827; margin-bottom: 8px;
    font-size: 0.9rem; color: #94a3b8;
}
.step-done  { color: #34d399; }
.step-doing { color: #60a5fa; }
.footer {
    text-align: center; color: #475569; font-size: 0.8rem;
    margin-top: 48px; padding-top: 24px; border-top: 1px solid #1e293b;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-header">
  <h1>🔍 <span class="hero-accent">FactCheck</span> AI</h1>
  <p>Upload any PDF — Gemini extracts every claim and cross-references it against live Google Search data.</p>
</div>
""", unsafe_allow_html=True)


# API key resolution (env → secrets → user input) 
def get_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("GOOGLE_API_KEY", "")
        except Exception:
            pass
    if not key:
        key = st.session_state.get("api_key", "")
    return key

# Extract PDF text
def extract_pdf_text(uploaded_file) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text.strip()


# Call Gemini (plain)
def call_gemini(prompt: str, system: str = "") -> str:
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system if system else None,
    )
    resp = model.generate_content(prompt)
    return resp.text.strip()


# Free web search: scrape top Google results 
def fetch_web_snippets(query: str, num: int = 3) -> str:
    """Scrape text snippets from top search results — no API key needed."""
    snippets = []
    try:
        urls = list(google_search(query, num_results=num, sleep_interval=1))
        for url in urls:
            try:
                r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(r.text, "html.parser")
                text = " ".join(soup.get_text(" ", strip=True).split())[:500]
                snippets.append(f"Source: {url}\n{text}")
            except Exception:
                continue
    except Exception:
        pass
    return "\n\n".join(snippets) if snippets else "No web results found."


# Step 1: Extract verifiable claims 
def extract_claims(pdf_text: str) -> list[dict]:
    system = """You are a fact-extraction engine. Given document text, extract every specific, verifiable claim.
Focus on: statistics, percentages, monetary figures, dates, counts, rankings, technical specs, named studies.
Return ONLY a valid JSON array — no markdown fences, no explanation, just raw JSON.
Each element: {"id": 1, "claim": "exact claim sentence", "category": "statistic|date|financial|technical|other"}
Extract 5-15 of the most important verifiable claims."""

    raw = call_gemini(
        f"Extract all verifiable claims from this document:\n\n{pdf_text[:6000]}",
        system=system,
    )
    raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    return json.loads(raw)


# ── Step 2: Verify each claim using real web search + Gemini ─────────────────
def verify_claim(claim_obj: dict) -> dict:
    # 1. Fetch live web snippets for this claim (free, no API needed)
    web_context = fetch_web_snippets(claim_obj["claim"])

    # 2. Send claim + web evidence to Gemini for verdict
    system = """You are a rigorous fact-checker. You will be given:
- A claim extracted from a document
- Real web search results fetched live for that claim

Your job: compare the claim against the web evidence and return ONLY valid JSON.
No markdown, no explanation outside JSON. Exact shape:
{
  "verdict": "Verified" | "Inaccurate" | "False",
  "confidence": "High" | "Medium" | "Low",
  "explanation": "1-2 sentence explanation referencing the web evidence",
  "real_fact": "Correct/current figure if different from claim, else null",
  "source_hint": "Domain or URL from the evidence, else null"
}
Verdict meanings:
- Verified   : claim matches web evidence
- Inaccurate : claim is outdated or the number is slightly off
- False      : claim contradicts web evidence or no support found"""

    prompt = f"""Claim: "{claim_obj['claim']}"

Live web search results:
{web_context}

Now return the JSON verdict."""

    raw = call_gemini(prompt, system=system)
    raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()

    try:
        result = json.loads(raw)
    except Exception:
        result = {
            "verdict": "False",
            "confidence": "Low",
            "explanation": "Could not parse verdict from model response.",
            "real_fact": None,
            "source_hint": None,
        }

    return {**claim_obj, **result}


# Sidebar / inputs 
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    env_key     = os.getenv("GOOGLE_API_KEY", "")
    secrets_key = ""
    try:
        secrets_key = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        pass

    if not env_key and not secrets_key:
        st.markdown("### Google Gemini API Key")
        typed_key = st.text_input(
            "Paste your key here",
            type="password",
            placeholder="AIza...",
            help="Get a free key at aistudio.google.com/apikey",
        )
        if typed_key:
            st.session_state.api_key = typed_key
    else:
        st.session_state.api_key = env_key or secrets_key

    st.markdown("###  Upload PDF")
    uploaded = st.file_uploader("Drop your PDF here", type=["pdf"])
    if uploaded:
        st.success(f"**{uploaded.name}** ({uploaded.size // 1024} KB)")

    has_key = bool(get_api_key())
    run_btn = st.button(
        " Run Fact-Check",
        type="primary",
        use_container_width=True,
        disabled=(not uploaded or not has_key),
    )

with col_right:
    st.markdown("### How It Works")
    st.markdown("""
| Step | What happens |
|------|-------------|
| **Extract** | Gemini reads PDF & pulls out verifiable claims |
| **Verify** | Each claim is cross-checked via live Google Search |
| **Report** | Claims labelled Verified /  Inaccurate /  False |
    """)
    st.info(" Works best on documents with stats, financial figures, and research data.")

st.divider()

# Main pipeline
if run_btn and uploaded and has_key:
    uploaded.seek(0)
    progress_placeholder = st.empty()

    def show_progress(step: int, total: int = 0):
        labels = [
            ( "Extracting text from PDF"),
            ("Identifying verifiable claims with Gemini"),
            ( f"Verifying {total} claims via Google Search"),
            ( "Generating report"),
        ]
        html = ""
        for i, (icon, label) in enumerate(labels):
            if i < step:
                cls, ico = "step-done"
            elif i == step:
                cls, ico = "step-doing", icon
            else:
                cls, ico = "", icon
            html += f'<div class="progress-step {cls}">{ico} {label}</div>'
        progress_placeholder.markdown(f'<div style="margin-bottom:24px">{html}</div>', unsafe_allow_html=True)

    try:
        show_progress(0)
        time.sleep(0.3)
        pdf_text = extract_pdf_text(uploaded)

        if not pdf_text:
            st.error(" No text found. Ensure the PDF isn't scanned/image-only.")
            st.stop()

        show_progress(1)
        claims = extract_claims(pdf_text)

        show_progress(2, len(claims))
        results = []
        bar = st.progress(0, text="Verifying claims…")
        for i, claim in enumerate(claims):
            bar.progress((i + 1) / len(claims), text=f"Verifying claim {i+1}/{len(claims)}…")
            results.append(verify_claim(claim))
            time.sleep(0.3)

        bar.empty()
        show_progress(3, len(claims))
        time.sleep(0.3)
        progress_placeholder.empty()

        # Summary stats 
        verified_n   = sum(1 for r in results if r["verdict"] == "Verified")
        inaccurate_n = sum(1 for r in results if r["verdict"] == "Inaccurate")
        false_n      = sum(1 for r in results if r["verdict"] == "False")
        total_n      = len(results)

        st.markdown(f"##  Results — {total_n} Claims Analysed")
        c1, c2, c3, c4 = st.columns(4)
       # REPLACE with these 4 lines:
c1.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#60a5fa">{total_n}</div><div class="stat-label">Total Claims</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#10b981">{verified_n}</div><div class="stat-label">✅ Verified</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#f59e0b">{inaccurate_n}</div><div class="stat-label">⚠️ Inaccurate</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#ef4444">{false_n}</div><div class="stat-label">❌ False</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Filter
        filter_opt  = st.selectbox("Filter by verdict", ["All", " Verified", " Inaccurate", " False"])
        verdict_map = {"All": None, " Verified": "Verified", "Inaccurate": "Inaccurate", "False": "False"}
        filtered    = [r for r in results if verdict_map[filter_opt] is None or r["verdict"] == verdict_map[filter_opt]]

        # Claim cards 
        for r in filtered:
            v          = r["verdict"]
            card_cls   = {"Verified": "verified", "Inaccurate": "inaccurate", "False": "false"}.get(v, "")
            badge_cls  = {"Verified": "badge-verified", "Inaccurate": "badge-inaccurate", "False": "badge-false"}.get(v, "")
            badge_icon = {"Verified": "Verified", "Inaccurate": " Inaccurate", "False": "False"}.get(v, v)
            conf_color = {"High": "#34d399", "Medium": "#fbbf24", "Low": "#f87171"}.get(r.get("confidence", ""), "#94a3b8")
            real_html  = f'<div class="real-fact"> <b>Correct fact:</b> {r["real_fact"]}</div>' if r.get("real_fact") else ""
            src_html   = f'<div style="color:#475569;font-size:0.8rem;margin-top:6px"> {r["source_hint"]}</div>' if r.get("source_hint") else ""

            st.markdown(f"""
<div class="claim-card {card_cls}">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
    <span class="badge {badge_cls}">{badge_icon}</span>
    <span style="color:{conf_color};font-size:0.8rem;font-weight:600">Confidence: {r.get('confidence','—')}</span>
  </div>
  <div class="claim-text">"{r['claim']}"</div>
  <div class="verdict-box">{r.get('explanation','')}</div>
  {real_html}{src_html}
</div>""", unsafe_allow_html=True)

        # Download
        st.divider()
        st.download_button(
            "Download Full Report (JSON)",
            data=json.dumps(results, indent=2),
            file_name=f"factcheck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    except json.JSONDecodeError as e:
        st.error(f"JSON parse error: {e}")
    except Exception as e:
        msg = str(e).lower()
        if "api key" in msg or "api_key" in msg:
            st.error(" Invalid API key. Check your Google Gemini key.")
        elif "quota" in msg or "rate" in msg:
            st.error(" Rate limit hit. Wait a moment and try again.")
        else:
            st.error(f"Error: {e}")

st.markdown("""
<div class="footer">
  Built for CogCulture 2026
</div>
""", unsafe_allow_html=True)