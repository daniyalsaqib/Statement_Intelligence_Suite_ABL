# ABL Customer Statement Intelligence Suite

> **Production Functional — Final Hardening & Handover Phase**
>
> **Production-functional milestone:** 10 September 2026
> **Unified assistant hardening completed:** 22 September 2026
> **Latest project update:** 22 September 2026
> **Developer:** Daniyal Saqib — IT Intern, Allied Bank Internship Program (ABIP)
> **Sponsor / Reviewer:** Sir Affan Wahid

An AI-powered banking intelligence application combining deterministic financial-data processing, recurring-payment analysis, retrieval-augmented generation (RAG), semantic search, and grounded LLM responses.

The project uses **synthetic/local statement data only** and a curated set of **public Allied Bank information**. It does not connect to live Allied Bank customer accounts, production banking systems, or confidential internal banking data.

---

## Live Application

- **Frontend:** https://statement-intelligence-suite-abl.vercel.app
- **Backend:** https://pure-temple-45004-09958cbb6652.herokuapp.com
- **Health:** https://pure-temple-45004-09958cbb6652.herokuapp.com/health
- **Swagger:** https://pure-temple-45004-09958cbb6652.herokuapp.com/docs
- **Repository:** https://github.com/daniyalsaqib/Statement_Intelligence_Suite_ABL

---

# Project Status

**Current status:** Production Functional — conversational hardening complete, with final documentation and handover preparation in progress.

The application reached its main **production-functional milestone on 10 September 2026**. The post-functional phase has focused on making the prototype safer, easier to demonstrate, and more coherent as one banking-intelligence experience.

Production hardening completed or verified to date includes:

- Search-engine and social-sharing metadata
- Frontend performance validation
- Unified assistant workspace UX
- Deterministic capability routing
- Natural financial-language handling
- Safe multi-turn statement follow-ups
- Cross-capability conversation robustness
- Deterministic recurring-payment rules
- Public-policy RAG with fail-closed behavior
- Project-wide formatting standards
- Expanded backend regression coverage
- GitHub Actions CI validation
- Heroku production deployment and smoke testing

The internship/project handover remains within the original internship window ending **25 September 2026**.

### Current production validation

The current production build has passed:

- **153/153 automated backend tests**
- GitHub Actions CI on commit `ebf1a47`
- Synthetic CSV upload and deterministic analysis
- Verified statement Q&A
- Natural financial-language handling
- Month-specific filtering
- Multi-turn month follow-ups
- Cross-capability follow-up regression
- Deterministic recurring-payment analysis
- Public-policy RAG
- Policy fail-closed behavior
- Unified `/assistant/chat` routing
- Heroku health validation
- Production mixed-capability follow-up smoke testing

### Recent production checkpoints

```text
ebf1a47  Harden cross-capability statement follow-ups
153df3b  Harden unified assistant capability routing
2e65783  Add project formatting configuration
5d18291  Standardize project formatting
4d37e82  Harden natural financial language handling
9d2a678  Unify banking assistant workspace UX
594774d  Add unified banking assistant router
9d9b4eb  Add multi-month synthetic statement sample
f577fff  Add multi-turn statement chat interface
8b6898f  Add safe multi-turn statement follow-up foundation
```

---

# Unified Banking Intelligence Assistant

The production frontend presents the application as **one conversational banking-intelligence workspace** instead of requiring the user to switch between separate statement, recurring-payment, and policy tools.

The primary conversational endpoint is:

```http
POST /assistant/chat
```

The FastAPI backend uses deterministic routing to select one of three internal capabilities:

```text
Unified User Question
        |
        v
Deterministic Capability Router
        |
        +----------------+----------------+
        |                |                |
        v                v                v
   Statement         Recurring          Policy
 Intelligence       Payment Rules        RAG
        |                |                |
        v                v                v
 Verified Python   Deterministic     PostgreSQL +
 Facts / Guard      Python Rules       pgvector
        |                |                |
        +----------------+----------------+
                         |
                         v
                Unified Response
                + Provenance
```

The LLM is **not** used as the capability router. This keeps financial routing predictable, recurring-payment detection deterministic, and policy questions inside the RAG trust boundary.

Response provenance is exposed through method values such as:

```text
verified_statement_intelligence
deterministic_recurring_rules
policy_rag
```

### Safe multi-turn follow-ups

Recent conversation history can be supplied to the unified assistant to improve follow-up UX.

