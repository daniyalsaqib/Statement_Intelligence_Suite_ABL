# ABL Customer Statement Intelligence Suite

> **App 1 of 2 — Production Functional**
>
> **Production-functional milestone:** 10 September 2026
> **Production hardening & documentation phase:** In progress
> **Latest project update:** 16 September 2026
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

**Current status:** Production Functional — production polish and documentation in progress.

The application reached its main **production-functional milestone on 10 September 2026**. At that point, all three application modules were deployed and production-tested.

Work continued after that milestone to improve:

- Search-engine metadata
- Crawler configuration
- Social-sharing metadata
- Project favicon
- Frontend performance validation
- Architecture documentation
- Final handover documentation

The final internship/project handover remains scheduled within the original internship window ending **25 September 2026**.

### Core production validation

The production-functional build passed:

- 38/38 automated backend tests
- Production statement upload and analysis
- Deterministic statement Q&A
- Guarded open-ended statement Q&A
- Month-specific filtering
- Recurring-payment analysis
- Policy RAG with public Allied Bank sources
- Policy fail-closed behavior
- Cloud policy corpus verification at 7 rows
- Production validation without new Heroku R14 memory errors

### Recent production checkpoints

```text
64c6189  Stabilize Groq agents and optimize policy embeddings
54c163f  Remove Allied Bank logo from public application
cb84d32  Add frontend SEO metadata and crawler files
7fa95a1  Add social preview and project favicon
```

---

# Modules

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

> **Layered client-server architecture with a modular FastAPI backend, hybrid deterministic + LLM processing, and a Retrieval-Augmented Generation subsystem.**

It is implemented as a **modular monolith**, not as a microservices architecture.

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
                 | FastAPI Backend         |
                 | Python 3.12             |
                 | Hosted on Heroku        |
                 +------------+------------+
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
      Statement APIs    Statement Q&A      Policy Q&A
             |                |                |
             |                |                |
      +------+-----+          |           FastEmbed
      |            |          |               |
      v            v          v               v
 CSV Parser    Recurring   Verified       MiniLM-L6-v2
      |         Analysis    Python Facts      384D
      v            |          |               |
 Statement         |          |               v
 Analysis          |          |          PostgreSQL
      |            |          |           + pgvector
      v            v          |               |
   Summary      Candidates    |         Semantic Search
                              |               |
                              +-------+-------+
                                      |
                                      v
                                   Groq API
                           openai/gpt-oss-20b
                                      |
                                      v
                               Grounded Answer
```

---

# Architectural Layers

## Presentation Layer

Implemented with:

- React.js
- Tailwind CSS
- Vite

Responsibilities:

- Statement upload UI
- Financial-analysis presentation
- Natural-language question interface
- Recurring-payment presentation
- Policy Assistant interface
- Source-link presentation

Hosted on **Vercel**.

---

## API / Routing Layer

Implemented with **FastAPI**.

Main routers:

```text
backend/app/routers/statements.py
backend/app/routers/statement_qa.py
backend/app/routers/policy_qa.py
```

Responsibilities:

- HTTP request handling
- Input validation
- Routing requests into backend services
- Controlled API errors
- JSON responses

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

| Layer | Technology |
|---|---|
| Frontend | React.js |
| Styling | Tailwind CSS |
| Build Tool | Vite |
| Frontend Hosting | Vercel |
| Backend | FastAPI |
| Backend Language | Python 3.12 |
| Backend Hosting | Heroku |
| LLM Provider | Groq |
| LLM Model | `openai/gpt-oss-20b` |
| Embedding Runtime | FastEmbed / ONNX |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding Dimensions | 384 |
| Database | PostgreSQL |
| Vector Search | pgvector |
| PostgreSQL Driver | psycopg |
| Version Control | Git |
| Repository Hosting | GitHub |

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

## Statement Upload

```text
CSV Upload
    ↓
FastAPI /statement/upload
    ↓
CSV validation
    ↓
statement_parser.py
    ↓
Structured transactions
    ↓
