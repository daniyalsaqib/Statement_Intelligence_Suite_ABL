# ABL Customer Statement Intelligence Suite

An agentic AI-powered banking intelligence application developed as part of the **Allied Bank Internship Program (ABIP)**.

The system demonstrates how artificial intelligence, semantic search, retrieval-augmented generation (RAG), and structured financial-data analysis can be combined into a modern banking-oriented web application.

The application contains three major modules:

1. **Statement Intelligence**
2. **Recurring Payment Analysis**
3. **ABL Policy Assistant**

The project uses **synthetic/local account statement data only** and publicly available Allied Bank policy information. It does not connect to live Allied Bank customer accounts, production banking systems, or confidential internal banking data.

---

# Project Information

**Project:** ABL Customer Statement Intelligence Suite  
**Organization:** Allied Bank Limited  
**Program:** Allied Bank Internship Program (ABIP)  
**Developer:** Daniyal Saqib  
**Role:** IT Intern  
**Project Sponsor / Reviewer:** Sir Affan Wahid  
**Development Period:** August–September 2026

---

# Live Application

## Frontend

Production frontend:

https://statement-intelligence-suite-abl.vercel.app

Hosted using **Vercel**.

## Backend

Production backend:

https://pure-temple-45004-09958cbb6652.herokuapp.com

Hosted using **Heroku**.

### Backend Health Check

https://pure-temple-45004-09958cbb6652.herokuapp.com/health

Expected response:

```json
{
  "status": "ok"
}
```

### Swagger API Documentation

https://pure-temple-45004-09958cbb6652.herokuapp.com/docs

---

# Main Features

## 1. Statement Intelligence

The Statement Intelligence module allows a synthetic CSV bank statement to be uploaded and analyzed.

The backend:

- Reads the uploaded CSV.
- Parses each transaction.
- Validates transaction structure.
- Calculates statement statistics.
- Returns structured transaction information to the frontend.

The module currently calculates:

- Number of transactions
- Total debit
- Total credit
- Opening balance
- Closing balance

After the statement is analyzed, the user can ask natural-language questions about it.

Example:

```text
How much did I spend in total?
```

The statement data and question are sent to the AI agent, which is instructed to answer using only the supplied statement.

---

## 2. Statement Q&A Agent

The Statement Q&A Agent allows natural-language interaction with an uploaded synthetic account statement.

Flow:

```text
CSV Statement
     ↓
Statement Parser
     ↓
Structured Transactions
     ↓
User Question
     ↓
Statement Q&A Agent
     ↓
Gemini
     ↓
Grounded Answer
```

The statement transactions are passed as context to the model.

The prompt explicitly instructs the model to answer using only the statement data supplied to it.

Example question:

```text
How much did I spend in total?
```

Using the included sample statement, the expected total debit is:

```text
31,500
```

---

# 3. Recurring Payment Analysis

The Recurring Payment Analysis module detects repeated outgoing payment patterns from the uploaded statement.

The current implementation groups debit transactions using their normalized transaction descriptions.

A description appearing more than once is returned as a **recurring payment candidate**.

For example:

```text
Netflix
Spotify
Grocery Store
```

The application displays:

- Description
- Number of occurrences
- Amounts
- Dates

## Important Limitation

The current recurring-payment algorithm is intentionally simple.

It detects:

```text
Repeated outgoing description = recurring candidate
```

This means that a repeated merchant such as a grocery store can also be detected even though it may not represent a formal subscription.

A future implementation could improve classification using:

- Date intervals
- Amount similarity
- Merchant normalization
- Transaction categories
- Machine-learning classification
- LLM-assisted classification

---

# 4. ABL Policy Assistant

The ABL Policy Assistant is a **Retrieval-Augmented Generation (RAG)** system.

It answers questions using a small knowledge base constructed from publicly available Allied Bank information.

Example:

```text
What documents do I need to claim an unclaimed deposit?
```

The system retrieves semantically relevant policy chunks and supplies them to Gemini as context.

The generated answer is accompanied by source references.

---

# Policy RAG Architecture

