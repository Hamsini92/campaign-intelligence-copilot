# Campaign Intelligence Co-pilot
## Project Plan & Architecture Document
### Portfolio Project

---

## 1. Executive Summary

An AI-powered Campaign Intelligence Co-pilot that helps banking marketing teams
make data-driven decisions about term deposit campaigns. The system combines
traditional ML (propensity scoring) with **Amazon Bedrock Agents** (managed
orchestration, tool-calling, multi-step reasoning) and **Bedrock Guardrails**
(content safety, topic control, PII protection) to transform raw campaign
data into actionable intelligence — accessible via natural language.

**Key AWS GenAI Services Used:**
- **Bedrock Foundation Models** — Claude 3.5 Sonnet for reasoning and generation
- **Bedrock Agents** — Managed agent orchestration with Action Groups (replaces custom Lambda routing)
- **Bedrock Guardrails** — Content filtering, denied topics, PII redaction, grounded responses
- **Bedrock Knowledge Bases** — (Optional) RAG over campaign documentation/policies

---

## 1.1 Portfolio Context

This is a portfolio project demonstrating end-to-end expertise across:

**Skills Demonstrated:**
- AWS Cloud Architecture (ECS, Lambda, S3, ALB, ECR, IAM, CloudWatch)
- Generative AI (Bedrock Agents, Guardrails, Foundation Models, Knowledge Bases)
- Traditional ML (XGBoost, SHAP explainability, feature engineering)
- Full-stack development (Streamlit frontend, Python backend)
- Infrastructure as Code (SAM/CloudFormation)
- Containerization (Docker, Nginx, ECS Fargate)
- Data Engineering (Pandas, data cleaning, feature pipelines)
- Responsible AI (guardrails, PII filtering, grounding, denied topics)

**What makes this project stand out:**
1. Not just another chatbot — combines ML scoring with GenAI reasoning
2. Production-grade architecture (not a Jupyter notebook demo)
3. Responsible AI built-in from day one (Bedrock Guardrails)
4. Demonstrates real business value, not just technology for its own sake
5. Full AWS deployment — not just local scripts

**Portfolio Deliverables:**
- GitHub repository with clean, documented code
- Architecture diagram (for resume / LinkedIn)
- Demo video (2-3 min walkthrough)
- Live deployment (spin up for interviews, tear down after)
- Blog post / write-up explaining design decisions

---

## 2. Business Value

### 2.1 Problem Statement

Marketing teams currently:
- Run campaigns with limited data-driven targeting (spray and pray)
- Rely on static reports and dashboards that require analyst involvement
- Have no systematic way to answer "why did this campaign fail?"
- Lack tooling to simulate campaign scenarios before committing budget
- Get ML model scores but no guidance on what to DO with them

### 2.2 Value Proposition

| Capability | Without Co-pilot | With Co-pilot |
|---|---|---|
| Customer targeting | Manual segmentation, gut feel | ML-scored propensity ranking with explanations |
| Campaign planning | Historical averages, trial & error | Scenario simulation ("what if we target X via Y?") |
| Post-campaign analysis | Analyst builds slides in 2 weeks | Instant natural language Q&A over results |
| Strategy per segment | Generic playbook | LLM-generated approach based on segment profile + economic context |
| Accessibility | Only data team can query data | Any marketing manager can ask questions in English |

### 2.3 Key Metrics (Expected Impact)

- Improve campaign conversion rate by better targeting (top-N selection vs. random)
- Reduce analyst time spent on ad-hoc campaign queries
- Enable non-technical stakeholders to self-serve data insights
- Faster campaign iteration through simulation before execution

---

## 3. Data Overview

### 3.1 Available Datasets

**Dataset 1 — Bank Marketing (Newer Version)**
- 20 features, no target variable in provided sample
- Features: age, job, marital, education, default, housing, loan, contact,
  month, day_of_week, duration, campaign, pdays, previous, poutcome
- Economic indicators: emp.var.rate, cons.price.idx, cons.conf.idx,
  euribor3m, nr.employed
- pdays=999 means customer was never previously contacted

**Dataset 2 — Bank Marketing (Older Version)**
- 17 features including target variable `y` (yes/no term deposit subscription)
- Includes `balance` (account balance) — valuable financial capacity signal
- pdays=-1 means customer was never previously contacted
- poutcome values: unknown, failure, success, other

### 3.2 How We Leverage the Data

