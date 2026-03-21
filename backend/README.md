# Onboarding Engine — Backend Service

A lightweight Express.js service that acts as the deployable backend entry point for the Onboarding Engine on Railway. It exposes health-check and test endpoints out of the box and is structured to be extended with additional routes as the project grows.

---

## Requirements

- Node.js ≥ 18
- npm ≥ 9

---

## Getting Started

### 1 — Install dependencies

```bash
cd backend
npm install
```

### 2 — Configure environment

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Port the server listens on |
| `NODE_ENV` | `development` | Runtime environment |

### 3 — Run the server

```bash
# Development (auto-restarts on file changes)
npm run dev

# Production
npm start
```

The server will be available at `http://localhost:5000`.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{ status, timestamp, uptime }` |
| `GET` | `/api/test` | Smoke test — confirms the API layer is reachable |

### Example responses

**GET /health**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "uptime": 42.3
}
```

**GET /api/test**
```json
{
  "success": true,
  "message": "Onboarding Engine backend is running",
  "environment": "production"
}
```

---

## Project Structure

```
backend/
├── server.js       # Express app — middleware, routes, error handler, server start
├── package.json    # Dependencies and npm scripts
├── .gitignore      # Excludes node_modules, .env, logs, etc.
└── README.md       # This file
```

---

## Connecting the React Client

The React client (`client/`) reads the API base URL from the `VITE_API_URL` environment variable. Set it to point at this service:

```env
# client/.env
VITE_API_URL=https://your-backend-service.railway.app/api
```

If `VITE_API_URL` is not set, the client defaults to `http://localhost:3001/api/v1`.

---

## Deployment (Railway)

Railway will automatically detect the `backend/` directory as a Node.js service. Ensure the following settings are configured in your Railway service:

- **Root Directory:** `backend`
- **Build Command:** `npm install`
- **Start Command:** `npm start`
- **PORT:** set automatically by Railway via the `PORT` environment variable