The policy assistant follows this pipeline:

```text
User Question
      ↓
Sentence Transformer
      ↓
384-Dimensional Query Embedding
      ↓
PostgreSQL + pgvector
      ↓
Vector Similarity Search
      ↓
Relevant ABL Policy Chunks
      ↓
Gemini AI
      ↓
Grounded Answer + Sources
```

---

# Embedding Model

The application uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Properties:

- Open source
- Runs locally
- Lightweight compared with larger embedding models
- Produces **384-dimensional embeddings**
- Suitable for semantic similarity search

The embedding model does not require a paid embedding API.

---

# Vector Database

Vector storage is implemented using:

```text
PostgreSQL + pgvector
```

Instead of introducing another standalone vector database, PostgreSQL stores both document information and vector embeddings.

The policy table contains fields similar to:

```text
id
title
source
content
embedding
```

The embedding column is:

```text
vector(384)
```

---

# Semantic Search

When a policy question is submitted:

1. The question is converted into a 384-dimensional embedding.
2. PostgreSQL/pgvector compares it against stored policy embeddings.
3. The nearest policy chunks are retrieved.
4. Retrieved chunks are filtered by semantic distance.
5. Relevant context is sent to Gemini.

The current relevance threshold is:

```text
distance <= 0.75
```

The search currently retrieves up to:

```text
3 policy chunks
```

---

# Fail-Closed Policy Behaviour

The Policy Assistant is intentionally designed to avoid answering unsupported Allied Bank policy questions.

If no retrieved policy chunk satisfies the relevance threshold, the API returns:

```text
I could not find relevant information in the available Allied Bank public policy documents.
```

The system therefore attempts to avoid inventing an Allied Bank policy when its local public-policy knowledge base does not contain sufficient relevant information.

Gemini is additionally instructed:

- Use only retrieved policy context.
- Do not use outside knowledge.
- Do not invent Allied Bank policies.
- Do not invent source URLs.
- State when the available context is insufficient.

---

# Public Policy Knowledge Base

The current demonstration corpus contains **7 policy/document chunks**.

They cover topics including:

1. Account and Electronic Banking Terms
2. Changes to Terms and Conditions
3. Financial Consumer Protection Framework
4. Customer Complaints and Confidentiality
5. Unclaimed Deposit Refund
6. Unclaimed Deposit Required Documents
7. Schedule of Charges

The policy material is based on publicly accessible Allied Bank information.

Example public sources include:

```text
https://www.abl.com/terms/
https://www.abl.com/services/financial-consumer-protection-framework/
https://www.abl.com/services/downloads/deposit-guidelines/
https://www.abl.com/services/downloads/schedule-of-charges/
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React.js |
| Styling | Tailwind CSS |
| Frontend Build Tool | Vite |
| Frontend Hosting | Vercel |
| Backend | FastAPI |
| Backend Language | Python |
| Backend Hosting | Heroku |
| LLM | Google Gemini 3.8 Flash |
| Embeddings | Sentence Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Database | PostgreSQL |
| Vector Extension | pgvector |
| ORM/DB Driver | psycopg |
| Version Control | Git |
| Repository Hosting | GitHub |

---

# Why These Technologies Were Used

## React.js

React provides a component-based frontend architecture and makes interactive application interfaces easier to maintain.

## Tailwind CSS

Tailwind allows rapid UI development using utility classes and is used for the Allied Bank-inspired blue/orange interface.

## Vite

Vite provides a lightweight development server and optimized production frontend builds.

## FastAPI

FastAPI provides:

- Python-based backend development
- Automatic API validation
- Pydantic integration
- Automatic Swagger documentation
- Straightforward AI/ML integration

## Heroku

Heroku provides a straightforward deployment platform for the Python backend and managed PostgreSQL database.

## Gemini

Gemini provides the natural-language reasoning/generation layer for:

- Statement Q&A
- Policy Q&A

The originally planned model was Gemini 3.7 Flash. During implementation, Gemini 3.7 experienced availability/high-demand problems, so the working implementation was moved to **Gemini 3.8 Flash**.

## Sentence Transformers

Sentence Transformers provides local semantic embeddings without requiring a paid embedding service.

## PostgreSQL

PostgreSQL provides reliable relational storage and can also support vector search through pgvector.

## pgvector

pgvector allows embedding vectors to be stored and searched directly inside PostgreSQL.

---

# High-Level Architecture

```text
                         ┌───────────────────────────┐
                         │      React Frontend       │
                         │      Vite + Tailwind      │
                         └─────────────┬─────────────┘
                                       │
                                       │ HTTPS / REST
                                       ↓
                         ┌───────────────────────────┐
                         │      FastAPI Backend      │
                         └─────────────┬─────────────┘
                                       │
              ┌────────────────────────┼──────────────────────┐
              │                        │                      │
              ↓                        ↓                      ↓
     Statement Intelligence    Recurring Analysis     Policy RAG Agent
              │                        │                      │
              ↓                        ↓                      ↓
       Statement Parser       Pattern Detection      MiniLM Embeddings
              │                                               │
              ↓                                               ↓
         Gemini Q&A                                PostgreSQL + pgvector
                                                              │
                                                              ↓
                                                      Relevant Context
                                                              │
                                                              ↓
                                                           Gemini
                                                              │
                                                              ↓
                                                    Answer + Sources