```
FEATURE                  WHAT IT ENABLES
─────────────────────────────────────────────────────────────────
age, job, marital,       Customer profiling & segmentation
education                → Agent uses these to characterize segments

balance (Dataset 2)      Financial capacity signal
                         → ML model uses for propensity scoring
                         → LLM reasons about affordability

housing, loan, default   Financial obligations
                         → Risk indicators for term deposit lock-in

contact, month,          Channel & timing optimization
day_of_week              → Data agent finds best contact strategies
                         → "Cellular on Thursday converts 2.1x better"

duration                 Engagement signal (used carefully — only
                         known after call, so excluded from
                         prediction but useful for analysis)

campaign, pdays,         Contact history
previous, poutcome       → "Called 3 times, all failed — stop calling"
                         → Agent reasons about contact fatigue

emp.var.rate,            Economic context
cons.price.idx,          → LLM agent reasons about macro conditions
cons.conf.idx,           → "Consumer confidence is low — bad time
euribor3m, nr.employed     for long-term commitments"

y (target)               Train propensity model
                         → Binary classification: will they subscribe?
```

### 3.3 Data Limitations (Honest Assessment)

| What we CAN'T do | Why | Workaround |
|---|---|---|
| Multi-product recommendations | Only one product (term deposit) | Position as "propensity + strategy" not "recommendation engine" |
| Personalized contact scripts | No customer names, interaction logs, or product catalog | Generate segment-level strategy guidance instead |
| Real-time scoring | Static dataset, no live feed | Batch scoring + on-demand single-customer scoring via UI |
| Cross-sell / upsell | No multi-product purchase history | Focus on single-product conversion optimization |

---

## 4. Solution Architecture

### 4.1 High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                            AWS Cloud                                 │
│                                                                      │
│  ┌─────────┐    ┌───────────────────────────────────────────┐        │
│  │         │    │     ECS Fargate (Frontend Service)         │        │
│  │   ALB   │    │                                           │        │
│  │         │───▶│  ┌─────────┐    ┌──────────────────────┐  │        │
│  │ :443    │    │  │  Nginx  │───▶│  Streamlit App       │  │        │
│  │ (SSL)   │    │  │ (proxy) │    │  :8080               │  │        │
│  │         │    │  └─────────┘    │  - Chat Interface    │  │        │
│  └─────────┘    │                 │  - Dashboard Views   │  │        │
│                 │                 │  - File Upload       │  │        │
│                 │                 └──────────┬───────────┘  │        │
│                 └───────────────────────────┼──────────────┘        │
│                                             │                        │
│                                             │ Bedrock Agent          │
│                                             │ Runtime API            │
│                                             ▼                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    BEDROCK AGENT                              │    │
│  │              (Managed Orchestration)                          │    │
│  │                                                              │    │
│  │  ┌────────────────────────────────────────────────────────┐  │    │
│  │  │              BEDROCK GUARDRAILS                         │  │    │
│  │  │  - Content filtering (block harmful content)           │  │    │
│  │  │  - Denied topics (no financial advice, no legal)       │  │    │
│  │  │  - PII detection & redaction (SSN, account numbers)    │  │    │
│  │  │  - Grounding check (responses must cite data)          │  │    │
│  │  │  - Word/phrase filters (competitor names, etc.)         │  │    │
│  │  └────────────────────────────────────────────────────────┘  │    │
│  │                                                              │    │
│  │  Foundation Model: Claude 3.5 Sonnet (via Bedrock)          │    │
│  │  Instruction: System prompt with banking campaign context    │    │
│  │  Session: Managed conversation memory per user session       │    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐    │    │
│  │  │              ACTION GROUPS (Tools)                    │    │    │
│  │  │                                                      │    │    │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐   │    │    │
│  │  │  │ Action Group│  │ Action Group│  │Action Group│   │    │    │
│  │  │  │ 1: DATA     │  │ 2: ML SCORE │  │ 3: STRATEGY│   │    │    │
│  │  │  │ ANALYST     │  │             │  │ & INSIGHT  │   │    │    │
│  │  │  │             │  │             │  │            │   │    │    │
│  │  │  │ Lambda fn   │  │ Lambda fn   │  │ Lambda fn  │   │    │    │
│  │  │  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘   │    │    │
│  │  └─────────┼────────────────┼───────────────┼──────────┘    │    │
│  └────────────┼────────────────┼───────────────┼───────────────┘    │
│               │                │               │                     │
│               ▼                ▼               ▼                     │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │       S3         │  │     S3       │  │   Bedrock    │           │
│  │  (CSV dataset)   │  │  (ML model   │  │   FM for     │           │
│  │                  │  │   .joblib)   │  │   reasoning  │           │
│  └──────────────────┘  └──────────────┘  └──────────────┘           │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    Supporting Services                        │    │
│  │  CloudWatch (logs/metrics)  │  ECR (container images)        │    │
│  │  Secrets Manager            │  IAM (roles/policies)          │    │
│  │  Bedrock Knowledge Bases    │  (optional: campaign docs RAG) │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 AWS Services Breakdown

