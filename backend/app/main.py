import os
import sys
from pathlib import Path

# Set up paths before any handler imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "lambdas"))

# Set env vars for Lambda handlers before they are imported
os.environ.setdefault("MODEL_PATH", str(PROJECT_ROOT / "model" / "artifacts" / "propensity_model.joblib"))
os.environ.setdefault("FEATURE_PATH", str(PROJECT_ROOT / "model" / "artifacts" / "feature_list.csv"))
os.environ.setdefault("DATA_PATH", str(PROJECT_ROOT / "data" / "train.csv"))
os.environ.setdefault("LOCAL_MODE", "true")
os.environ.setdefault("THRESHOLD", "0.6717")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scoring, analytics, strategy, chat

app = FastAPI(
    title="Campaign Intelligence Co-pilot",
    description="ML-powered campaign scoring, analytics, and strategy API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scoring.router, tags=["Scoring"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(strategy.router, tags=["Strategy"])
app.include_router(chat.router, tags=["Chat"])


@app.get("/")
def root():
    return {"status": "ok", "service": "Campaign Intelligence Co-pilot API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
