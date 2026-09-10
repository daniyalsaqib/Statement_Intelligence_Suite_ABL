# ABL Customer Statement Intelligence Suite

> **App 1 of 2 — Final Production Build**
> **Completed:** 10 September 2026
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

## Final Status

**Status:** Production Functional
**Development period:** 27 Aug 2026 — 10 Sep 2026
**Final stabilization checkpoint:** `64c6189` — `Stabilize Groq agents and optimize policy embeddings`

Final validation included:

- 38/38 automated backend tests passed
- Production statement upload and analysis passed
- Deterministic statement Q&A passed
- Guarded open-ended statement Q&A passed
- Month-specific filtering passed
- Recurring-payment analysis passed
- Policy RAG with public ABL sources passed
- Policy fail-closed behavior passed
- Cloud policy corpus verified at 7 rows
- No new Heroku R14 memory errors during final production regression

---

# Modules

## 1. Statement Intelligence

The Statement Intelligence module accepts a synthetic CSV bank statement, validates it, parses transactions, and calculates verified financial facts.

The backend can calculate:

- Transaction count
- Debit / credit transaction counts
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

Exact banking figures are calculated in **Python**, not by the LLM.

Example:

```text
How much did I spend?
```

For the included sample statement:

```text
31,500.00
```

### Open-ended / compound questions

Open-ended questions use this flow:

```text
User Question
     ↓
Statement Parser
     ↓
Verified Python Financial Facts
     ↓
Groq / GPT-OSS qualitative interpretation
     ↓
Python numeric guard
     ↓
Final grounded answer
```

The verified Python facts are authoritative. The LLM is used for interpretation, not as the source of truth for financial arithmetic.

---

## 2. Recurring Payment Analysis

The recurring-payment module detects repeated outgoing transaction descriptions and returns them as **recurring payment candidates**.

Current rule:

```text
Repeated outgoing description = recurring payment candidate
```

Returned information includes:

- Description
- Number of occurrences
- Amounts
- Dates

For the included sample statement, expected candidates are:

```text
Netflix
Spotify
Grocery Store
```

Expected count:

```text
3
```

These are candidates rather than guaranteed subscriptions. A repeated merchant such as a grocery store can therefore be detected even when it is not a formal subscription.

---

## 3. ABL Policy Assistant

The Policy Assistant is a retrieval-augmented generation system over a curated public Allied Bank corpus.

Final pipeline:

```text
User Policy Question
       ↓
FastEmbed / ONNX
       ↓
all-MiniLM-L6-v2
384-dimensional embedding
       ↓
PostgreSQL + pgvector
       ↓
Vector similarity search
       ↓
Relevance threshold
       ↓
Relevant public ABL chunks
       ↓
Groq / openai/gpt-oss-20b
       ↓
Grounded answer + public sources
```

### Retrieval configuration

- Embedding runtime: **FastEmbed / ONNX**
- Embedding model: **sentence-transformers/all-MiniLM-L6-v2**
- Dimensions: **384**
- Vector store: **PostgreSQL + pgvector**
- Retrieved chunks: up to **3**
- Relevance threshold: **distance <= 0.75**

### Fail-closed behavior

If no policy chunk is sufficiently relevant, the API returns:

```text
I could not find relevant information in the available Allied Bank public policy documents.
```

The assistant is instructed not to invent Allied Bank policies or source URLs.

---

# Public Policy Corpus

The demonstration corpus contains **7 public policy/document chunks**:

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

Gemini was used earlier in development, but production testing exposed availability/free-tier quota reliability problems.

The final application uses:

```text
Groq
openai/gpt-oss-20b
```

Provider-specific code is isolated inside `llm_service.py`, and provider failures are converted to controlled HTTP 502 responses.

## SentenceTransformers / PyTorch → FastEmbed / ONNX

The original embedding runtime used SentenceTransformers/PyTorch and contributed to Heroku memory pressure.

Local benchmarking showed approximately:

```text
SentenceTransformers path: first embedding ≈ 443 MB
FastEmbed path:            first embedding ≈ 203 MB
```