```

---

# Repository Structure

The important project structure is:

```text
Statement_Intelligence_Suite_ABL_2/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── models/
│   │   │   └── statement.py
│   │   │
│   │   ├── services/
│   │   │   ├── statement_parser.py
│   │   │   ├── statement_analysis.py
│   │   │   ├── gemini_service.py
│   │   │   ├── subscription_analysis.py
│   │   │   └── embedding_service.py
│   │   │
│   │   ├── routers/
│   │   │   ├── statements.py
│   │   │   ├── statement_qa.py
│   │   │   └── policy_qa.py
│   │   │
│   │   ├── agents/
│   │   │
│   │   └── db/
│   │       └── policy_vector_store.py
│   │
│   ├── data/
│   │   ├── sample_statement.csv
│   │   └── policy_corpus.py
│   │
│   ├── seed_policy_documents.py
│   └── tests/
│
├── frontend/
│   ├── public/
│   │   └── daniyal-signature.png
│   │
│   ├── src/
│   │   ├── App.jsx
│   │   └── index.css
│   │
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── .env
├── .gitignore
├── .python-version
├── requirements.txt
├── Procfile
├── README.md
├── App2_Statement_Intelligence_Suite.pdf
└── WorkPlanForAICHATBOT.pdf
```

`.venv` is normally also present locally but is excluded from Git.

---

# Backend API Endpoints

The backend currently exposes the following main endpoints.

## Health Check

```http
GET /health
```

Example:

```json
{
  "status": "ok"
}
```

---

## Upload and Analyze Statement

```http
POST /statement/upload
```

Input:

```text
multipart/form-data
file = CSV statement
```

The endpoint:

1. Verifies that the uploaded file is a CSV.
2. Reads the file.
3. Parses transactions.
4. Calculates statement statistics.
5. Returns the parsed transactions and analysis.

---

## Statement Q&A

```http
POST /statement/ask
```

Example request:

```json
{
  "question": "How much did I spend in total?",
  "statement_data": [
    {
      "date": "2026-07-02",
      "description": "Netflix",
      "debit": 1500,
      "credit": null,
      "balance": 48500
    }
  ]
}
```

The endpoint passes the question and supplied statement data to Gemini.

---

## Recurring Payment Analysis

```http
POST /statement/subscriptions
```

Input:

```text
multipart/form-data
file = CSV statement
```

The response contains:

```text
filename
recurring_payment_count
recurring_payments
```

---

## Policy Q&A

```http
POST /policy/ask
```

Example request:

```json
{
  "question": "What documents do I need to claim an unclaimed deposit?"
}
```

Example response structure:

```json
{
  "question": "What documents do I need to claim an unclaimed deposit?",
  "answer": "Grounded policy answer...",
  "sources": [
    {
      "title": "Unclaimed Deposit Required Documents",
      "url": "https://www.abl.com/services/downloads/deposit-guidelines/"
    }
  ]
}
```

---

# Sample Statement

A synthetic demonstration statement is included at:

```text
backend/data/sample_statement.csv
```

Current sample:

```csv
date,description,debit,credit,balance
2026-07-01,Opening Balance,,,50000
2026-07-02,Netflix,1500,,48500
2026-07-03,Salary,,80000,128500
2026-07-05,Electricity Bill,12000,,116500
2026-07-10,Spotify,500,,116000
2026-07-15,Grocery Store,7500,,108500
2026-08-02,Netflix,1500,,107000
2026-08-03,Salary,,80000,187000
2026-08-10,Spotify,500,,186500
2026-08-15,Grocery Store,8000,,178500
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
Netflix       2 occurrences
Spotify       2 occurrences
Grocery Store 2 occurrences
```

---

# Local Development Setup

The following instructions explain how to run the complete project locally.

## 1. Clone the Repository

```powershell
git clone https://github.com/daniyalsaqib/Statement_Intelligence_Suite_ABL.git
cd Statement_Intelligence_Suite_ABL
```

The author's original development location was:

```text
D:\Statement_Intelligence_Suite_ABL_2
```

The `_2` suffix is only the local folder name and is not part of the public GitHub repository name.

---

# 2. Python Version

The project was developed using:

```text
Python 3.12
```

The repository contains:

```text
.python-version
```

with:

```text
3.12
```

Check Python:

```powershell
python --version
```

---

# 3. Create a Virtual Environment

From the project root:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents script execution for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

When activated, PowerShell should show:

```text
(.venv)
```

---

# 4. Install Python Dependencies

From the project root:

```powershell
pip install -r requirements.txt
```

The project includes the CPU build of PyTorch rather than CUDA/GPU packages because the embedding model does not require GPU acceleration for this demonstration.

This is particularly important for Heroku deployment because GPU/CUDA dependencies dramatically increase deployment slug size.

---

# 5. Install PostgreSQL

Install PostgreSQL and ensure the PostgreSQL service is running.

The original development environment used:

```text
PostgreSQL 17
Port 5432
```

Check PostgreSQL using:

```powershell
psql --version
```

---

# 6. Create the Local Database

Create a PostgreSQL database named:

```text
statement_intelligence_suite
```

Example from PostgreSQL:

```sql
CREATE DATABASE statement_intelligence_suite;
```

Connect to it:

```sql
\c statement_intelligence_suite
```

---

# 7. Install and Enable pgvector

The project requires the PostgreSQL `vector` extension.

After pgvector has been installed for your PostgreSQL installation, connect to the project database and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Verify:

```sql
SELECT extname
FROM pg_extension
WHERE extname = 'vector';
```

Expected:

```text
vector
```

---

# 8. Configure Environment Variables

Create:

```text
.env
```

in the project root.

Example:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/statement_intelligence_suite
```