Conversation history is never treated as authoritative financial truth. When a follow-up changes the time scope, the backend recalculates the answer from the currently supplied statement rows.

Example:

```text
How much did I spend in August?
What about July?
```

The July amount is recomputed from July transactions.

The backend also handles cross-capability conversation history safely:

```text
How much did I spend in August?
Which payments keep repeating?
What about July?
```

The recurring-payment question does not replace the earlier reusable statement-spending intent. The backend scans backward for a deterministic statement intent that can be safely reapplied to the current scope.

---

# Core Capabilities

## 1. Statement Intelligence

The Statement Intelligence module accepts a synthetic CSV bank statement, validates it, parses transactions, and calculates verified financial facts.

The backend can calculate:

- Transaction count
- Debit transaction count
- Credit transaction count
- Total debit / spending
- Total credit
- Opening balance
- Closing balance
- Monthly spending
- Monthly credits
- Spending by description
- Largest debit
- Largest credit

### Deterministic financial calculations

Exact financial figures are calculated in **Python**, not by the LLM.

Example:

```text
How much did I spend?
```

For the included demonstration statement:

```text
31,500.00
```

Python is treated as the authoritative source for financial arithmetic.

### Open-ended and compound questions

Interpretive or multi-part questions use a hybrid deterministic + LLM workflow.

```text
User Question
     ↓
Statement Data
     ↓
Question Classification
     ↓
Verified Python Financial Facts
     ↓
Groq / GPT-OSS qualitative interpretation
     ↓
Python numeric guard
     ↓
Final grounded answer
```

Simple exact questions can be answered directly through deterministic Python logic.

Open-ended or compound questions continue into the verified-facts + LLM pipeline.

The LLM is used for explanation and interpretation, not as the source of truth for banking arithmetic.

When Python supplies verified figures, numeric or currency output produced independently by the LLM can be discarded rather than risking presentation of an incorrect financial value.

---

## 2. Recurring Payment Analysis

The recurring-payment module detects repeated outgoing transaction descriptions and returns them as **recurring payment candidates**.

Current rule:

```text
Repeated outgoing description
        ↓
Recurring payment candidate
```

Returned information includes:

- Description
- Number of occurrences
- Amounts
- Dates

For the included demonstration statement, expected candidates include:

```text
Netflix
Spotify
Grocery Store
```

Expected candidate count:

```text
3
```

These are intentionally described as **candidates**, not guaranteed subscriptions.

A repeated merchant such as a grocery store can therefore be detected even when it is not a formal subscription.

---

## 3. ABL Policy Assistant

The Policy Assistant is a retrieval-augmented generation system over a curated public Allied Bank information corpus.

### Policy RAG pipeline

```text
User Policy Question
       ↓
FastEmbed / ONNX
       ↓
sentence-transformers/all-MiniLM-L6-v2
       ↓
384-dimensional query embedding
       ↓
PostgreSQL + pgvector
       ↓
Vector similarity search
       ↓
Top 3 candidate chunks
       ↓
Distance <= 0.75 relevance filter
       ↓
Relevant public policy context
       ↓
Groq / openai/gpt-oss-20b
       ↓
Grounded answer + public source links
```

### Retrieval configuration

- **Embedding runtime:** FastEmbed / ONNX
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding dimensions:** 384
- **Vector store:** PostgreSQL + pgvector
- **Retrieved chunks:** Up to 3
- **Relevance threshold:** cosine distance `<= 0.75`

### Fail-closed behavior

If no policy chunk passes the relevance threshold, the assistant does not attempt to fabricate an answer.

Example response:

```text
I could not find relevant information in the available Allied Bank public policy documents.
```

The assistant is instructed not to invent Allied Bank policies, unsupported facts, or source URLs.

---

# Public Policy Corpus

The demonstration corpus currently contains **7 public policy/document chunks**:

1. Account and Electronic Banking Terms
2. Changes to Terms and Conditions
3. Financial Consumer Protection Framework
4. Customer Complaints and Confidentiality
5. Unclaimed Deposit Refund
6. Unclaimed Deposit Required Documents
7. Schedule of Charges

Example public sources:

```text
https://www.abl.com/terms/
https://www.abl.com/services/financial-consumer-protection-framework/
https://www.abl.com/services/downloads/deposit-guidelines/
https://www.abl.com/services/downloads/schedule-of-charges/
```

---

# System Architecture

The application uses a:

> **Layered client-server architecture with a modular FastAPI backend, deterministic financial processing, conversational orchestration, and a Retrieval-Augmented Generation subsystem.**

