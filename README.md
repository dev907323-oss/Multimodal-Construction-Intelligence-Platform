# Multimodal Construction Intelligence Platform

**SkillWallet Capstone Project 1** — construction decision-support prototype built with Streamlit, Python, Gemini multimodal AI, Open-Meteo weather, and optional Pollinations concept image generation.

> **Safety notice:** This is an educational prototype. It is not a certified PPE inspection, structural assessment, engineering design, bill of quantities, or licensed property valuation. AI can be wrong. Consult qualified professionals and local authorities before real-world decisions.

## Included modules

1. **Overview & architecture** — system outline and responsible-use checklist.
2. **Site Safety & PPE Audit** — JPG/PNG upload; Gemini prompt for helmet, high-visibility vest, steel-toe boots, harness (when relevant), visible hazards, severity, corrective actions, structured JSON export, metric/status display. OSHA and IS 456 are contextual references, not certification claims.
3. **Crack Diagnostics & Structural Integrity** — image upload, defect category, cautious width estimate (nullable if no scale), possible causes, engineer-directed repair options/follow-up, urgency and JSON export.
4. **Planning & Real Estate Valuation** — structure, built-up area, city/location tier and completion inputs; budget, incurred capex, indicative INR market valuation; steel/cement assumption-based quantities; progress bar; AI schedule draft; JSON export. All rates/quantity factors are editable assumptions, not market quotations or structural BOQ.
5. **Daily Site Assistant & Weather Advisory** — condition-specific safety reminders, Open-Meteo current weather lookup, contextual multi-turn chatbot, downloadable chat transcript.
6. **Concept Rendering** — optional Pollinations image endpoint for conceptual building visualization. Image service availability is external; output is not a construction drawing.

The app has no required external database. Without a Gemini API key, image/text AI functions show an explicitly labeled demo response. Live AI needs an API key.

## Run on Windows (VS Code)

1. Download and extract this ZIP.
2. Install Python 3.9+ (Python 3.11 is a practical choice).
3. Open the extracted folder in VS Code.
4. Open Terminal and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Alternatively, double-click `run-streamlit.bat` (it installs requirements and starts Streamlit).

## Gemini API key

Enter the key in the password field in the app sidebar. The app uses it in the current app session and does not write it into source files. **Never commit API keys to GitHub.** If deploying to Streamlit Community Cloud, use App settings → Secrets, for example:

```toml
GEMINI_API_KEY = "your-key"
```

The UI key input is the supported session configuration in this version; use a private deployment and follow provider terms.

## Streamlit Community Cloud deployment

- Push this project to a GitHub repository.
- In Streamlit Community Cloud, create an app pointing to `app.py` at the repository root.
- `requirements.txt` is included at root for dependency installation.
- Add secrets only in the deployment's Secrets panel; do not commit secret files.
- Test image uploads, weather/network behavior, and API access in the hosted environment.

## Existing full-stack implementation

The ZIP also retains the original React + TypeScript frontend and FastAPI backend, including their Docker files and launch scripts. The Streamlit app is the course-guide-oriented capstone entry point.

## Validation

Python syntax can be checked with:

```powershell
python -m py_compile app.py
```

Live Gemini, weather, and external image service calls require network access and should be tested in the user's own environment. This packaged project has not been represented as externally certified or fully cloud-tested.