Do **not** commit the real `.env` file.

The `.gitignore` is configured to exclude environment files and credentials.

Never place:

```text
GEMINI_API_KEY
DATABASE_URL
database passwords
API credentials
```

inside frontend source code.

---

# 9. Seed the Policy Knowledge Base

After PostgreSQL, pgvector, `.env`, and Python dependencies are configured, seed the policy corpus.

Run this from the **project root**:

```powershell
python -m backend.seed_policy_documents
```

Do not run:

```powershell
python backend\seed_policy_documents.py
```

because the package imports are designed to run from the project root using Python's module execution syntax.

A successful run stores the policy chunks in PostgreSQL.

To verify using SQL:

```sql
SELECT COUNT(*) FROM policy_documents;
```

For the current corpus, the expected result is:

```text
7
```

## Important

The current seeding script inserts documents.

Do not repeatedly run it against an already-seeded database unless you intend to insert another copy of the corpus.

---

# 10. Run the FastAPI Backend

Make sure:

- Virtual environment is active.
- PostgreSQL is running.
- `.env` exists.
- Policy database has been seeded.

From the **project root**:

```powershell
uvicorn backend.app.main:app --reload
```

The backend should become available at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# 11. Install Frontend Dependencies

Open another PowerShell terminal.

Move into:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