It is implemented as a **modular monolith**, not as a microservices architecture.

For the complete architecture, deployment model, request flows, RAG pipeline, data boundaries, and design decisions, see:

**[Detailed System Architecture](docs/ARCHITECTURE.md)**

```text
                         USER / BROWSER
                              |
                              v
                 +-------------------------+
                 | React + Tailwind CSS    |
                 | Vite Frontend           |
                 | Hosted on Vercel        |
                 +------------+------------+
                              |
                        HTTPS / REST
                              |
                              v
                 +-------------------------+
                 | /assistant/chat         |
                 | Unified Assistant       |
                 +------------+------------+
                              |
                    Deterministic Routing
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
      Statement         Recurring          Policy
      Intelligence      Rules              RAG
             |                |                |
             v                v                v
      Verified Python   Deterministic      FastEmbed
      Facts + Guard     Python Rules       MiniLM 384D
             |                                 |
             |                                 v
             |                           PostgreSQL
             |                            + pgvector
             |                                 |
             |                          Semantic Search
             |                                 |
             +----------------+----------------+
                              |
                              v
                           Groq API
                   openai/gpt-oss-20b
                              |
                              v
                       Grounded Answer
```

The specialized endpoints remain available for backward compatibility, while the production frontend uses the unified assistant as its primary conversational interface.

---

# Architectural Layers

## Presentation Layer

Implemented with:

- React.js
- Tailwind CSS
- Vite

Responsibilities:

- Synthetic statement upload and analysis
- Unified conversational assistant workspace
- Verified financial-analysis presentation
- Multi-turn statement follow-ups
- Recurring-payment candidate presentation
- Policy-source presentation

Hosted on **Vercel**.

---

## API / Routing Layer

Implemented with **FastAPI**.

Main routers:

```text
backend/app/routers/assistant.py
backend/app/routers/statements.py
backend/app/routers/statement_qa.py
backend/app/routers/policy_qa.py
```

Responsibilities:

- Unified capability routing
- HTTP request handling
- Input validation
- Statement conversation-history validation
- Routing requests into backend services
- Controlled API errors
- JSON responses with capability/method provenance

The unified assistant router is a thin orchestration layer over the existing statement, recurring-payment, and policy capabilities. The underlying specialized endpoints remain available for backward compatibility.

---

## Service Layer

Main services include:

```text
statement_parser.py
statement_analysis.py
statement_facts.py
statement_qa_deterministic.py
statement_qa_filter.py
subscription_analysis.py
embedding_service.py
llm_service.py
```

Responsibilities include:

- CSV parsing
- Financial calculations
- Verified fact generation
- Deterministic Q&A
- Date/month filtering
- Recurring-payment detection
- Embedding generation
- LLM communication

---

## Data Layer

The Policy Assistant uses:

- PostgreSQL
- pgvector
- `psycopg`

Policy text and 384-dimensional embeddings are stored inside the PostgreSQL `policy_documents` table.

The statement workflow does **not** persist uploaded statement data into the policy vector database.

---

## External AI Layer

Groq provides language generation using:

```text
openai/gpt-oss-20b
```

Current production configuration includes:

- Low reasoning effort
- Temperature `0.0`
- Maximum completion tokens: `1600`
- Request timeout: `15 seconds`
- No automatic retries

Provider-specific logic is isolated inside:

```text
backend/app/services/llm_service.py
```

---

# Final Technology Stack

| Layer                | Technology                               |
| -------------------- | ---------------------------------------- |
| Frontend             | React.js                                 |
| Styling              | Tailwind CSS                             |
| Build Tool           | Vite                                     |
| Frontend Hosting     | Vercel                                   |
| Backend              | FastAPI                                  |
| Backend Language     | Python 3.12                              |
| Backend Hosting      | Heroku                                   |
| LLM Provider         | Groq                                     |
| LLM Model            | `openai/gpt-oss-20b`                     |
| Embedding Runtime    | FastEmbed / ONNX                         |
| Embedding Model      | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding Dimensions | 384                                      |
| Database             | PostgreSQL                               |
| Vector Search        | pgvector                                 |
| PostgreSQL Driver    | psycopg                                  |
| Version Control      | Git                                      |
| Repository Hosting   | GitHub                                   |

---

# Important Architecture Changes

## Gemini → Groq

Gemini was used earlier during development.

Production testing exposed reliability and quota-related availability problems, so the production LLM path was migrated to:

```text
Groq
openai/gpt-oss-20b
```

Provider-specific logic is isolated inside `llm_service.py`, and provider failures are converted into controlled HTTP errors.

---

## SentenceTransformers / PyTorch → FastEmbed / ONNX

The original embedding runtime used SentenceTransformers/PyTorch.

That runtime contributed significant memory overhead on Heroku.

Local benchmarking during development showed approximately:

```text
SentenceTransformers path: first embedding ≈ 443 MB
FastEmbed path:            first embedding ≈ 203 MB
```

The final implementation keeps the same MiniLM 384-dimensional embedding model while using the lighter FastEmbed / ONNX runtime.

The embedding model is lazy-loaded only when Policy RAG actually requires it.

---

## LLM arithmetic → verified Python facts

Exact financial arithmetic was moved fully into deterministic Python code.

Final design rule:

```text
Python computes authoritative financial facts.
Groq explains or summarizes those verified facts.
```

This reduces the risk of incorrect financial arithmetic being generated by the LLM.

---

# Main Request Flows

## Unified Assistant

```text
User Question
      |
      v
POST /assistant/chat
      |
      v
Deterministic Capability Routing
      |
 +----+-------------+-------------+
 |                  |             |
 v                  v             v
Statement         Recurring      Policy
 |                  |             |
 v                  v             v
Verified Python   Python Rules   RAG Retrieval
 |                  |             |
 +------------------+-------------+
                    |
                    v
             Unified Answer
             + provenance
```

For statement conversations, the frontend can send recent `conversation_history`. That history helps recover safe follow-up intent, but financial values are always recalculated from the supplied statement data.

---

## Statement Upload

```text
CSV Upload
    |
    v
POST /statement/upload
    |
    v
CSV validation
    |
    v
statement_parser.py
    |
    v
Structured transactions
    |
    v
statement_analysis.py
    |
    v
Financial summary
    |
    v
JSON response
```

---

## Statement Intelligence

```text
User Question + Statement Data
           |
           v
Statement capability
           |
           v
Month / scope resolution
           |
           v
Deterministic question?
       /             \
     Yes              No
      |                |
      v                v
Verified Python    Verified Python
Answer             Facts
                       |
                       v
                    Groq
                       |
                       v
                 Numeric Guard
                       |
                       v
                 Final Answer
```

Simple exact questions are answered directly through deterministic Python logic. Open-ended or compound questions may use Groq for qualitative interpretation, while verified Python facts remain authoritative.

---

## Recurring Payment Analysis

```text
Statement Data
    |
    v
Recurring capability
    |
    v
Debit transactions
    |
    v
Description normalization
    |
    v
Group matching descriptions
    |
    v
Repeated description?
    |
    v
Recurring-payment candidate
```

---

## Policy Assistant

```text
Policy Question
      |
      v
Policy capability
      |
      v
FastEmbed query embedding
      |
      v
MiniLM 384D vector
      |
      v
PostgreSQL + pgvector
      |
      v
Top 3 vector matches
      |
      v
Distance <= 0.75
      |
      v
Relevant public context
      |
      v
Groq
      |
      v
Grounded answer + sources
```

---

# Main API Endpoints

## Unified Assistant

```http
POST /assistant/chat
```

Primary conversational endpoint used by the production frontend.

Request capabilities:

- Verified statement intelligence
- Deterministic recurring-payment detection
- Public-policy RAG
- Optional recent conversation history for safe statement follow-ups

Response metadata includes:

- `capability`
- `method`
- `answer`
- `sources`
- `structured_data`

---

## Health

```http
GET /health
```

---

## Upload Statement

```http
POST /statement/upload
```

Input:

```text
multipart/form-data
CSV file
```

---

## Backward-Compatible Statement Q&A

```http
POST /statement/ask
```

Supports statement data plus optional `conversation_history`.

---

## Backward-Compatible Recurring-Payment Analysis

```http
POST /statement/subscriptions
```

Input:

```text
multipart/form-data
CSV file
```

---

## Backward-Compatible Policy Q&A

```http
POST /policy/ask
```

Responses include:

- Question
- Grounded answer
- Relevant public source links

---

# SEO & Discoverability

Production SEO hardening was completed during the post-functional production-polish phase.

Implemented:

- Descriptive page title
- Meta description
- Search-engine robots metadata
- Canonical URL
- Open Graph metadata
- Twitter / large-image social metadata
- SoftwareApplication structured data
- `robots.txt`
- `sitemap.xml`
- Custom project favicon
- Social preview image

