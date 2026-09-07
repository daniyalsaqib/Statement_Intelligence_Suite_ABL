# ABL Customer Statement Intelligence Suite

AI-powered customer statement intelligence system developed as part of the Allied Bank Internship Program.

## Project Modules

- Account Statement Q&A Agent
- Subscription / Recurring Payment Analysis Agent
- ABL Policy Q&A Agent using RAG

## Current Progress

### Implemented

- FastAPI backend setup
- Health check API endpoint
- Synthetic CSV statement upload
- CSV statement parsing
- Structured transaction validation using Pydantic
- Basic statement analysis:
  - Transaction count
  - Total debit
  - Total credit
  - Opening balance
  - Closing balance
- API testing through Swagger UI

### Upcoming

- Statement Q&A Agent
- Subscription / recurring payment detection
- PostgreSQL integration
- ABL Policy RAG pipeline
- Sentence Transformer embeddings
- Google Gemini integration
- React.js + Tailwind CSS frontend
- Deployment

## Technology Stack

- Frontend: React.js + Tailwind CSS
- Backend: FastAPI
- Database: PostgreSQL
- Vector Database: PostgreSQL + pgvector
- LLM: Google Gemini 3.7 Flash
- Embeddings: Sentence Transformers (`all-MiniLM-L6-v2`)
- Frontend Deployment: Vercel
- Backend Deployment: Heroku

## Data Safety

The project uses synthetic/local statement data for development and demonstration purposes. No real customer banking data is used.