---

# 12. Run the React Frontend

From the `frontend` directory:

```powershell
npm run dev
```

The Vite development server normally runs at:

```text
http://localhost:5173
```

Open this URL in a browser.

---

# Important Working-Directory Rule

This project has two different working directories.

## FastAPI / Python commands

Run them from:

```text
Statement_Intelligence_Suite_ABL/
```

Example:

```powershell
uvicorn backend.app.main:app --reload
```

## React / npm commands

Run them from:

```text
Statement_Intelligence_Suite_ABL/frontend/
```

Example:

```powershell
npm run dev
```

If `npm run dev` is accidentally executed from the repository root, npm may report an error similar to:

```text
ENOENT
Could not find package.json
```

Solution:

```powershell
cd frontend
npm run dev
```

---

# Local Quick Start

For someone returning to this project later, the normal startup sequence is:

## Terminal 1 — Backend

```powershell
cd D:\Statement_Intelligence_Suite_ABL_2

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

.\.venv\Scripts\Activate.ps1

uvicorn backend.app.main:app --reload
```

Then verify:

```text
http://127.0.0.1:8000/health
```

---

## Terminal 2 — Frontend

```powershell
cd D:\Statement_Intelligence_Suite_ABL_2\frontend

npm run dev
```

Then open:

```text
http://localhost:5173
```

You normally do **not** need to reinstall dependencies, recreate the database, or reseed the policy corpus every time you start the project.

---

# Frontend API Configuration

The frontend uses:

```javascript
const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
```

Therefore:

- Local development falls back to FastAPI on port `8000`.
- Production can use the Vercel `VITE_API_BASE_URL` environment variable.

---

# Frontend Production Build

From:

```text
frontend/
```

run:

```powershell
npm run build
```

Vite generates the optimized production application in:

```text
frontend/dist/
```

A successful build should complete without compilation errors.

---

# Frontend Design

The final frontend uses an Allied Bank-inspired visual architecture based around:

- Allied Bank blue
- Allied Bank orange
- White/light neutral content surfaces
- Banking-oriented navigation
- Module-based workflow
- Modern summary cards
- Upload panels
- AI response panels
- Policy source references
- Synthetic-data disclaimers

The application includes three primary navigation modules:

```text
Statement Intelligence
Recurring Payments
ABL Policy Assistant
```

The footer identifies:

```text
Daniyal Saqib
IT Intern • ABIP
```

and includes the developer signature asset:

```text
frontend/public/daniyal-signature.png
```

---

# AI Answer Formatting

The frontend includes lightweight formatting for common AI response syntax, including:

```markdown
**bold text**
```

and simple bullet-style output.

This prevents raw Markdown markers such as:

```text
**31,500**
```

from appearing directly in the final interface.

---

# Production Deployment Architecture

```text
User Browser
     │
     ↓
Vercel
React + Vite Frontend
     │
     │ HTTPS API Requests
     ↓
Heroku
FastAPI Backend
     │
     ├─────────────→ Gemini API
     │
     └─────────────→ Heroku PostgreSQL
                           │
                           ↓
                        pgvector
```

---

# Heroku Backend Deployment

The Heroku application is:

```text
pure-temple-45004
```

The repository contains a `Procfile`:

```text
web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Heroku supplies the `$PORT` value dynamically.

---

# Heroku Environment Variables

The production backend requires:

```text
DATABASE_URL
GEMINI_API_KEY
```

`DATABASE_URL` is automatically attached when using Heroku Postgres.

The Gemini key must be configured as a Heroku config variable.

Do not commit either value to GitHub.

---

# Heroku PostgreSQL

The production application uses managed Heroku PostgreSQL.

The production database has the `vector` extension enabled:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The policy corpus has also been seeded into the production database.

Expected policy row count:

```text
7
```

---

# Heroku Python Version

The root `.python-version` contains:

```text
3.12
```

This prevents the deployment platform from selecting an unintended newer Python runtime.

---

# PyTorch / Heroku Deployment Note

An earlier deployment attempted to install standard PyTorch packages that pulled large CUDA/NVIDIA dependencies.

The resulting deployment slug became approximately:

```text
3 GB
```

which exceeded Heroku's slug limit.

The project was corrected to use the **CPU-only PyTorch distribution**.

The requirements configuration includes the PyTorch CPU package index and CPU build.

This dramatically reduced the deployment size.

The successful backend deployment produced a slug of approximately:

```text
394 MB
```

If a future dependency update suddenly installs packages such as:

```text
nvidia-cublas
nvidia-cudnn
CUDA
Triton GPU dependencies
```

check the PyTorch installation first.

This application does not need CUDA for its current MiniLM workload.

---

# Vercel Deployment

The frontend is deployed through Vercel using the GitHub repository.

Important Vercel configuration:

## Framework

```text
Vite
```

## Root Directory

```text
frontend
```

This is important because the repository contains both FastAPI and React.

If Vercel uses the repository root, it may incorrectly detect the backend instead of the frontend.

---

# Vercel Environment Variable

Production uses:

```text
VITE_API_BASE_URL
```

Value:

```text
https://pure-temple-45004-09958cbb6652.herokuapp.com
```

Do not add backend secrets such as:

```text
GEMINI_API_KEY
DATABASE_URL
```

to frontend/Vite environment variables.

Values prefixed with `VITE_` are exposed to frontend code.

---

# CORS

FastAPI allows the local frontend origins:

```text
http://localhost:5173
http://127.0.0.1:5173
```

and the production frontend:

```text
https://statement-intelligence-suite-abl.vercel.app
```

If the production frontend domain changes, update the FastAPI CORS configuration.

Otherwise browser requests may fail even if both the frontend and backend are independently online.

---

# GitHub Repository

Repository:

```text
https://github.com/daniyalsaqib/Statement_Intelligence_Suite_ABL
```

The local development folder is:

```text
D:\Statement_Intelligence_Suite_ABL_2
```

These names are intentionally different.

---

# Git Workflow

After completing a logical development milestone:

```powershell
git status
git add .
git commit -m "Describe the milestone"
git push origin main
```

Because Vercel is connected to the GitHub repository, frontend changes pushed to `main` can automatically trigger a new Vercel deployment.

Backend changes must also be deployed to Heroku when required.

Example:

```powershell
git push heroku main
```

---

# Important Git Checkpoints

Some major development checkpoints include:

```text
a106f43  Initial project setup + adding affan bhai in repo
caf8ba7  Add basic statement analysis for debit credit and balances
aef6874  Update README with current project progress
735d877  Implement AI agents, recurring analysis and policy RAG
f85bfda  Add React frontend and complete local application integration
4974c93  Add Heroku deployment configuration
3e08b68  Optimize Heroku Python deployment
f9e2196  Configure frontend API base for deployment
1baf4f0  Allow Vercel frontend in production CORS
6244ef7  Polish Allied Bank frontend branding and signature
```

---

# Security and Data Safety

This project is a demonstration system.

## Statement Data

The project uses:

```text
synthetic/local statement data
```

No real Allied Bank customer statements should be committed to this repository or used for public demonstrations.

## Policy Data

The Policy Assistant uses publicly available Allied Bank information.

Do not add:

- Confidential internal policies
- Private banking documentation
- Customer information
- Employee credentials
- Production system information

without proper authorization.

## Secrets

Never commit:

```text
.env
GEMINI_API_KEY
DATABASE_URL credentials
database passwords
access tokens
private API keys
```

---

# Statement Data Persistence

The intended project architecture does not require uploaded synthetic statement information to be stored permanently in a database.

Statement data is processed for the active workflow and supplied to the relevant analysis/Q&A functions.

This keeps the statement demonstration separate from the persistent policy vector knowledge base.

---

# Troubleshooting

## `npm run dev` says package.json cannot be found

You are probably in the wrong directory.

Use:

```powershell
cd frontend
npm run dev
```

---

## FastAPI module cannot be found

Run the backend from the project root:

```powershell
cd D:\Statement_Intelligence_Suite_ABL_2
uvicorn backend.app.main:app --reload
```

---

## Policy seeding reports import errors

Use:

```powershell
python -m backend.seed_policy_documents
```

from the repository root.

Do not run the file directly.

---

## PostgreSQL connection fails

Check:

1. PostgreSQL service is running.
2. `DATABASE_URL` is correct.
3. Database exists.
4. Username/password are correct.
5. Port `5432` is available.

---

## `vector` extension error

Verify pgvector is installed and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

inside the correct database.

---

## Policy Assistant returns no relevant information

Possible causes:

- Policy table is empty.
- Corpus was not seeded.
- pgvector is unavailable.
- Question is outside the current seven-document knowledge base.
- Retrieved semantic distance exceeds `0.75`.

Check:

```sql
SELECT COUNT(*) FROM policy_documents;
```

Expected:

```text
7
```

---

## Gemini API key is not configured

Check `.env` locally:

```env
GEMINI_API_KEY=...
```

For Heroku:

```powershell
heroku config -a pure-temple-45004
```

Do not paste or publish the actual key.

---

## Gemini returns availability/high-demand errors

The application originally targeted Gemini 3.7 Flash but moved to Gemini 3.8 Flash after availability issues.

Check the configured model and current Gemini service availability if this occurs again.

---

## Browser shows a CORS error

Check that the frontend URL is present in:

```python
allow_origins
```

inside the FastAPI CORS configuration.

For local development:

```text
http://localhost:5173
http://127.0.0.1:5173
```

For production:

```text
https://statement-intelligence-suite-abl.vercel.app
```

---

## Vercel deploys the wrong application

Set:

```text
Root Directory = frontend
Framework = Vite
```

The repository contains both frontend and backend code.

---

## Frontend calls localhost after production deployment

Check the Vercel environment variable:

```text
VITE_API_BASE_URL
```

It should point to:

```text
https://pure-temple-45004-09958cbb6652.herokuapp.com
```

Then redeploy the frontend.

---

## Heroku slug is too large

Check whether PyTorch has installed CUDA/NVIDIA packages.

The project is designed to use CPU-only PyTorch.

Large GPU packages are unnecessary for this application.

---

## Hugging Face model downloads during startup

`all-MiniLM-L6-v2` may need to be downloaded when first initialized in a fresh environment.

Initial startup can therefore take longer than subsequent model use.

---

# Testing Checklist

## Backend

Check:

```text
GET /health
```

Expected:

```json
{"status":"ok"}
```

---

## Statement Analysis

Upload:

```text
backend/data/sample_statement.csv
```

Expected:

```text
Transactions:    10
Total Debit:     31500
Total Credit:    160000
Opening Balance: 50000
Closing Balance: 178500
```

---

## Statement Q&A

Ask:

```text
How much did I spend in total?
```

Expected core answer:

```text
31,500
```

---

## Recurring Payments

Expected candidates:

```text
Netflix
Spotify
Grocery Store
```

Expected count:

```text
3
```

---

## Policy Assistant

Ask:

```text
What documents do I need to claim an unclaimed deposit?
```

The response should discuss documents such as:

- Signed application containing account information
- Valid identification such as CNIC
- Additional documentation for deceased customers where applicable

and return public Allied Bank source references.

---

# Production Verification

The following complete production flow has been successfully tested:

```text
Browser
  ↓