Production crawler files:

```text
https://statement-intelligence-suite-abl.vercel.app/robots.txt
https://statement-intelligence-suite-abl.vercel.app/sitemap.xml
```

---

# Frontend Performance Validation

Production performance was measured using Lighthouse against the deployed Vercel application.

Three repeated performance runs produced:

| Run | Performance |   FCP |   LCP |   TBT | CLS |
| --- | ----------: | ----: | ----: | ----: | --: |
| 1   |          89 | 1.7 s | 1.7 s | 10 ms |   0 |
| 2   |          95 | 1.2 s | 1.2 s | 10 ms |   0 |
| 3   |          93 | 1.3 s | 1.3 s | 20 ms |   0 |

Median performance score:

```text
93
```

Additional Lighthouse category results:

```text
SEO:            100
Best Practices: 100
Accessibility:   92
```

Production characteristics observed during testing:

- FCP/LCP approximately `1.2–1.7 seconds`
- Total Blocking Time `10–20 ms`
- Cumulative Layout Shift `0`
- Production JS bundle approximately `65 KB gzip`
- CSS approximately `6 KB gzip`
- Normal network payload approximately `193 KiB`

These results indicate that the initial application render is lightweight and visually stable.

---

# Sample Statement

Development/demo statement data is synthetic.

Expected analysis for the standard demonstration statement:

| Metric          |  Result |
| --------------- | ------: |
| Transactions    |      10 |
| Total Debit     |  31,500 |
| Total Credit    | 160,000 |
| Opening Balance |  50,000 |
| Closing Balance | 178,500 |

Expected recurring-payment candidates:

```text
Netflix        2 occurrences
Spotify        2 occurrences
Grocery Store  2 occurrences
```

---

# Local Development

## Clone

```powershell
git clone https://github.com/daniyalsaqib/Statement_Intelligence_Suite_ABL.git
cd Statement_Intelligence_Suite_ABL
```

---

## Create Python Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

## Install Backend Dependencies

```powershell
pip install -r requirements.txt
```

---

## PostgreSQL + pgvector

Enable pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The original local development database was:

```text
statement_intelligence_suite
```

---

## Environment Variables

Create `.env` in the repository root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/statement_intelligence_suite
```

Never commit the real `.env`.

---

## Seed Policy Corpus

From the repository root:

```powershell
python -m backend.seed_policy_documents
```

The seeding workflow replaces the current policy corpus rather than blindly appending duplicate rows.

Expected policy row count:

```text
7
```

---

## Run Backend

```powershell
python -m uvicorn backend.app.main:app --reload
```

Local backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## Run Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Local frontend:

```text
http://localhost:5173
```

---

# Deployment

## Vercel

```text
Framework: Vite
Root Directory: frontend
```

Production frontend environment variable:

```text
VITE_API_BASE_URL=https://pure-temple-45004-09958cbb6652.herokuapp.com
```

Do not place backend secrets inside Vite environment variables.

---

## Heroku

Application:

```text
pure-temple-45004
```

Procfile:

```text
web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Required production configuration:

```text
DATABASE_URL
GROQ_API_KEY
GROQ_MODEL=openai/gpt-oss-20b
```

The production PostgreSQL database has pgvector enabled and contains the 7-row policy demonstration corpus.

---

# Testing

Core backend validation:

```powershell
python -m compileall backend -q
python -m unittest discover -s backend	ests -t . -v
python -m pip check
git diff --check
```

Current automated backend result:

```text
153 tests passed
```

Current regression coverage includes:

```text
API_INPUT_HARDENING_OK
API_FAILURE_HANDLING_OK
DETERMINISTIC_STATEMENT_QA_OK
NATURAL_FINANCIAL_LANGUAGE_OK
MONTH_FILTERING_OK
MULTI_TURN_STATEMENT_FOLLOW_UP_OK
CROSS_CAPABILITY_FOLLOW_UP_OK
RECURRING_PAYMENT_RULES_OK
POLICY_RAG_OK
LLM_TRUST_BOUNDARIES_OK
UNIFIED_ASSISTANT_ROUTING_OK
NUMERIC_GUARD_OK
```

The current backend commit `ebf1a47` passed GitHub Actions CI.

The latest production backend deployment was verified as:

```text
HEROKU_RELEASE_V16_OK
HEALTH_ENDPOINT_OK
UNIFIED_ASSISTANT_SMOKE_OK
CROSS_CAPABILITY_FOLLOW_UP_OK
```