| Service | Role | Why This Service |
|---|---|---|
| **ECS Fargate** | Host Streamlit frontend + Nginx | Persistent WebSocket connections needed for Streamlit; matches internal deployment guide |
| **ALB** | Load balancing, SSL termination, health checks | Required for ECS; handles `/health` endpoint |
| **ECR** | Docker image registry | Store frontend container images |
| **Bedrock Agents** | Managed orchestration — intent routing, tool selection, multi-step reasoning, session memory | Replaces custom orchestrator Lambda; handles agent chaining, retries, and conversation context natively |
| **Bedrock Guardrails** | Content safety, denied topics, PII filtering, grounding checks | Enterprise requirement for banking; applied to all agent inputs and outputs |
| **Bedrock Foundation Models** | LLM inference (Claude 3.5 Sonnet) | Native AWS; no API keys; powers the agent's reasoning |
| **Bedrock Knowledge Bases** | (Optional) RAG over campaign policy documents | Could index marketing guidelines, compliance rules for the agent to reference |
| **Lambda** | Execute Action Group logic (data queries, ML scoring) | Bedrock Agent calls Lambda as tools; stateless, scalable |
| **S3** | Store dataset CSV + trained ML model (.joblib) | Durable storage; Lambda reads on invocation |
| **API Gateway** | (Optional) Direct API access to agent bypassing UI | REST endpoint for programmatic access |
| **CloudWatch** | Logging and monitoring | Centralized logs for all services; Bedrock Agent trace logs |
| **IAM** | Service-to-service auth | Bedrock Agent→Lambda, Lambda→S3, ECS→Bedrock permissions |

### 4.3 Bedrock Agents — How It Works

**Without Bedrock Agents (custom approach):**
```
User → API Gateway → Orchestrator Lambda (custom routing code)
     → manually calls other Lambdas → manually aggregates responses
     → manually manages conversation history
```

**With Bedrock Agents (managed approach):**
```
User → Bedrock Agent Runtime API (InvokeAgent)
     → Agent automatically decides which Action Group(s) to call
     → Agent chains multiple tools if needed
     → Agent manages session memory
     → Agent applies Guardrails to input AND output
     → Returns final response
```

**What Bedrock Agent handles for us (no custom code needed):**
- Intent classification (which tool to call)
- Multi-step reasoning (call data agent, then pass results to strategy agent)
- Conversation memory (session-based, managed by Bedrock)
- Retry logic and error handling
- Guardrails enforcement on every turn
- Trace logging for debugging agent decisions

**What we still build (as Lambda Action Groups):**
- Data Analyst logic (Pandas queries on S3 data)
- ML Prediction logic (load model, score, SHAP)
- Strategy/Insight templates (structured prompts for the agent)

### 4.4 Bedrock Guardrails — Configuration

```
┌───────────────────────────────────────────────────────────┐
│                  GUARDRAIL: CampaignCopilotGuardrail       │
│                                                           │
│  LAYER 1: Content Filters                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Category          │ Input Filter │ Output Filter    │  │
│  │ Hate              │ HIGH         │ HIGH             │  │
│  │ Insults           │ HIGH         │ HIGH             │  │
│  │ Sexual            │ HIGH         │ HIGH             │  │
│  │ Violence          │ HIGH         │ HIGH             │  │
│  │ Misconduct        │ HIGH         │ HIGH             │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  LAYER 2: Denied Topics                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ - Personal financial advice                         │  │
│  │   ("You should invest in..." / "Buy this product")  │  │
│  │ - Legal or compliance guidance                      │  │
│  │   ("This is legally required..." / "You must...")    │  │
│  │ - Competitor analysis or comparison                 │  │
│  │   ("Bank X is better/worse than...")                │  │
│  │ - Individual customer identification                │  │
│  │   ("Customer John Smith at address...")             │  │
│  │ - Credit decisions or approvals                     │  │
│  │   ("This customer should be approved for...")       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  LAYER 3: PII Filters                                     │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Type              │ Action                          │  │
│  │ SSN               │ BLOCK                           │  │
│  │ Credit Card       │ BLOCK                           │  │
│  │ Account Number    │ ANONYMIZE                       │  │
│  │ Phone Number      │ ANONYMIZE                       │  │
│  │ Email Address     │ ANONYMIZE                       │  │
│  │ Name              │ ANONYMIZE                       │  │
│  │ Address           │ ANONYMIZE                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  LAYER 4: Grounding Check                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Grounding threshold: 0.7                            │  │
│  │ Source: Data returned by Action Group Lambdas       │  │
│  │ Effect: If agent claims a statistic, it must be     │  │
│  │         traceable to actual data query results.     │  │
│  │         Prevents hallucinated conversion rates,     │  │
│  │         fabricated percentages, or made-up trends.  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  LAYER 5: Word/Phrase Filters                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ - Block competitor bank names (configurable list)   │  │
│  │ - Block guaranteed return language ("guaranteed",   │  │
│  │   "risk-free", "no-loss")                          │  │
│  │ - Block urgency manipulation ("act now", "limited   │  │
│  │   time only", "don't miss out")                    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

**Why Guardrails are critical for this use case:**
- Banking is a regulated industry — the agent must NOT give financial advice
- Marketing strategies must not use manipulative language
- PII must never appear in agent responses (even if present in data)
- Statistics must be grounded in actual data, not hallucinated
- Compliance team needs audit trail of what guardrails caught

### 4.5 Why This Architecture Split

**Frontend on ECS (not Lambda):**
- Streamlit requires persistent WebSocket connections
- Lambda has 29-second API Gateway timeout — too short for interactive UI
- Nginx reverse proxy handles WebSocket upgrade headers
- Matches internal ECS deployment standard

**Bedrock Agent (not custom orchestrator Lambda):**
- No custom routing code to maintain
- Multi-step reasoning handled natively (agent decides tool order)
- Session memory managed by Bedrock (no DynamoDB needed)
- Guardrails applied automatically on every interaction
- Trace/debug logs built in via CloudWatch
- Scales with Bedrock service limits, no Lambda concurrency tuning

**Action Groups on Lambda (the actual tools):**
- Each Action Group is a Lambda function the Bedrock Agent can invoke
- Agent decides WHEN and WHETHER to call each tool
- Stateless, scalable, pay-per-invocation
- Clean separation: agent reasons, Lambda executes

---

## 5. Agent Design (Bedrock Agents + Action Groups)

### 5.1 Bedrock Agent Configuration

```
Agent Name:        CampaignIntelligenceCopilot
Foundation Model:  anthropic.claude-3-5-sonnet (via Bedrock)
Guardrail:         CampaignCopilotGuardrail (attached to agent)
Idle Timeout:      1800 seconds (30-min session memory)
```

**Agent Instruction (System Prompt):**
```
You are a Campaign Intelligence Co-pilot for a banking marketing team.
You help with term deposit campaign targeting, analysis, and strategy.