Vercel React Frontend
  ↓
Heroku FastAPI Backend
  ↓
Statement Services / RAG
  ↓
Heroku PostgreSQL + pgvector
  ↓
Gemini
  ↓
Frontend Result
```

The following modules were verified after deployment:

- Statement upload and analysis
- Statement Q&A
- Recurring payment analysis
- Policy RAG Q&A
- Policy source references

---

# Known Limitations

The current application is a demonstration/MVP and has several intentional limitations.

## Statement Format

Only the expected CSV structure is currently supported.

A production implementation would require robust support for:

- Different statement formats
- PDFs
- XLSX
- Different column names
- Different date formats
- Currency formats
- Invalid/missing rows

## Recurring Payment Detection

Current detection is description-based and does not guarantee that a recurring candidate is a true subscription.

## Policy Corpus

The RAG knowledge base contains only a small curated set of public Allied Bank policy/document chunks.

It is not a complete representation of all Allied Bank products, terms, policies, or procedures.

## Authentication

The demonstration does not implement production customer authentication or authorization.

## Live Banking Integration

There is no live Allied Bank core-banking integration.

## Customer Data

The system is not intended to process real customer information in its current demonstration configuration.

---

# Potential Future Improvements

Possible future development includes:

- PDF statement parsing
- XLSX statement support
- Improved merchant normalization
- ML/AI subscription classification
- Recurring-payment interval detection
- Spending categorization
- Monthly spending trends
- Interactive charts
- Conversation history
- Expanded Allied Bank public-document corpus
- Automated policy ingestion
- Metadata-based RAG filtering
- Hybrid lexical + vector search
- Reranking retrieved documents
- Improved citation rendering
- User authentication
- Role-based access control
- Audit logging
- Automated tests
- Docker deployment
- CI/CD pipeline
- Production monitoring
- Improved accessibility
- Mobile optimization

---

# How to Resume This Project Months Later

If the development environment already exists:

## 1. Start PostgreSQL

Ensure the PostgreSQL service is running.

## 2. Open backend terminal

```powershell
cd D:\Statement_Intelligence_Suite_ABL_2
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload
```

## 3. Check backend

Open:

```text
http://127.0.0.1:8000/health
```

## 4. Open frontend terminal

```powershell
cd D:\Statement_Intelligence_Suite_ABL_2\frontend
npm run dev
```

## 5. Open application

```text
http://localhost:5173
```

## 6. Test using

```text
backend/data/sample_statement.csv
```

That is normally all that is required to resume local development.

---

# Rebuilding From a Fresh Computer

For a completely fresh environment:

```text
1. Install Git
2. Install Python 3.12
3. Install Node.js/npm
4. Install PostgreSQL
5. Install pgvector
6. Clone repository
7. Create Python virtual environment
8. Install requirements.txt
9. Create PostgreSQL database
10. Create .env
11. Enable vector extension
12. Seed policy corpus
13. npm install inside frontend
14. Start FastAPI
15. Start Vite
16. Test sample statement
```

---

# Data Disclaimer

This project was created for development, learning, demonstration, and internship purposes.

**No real customer banking data is included in the repository.**

Statement examples are synthetic/local.

The ABL Policy Assistant is based on a limited set of publicly available Allied Bank information and must not be treated as a complete or authoritative substitute for official Allied Bank policies, staff guidance, contractual documentation, or regulatory requirements.

For authoritative banking information, consult official Allied Bank channels and documentation.

---

# Author

**Daniyal Saqib**  
IT Intern — Allied Bank Internship Program (ABIP)

GitHub:

```text
https://github.com/daniyalsaqib
```

Project repository:

```text
https://github.com/daniyalsaqib/Statement_Intelligence_Suite_ABL
```

---

# Project Status

**App 2 — ABL Customer Statement Intelligence Suite**

```text
Statement parsing                    COMPLETE
Statement analysis                   COMPLETE
Statement Q&A Agent                  COMPLETE
Recurring payment analysis           COMPLETE
Sentence Transformer embeddings      COMPLETE
PostgreSQL integration               COMPLETE
pgvector integration                 COMPLETE
Public ABL policy corpus             COMPLETE
Semantic retrieval                   COMPLETE
Policy RAG Agent                     COMPLETE
Gemini integration                   COMPLETE
React frontend                       COMPLETE
Allied Bank-inspired UI              COMPLETE
Heroku backend deployment            COMPLETE
Heroku PostgreSQL deployment         COMPLETE
Vercel frontend deployment           COMPLETE
Production end-to-end testing        COMPLETE
```

**Current status: Functionally complete and deployed.**