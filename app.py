"""Multimodal Construction Intelligence Platform — Skill Wallet Capstone Project 1.
Educational decision-support prototype; not a substitute for licensed professionals.
"""
from __future__ import annotations
import json, os, re, urllib.parse
from datetime import datetime
from typing import Any
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Multimodal Construction Intelligence", page_icon="🏗️", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.4rem;padding-bottom:2rem}.hero{padding:1rem 1.2rem;border-radius:14px;background:linear-gradient(120deg,#12345b,#176b87);color:white}
.small-note{font-size:.82rem;color:#6b7280}.stMetric{border:1px solid #e5e7eb;padding:.7rem;border-radius:12px;background:#fbfdff}
</style>""", unsafe_allow_html=True)

MODEL_DEFAULT = "gemini-2.5-flash"
SAFETY_PROMPT = """You are a cautious construction-site visual screening assistant. Review the supplied photo for visible PPE: helmets, high-visibility vests, steel-toe safety boots, and harnesses where relevant. Use OSHA and IS 456 only as contextual references; do not claim formal compliance certification. Consider visible hazards, but do not infer hidden facts. Return ONLY valid JSON with keys: safety_score (integer 0-100 or null), overall_status (Compliant/Needs Attention/High Risk/Not Assessable), ppe_detection (object with helmet, high_visibility_vest, safety_footwear, harness_if_required; each Compliant/Not visible/Non-compliant/Not applicable), hazards (array of objects with hazard, severity [Low/Medium/High/Critical], remedy), corrective_remedies (array), limitations (string). Do not claim formal OSHA or IS 456 certification; say this is a preliminary visual screen."""
CRACK_PROMPT = """Analyze the uploaded concrete/wall photo for visible defect cues only. Return ONLY valid JSON with defect_type (Hairline/Settlement/Structural Shear/Thermal Expansion/Spalling/Other or Unclear), estimated_width_mm (number or null; do not invent if scale absent), severity (Low/Medium/High/Unclear), likely_causes (array), recommended_follow_up (array), recommended_repairs (array; possible engineer-directed options such as epoxy injection or structural re-grouting), urgency (Routine/Prompt/Urgent/Unclear), limitations (string). Never declare structural safety based on a photo; recommend a qualified structural engineer for concerning signs."""

@st.cache_resource
def get_gemini(api_key: str):
    if not api_key: return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception: return None

def parse_json(text: str) -> Any:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(), flags=re.I)
    try: return json.loads(cleaned)
    except Exception: return {"raw_response": text}

def image_analysis(client, model: str, prompt: str, image: Image.Image, context: str=""):
    if not client:
        return {"mode":"DEMO — no image model executed", "note":"Configure Gemini API key in sidebar for live multimodal analysis.", "limitations":"Demo mode does not assess the uploaded image."}, "Demo mode"
    try:
        from google.genai import types
        prompt = prompt + (" Site context: " + context if context.strip() else "") + " Return only valid JSON."
        response=client.models.generate_content(model=model,contents=[prompt,image],config=types.GenerateContentConfig(response_mime_type="application/json"))
        return parse_json(response.text or "{}"), "Gemini AI"
    except Exception as exc:
        return {"error":str(exc),"note":"AI request failed. No result should be treated as an assessment."}, "Gemini error"

def text_ai(client, model: str, prompt: str):
    if not client: return "Demo mode is active. Add a Gemini API key in the sidebar to generate an AI response."
    try:
        r=client.models.generate_content(model=model,contents=prompt)
        return r.text or "The model returned an empty response."
    except Exception as e: return f"AI request error: {e}"

def inr_compact(value: float) -> str:
    if abs(value) >= 1e7: return f"₹{value/1e7:,.2f} Cr"
    if abs(value) >= 1e5: return f"₹{value/1e5:,.2f} L"
    return f"₹{value:,.0f}"

def download_json(data: Any, filename: str):
    st.download_button("Download JSON report",json.dumps(data,indent=2,ensure_ascii=False,default=str),filename,"application/json")

def report_meta(result, provider):
    result["provider"]=provider
    result["created_at"]=datetime.now().isoformat(timespec="seconds")
    return result

st.markdown('<div class="hero"><h1>🏗️ Multimodal Construction Intelligence Platform</h1><p>AI-assisted construction planning, visual screening, site advisory and documentation</p></div>',unsafe_allow_html=True)
st.caption("Skill Wallet Capstone Project 1 · Streamlit + Python · Multimodal AI · Structured reports")
with st.sidebar:
    st.header("Configuration")
    api_key=st.text_input("Google Gemini API key",type="password",help="Optional. Kept in this app session; never commit it to GitHub.")
    model=st.text_input("Gemini model",value=MODEL_DEFAULT)
    client=get_gemini(api_key.strip())
    st.success("Gemini client ready") if client else st.info("Demo mode — configure key for live AI")
    st.divider(); st.subheader("Navigation")
    st.markdown("- Overview & architecture\n- PPE Safety Vision\n- Crack Diagnostics\n- Planning & valuation\n- Daily assistant & weather\n- Concept rendering")
    st.caption("AI outputs are advisory. Obtain competent safety, structural, valuation and engineering review.")

# Course rubric modules, presented as a clear dashboard and functional workflows.
tabs=st.tabs(["Overview", "PPE Safety Vision", "Crack Diagnostics", "Planning & Valuation", "Site Chat & Weather", "Concept Rendering"])
with tabs[0]:
    st.subheader("Project overview")
    st.write("A multimodal decision-support prototype for construction teams. Upload a site or surface image, provide project assumptions, explore weather-aware guidance, and export structured outputs.")
    a,b,c=st.columns(3)
    a.metric("Core modules", "6")
    b.metric("Report format", "JSON")
    c.metric("AI provider", "Gemini (optional)")
    st.markdown("#### Architecture")
    st.code("Streamlit UI → Python analysis helpers → Gemini multimodal/text API (optional)\n                 ↘ Open-Meteo geocoding + forecast\n                 ↘ Pollinations image generation endpoint (optional)\n                 ↘ JSON report downloads",language="text")
    st.info("When no API key/network is available, the app labels demo outputs instead of pretending that a real model assessment ran.")
    st.markdown("#### Responsible-use checklist")
    for item in ["Visual AI is not a formal PPE inspection or structural certification.","Valuation and quantities depend on user-entered assumptions; no live market quote is implied.","Check local codes and consult qualified professionals for safety-critical decisions.","Do not upload confidential site imagery unless you are authorized to share it."]:
        st.markdown(f"- {item}")

with tabs[1]:
    st.subheader("Tab 1 · Site Safety & PPE Audit")
    st.write("Upload a JPG/PNG site photo. The multimodal prompt screens visible helmets, high-visibility vests, footwear, harnesses and potential hazards.")
    f=st.file_uploader("Construction site photo",type=["jpg","jpeg","png"],key="safety_file")
    context=st.text_area("Work context (optional)",placeholder="e.g. workers near slab edge; lifting operation",key="safety_context")
    if f:
        img=Image.open(f).convert("RGB"); st.image(img,caption="Uploaded image",use_container_width=True)
        if st.button("Run PPE & hazard screening",key="safety_button"):
            with st.spinner("Analyzing visible scene cues…"):
                result,provider=image_analysis(client,model,SAFETY_PROMPT,img,context)
            st.session_state.safety_result=report_meta(result,provider)
    result=st.session_state.get("safety_result")
    if result:
        score=result.get("safety_score")
        if isinstance(score,(int,float)):
            st.metric("Visual safety score (AI estimate)",f"{score}/100")
            st.progress(max(0,min(100,int(score)))/100)
        status=result.get("overall_status","Not assessed")
        if status in ["Compliant", "Low Risk"]: st.success(f"Overall status: {status}")
        elif status in ["High Risk", "Needs Attention"]: st.warning(f"Overall status: {status}")
        else: st.info(f"Overall status: {status}")
        ppe=result.get("ppe_detection",{})
        if isinstance(ppe,dict) and ppe:
            cols=st.columns(4)
            for col,(label,value) in zip(cols,ppe.items()): col.metric(label.replace("_"," ").title(),str(value))
        hazards=result.get("hazards",[])
        if hazards:
            st.markdown("#### Visible hazard cues & corrective actions")
            for h in hazards:
                if isinstance(h,dict): st.warning(f"**{h.get('hazard','Hazard')}** · Severity: {h.get('severity','Unclear')}\n\nRemedy: {h.get('remedy','Refer to competent site supervisor.')}")
                else: st.write(h)
        if result.get("corrective_remedies"): st.markdown("**Remedies:** " + "; ".join(map(str,result["corrective_remedies"])) )
        st.caption("Screening result only; PPE may be obscured and the model can miss hazards.")
        with st.expander("View complete structured result"): st.json(result)
        download_json(result,"site_safety_audit.json")

with tabs[2]:
    st.subheader("Tab 2 · Crack Diagnostics & Structural Integrity")
    f=st.file_uploader("Concrete / wall surface photo",type=["jpg","jpeg","png"],key="crack_file")
    context=st.text_area("Observation context",placeholder="e.g. crack location, first noticed date, recent rainfall",key="crack_context")
    if f:
        img=Image.open(f).convert("RGB"); st.image(img,caption="Uploaded surface",use_container_width=True)
        if st.button("Analyze visible defect",key="crack_button"):
            with st.spinner("Reviewing visible defect cues…"):
                result,provider=image_analysis(client,model,CRACK_PROMPT,img,context)
            st.session_state.crack_result=report_meta(result,provider)
    result=st.session_state.get("crack_result")
    if result:
        x,y,z=st.columns(3); x.metric("Defect type",str(result.get("defect_type","Unclear"))); y.metric("Estimated width",f"{result.get('estimated_width_mm','N/A')} mm" if result.get("estimated_width_mm") is not None else "Not estimated"); z.metric("Urgency",str(result.get("urgency","Unclear")))
        st.markdown(f"**Severity:** {result.get('severity','Unclear')}")
        st.markdown("#### Possible causes")
        causes=result.get("likely_causes",[]); st.write("\n".join(f"- {x}" for x in causes) if causes else "Not supplied")
        repairs=result.get("recommended_repairs",[])
        if repairs:
            st.markdown("#### Possible repair approaches (engineer-directed)")
            st.write("\n".join(f"- {item}" for item in repairs))
        st.markdown("#### Recommended follow-up")
        follow=result.get("recommended_follow_up",[]); st.write("\n".join(f"- {x}" for x in follow) if follow else "Have a qualified engineer inspect in person.")
        st.error("A photo cannot establish structural integrity. Arrange a qualified structural engineer's assessment for significant, widening, diagonal, leaking or displaced cracks.")
        with st.expander("View complete structured result"): st.json(result)
        download_json(result,"crack_diagnostics.json")

with tabs[3]:
    st.subheader("Tab 3 · Project Planning & Real Estate Valuation")
    left,right=st.columns(2)
    with left:
        structure=st.selectbox("Structure type",["Residential house","Apartment","Commercial building","Warehouse","Other"])
        area=st.number_input("Built-up area (sq ft)",min_value=1,value=1200,step=100)
        city=st.text_input("City / locality",value="Indore")
        tier=st.selectbox("Location tier",["Tier 1","Tier 2","Tier 3"])
        completion=st.slider("Project completion (%)",0,100,25)
    with right:
        rate=st.number_input("Assumed construction rate (₹/sq ft)",min_value=100,value=1800,step=100)
        market=st.number_input("Assumed market rate (₹/sq ft)",min_value=100,value=3500,step=100)
        months=st.number_input("Timeline (months)",min_value=1,value=12)
        steel_rate=st.number_input("Steel assumption (kg per sq ft)",min_value=0.0,value=4.0,step=.25)
        cement_rate=st.number_input("Cement assumption (50kg bags per sq ft)",min_value=0.0,value=.40,step=.05)
    budget=area*rate; incurred=budget*completion/100; valuation=area*market
    steel_kg=area*steel_rate; cement_bags=area*cement_rate
    m1,m2,m3=st.columns(3); m1.metric("Indicative total budget",inr_compact(budget),help=f"₹{budget:,.0f}"); m2.metric("Capex incurred",inr_compact(incurred),help=f"₹{incurred:,.0f}"); m3.metric("Indicative asset valuation",inr_compact(valuation),help=f"₹{valuation:,.0f}")
    m4,m5=st.columns(2); m4.metric("Steel estimate",f"{steel_kg:,.0f} kg"); m5.metric("Cement estimate",f"{cement_bags:,.0f} bags (50 kg)")
    st.progress(completion/100,text=f"Milestone progress: {completion}%")
    st.caption("Steel/cement factors are editable planning assumptions, not a structural design or bill of quantities. Confirm with a licensed engineer.")
    if st.button("Generate AI project schedule",key="schedule_button"):
        prompt=f"Prepare a practical high-level construction schedule in phases with tasks, dependencies, milestones, risks, and monthly progress checks. Structure {structure}; city/locality {city}; area {area} sq ft; budget INR {budget}; timeline {months} months; progress {completion}%. Clearly state assumptions; do not provide structural design."
        st.session_state.schedule=text_ai(client,model,prompt)
    if st.session_state.get("schedule"): st.markdown(st.session_state.schedule)
    planning={"structure_type":structure,"area_sqft":area,"city":city,"location_tier":tier,"completion_percent":completion,"construction_rate_inr_sqft":rate,"estimated_budget_inr":budget,"estimated_capex_incurred_inr":incurred,"market_rate_inr_sqft":market,"indicative_market_valuation_inr":valuation,"timeline_months":months,"steel_assumption_kg_sqft":steel_rate,"steel_estimate_kg":steel_kg,"cement_assumption_bags_sqft":cement_rate,"cement_estimate_50kg_bags":cement_bags,"disclaimer":"Indicative estimates only; not a certified valuation, design, or BOQ."}
    download_json(planning,"planning_valuation_and_materials.json")

with tabs[4]:
    st.subheader("Tab 4 · Daily Site Assistant & Weather Advisory")
    condition=st.selectbox("Weather condition",["Normal","High Wind","Heavy Rain","Extreme Heat"])
    advice={"Normal":"Continue toolbox talks, housekeeping, PPE checks and routine supervision.","High Wind":"Suspend crane/lifting and work at height if site/equipment limits are exceeded; secure loose materials.","Heavy Rain":"Check flooding, excavation stability, slippery routes and electrical exposure; stop unsafe work and inspect before restart.","Extreme Heat":"Provide water, shade, rest breaks and heat-stress monitoring; consider adjusted work hours."}
    st.warning(advice[condition])
    location=st.text_input("Weather location",value="Indore",key="weather_location")
    if st.button("Fetch current weather from Open-Meteo",key="weather_button"):
        try:
            import requests
            geo=requests.get("https://geocoding-api.open-meteo.com/v1/search",params={"name":location,"count":1,"language":"en","format":"json"},timeout=12).json()
            if not geo.get("results"): st.error("Location not found. Check spelling.")
            else:
                place=geo["results"][0]
                w=requests.get("https://api.open-meteo.com/v1/forecast",params={"latitude":place["latitude"],"longitude":place["longitude"],"current":"temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code","timezone":"auto"},timeout=12).json().get("current",{})
                st.json({"location":place.get("name"),"current_weather":w,"site_advisory":advice[condition],"note":"Weather data does not replace onsite observation."})
        except Exception as e: st.error(f"Weather service unavailable: {e}")
    st.divider(); st.subheader("Construction knowledge assistant · multi-turn chat")
    if "chat_history" not in st.session_state: st.session_state.chat_history=[]
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    question=st.chat_input("Ask about planning, documentation, or site practices")
    if question:
        st.session_state.chat_history.append({"role":"user","content":question})
        # Include recent dialogue to support contextual follow-up turns.
        recent=st.session_state.chat_history[-8:]
        transcript="\n".join(f"{m['role']}: {m['content']}" for m in recent)
        answer=text_ai(client,model,"You are a cautious construction engineering knowledge assistant. Use conversational context, state assumptions, avoid inventing local code rules, and direct high-risk safety/structural decisions to qualified professionals. Conversation:\n"+transcript)
        st.session_state.chat_history.append({"role":"assistant","content":answer})
        st.rerun()
    if st.session_state.chat_history:
        download_json(st.session_state.chat_history,"construction_chat_transcript.json")

with tabs[5]:
    st.subheader("Tab 5 · Conceptual 3D Architectural Rendering")
    st.write("Create an illustrative concept image from a text prompt using the Pollinations image endpoint. This is a visualization only—not a construction drawing or engineered design.")
    render_prompt=st.text_area("Describe the building concept",value="A contemporary two-storey Indian residential house, front elevation, clean architectural concept, landscaped entry, daylight, realistic materials")
    style=st.selectbox("Rendering style",["Photorealistic architectural concept","Minimal modern elevation","Sustainable green building concept","Isometric massing concept"])
    if st.button("Generate concept rendering",key="render_button"):
        prompt=urllib.parse.quote((render_prompt+", "+style+", architectural visualization, no text overlay").strip())
        # The endpoint is fetched by the user's browser via a normal URL; service availability varies.
        url=f"https://image.pollinations.ai/prompt/{prompt}?width=1024&height=768&nologo=true"
        st.session_state.render_url=url
        st.session_state.render_prompt=render_prompt
    if st.session_state.get("render_url"):
        st.image(st.session_state.render_url,caption="AI-generated conceptual visualization (service response may vary)",use_container_width=True)
        st.link_button("Open generated image in new tab",st.session_state.render_url)
        download_json({"prompt":st.session_state.get("render_prompt"),"style":style,"image_endpoint":st.session_state.render_url,"disclaimer":"Concept only; verify dimensions, code, structure, and constructability with qualified professionals."},"concept_rendering_metadata.json")
    st.caption("If the external image service is unavailable, retry later. No API key is required by this app for the endpoint; service terms/availability are external.")

st.divider()
st.caption("Educational capstone prototype. AI may miss hazards, misclassify cracks, or produce inaccurate estimates. Consult qualified safety officers, structural engineers, licensed valuers and local authorities before real-world decisions.")