You have access to three tool groups:
1. DATA ANALYST — query and analyze campaign data
2. ML SCORER — predict customer subscription propensity
3. STRATEGY ADVISOR — generate contact strategies

Rules:
- Always cite specific numbers from the data tools (never invent statistics)
- Never give personal financial advice to end customers
- Position all output as internal marketing team guidance
- When asked "who to target", always run the ML scorer first, then filter
- When asked "why", always query data first, then reason over results
- Flag when economic indicators suggest poor timing for campaigns
```

**How the Bedrock Agent decides what to do (no custom code):**
```
User: "Who should we call this week?"
Agent thinks: Need propensity scores → call ML SCORER Action Group
              Then need to rank and filter → call DATA ANALYST Action Group
              Then need contact approach → use built-in reasoning
Agent: Returns ranked list with strategies

User: "Why did May campaigns fail?"
Agent thinks: Need May campaign data → call DATA ANALYST Action Group
              Then need to reason over patterns → use built-in reasoning
Agent: Returns analysis citing specific data points
```

### 5.2 Action Group 1: Data Analyst

```
Action Group Name:  DataAnalyst
Lambda Function:    campaign-copilot-data-analyst
Description:        Query, filter, and aggregate the bank marketing dataset
```

**OpenAPI Schema (defines tools the agent can call):**
```yaml
paths:
  /query:
    post:
      summary: Run a data query on the campaign dataset
      operationId: queryData
      requestBody:
        content:
          application/json:
            schema:
              properties:
                query_description:
                  type: string
                  description: Natural language description of what data to retrieve
                filters:
                  type: object
                  description: Optional filters (age_min, age_max, job, marital, etc.)
                aggregation:
                  type: string
                  enum: [count, mean, sum, group_by, distribution]
                group_by_field:
                  type: string
                  description: Field to group results by

  /compare:
    post:
      summary: Compare two segments or time periods
      operationId: compareSegments
      requestBody:
        content:
          application/json:
            schema:
              properties:
                segment_a:
                  type: object
                  description: First segment filters
                segment_b:
                  type: object
                  description: Second segment filters
                metric:
                  type: string
                  enum: [conversion_rate, avg_duration, avg_contacts, count]

  /simulate:
    post:
      summary: Simulate a campaign scenario
      operationId: simulateCampaign
      requestBody:
        content:
          application/json:
            schema:
              properties:
                target_filters:
                  type: object
                  description: Who to target (age, job, channel, etc.)
                budget_contacts:
                  type: integer
                  description: How many contacts the budget allows