statement_analysis.py
    ↓
Financial summary
    ↓
JSON response
```

---

## Statement Question

```text
User Question + Statement Data
           ↓
POST /statement/ask
           ↓
Question filtering / month extraction
           ↓
Is it a simple exact question?
       /             \
     Yes              No
      |                |
      v                v
Deterministic      Verified Python
Python Answer         Facts
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

---

## Recurring Payment Analysis

```text
CSV Upload
    ↓
POST /statement/subscriptions
    ↓
Statement Parser
    ↓
Debit transactions
    ↓
Description normalization
    ↓
Group matching descriptions
    ↓
Repeated description?
    ↓
Recurring-payment candidate
```

---

## Policy Assistant

```text
Policy Question
      ↓
POST /policy/ask
      ↓
FastEmbed query embedding
      ↓
MiniLM 384D vector
      ↓
PostgreSQL + pgvector
      ↓
Top 3 vector matches
      ↓
Distance <= 0.75
      ↓
Relevant context
      ↓
Groq
      ↓
Grounded answer
      ↓
Public source links
```

---

# Main API Endpoints

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

## Ask About Statement

```http
POST /statement/ask
```

---

## Recurring-Payment Analysis

```http
POST /statement/subscriptions
```

Input:

```text
multipart/form-data
CSV file
```

---

## Policy Q&A

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

| Run | Performance | FCP | LCP | TBT | CLS |
|---|---:|---:|---:|---:|---:|
| 1 | 89 | 1.7 s | 1.7 s | 10 ms | 0 |
| 2 | 95 | 1.2 s | 1.2 s | 10 ms | 0 |
| 3 | 93 | 1.3 s | 1.3 s | 20 ms | 0 |

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

| Metric | Result |
|---|---:|
| Transactions | 10 |
| Total Debit | 31,500 |
| Total Credit | 160,000 |
| Opening Balance | 50,000 |
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
python -m unittest discover -s backend\tests -t . -v
python -m pip check
git diff --check
```

Automated backend result at the production-functional checkpoint:

```text
38 tests passed
```

Production regression verified:

```text
PRODUCTION_UPLOAD_OK
PRODUCTION_DETERMINISTIC_QA_OK
PRODUCTION_GUARDED_QA_OK
PRODUCTION_MONTH_FILTER_OK
PRODUCTION_RECURRING_OK
NO_R14_ON_CURRENT_RELEASE
PRODUCTION_REGRESSION_COMPLETE
```

Frontend production hardening later added SEO validation and Lighthouse performance testing.

---

# Reliability & Production Hardening

| Risk / Failure Mode | Mitigation |
|---|---|
| LLM quota / availability | Final LLM path migrated to Groq; failures return controlled backend errors |
| Incorrect LLM financial arithmetic | Financial values are calculated deterministically in Python |
| Heroku memory pressure | PyTorch-heavy embedding runtime replaced with FastEmbed / ONNX |
| Weak policy retrieval | Distance threshold enforced before generation |
| Unsupported policy question | Fail-closed response instead of hallucinating policy |
| Duplicate policy reseeding | Corpus replacement is handled transactionally |
| Statement-format variation | CSV parser includes validation and format handling |
| Frontend discoverability | SEO metadata, sitemap, robots configuration and structured data added |
| Frontend loading quality | Production Lighthouse performance validation completed |

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

16 Sep 2026
Architecture review and final documentation phase started

25 Sep 2026
Original internship handover window
```

The **10 September milestone represents completion of the production-functional application**, while the remaining internship period is being used for production polish, architecture documentation, validation, and final handover preparation.

---

# Current Project Position

The **ABL Customer Statement Intelligence Suite — App 1 of 2** is currently:

```text
PRODUCTION FUNCTIONAL
SEO HARDENED
PERFORMANCE VALIDATED
ARCHITECTURE DOCUMENTATION IN PROGRESS
FINAL HANDOVER PREPARATION IN PROGRESS
```

All three core modules are deployed and functional through the Vercel frontend and FastAPI/Heroku backend.
