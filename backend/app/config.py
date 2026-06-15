import os
from pathlib import Path

# Project root is one level above backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

MODEL_PATH = os.environ.get("MODEL_PATH", str(PROJECT_ROOT / "model" / "artifacts" / "propensity_model.joblib"))
FEATURE_PATH = os.environ.get("FEATURE_PATH", str(PROJECT_ROOT / "model" / "artifacts" / "feature_list.csv"))
DATA_PATH = os.environ.get("DATA_PATH", str(PROJECT_ROOT / "data" / "train.csv"))
THRESHOLD = float(os.environ.get("THRESHOLD", "0.6717"))
LOCAL_MODE = os.environ.get("LOCAL_MODE", "true").lower() == "true"