```

**Lambda Implementation:** Reads CSV from S3, executes Pandas operations,
returns structured JSON results back to the Bedrock Agent.

### 5.3 Action Group 2: ML Scorer

```
Action Group Name:  MLScorer
Lambda Function:    campaign-copilot-ml-scorer
Description:        Score customers for term deposit subscription propensity
```

**OpenAPI Schema:**
```yaml
paths:
  /score:
    post:
      summary: Score a single customer for subscription propensity
      operationId: scoreCustomer
      requestBody:
        content:
          application/json:
            schema:
              properties:
                age:
                  type: integer
                job:
                  type: string
                marital:
                  type: string
                education:
                  type: string
                balance:
                  type: number
                housing:
                  type: string
                loan:
                  type: string
                contact:
                  type: string
                previous:
                  type: integer
                poutcome:
                  type: string
      responses:
        200:
          content:
            application/json:
              schema:
                properties:
                  probability:
                    type: number
                  risk_tier:
                    type: string
                    enum: [high_propensity, medium_propensity, low_propensity]
                  top_factors:
                    type: array
                    items:
                      properties:
                        feature:
                          type: string
                        impact:
                          type: number
                        direction:
                          type: string

  /score-batch:
    post:
      summary: Score top-N customers from the dataset
      operationId: scoreBatch
      requestBody:
        content:
          application/json:
            schema:
              properties:
                filters:
                  type: object
                  description: Optional filters to narrow the batch
                top_n:
                  type: integer
                  description: Return top N highest-scoring customers
```

**Lambda Implementation:** Loads XGBoost model + SHAP explainer from S3,
runs prediction, computes top SHAP features, returns structured response.

### 5.4 Action Group 3: Strategy Advisor

```
Action Group Name:  StrategyAdvisor
Lambda Function:    campaign-copilot-strategy
Description:        Generate data-driven contact strategies for customer segments
```

**OpenAPI Schema:**
```yaml
paths:
  /strategy:
    post:
      summary: Generate a contact strategy for a customer segment
      operationId: generateStrategy
      requestBody:
        content:
          application/json:
            schema:
              properties:
                segment_profile:
                  type: object
                  description: Segment characteristics (avg age, common job, etc.)
                propensity_score:
                  type: number
                top_factors:
                  type: array
                  description: SHAP-derived key factors
                economic_context:
                  type: object
                  description: Current economic indicators
                historical_performance:
                  type: object
                  description: Past campaign results for this segment

  /explain-trend:
    post:
      summary: Explain a campaign trend or anomaly
      operationId: explainTrend
      requestBody:
        content:
          application/json:
            schema:
              properties:
                trend_data:
                  type: object
                  description: The data showing the trend
                question:
                  type: string
                  description: What the user wants explained
```

**Lambda Implementation:** Structures the data into a prompt template,
calls Bedrock FM for reasoning, returns strategy recommendation.
The Guardrail filters the output before it reaches the user.

### 5.5 Agent Flow Examples

**Example 1: Targeting query (multi-step)**
```
User: "I have budget for 200 calls. Who should we target?"

Bedrock Agent trace:
  Step 1: Invoke MLScorer.scoreBatch(top_n=200)
          → Returns 200 customers ranked by propensity
  Step 2: Invoke DataAnalyst.query(group_by="job", metric="count")
          → Groups the 200 into segments
  Step 3: Invoke StrategyAdvisor.strategy(segment_profile=...)
          → Generates approach per segment
  Step 4: Agent synthesizes final response
          → Guardrail checks output (PII, grounding, denied topics)
          → Returns to user
```

**Example 2: Analysis query (single-step)**
```
User: "What's the conversion rate for customers with housing loans?"

Bedrock Agent trace:
  Step 1: Invoke DataAnalyst.query(filters={housing: "yes"},
          aggregation="group_by", group_by_field="y")
          → Returns: yes=8.2%, no=91.8%
  Step 2: Agent formats response with context
          → Guardrail checks output
          → Returns to user
```

**Example 3: Guardrail intervention**
```
User: "Should this customer invest in term deposits?"

Bedrock Agent trace:
  Step 1: Guardrail INPUT filter catches "should...invest"
          → Denied topic: personal financial advice
  Response: "I can provide campaign targeting insights and
            propensity scores for marketing teams, but I cannot
            provide personal investment advice. Would you like
            me to score this customer's likelihood of subscribing
            to a term deposit campaign instead?"
```

---

## 6. High-Level Project Flow

### 6.1 User Interaction Flow

```
                    ┌─────────────────────┐
                    │   User opens app    │
                    │   (Streamlit UI)    │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │   Choose mode:      │
                    │   1. Chat (Q&A)     │
                    │   2. Score Customer  │
                    │   3. Campaign Sim   │
                    │   4. Dashboard      │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
     ┌────────▼──────┐ ┌─────▼──────┐ ┌──────▼───────┐
     │  CHAT MODE    │ │ SCORE MODE │ │  DASHBOARD   │
     │               │ │            │ │              │
     │ "Why did May  │ │ Enter or   │ │ Conversion   │
     │  fail?"       │ │ upload     │ │ by segment,  │
     │               │ │ customer   │ │ channel,     │
     │ Orchestrator  │ │ profile    │ │ time, econ   │
     │ routes to     │ │            │ │ indicators   │
     │ right agent   │ │ ML Agent   │ │              │
     │               │ │ scores +   │ │ Static +     │
     │ Multi-agent   │ │ explains   │ │ interactive  │
     │ chaining      │ │            │ │ Plotly charts │
     └───────────────┘ │ Strategy   │ └──────────────┘
                       │ Agent      │
                       │ advises    │
                       └────────────┘