Production mixed-capability regression:

```text
August spending question
        |
        v
Recurring-payment question
        |
        v
"What about July?"
        |
        v
Earlier statement intent recovered
        |
        v
July spending recalculated deterministically
```

Frontend production hardening also includes SEO validation and Lighthouse performance testing.

---

# Reliability & Production Hardening

| Risk / Failure Mode                | Mitigation                                                                 |
| ---------------------------------- | -------------------------------------------------------------------------- |
| LLM quota / availability           | Final LLM path migrated to Groq; failures return controlled backend errors |
| Incorrect LLM financial arithmetic | Financial values are calculated deterministically in Python                |
| Heroku memory pressure             | PyTorch-heavy embedding runtime replaced with FastEmbed / ONNX             |
| Weak policy retrieval              | Distance threshold enforced before generation                              |
| Unsupported policy question        | Fail-closed response instead of hallucinating policy                       |
| Duplicate policy reseeding         | Corpus replacement is handled transactionally                              |
| Statement-format variation         | CSV parser includes validation and format handling                         |
| Frontend discoverability           | SEO metadata, sitemap, robots configuration and structured data added      |
| Frontend loading quality           | Production Lighthouse performance validation completed                     |

---

# Prototype Disclosure

The production interface keeps the following disclosures visible:

> **Internship prototype — not an official Allied Bank customer website.**
>
> **This independent student project is a synthetic-data demonstration created for educational and internship purposes. Do not upload real customer statements, credentials, or confidential information.**

---

# Security and Data Safety

The project is intended for demonstration and internship development.

Use only synthetic/local statement data.

Never commit:

```text
.env
GROQ_API_KEY
DATABASE_URL credentials
database passwords
access tokens
private API keys
real customer/account data
```

Additional constraints:

- No live core-banking connection
- No live Allied Bank customer-account integration
- No confidential internal Allied Bank documents
- Policy Assistant corpus uses public information only
- Uploaded statement data is not stored inside the persistent policy vector database
- API keys should immediately be revoked and rotated if exposed

---

# Known MVP Limitations

- Synthetic/demonstration statement data only
- No live core-banking integration
- No production customer authentication
- CSV-oriented statement workflow
- Recurring-payment results are candidates, not guaranteed subscription classifications
- Policy corpus is intentionally limited
- Public-policy freshness is not automatically synchronized with the Allied Bank website
- Policy RAG is a demonstration corpus rather than a complete representation of every Allied Bank policy

---

# Potential Future Improvements

- PDF statement parsing
- XLSX statement support
- Improved merchant normalization
- Recurring-payment interval classification
- Spending categorization
- Spending charts
- Expanded public-policy ingestion
- Automated policy-corpus synchronization
- Hybrid lexical + vector retrieval
- Reranking
- Authentication
- Role-based access control
- CI/CD improvements
- Production monitoring
- Request tracing and observability

---

# Project Timeline

```text
27 Aug 2026
Development started
10 Sep 2026
Production-functional milestone reached
Core application deployed and regression-tested
15–16 Sep 2026
SEO, social metadata and frontend performance hardening
17–19 Sep 2026
Multi-turn statement conversation work
Unified banking-assistant UX and routing
22 Sep 2026
Natural financial-language hardening
Unified capability-routing hardening
Cross-capability follow-up hardening
153-test backend suite verified
GitHub Actions CI verified
Heroku release v16 verified
25 Sep 2026
Original internship handover window
```

The **10 September milestone** represents completion of the original production-functional application.

The remaining internship period has been used to convert that functional build into a more polished conversational banking-intelligence prototype with stronger deterministic routing, safer multi-turn behavior, broader regression coverage, updated documentation, and production validation.

---

# Current Project Position

The **ABL Customer Statement Intelligence Suite** is currently:

```text
PRODUCTION FUNCTIONAL
UNIFIED ASSISTANT DEPLOYED
153 BACKEND TESTS PASSING
GITHUB ACTIONS CI PASSING
HEROKU RELEASE V16 VERIFIED
SEO HARDENED
PERFORMANCE VALIDATED
FINAL DOCUMENTATION & HANDOVER PREPARATION IN PROGRESS
```

The production application now exposes one unified conversational banking-intelligence experience while retaining three specialized backend capabilities:

```text
Verified Statement Intelligence
Deterministic Recurring-Payment Detection
Grounded Public-Policy RAG
```

The system remains an internship prototype using synthetic statement data and public policy information only.
