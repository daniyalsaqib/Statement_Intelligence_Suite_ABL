# Customer Statement Intelligence Suite — Frontend

React/Vite frontend for the **ABL Customer Statement Intelligence Suite**.

The production UI presents the project as one conversational banking-intelligence workspace over three backend capabilities:

- Verified Statement Intelligence
- Deterministic Recurring-Payment Detection
- Grounded Public-Policy RAG

The frontend uses synthetic statement data only and is part of an internship prototype.

> **Internship prototype — not an official Allied Bank customer website.**
>
> **This independent student project is a synthetic-data demonstration created for educational and internship purposes. Do not upload real customer statements, credentials, or confidential information.**

---

## Technology

- React.js
- Tailwind CSS
- Vite
- Vercel

---

## Production

Frontend:

```text
https://statement-intelligence-suite-abl.vercel.app
```

Backend:

```text
https://pure-temple-45004-09958cbb6652.herokuapp.com
```

The production frontend communicates with the FastAPI backend over HTTPS.

---

## Frontend Experience

The application uses a compact, unified assistant workflow instead of separate user-facing modules.

### Before a statement is loaded

The user can:

- Browse for a synthetic CSV statement
- Analyze the selected CSV
- Generate and analyze a fresh runtime demo statement
- Ask supported public-policy questions without uploading a statement

### After a statement is loaded

The workspace provides:

- Verified financial summary
- Unified conversational assistant
- Statement Q&A
- Multi-turn month follow-ups
- Recurring-payment questions
- Policy questions
- Provenance labels for assistant responses
- Collapsible transaction evidence
- Source links for grounded policy answers

Starter prompts are adapted depending on whether statement data is currently loaded.

---

## Unified Assistant

The production frontend sends conversational questions to:

```http
POST /assistant/chat
```

Each request includes:

```text
question
statement_data
conversation_history
```

The frontend sends up to the most recent **8** previous user/assistant messages as conversation history.

The current question is sent separately from that history.

Example request shape:

```json
{
  "question": "What about July?",
  "statement_data": [],
  "conversation_history": [
    {
      "role": "user",
      "content": "How much did I spend in August?"
    },
    {
      "role": "assistant",
      "content": "Previous verified answer."
    }
  ]
}
```

Conversation history improves follow-up UX, but the backend remains authoritative for financial calculations.

---

## Assistant Provenance

The frontend preserves backend response metadata so the UI can explain how an answer was produced.

Current method values include:

```text
verified_statement_intelligence
deterministic_recurring_rules
policy_rag
```

These correspond to UI provenance labels such as:

```text
Verified Statement Intelligence
Deterministic Pattern Detection
Grounded Public Policy
```

Policy responses can also include public source links.

Recurring-payment responses can include structured recurring-payment candidates.

---

## Runtime Demo Statement

The **Use Fresh Demo** action generates a new synthetic CSV in the browser at runtime.

The demo is not a static reused file.

Current demo behavior includes:

- Recent complete calendar months
- Synthetic opening balance
- Synthetic salary credits
- Repeated merchant descriptions
- Repeated Netflix / PTCL-style transactions
- Grocery / ATM-style transactions
- Enough repeated descriptions to demonstrate recurring-payment detection

The generated file is synthetic and intended only for demonstration.

---

## Environment Variable

Local development default:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Production Vercel configuration:

```env
VITE_API_BASE_URL=https://pure-temple-45004-09958cbb6652.herokuapp.com
```

Only public frontend configuration should use the `VITE_` prefix.

Backend secrets such as API keys, database credentials, and private tokens must never be exposed through Vite environment variables.

---

## Local Development

From the repository root:

```powershell
cd D:\Statement_Intelligence_Suite_ABL_1\frontend
npm install
npm run dev
```

Default development URL:

```text
http://localhost:5173
```

---

## Production Build

```powershell
cd D:\Statement_Intelligence_Suite_ABL_1\frontend
npm run build
```

The generated production build is written to:

```text
frontend/dist/
```

Formatting / quality checks:

```powershell
npx prettier . --write
npm run lint
npm run build
```

---

## Application Entry Points

```text
src/main.jsx
src/App.jsx
src/index.css
```

`App.jsx` contains the main application workflow and communicates with the backend through `VITE_API_BASE_URL`.

Current application state includes:

```text
upload
processing
workspace
```

The frontend resets conversation state when a new statement workflow begins.

---

## Backend API

Production API:

```text
https://pure-temple-45004-09958cbb6652.herokuapp.com
```

Health endpoint:

```text
https://pure-temple-45004-09958cbb6652.herokuapp.com/health
```

API documentation:

```text
https://pure-temple-45004-09958cbb6652.herokuapp.com/docs
```

### Primary production endpoints

```text
POST /statement/upload
POST /assistant/chat
GET  /health
```

### Backward-compatible specialized endpoints

```text
POST /statement/ask
POST /statement/subscriptions
POST /policy/ask
```

The production frontend uses `/assistant/chat` for conversational statement, recurring-payment, and policy questions.

---

## Frontend / Backend Trust Boundary

The frontend does not calculate authoritative financial totals.

Financial logic remains server-side.

Key rules:

```text
Frontend:
- Collects synthetic input
- Displays analysis
- Maintains recent conversation UX state
- Displays provenance and evidence

Backend:
- Validates statement data
- Calculates authoritative financial facts
- Resolves statement scopes
- Detects recurring-payment candidates
- Retrieves public policy context
- Applies numeric safeguards
- Routes unified assistant capabilities
```

Previous assistant responses are never treated as authoritative financial facts.

---

## Architecture

For the complete application architecture, see:

**[Detailed System Architecture](../docs/ARCHITECTURE.md)**

The frontend is the presentation layer of a layered client-server architecture.

The backend remains responsible for:

- Input validation
- CSV parsing
- Deterministic financial calculations
- Conversation-safe statement follow-ups
- Deterministic recurring-payment rules
- Policy RAG
- LLM integration
- Provenance metadata
- Controlled API failures

---

## Current Validation

Current project-level validation as of **22 September 2026** includes:

```text
156 backend tests passing
GitHub Actions CI passing
Heroku release v17 verified
Production health endpoint verified
Unified assistant production smoke test verified
Cross-capability follow-up production regression verified
```

Frontend production hardening also includes SEO metadata, crawler configuration, social metadata, and Lighthouse performance validation.
