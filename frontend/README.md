# Customer Statement Intelligence Suite — Frontend

React frontend for the **ABL Customer Statement Intelligence Suite — App 1 of 2**.

The frontend provides the user interface for:

- Statement Intelligence
- Statement Q&A
- Recurring Payment Analysis
- ABL Policy Assistant

## Technology

- React.js
- Tailwind CSS
- Vite
- Vercel

## Production

https://statement-intelligence-suite-abl.vercel.app

The production frontend communicates with the FastAPI backend hosted on Heroku.

## Environment Variable

The frontend uses:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

For production, configure Vercel with:

```env
VITE_API_BASE_URL=https://pure-temple-45004-09958cbb6652.herokuapp.com
```

Only public frontend configuration should use the `VITE_` prefix.

Backend secrets such as API keys and database credentials must never be exposed through Vite environment variables.

## Local Development

From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Default development URL:

```text
http://localhost:5173
```

## Production Build

```powershell
npm run build
```

The production build is generated in:

```text
frontend/dist/
```

## Application Entry Points

```text
src/main.jsx
src/App.jsx
src/index.css
src/App.css
```

`App.jsx` communicates with the backend through `VITE_API_BASE_URL`.

## Backend

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

## Main Backend Endpoints

```text
POST /statement/upload
POST /statement/ask
POST /statement/subscriptions
POST /policy/ask
GET  /health
```

## Architecture

For the complete application architecture, see:

**[Detailed System Architecture](../docs/ARCHITECTURE.md)**

The frontend is the presentation layer of a layered client-server architecture.

Financial calculations, statement processing, RAG retrieval, and LLM integration remain server-side in the FastAPI backend.
