import json
import os
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .prompts import MODULES, SYSTEM_OUTPUT


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_json(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\s*```$", "", candidate)
    try:
        data = json.loads(candidate)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                return None
        return None


def _demo_result(module: str, prompt: str, context: dict[str, str]) -> dict[str, Any]:
    user_text = prompt.strip() or "No additional description was supplied."
    label = MODULES[module]["label"]
    templates: dict[str, tuple[str, str, list[dict[str, str]], list[str], list[str]]] = {
        "safety": ("Site safety review (demo)", "This is a demonstration checklist based on the submitted description. No real computer-vision detection has been performed because Gemini is not configured or unavailable.", [
            {"label": "PPE and access checks", "severity": "Moderate", "detail": "Verify required PPE, safe access and egress, edge protection, signage, and exclusion zones directly on site."},
            {"label": "Housekeeping and hazards", "severity": "Moderate", "detail": "Check loose materials, trip hazards, exposed services, lifting operations, and safe storage before work continues."}], ["Pause the affected task if an immediate danger is present.", "Have the site safety lead complete and record a physical inspection.", "Photograph the hazard from a safe location and track corrective actions."], ["Demo template only; observations are not image findings.", "A competent site safety professional must verify conditions."]),
        "cracks": ("Crack review checklist (demo)", "This is an illustrative crack-inspection workflow, not an analysis of the uploaded image. Connect Gemini for image-aware observations and have a qualified structural engineer assess concerning cracks.", [
            {"label": "Document the crack", "severity": "Info", "detail": "Capture a close-up and a wider context photo with a scale, date, location, and building element."},
            {"label": "Check for change or movement", "severity": "Moderate", "detail": "Record whether the crack is widening, displaced, damp, associated with sagging, or accompanied by sticking doors/windows."}], ["Avoid patching or concealing a crack before documentation and assessment.", "Restrict access if there are signs of movement or falling material.", "Arrange a structural engineer assessment for active, wide, displaced, or multiple related cracks."], ["No crack measurements or diagnosis have been made.", "A photo alone cannot certify structural safety."]),
        "valuation": ("Property valuation framework (demo)", "A reliable value requires local comparable transactions and property-specific facts. This demo does not invent a market rate; it outlines the key inputs to collect.", [
            {"label": "Comparable sales", "severity": "Info", "detail": "Collect at least 3-5 recent comparable sales in the same locality, adjusting for date, condition, floor, frontage, and amenities."},
            {"label": "Property facts", "severity": "Info", "detail": "Verify measured area, age, condition, title, zoning, access, occupancy, and any encumbrances."}], ["Add recent verified sale rates for the same micro-market.", "Separate land value, built-up area, age/condition adjustments, and transaction costs.", "Obtain a report from a qualified local valuer before a financial or legal decision."], ["No certified property value is produced in demo mode.", "Market values and regulations vary by locality."]),
        "planning": ("Project execution outline (demo)", "This sample sequence is intended as a starting checklist. The schedule and dependencies must be validated against approved drawings, site conditions, labour, procurement, and local approvals.", [
            {"label": "Pre-construction", "severity": "Info", "detail": "Confirm scope, permits, design approvals, geotechnical/site information, budget, procurement plan, and baseline schedule."},
            {"label": "Execution and quality gates", "severity": "Moderate", "detail": "Sequence site setup, substructure, superstructure, services, finishes, inspections, testing, and handover with hold points."}], ["Assign a responsible owner and duration to every work package.", "Identify long-lead materials and approval dependencies early.", "Include daily safety briefings, inspection records, change control, and contingency."], ["This is not an approved construction method statement.", "Structural work must follow approved designs and qualified supervision."]),
        "daily_assistance": ("Daily site guidance (demo)", "This response uses a general checklist because no AI service is connected. Add the specific activity, materials, drawing reference, and site constraints for more relevant guidance.", [
            {"label": "Clarify the work area", "severity": "Info", "detail": "Identify the activity, exact location, current stage, approved drawing revision, and who is supervising."},
            {"label": "Safety and quality", "severity": "Moderate", "detail": "Review task risk assessment, PPE, access, tools, material specifications, inspection points, and required permits."}], ["Do not proceed where drawings, approvals, or safety controls are unclear.", "Record the issue and raise it with the site engineer or supervisor.", "Take before/after photos and log materials, quantities, and inspection outcomes."], ["General workflow only; verify against site requirements."]),
        "knowledge": ("Construction knowledge response (demo)", "This demo provides a general learning framework. Connect Gemini to generate a tailored explanation for the question you supplied.", [
            {"label": "Start with approved information", "severity": "Info", "detail": "Use current drawings, specifications, method statements, local code requirements, and manufacturer instructions as primary references."},
            {"label": "Record decisions", "severity": "Info", "detail": "Track assumptions, revisions, inspections, responsible people, and open questions in a controlled project log."}], ["Break the question into definition, inputs, process, quality checks, safety points, and references.", "Verify jurisdiction-specific requirements with a competent professional."], ["General information is not a substitute for project-specific engineering advice."]),
    }
    title, summary, findings, recommendations, assumptions = templates[module]
    if module == "valuation":
        def numeric(value: str) -> float | None:
            cleaned = re.sub(r"[^0-9.]", "", value or "")
            try:
                return float(cleaned) if cleaned else None
            except ValueError:
                return None
        area = numeric(context.get("area_sqft", ""))
        rate = numeric(context.get("market_rate_sqft", ""))
        if area and rate and area > 0 and rate > 0:
            base = area * rate
            low = round(base * 0.92)
            high = round(base * 1.08)
            currency = lambda amount: f"₹{amount:,.0f}"
            title = "Indicative property valuation (user-provided rate)"
            summary = (f"Using the area ({area:,.0f} sq ft) and local rate (₹{rate:,.0f}/sq ft) you supplied, the arithmetic base estimate is {currency(round(base))}. An illustrative ±8% sensitivity range is {currency(low)}–{currency(high)}. This is a calculation from your input, not an independently verified market valuation.")
            findings = [
                {"label": "Calculation basis", "severity": "Info", "detail": f"{area:,.0f} sq ft × ₹{rate:,.0f} per sq ft = {currency(round(base))}; rate supplied by the user."},
                {"label": "Illustrative sensitivity", "severity": "Info", "detail": f"A purely illustrative ±8% range gives {currency(low)} to {currency(high)} before transaction costs, condition adjustments, title issues, taxes, or other property-specific factors."},
            ]
            recommendations = ["Validate the rate against recent registered transactions or at least 3–5 comparable properties in the same micro-market.", "Confirm measured area, property condition and age, title, zoning, access, amenities, and encumbrances.", "Obtain a qualified local valuer's report before any binding financial or legal decision."]
            assumptions = ["The per-square-foot rate and area are user-provided and have not been independently verified.", "The ±8% sensitivity is an illustrative arithmetic band, not a statistical confidence interval or appraisal opinion.", "The calculation excludes taxes, transaction costs, legal/title issues, structural condition adjustments, and financing costs."]
    if context.get("location"):
        assumptions.append(f"Location supplied: {context['location']}; no local database has been consulted.")
    if prompt.strip():
        assumptions.append("User-provided context was captured but not interpreted by an AI model in demo mode.")
    return {
        "title": title,
        "summary": summary,
        "risk_level": "Informational" if module in {"valuation", "planning", "knowledge"} else "Moderate",
        "findings": findings,
        "recommendations": recommendations,
        "assumptions": assumptions,
        "disclaimer": "Demo output only. Verify all safety, structural, valuation, and engineering decisions with a qualified professional.",
    }


def _run_gemini(prompt_text: str, image_bytes: bytes | None, mime_type: str | None) -> dict[str, Any]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    contents: list[Any] = [prompt_text]
    if image_bytes and mime_type:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )
    parsed = _parse_json(response.text or "")
    if not parsed:
        raise ValueError("AI provider returned a response that was not valid JSON")
    return parsed


def analyze(module: str, prompt: str, context: dict[str, str], image_bytes: bytes | None = None, mime_type: str | None = None) -> dict[str, Any]:
    module_info = MODULES[module]
    context_lines = [f"Module: {module_info['label']}", f"User request/site notes: {prompt.strip() or 'No additional question supplied.'}"]
    for key in ("project_name", "location", "property_type", "area_sqft", "market_rate_sqft", "budget", "timeline"):
        if context.get(key):
            context_lines.append(f"{key.replace('_', ' ').title()}: {context[key]}")
    context_lines.append("An image is attached for visual review." if image_bytes else "No image is attached.")
    full_prompt = f"{module_info['prompt']}\n\nUser/project context:\n" + "\n".join(context_lines) + "\n\n" + SYSTEM_OUTPUT
    provider = "demo"
    error_note = None
    generated: dict[str, Any]
    if os.getenv("GEMINI_API_KEY", "").strip():
        try:
            generated = _run_gemini(full_prompt, image_bytes, mime_type)
            provider = "gemini"
        except Exception as exc:
            # Keep the UI usable, but explicitly signal that this response was not model-generated.
            error_note = str(exc)[:240]
            generated = _demo_result(module, prompt, context)
    else:
        generated = _demo_result(module, prompt, context)

    findings = generated.get("findings")
    if not isinstance(findings, list):
        findings = []
    recommendations = generated.get("recommendations")
    if not isinstance(recommendations, list):
        recommendations = []
    assumptions = generated.get("assumptions")
    if not isinstance(assumptions, list):
        assumptions = []
    result = {
        "id": str(uuid4()),
        "module": module,
        "module_label": module_info["label"],
        "title": str(generated.get("title") or module_info["label"])[:160],
        "summary": str(generated.get("summary") or "No summary was returned."),
        "risk_level": _normalise_risk(generated.get("risk_level")),
        "findings": [_normalise_finding(item) for item in findings[:12] if isinstance(item, dict)],
        "recommendations": [str(item)[:500] for item in recommendations[:12]],
        "assumptions": [str(item)[:500] for item in assumptions[:10]],
        "disclaimer": str(generated.get("disclaimer") or "Verify consequential decisions with a qualified professional."),
        "provider": provider,
        "provider_error": error_note,
        "created_at": _now(),
        "project_name": context.get("project_name") or "Untitled site project",
        "location": context.get("location") or "",
        "image_name": context.get("image_name") or "",
    }
    return result


def _normalise_risk(value: Any) -> str:
    options = {"low": "Low", "moderate": "Moderate", "medium": "Moderate", "high": "High", "critical": "Critical", "informational": "Informational", "info": "Informational"}
    return options.get(str(value or "informational").strip().lower(), "Informational")


def _normalise_finding(item: dict[str, Any]) -> dict[str, str]:
    allowed = {"info": "Info", "low": "Low", "moderate": "Moderate", "medium": "Moderate", "high": "High", "critical": "Critical"}
    raw_severity = str(item.get("severity", "Info")).strip().lower()
    return {
        "label": str(item.get("label") or "Observation")[:160],
        "severity": allowed.get(raw_severity, "Info"),
        "detail": str(item.get("detail") or "No further detail supplied.")[:1500],
    }
