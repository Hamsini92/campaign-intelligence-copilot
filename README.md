# Campaign Intelligence Co-pilot

ML-powered campaign scoring, analytics, and strategy recommendations for bank marketing campaigns.

## What It Does

A full-stack application that helps bank marketing teams make data-driven campaign decisions:

- **Score Customers** - Predict subscription likelihood using an XGBoost model with SHAP explainability
- **Dashboard** - Visualize conversion rates by job, month, channel, and economic indicators
- **Campaign Simulator** - Model campaign outcomes before committing budget, compare channels
- **Strategy Advisor** - Get AI-generated contact strategies (AWS Bedrock) or rule-based recommendations locally
- **Chat Co-pilot** - Natural language interface to query data, score customers, and get recommendations

## Architecture

```
frontend/          Next.js 16 + React 19 + shadcn/ui + Recharts
backend/           FastAPI + Python
lambdas/
  ml_scorer/       XGBoost scoring + SHAP explanations
  data_analyst/    Pandas-based data querying and simulation
  strategy_advisor/  Bedrock Claude (AWS) or local rule-based fallback
model/artifacts/   Trained XGBoost model + feature list
data/              UCI Bank Marketing dataset (28,903 records)
```

Each Lambda handler is a standalone module that can run locally (called by FastAPI) or deploy as an AWS Lambda function.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| Backend | FastAPI, Python, Uvicorn |
| ML Model | XGBoost, SHAP, scikit-learn, pandas |
| AI Strategy | AWS Bedrock (Claude 3.5 Sonnet) |
| Infra | Docker Compose, AWS Lambda (planned) |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- pip / npm

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000` with the API at `http://localhost:8000`.

### Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/score` | Score a single customer |
| `POST` | `/api/score-batch` | Score multiple customers |
| `GET` | `/api/dashboard-stats` | Dashboard analytics |
| `POST` | `/api/query` | Query campaign data |
| `POST` | `/api/compare` | Compare customer segments |
| `POST` | `/api/simulate` | Simulate campaign outcomes |
| `POST` | `/api/strategy` | Generate strategy recommendations |
| `POST` | `/api/chat` | Natural language chat interface |

## Model Details

- **Algorithm**: XGBoost binary classifier
- **Dataset**: UCI Bank Marketing (28,903 records, 41 features)
- **Target**: Term deposit subscription (binary)
- **Threshold**: 0.6717 (optimized for precision-recall balance)
- **Tiers**: High (70%+), Medium (40-70%), Low (<40%) propensity

## Project Structure

```
campaign-intelligence-copilot/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app + CORS
│       ├── config.py            # Centralized configuration
│       ├── routers/             # API route handlers
│       ├── schemas/             # Pydantic request models
│       └── services/            # Business logic
├── frontend/
│   └── src/
│       ├── app/                 # Next.js pages (dashboard, score, simulate, chat)
│       ├── components/          # UI components (shadcn/ui + sidebar)
│       └── lib/                 # API client
├── lambdas/
│   ├── ml_scorer/               # XGBoost + SHAP scoring
│   ├── data_analyst/            # Data queries + simulation
│   └── strategy_advisor/        # Bedrock / local strategy generation
├── model/artifacts/             # Trained model files
├── data/                        # Training dataset
├── docker-compose.yml
└── .gitignore
```
