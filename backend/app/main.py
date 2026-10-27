import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .ai_service import analyze
from .database import counts, get_analysis, init_db, list_analyses, save_analysis
from .prompts import MODULES
from .weather import get_weather

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Multimodal Construction Intelligence API",
    description="API for site safety, crack review, planning, valuation frameworks, construction assistance, and weather advisory.",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [item.strip() for item in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


@app.get("/")
def root():
    return {"name": "Multimodal Construction Intelligence Platform", "docs": "/docs", "api": "/api"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Multimodal Construction Intelligence API",
        "ai_enabled": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "ai_provider": "Gemini" if os.getenv("GEMINI_API_KEY", "").strip() else "Demo mode",
        "model": os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
        "modules": [{"id": key, "label": value["label"], "description": value["description"]} for key, value in MODULES.items()],
    }


@app.get("/api/dashboard")
def dashboard():
    return {**counts(), "recent_analyses": list_analyses(6), "modules": len(MODULES)}


@app.get("/api/analyses")
def analyses(limit: int = Query(default=20, ge=1, le=100)):
    return {"items": list_analyses(limit), "count": len(list_analyses(limit))}


@app.get("/api/analyses/{analysis_id}")
def analysis_detail(analysis_id: str):
    result = get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@app.post("/api/analyze")
async def create_analysis(
    module: Annotated[str, Form()],
    prompt: Annotated[str, Form()] = "",
    project_name: Annotated[str, Form()] = "",
    location: Annotated[str, Form()] = "",
    property_type: Annotated[str, Form()] = "",
    area_sqft: Annotated[str, Form()] = "",
    market_rate_sqft: Annotated[str, Form()] = "",
    budget: Annotated[str, Form()] = "",
    timeline: Annotated[str, Form()] = "",
    file: UploadFile | None = File(default=None),
):
    if module not in MODULES:
        raise HTTPException(status_code=422, detail=f"Unknown module. Choose one of: {', '.join(MODULES)}")
    if len(prompt) > 8000:
        raise HTTPException(status_code=413, detail="Prompt is too long (maximum 8,000 characters).")
    image_bytes = None
    mime_type = None
    image_name = ""
    if file is not None and file.filename:
        mime_type = (file.content_type or "").lower()
        if mime_type not in ALLOWED_IMAGES:
            raise HTTPException(status_code=415, detail="Upload a JPG, PNG, or WebP image only.")
        image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(image_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"Image exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
        if not image_bytes:
            raise HTTPException(status_code=400, detail="The uploaded image is empty.")
        image_name = Path(file.filename).name[:180]
    context = {
        "project_name": project_name[:120].strip(),
        "location": location[:160].strip(),
        "property_type": property_type[:100].strip(),
        "area_sqft": area_sqft[:80].strip(),
        "market_rate_sqft": market_rate_sqft[:80].strip(),
        "budget": budget[:100].strip(),
        "timeline": timeline[:100].strip(),
        "image_name": image_name,
    }
    result = analyze(module, prompt, context, image_bytes, mime_type)
    # Save only the result and original file name; the image bytes are not persisted.
    save_analysis(result)
    return JSONResponse(result)


@app.get("/api/weather")
async def weather(location: str = Query(min_length=2, max_length=100)):
    try:
        return await get_weather(location.strip())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Live weather could not be reached. Check internet access and try again.") from exc