```

### 6.2 Development Phases

```
PHASE 1: Data & ML Foundation
├── Merge and clean both datasets
├── Exploratory data analysis
├── Feature engineering
├── Train XGBoost propensity model
├── SHAP explainability integration
├── Save model artifact to S3
└── Validate model performance (AUC, precision-recall)

PHASE 2: Lambda Action Groups (Local Development)
├── Build Data Analyst Lambda (Pandas queries, S3 read)
├── Build ML Scorer Lambda (XGBoost predict + SHAP)
├── Build Strategy Advisor Lambda (Bedrock FM call + prompt template)
├── Write OpenAPI schemas for each Action Group
├── Test each Lambda locally with SAM CLI
└── Unit tests for all handlers

PHASE 3: Bedrock Agent & Guardrails Setup
├── Create Bedrock Guardrail (content filters, denied topics, PII, grounding)
├── Test Guardrail with sample inputs/outputs
├── Create Bedrock Agent with instruction prompt
├── Attach Action Groups (Lambda functions)
├── Attach Guardrail to Agent
├── (Optional) Create Knowledge Base for campaign docs
├── Test Agent via Bedrock console — verify multi-step reasoning
└── Test Guardrail interventions (financial advice, PII, etc.)

PHASE 4: Frontend (Streamlit)
├── Chat interface (calls Bedrock Agent Runtime API)
├── Customer scoring form (manual input → agent)
├── CSV upload for batch scoring
├── Dashboard tab (segment analysis, Plotly charts)
├── Health check endpoint (/health)
└── Local testing with Bedrock Agent

PHASE 5: AWS Deployment
├── Deploy Lambda functions (SAM / CloudFormation)
├── Upload model + data to S3
├── Deploy Bedrock Agent + Guardrail (via IaC or console)
├── Containerize Streamlit app (Dockerfile + nginx + ECS config)
├── Push to ECR
├── Deploy ECS service with ALB
├── Configure IAM roles (ECS → Bedrock Agent, Lambda → S3, etc.)
└── End-to-end testing on AWS

PHASE 6: Deploy to ENG/TEST
├── Push code to repository
├── Merge into main
├── Trigger deployment via GitHub Actions
└── Validate via ECS URL
```

---

## 7. ECS Deployment Configuration

Based on the internal deployment guide, the following files are required:

### 7.1 Dockerfile

```dockerfile
FROM python:3.11-slim-bullseye

RUN mkdir -p /python_project/.streamlit
RUN mkdir -p /python_project/app_modules
RUN mkdir -p /python_project/images

# Install nginx for reverse proxy (WebSocket support)
RUN apt-get -y update && \
    apt-get -y install nginx iproute2 jq lsof && \
    apt-get clean

COPY ./src/application/app.py /python_project/
COPY ./src/application/app_modules/ /python_project/app_modules/
COPY ./src/application/.streamlit/ /python_project/.streamlit/

COPY ./src/requirements.txt /python_project/
RUN cd /python_project && pip install --no-cache-dir -r requirements.txt

COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 443 8080

ENTRYPOINT [ "/start.sh" ]
```

> **Note:** The internal enterprise guide uses
> `vdocker.artifactory.opst.c1.vanguard.com/ecs-python:python3.11-debian11`
> as the base image and pulls packages from an internal PyPI mirror.
> For this portfolio project, we use the public `python:3.11-slim-bullseye`
> image and install nginx separately. The architecture and configuration
> patterns remain identical.

### 7.2 start-custom.sh

```bash
#!/bin/bash
echo "[INFO] Starting Streamlit Application"

cd /python_project
exec streamlit run app.py \
    --server.port=8080 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
```

### 7.3 nginx.conf (WebSocket Support)

```nginx
worker_processes 1;
error_log /dev/stdout error;

events {
    worker_connections 4096;
}

