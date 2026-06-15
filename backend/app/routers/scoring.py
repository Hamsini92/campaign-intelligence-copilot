from fastapi import APIRouter
from app.schemas.scoring import CustomerInput, BatchScoreRequest
from app.config import MODEL_PATH, FEATURE_PATH, THRESHOLD
import os
import json

# Configure env vars for the lambda handler before importing
os.environ["MODEL_PATH"] = MODEL_PATH
os.environ["FEATURE_PATH"] = FEATURE_PATH
os.environ["THRESHOLD"] = str(THRESHOLD)

# Fix SHAP/XGBoost 3.x compatibility: base_score stored as "[5E-1]"
# Monkey-patch XGBTreeModelLoader to handle bracketed scientific notation
import shap.explainers._tree as _shap_tree

_OrigInit = _shap_tree.XGBTreeModelLoader.__init__

def _patched_init(self, xgb_model):
    try:
        _OrigInit(self, xgb_model)
    except ValueError:
        # Parse base_score manually if float() fails on bracketed format
        booster = xgb_model.get_booster() if hasattr(xgb_model, "get_booster") else xgb_model
        config = json.loads(booster.save_config())
        bs = config["learner"]["learner_model_param"]["base_score"]
        if isinstance(bs, str) and bs.startswith("["):
            # Temporarily patch float to handle bracketed values
            import builtins
            orig_float = builtins.float
            def patched_float(x):
                if isinstance(x, str) and x.startswith("["):
                    return orig_float(x.strip("[]"))
                return orig_float(x)
            builtins.float = patched_float
            try:
                _OrigInit(self, xgb_model)
            finally:
                builtins.float = orig_float
        else:
            raise

_shap_tree.XGBTreeModelLoader.__init__ = _patched_init

from ml_scorer.handler import score_customer, score_batch
import pandas as pd

router = APIRouter()


@router.post("/api/score")
def score(customer: CustomerInput):
    result = score_customer(customer.model_dump())
    return result


@router.post("/api/score-batch")
def score_batch_endpoint(req: BatchScoreRequest):
    df = pd.DataFrame(req.customers)
    result = score_batch(df)
    return result.to_dict(orient="records")