The final implementation keeps the same all-MiniLM-L6-v2 384D model while using FastEmbed/ONNX. The final Heroku release showed no new R14 memory errors during production regression.

## LLM arithmetic → verified Python facts

After an LLM produced an incorrect monthly calculation during testing, exact financial arithmetic was moved fully into deterministic Python code.

Final rule:

```text
Python computes authoritative financial facts.
Groq explains or summarizes those verified facts.
```

---

# Production Architecture

```text
User Browser
     |
     v
Vercel
React + Vite + Tailwind
     |
     | HTTPS / REST
     v
Heroku
FastAPI
     |
     +--------------------+
     |                    |
     v                    v
Statement Services     Policy RAG
     |                    |
     |                    v
     |                FastEmbed
     |                    |
     |                    v
     |             PostgreSQL + pgvector
     |                    |
     +---------> Groq <----+
                  |
                  v
          Grounded Responses
```

---

# Main API Endpoints

### Health

```http
GET /health
```

### Upload statement

```http
POST /statement/upload
```

Input: `multipart/form-data` with a CSV file.

### Ask about statement

```http
POST /statement/ask
```

### Recurring-payment analysis

```http
POST /statement/subscriptions
```

Input: `multipart/form-data` with a CSV file.

### Policy Q&A

```http
POST /policy/ask
```

Responses include the answer and relevant public ABL source links.

---

# Sample Statement

Included file:

```text
backend/data/sample_statement.csv
```

Expected analysis:

| Metric | Result |
|---|---:|
| Transactions | 10 |
| Total Debit | 31,500 |
| Total Credit | 160,000 |
| Opening Balance | 50,000 |
| Closing Balance | 178,500 |

Expected recurring candidates:

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

## Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## Install backend dependencies

```powershell
pip install -r requirements.txt
```

## PostgreSQL + pgvector

Enable pgvector in the project database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The original local development database was:

```text
statement_intelligence_suite
```

## Environment variables

Create `.env` in the repository root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/statement_intelligence_suite
```

Never commit the real `.env`.

## Seed the Policy corpus

Run from the repository root:

```powershell
python -m backend.seed_policy_documents
```

The final seeding flow replaces the existing corpus rather than blindly appending duplicate copies.

Expected row count:

```text
7
```

## Run backend

```powershell
python -m uvicorn backend.app.main:app --reload
```

Local backend:

```text
http://127.0.0.1:8000
```

## Run frontend

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

Production environment variable:

```text
VITE_API_BASE_URL=https://pure-temple-45004-09958cbb6652.herokuapp.com
```

Do not place backend secrets in Vite variables.

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

The production PostgreSQL database has pgvector enabled and contains the 7-row policy corpus.

---

# Testing

Final local validation:

```powershell
python -m compileall backend -q
python -m unittest discover -s backend\tests -t . -v
python -m pip check
git diff --check
```

Final automated result:

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

---

# Security and Data Safety

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

The Policy Assistant should use public Allied Bank information only.

If an API key is printed or otherwise exposed, revoke/rotate it.

---

# Known MVP Limitations

- Synthetic/demonstration statement data only
- No live core-banking integration
- No production customer authentication
- CSV-oriented statement workflow
- Recurring-payment results are candidates, not guaranteed subscription classifications
- Policy corpus is intentionally limited and is not a complete representation of all Allied Bank policies
- Public-policy freshness is not automatically synchronized with the Allied Bank website

---

# Potential Future Improvements

- PDF statement parsing
- XLSX statement support
- Improved merchant normalization
- Recurring-payment interval classification
- Spending categorization and charts
- Expanded / automated public-policy ingestion
- Hybrid lexical + vector retrieval
- Reranking
- Authentication / RBAC
- CI/CD improvements
- Production monitoring

---

# Project Completion

The **ABL Customer Statement Intelligence Suite — App 1 of 2** reached its final production-functional milestone on:

```text
10 September 2026
```

All three modules were successfully demonstrated through the deployed Vercel frontend and Heroku backend.

**Status: COMPLETED — 10 SEP 2026**