http {
    proxy_read_timeout 3900;

    upstream app_endpoint {
        server 127.0.0.1:8080;
    }

    server {
        listen 443 ssl;

        location / {
            proxy_pass http://app_endpoint;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
        }

        location /_stcore/stream {
            proxy_pass http://app_endpoint/_stcore/stream;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        location /_stcore/upload_file {
            proxy_pass http://app_endpoint/_stcore/upload_file;
            client_max_body_size 200m;
            proxy_request_buffering off;
        }

        location /health {
            return 200 "healthy\n";
        }
    }
}
```

### 7.4 ecs.json

```json
{
    "nginx": { "conf": "nginx.conf" },
    "params": {
        "defaults": {
            "IsUIApplication": "true",
            "AlbIdleTimeout": "3600",
            "HealthcheckPath": "/health",
            "DockerCpu": "1024",
            "DockerMemory": "4096"
        }
    }
}
```

### 7.5 Key ECS Configuration Notes

- `IsUIApplication` must be `true` for Streamlit apps
- `/health` endpoint in nginx returns 200 — must match `HealthcheckPath`
- Extended timeouts (3600s ALB, 3900s nginx) required for Streamlit WebSocket
- DockerCpu=1024 (1 vCPU), DockerMemory=4096 (4 GB) — sufficient for UI tier
- File upload supported up to 200MB via `client_max_body_size`

---

## 8. Project Folder Structure

```
campaign-intelligence-copilot/
│
├── PROJECT_PLAN.md                    # This document
│
├── data/
│   ├── bank_marketing_v1.csv          # Dataset 1 (with economic indicators)
│   └── bank_marketing_v2.csv          # Dataset 2 (with balance + target)
│
├── model/
│   ├── train.py                       # Train propensity model
│   ├── evaluate.py                    # Model evaluation + metrics
│   ├── feature_engineering.py         # Data prep + feature transforms
│   └── artifacts/
│       └── propensity_model.joblib    # Trained model artifact
│
├── lambdas/                           # Bedrock Agent Action Groups
│   ├── data_analyst/
│   │   ├── handler.py                 # Pandas queries on S3 data
│   │   ├── requirements.txt
│   │   └── openapi.yaml              # Action Group API schema
│   ├── ml_scorer/
│   │   ├── handler.py                 # XGBoost predict + SHAP explain
│   │   ├── requirements.txt
│   │   └── openapi.yaml
│   └── strategy_advisor/
│       ├── handler.py                 # Strategy generation via Bedrock FM
│       ├── requirements.txt
│       └── openapi.yaml
│
├── bedrock/                           # Bedrock Agent & Guardrail configs
│   ├── agent_instruction.txt          # Agent system prompt
│   ├── guardrail_config.json          # Guardrail policies (topics, PII, etc.)
│   └── knowledge_base/               # (Optional) campaign docs for RAG
│       └── campaign_policies.pdf
│
├── frontend/                          # ECS deployment
│   ├── src/
│   │   ├── application/
│   │   │   ├── app.py                 # Streamlit main app
│   │   │   ├── .streamlit/
│   │   │   │   └── config.toml
│   │   │   └── your_app_modules/
│   │   │       ├── chat.py            # Chat interface component
│   │   │       ├── scoring.py         # Customer scoring form
│   │   │       ├── dashboard.py       # Analytics dashboard
│   │   │       ├── simulation.py      # Campaign simulation
│   │   │       └── api_client.py      # Calls API Gateway
│   │   └── requirements.txt
│   ├── Dockerfile
│   ├── start-custom.sh
│   ├── nginx.conf
│   └── ecs.json
│
├── infra/                             # Infrastructure as Code
│   ├── template.yaml                  # SAM / CloudFormation
│   ├── api-gateway.yaml               # API Gateway config
│   ├── lambda-roles.yaml              # IAM roles for Lambdas
│   └── s3-buckets.yaml                # S3 bucket definitions
│
├── tests/
│   ├── test_agents/
│   ├── test_model/
│   └── test_frontend/
│
├── notebooks/                         # EDA and experimentation
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_training.ipynb
│
├── requirements.txt                   # Local development deps
└── README.md                          # Setup and run instructions
```

---

## 9. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | Streamlit | 1.x |
| Charts | Plotly | 5.x |
| ML Model | XGBoost / LightGBM | latest |
| Explainability | SHAP | 0.4x |
| Data Processing | Pandas, NumPy | latest |
| Agent Orchestration | AWS Bedrock Agents | managed service |
| Agent Safety | AWS Bedrock Guardrails | managed service |
| LLM | AWS Bedrock FM (Claude 3.5 Sonnet) | latest |
| Knowledge Base | AWS Bedrock Knowledge Bases | (optional, for RAG) |
| Container | Docker (ECS-compatible base) | python3.11 |
| Reverse Proxy | Nginx | bundled with ECS image |
| Compute (Frontend) | ECS Fargate | - |
| Compute (Agents) | AWS Lambda | Python 3.11 |
| Storage | S3 | - |
| API | API Gateway (REST) | - |
| CI/CD | GitHub Actions | - |
| IaC | SAM / CloudFormation | - |

---

## 10. AWS Infrastructure Cost Estimate

### 10.1 Monthly Cost Breakdown (Development / Low Usage)

Assumes: ~500 agent invocations/day, 1 ECS task, small dataset (<100MB)

| Service | Unit | Usage Estimate | Monthly Cost (USD) |
|---|---|---|---|
| **ECS Fargate** | 1 vCPU, 4GB, 24/7 | 730 hours | ~$50-60 |
| **ALB** | Per hour + LCU | 730 hours + light traffic | ~$20-25 |
| **ECR** | Storage | <1 GB image | ~$0.10 |
| **Lambda (3 functions)** | Requests + duration | ~15,000 req/mo, 512MB, avg 3s | ~$5-10 |
| **S3** | Storage + requests | <100MB data + model, ~30K GET | ~$0.50 |
| **Bedrock FM (Claude 3.5 Sonnet)** | Input + output tokens | ~500 calls/day, avg 2K tokens each | ~$50-80 |
| **Bedrock Agents** | Per agent session | ~500 sessions/day | ~$15-25 |
| **Bedrock Guardrails** | Per text unit assessed | ~1000 assessments/day | ~$10-20 |
| **Bedrock Knowledge Bases** | (Optional) embedding + storage | Small corpus | ~$5-10 |
| **CloudWatch** | Logs + metrics | Standard logging | ~$5-10 |
| **API Gateway** | (If used) requests | ~15,000 req/mo | ~$1-2 |
| **NAT Gateway** | (If VPC) per hour + data | 730 hours | ~$35 (if needed) |
| | | | |
| **TOTAL (without NAT)** | | | **~$160-240/mo** |
| **TOTAL (with NAT Gateway)** | | | **~$195-275/mo** |

### 10.2 Monthly Cost Breakdown (Production / Moderate Usage)

Assumes: ~5,000 agent invocations/day, 2 ECS tasks, auto-scaling

| Service | Usage Estimate | Monthly Cost (USD) |
|---|---|---|
| **ECS Fargate (2 tasks)** | 2x (1 vCPU, 4GB), 24/7 | ~$100-120 |
| **ALB** | Moderate traffic | ~$30-40 |
| **Lambda (3 functions)** | ~150K req/mo, 512MB-1GB | ~$30-50 |
| **S3** | Data + model + logs | ~$2-5 |
| **Bedrock FM (Claude 3.5 Sonnet)** | ~5K calls/day, multi-step reasoning (2-3 FM calls per session) | ~$400-700 |
| **Bedrock Agents** | ~5K sessions/day | ~$100-150 |
| **Bedrock Guardrails** | ~10K assessments/day | ~$75-120 |
| **CloudWatch** | Extended logging | ~$15-25 |
| **NAT Gateway** | Standard | ~$35 |
| | | |
| **TOTAL** | | **~$800-1,250/mo** |

### 10.3 Cost Optimization Strategies

| Strategy | Savings |
|---|---|
| Use Claude 3 Haiku for simple intent classification, Sonnet only for complex reasoning | 60-80% on Bedrock FM costs |
| Cache frequent data queries in Lambda /tmp (warm starts) | Reduce S3 GET requests |
| Use Fargate Spot for non-production environments | 50-70% on ECS costs |
| Batch SHAP computations, cache per segment | Reduce Lambda duration |
| Guardrail: filter obvious non-queries client-side before hitting Bedrock | Reduce Guardrail assessment costs |
| Use provisioned throughput for Bedrock if consistent volume | Predictable pricing |

### 10.4 Cost Notes

- **Biggest cost driver is Bedrock FM tokens.** Each agent session may invoke
  the FM 2-4 times (intent → tool call → reasoning → response). At scale,
  consider using Haiku for routing and Sonnet only for final synthesis.
- **ECS is a fixed cost** — it runs 24/7 regardless of traffic. For
  dev/test, consider shutting down outside business hours.
- **Lambda costs are negligible** at this scale. Even 10x traffic barely
  moves the needle.
- **NAT Gateway** is a hidden cost if your Lambda/ECS are in a VPC
  (required for many enterprise setups). Can be avoided with VPC endpoints
  for S3 and Bedrock.

---

## 11. Risk & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Lambda cold start for ML scorer (loading XGBoost + SHAP) | 5-10s delay on first call | Use provisioned concurrency or package model in Lambda layer |
| Bedrock Agent multi-step latency | 10-15s for complex queries (multiple tool calls) | Show "thinking" animation in UI; use streaming responses |
| Bedrock rate limits | Throttled under load | Implement retry with backoff; request quota increase |
| Guardrail false positives | Blocks legitimate marketing queries | Tune guardrail thresholds; test extensively with real queries |
| Data drift (model trained on static data) | Predictions degrade over time | Log predictions; add monitoring; retrain pipeline |
| Single product limitation | Users expect multi-product recs | Set clear expectations in UI; position as "campaign targeting" |
| Bedrock Agent hallucination | Fabricates statistics | Grounding check guardrail + instruct agent to always cite tool results |
| Cost overrun from FM token usage | Unexpected bills | Set Bedrock budget alerts; use Haiku for simple tasks |

---

## 12. Next Steps

1. Set up the project folder structure with all scaffolding
2. Place the CSV data files in `/data`
3. Build the ML model (train.py) and validate performance
4. Develop Lambda Action Group handlers + OpenAPI schemas
5. Set up Bedrock Agent + Guardrails in AWS console (or via IaC)
6. Build the Streamlit frontend calling Bedrock Agent Runtime API
7. Containerize and test with Docker locally
8. Deploy Lambda functions, Bedrock Agent, and ECS to AWS
9. End-to-end integration testing
10. Deploy to ENG/TEST via GitHub Actions
