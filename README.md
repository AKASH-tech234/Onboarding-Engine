<p align="center">
  <img src="https://img.shields.io/badge/React-18.2-61DAFB?logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/Express-5.x-000000?logo=express&logoColor=white" alt="Express" />
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL+pgvector-3ECF8E?logo=supabase&logoColor=white" alt="Supabase" />
  <img src="https://img.shields.io/badge/LLM-Llama_3.3_70B_(Groq)-FF6F00" alt="LLM" />
  <img src="https://img.shields.io/badge/Embeddings-Gemini_768d-4285F4?logo=google&logoColor=white" alt="Embeddings" />
  <img src="https://img.shields.io/badge/License-ISC-blue" alt="License" />
</p>

<h1 align="center">⚡ Pathway AI — Adaptive Onboarding Engine</h1>

<p align="center">
  <strong>Upload a resume + job description → get a phased, AI-reasoned learning roadmap in real-time.</strong><br/>
  Semantic skill gap analysis · Vector-matched course catalog · Streamed LLM reasoning · Interactive DAG visualization
</p>

---

## Navigation

| Section | What's inside |
|---|---|
| [What It Does](#what-it-does) | End-to-end feature summary |
| [Quick Start](#quick-start) | Get running in 5 minutes |
| [Architecture](#architecture) | System diagram + data flow |
| [AI Pipeline](#ai-pipeline) | 6-step analysis pipeline |
| [Database Schema](#database-schema) | Tables, RPCs, and vector indexes |
| [API Reference](#api-reference) | Endpoints and SSE event types |
| [Project Structure](#project-structure) | Full file tree with annotations |
| [Tech Stack](#tech-stack) | Client and server dependencies |
| [Course Catalog](#course-catalog) | 47 seeded courses across 4 domains |
| [Testing & Scripts](#testing--scripts) | Test suite and available commands |
| [Contributing](#contributing) | How to submit a PR |

---

## What It Does

Pathway AI is a full-stack adaptive onboarding engine for HR and L&D teams. Given a candidate's resume (PDF/DOCX) and a target job description, it runs a 6-step AI pipeline and returns a personalized learning roadmap streamed live to the browser.

### Core Features

| Feature | Description |
|---|---|
| **Resume Intelligence** | Extracts candidate name, role, experience, and skills with evidence from PDF/DOCX |
| **JD Parsing** | Extracts job title, seniority, and required/preferred skills from job descriptions |
| **Semantic Skill Normalization** | Maps free-text skill names to canonical IDs using 768-d Gemini embeddings (≥ 0.85 similarity) |
| **Skill Gap Analysis** | Classifies each skill as *missing*, *level gap*, or *already met* |
| **Adaptive Pathway Generation** | Courses scored (4-axis formula), phased Foundation→Core→Specialization→Stretch, and topologically sorted |
| **Vector Course Matching** | Falls back to pgvector cosine similarity when no direct skill→course mapping exists |
| **Streamed Reasoning Trace** | LLM-written explanation of every recommendation, streamed in real-time via SSE |
| **Interactive Graph** | ReactFlow + dagre auto-layout with animated edges and a course detail drawer |
| **PDF Export** | One-click A4 export of the full roadmap (stats, phases, reasoning trace) |
| **Session Persistence** | Every analysis persisted in Supabase, retrievable by session ID |

---

## Quick Start

### Prerequisites

- Node.js ≥ 18, npm ≥ 9
- [Supabase](https://supabase.com) project with `pgvector` extension enabled
- [Groq](https://console.groq.com) API key (Llama 3.3 70B)
- [Google AI Studio](https://aistudio.google.com) API key (Gemini embeddings)

### 1 — Environment Setup

```bash
cp server/.env.example server/.env
```

```env
# server/.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIs...
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
PORT=3001
SEED_SECRET=your-seed-secret
```

```env
# client/.env  (optional — defaults to localhost)
VITE_API_URL=http://localhost:3001/api/v1
```

### 2 — Database Setup

Run these in your Supabase SQL editor in order:

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;
```

Then run the full schema from [`server/src/db/schema.sql`](server/src/db/schema.sql), followed by the two RPC functions in the [Database Schema](#required-rpc-functions) section below.

### 3 — Seed the Course Catalog

```bash
cd server && npm install && npm run seed
```

> Seeding embeds all 47 courses and skills via the Gemini API — takes ~2 minutes on first run.

### 4 — Run the Application

```bash
# Terminal 1 — Server (http://localhost:3001)
cd server && npm run dev

# Terminal 2 — Client (http://localhost:5173)
cd client && npm install && npm run dev
```

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          CLIENT (Vite + React 18)                        │
│                                                                           │
│  UploadPage ──► useAnalyze() ──► SSE stream ──► ResultsPage              │
│       │                                              │                    │
│  UploadZone (resume/JD)                   ┌──────────┼──────────┐        │
│                                           │          │          │        │
│                                    PathwayFlow  ReasoningTrace  PDF      │
│                                   (ReactFlow)   (parsed LLM)  Export    │
└──────────────────────────────────────┬────────────────────────────────────┘
                                       │ POST /api/v1/sessions/analyze
                                       │ (multipart/form-data → SSE)
┌──────────────────────────────────────▼────────────────────────────────────┐
│                       SERVER (Express 5 + Node.js)                        │
│                                                                           │
│  routes/sessions.js ──► extractText (pdf-parse/mammoth)                  │
│       │                                                                   │
│       ├──► extractResumeSkills (LLM + Zod) ─────────┐                    │
│       ├──► extractJDRequirements (LLM + Zod) ────────┤  (parallel)       │
│       │                                              │                    │
│       ├──► normalizeSkills (Gemini embed + Supabase) ◄┘                   │
│       ├──► computeSkillGap (deterministic diff)                           │
│       ├──► adaptivePathway (score + toposort + vector search)             │
│       └──► generateReasoningTraceStream (LLM stream)                      │
│                                                                           │
│  AI Layer: Groq (Llama 3.3 70B) · Gemini (embeddings)                   │
└──────────────────────────────────────┬────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼────────────────────────────────────┐
│                     DATABASE (Supabase + pgvector)                        │
│                                                                           │
│  skills (id, name, embedding[768]) ──► skill_course_map (impact)         │
│  courses (id, title, embedding[768], prerequisites[], level_num)          │
│  sessions (id, resume_text, skill_gap, pathway, reasoning_trace)         │
│                                                                           │
│  RPC: match_skill_by_embedding() · match_courses_by_vector()             │
│  Indexes: IVFFlat (vector_cosine_ops, lists=50)                          │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## AI Pipeline

The pipeline runs end-to-end inside `server/src/routes/sessions.js` and streams progress to the client via SSE.

```
Step 1 ── Extract Text
          pdf-parse (PDF) or mammoth (DOCX) → raw text
          Validation: minimum 150 words

Step 2 ── Extract Skills  [parallel]
          ├── extractResumeSkills  →  { candidate_name, current_role, skills[{name, level, years, evidence}] }
          └── extractJDRequirements →  { job_title, seniority_level, skills[{name, level, required, context}] }
          Both: LLM (Llama 3.3 70B) + Zod schema validation

Step 3 ── Normalize Skills
          embed(skill_name) → match_skill_by_embedding(threshold ≥ 0.85) → canonical UUID
          No match → insert new skill into registry

Step 4 ── Compute Skill Gap  [deterministic]
          For each required skill, compare candidate level vs. required level
          Output: missing | gap | already_met

Step 5 ── Adaptive Pathway
          For each gap → query skill_course_map (top 3 by impact)
                       → fallback: match_courses_by_vector (threshold 0.6)
          Score formula: 0.4 × criticality + 0.3 × impact + 0.2 × level_fit + 0.1 × efficiency
          Topological sort by prerequisites → assign phase by level

Step 6 ── Reasoning Trace  [streamed]
          Llama 3.3 70B generates a 5-section explanation
          Streamed chunk-by-chunk to the client via SSE
```

### LLM Configuration

| Component | Model | Provider |
|---|---|---|
| Skill Extraction | Llama 3.3 70B Versatile | Groq |
| JD Parsing | Llama 3.3 70B Versatile | Groq |
| Reasoning Trace | Llama 3.3 70B Versatile | Groq |
| Embeddings | gemini-embedding-001 (768-d) | Google AI |

---

## Database Schema

### Tables

```sql
-- Canonical skill registry
CREATE TABLE skills (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL UNIQUE,
  category   TEXT NOT NULL,
  domain     TEXT NOT NULL,
  embedding  vector(768),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Course catalog
CREATE TABLE courses (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title         TEXT NOT NULL,
  description   TEXT NOT NULL,
  skill_id      UUID REFERENCES skills(id),
  level         TEXT CHECK (level IN ('beginner', 'intermediate', 'advanced')),
  level_num     INTEGER CHECK (level_num IN (1, 2, 3)),
  duration_hrs  NUMERIC(4,1),
  domain        TEXT NOT NULL,
  provider      TEXT,
  url           TEXT,
  prerequisites UUID[] DEFAULT '{}',
  embedding     vector(768),
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- Analysis sessions
CREATE TABLE sessions (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resume_text      TEXT,
  jd_text          TEXT,
  extracted_skills JSONB,
  required_skills  JSONB,
  skill_gap        JSONB,
  pathway          JSONB,
  reasoning_trace  JSONB,
  created_at       TIMESTAMPTZ DEFAULT now()
);

-- Skill ↔ course impact scores
CREATE TABLE skill_course_map (
  course_id UUID REFERENCES courses(id),
  skill_id  UUID REFERENCES skills(id),
  impact    NUMERIC(3,2) CHECK (impact BETWEEN 0 AND 1),
  PRIMARY KEY (course_id, skill_id)
);

-- Vector indexes
CREATE INDEX ON skills  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
CREATE INDEX ON courses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

### Required RPC Functions

Run these in the Supabase SQL editor after creating the schema:

```sql
-- Find nearest skill by embedding
CREATE OR REPLACE FUNCTION match_skill_by_embedding(
  query_embedding vector(768),
  match_threshold float,
  match_count     int
)
RETURNS TABLE (id uuid, name text, similarity float)
LANGUAGE sql STABLE AS $$
  SELECT id, name, 1 - (embedding <=> query_embedding) AS similarity
  FROM skills
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Find nearest courses by embedding (fallback retrieval)
CREATE OR REPLACE FUNCTION match_courses_by_vector(
  query_embedding vector(768),
  match_threshold float,
  match_count     int
)
RETURNS SETOF courses
LANGUAGE sql STABLE AS $$
  SELECT *
  FROM courses
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
```

---

## API Reference

### `POST /api/v1/sessions/analyze`

Runs the full analysis pipeline. Responds as **Server-Sent Events (SSE)**.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `resume` | File (PDF/DOCX) | ✅ | Candidate resume |
| `jd` | File (PDF/DOCX) | ❌ * | Job description file |
| `jd_text` | String | ❌ * | Job description as plain text |

*At least one of `jd` or `jd_text` is required.

**SSE Event Types**

| Event | Payload | When |
|---|---|---|
| `status` | `{ message: string }` | Pipeline progress updates |
| `trace_chunk` | `string` | Reasoning trace, streamed token-by-token |
| `pathway_ready` | `{ candidate, skill_gap_summary, pathway }` | Before trace completes |
| `complete` | Full session JSON | Final result with `session_id` |
| `error` | `{ error: string, status: number }` | On any failure |

---

### `GET /api/v1/sessions/:id`

Returns a saved analysis session by ID, including `extracted_skills`, `required_skills`, `skill_gap`, `pathway`, and `reasoning_trace`.

---

### `GET /api/v1/courses`

Lists catalog courses. Supports query params: `domain`, `level`, `skill_id`.

---

### `GET /api/v1/skills`

Lists all canonical skills ordered alphabetically.

---

### `GET /health`

Returns `{ status: "ok", timestamp: "..." }`.

---

## Project Structure

```
Onboarding-Engine/
├── client/                               # React frontend (Vite)
│   └── src/
│       ├── App.jsx                       # Router: / → Upload, /results/:id → Results
│       ├── hooks/
│       │   ├── useAnalyze.js             # SSE hook — streams status, trace, result
│       │   └── useSession.js             # GET /sessions/:id fetcher
│       ├── pages/
│       │   ├── UploadPage.jsx            # Resume + JD upload, live SSE preview
│       │   └── ResultsPage.jsx           # Stats, graph, timeline, reasoning, export
│       ├── components/
│       │   ├── PathwayFlow.jsx           # ReactFlow graph (dagre layout, animated edges)
│       │   ├── CourseNode.jsx            # Custom node (phase-colored, hover effects)
│       │   ├── CourseDrawer.jsx          # Slide-out panel: score breakdown + details
│       │   ├── PhaseTimeline.jsx         # Horizontal phase timeline with duration badges
│       │   ├── ReasoningTrace.jsx        # 5-section parsed LLM reasoning display
│       │   ├── GapSummaryCard.jsx        # Skill gap overview (gaps / required / met)
│       │   ├── SkillChips.jsx            # Skill tag chips with shimmer
│       │   ├── FloatingExportButton.jsx  # Fixed-position PDF export FAB
│       │   ├── UploadZone.jsx            # Drag-and-drop (PDF/DOCX, 5 MB max)
│       │   └── ...                       # BackgroundGradient, TypewriterEffectSmooth
│       └── utils/
│           ├── exportRoadmapPDF.js       # jsPDF multi-page export
│           ├── formatDuration.js         # Hours → "Xh Ym"
│           └── cn.js                     # clsx + tailwind-merge
│
├── server/                               # Express 5 backend
│   └── src/
│       ├── index.js                      # App setup (CORS, JSON, routes, error handler)
│       ├── ai/
│       │   ├── gemini.js                 # Groq LLM + Gemini embedding clients
│       │   ├── extractResumeSkills.js    # Resume → structured skills (LLM + Zod)
│       │   ├── extractJDRequirements.js  # JD → structured requirements (LLM + Zod)
│       │   ├── normalizeSkills.js        # Skill name → canonical UUID
│       │   ├── computeSkillGap.js        # Deterministic gap diff
│       │   ├── adaptivePathway.js        # Scoring, phasing, topological sort
│       │   └── generateReasoningTrace.js # LLM reasoning (stream + complete modes)
│       ├── db/
│       │   ├── supabaseClient.js         # Supabase client init
│       │   └── schema.sql                # Full database schema
│       ├── routes/
│       │   ├── sessions.js               # POST /analyze (SSE pipeline), GET /:id
│       │   ├── courses.js                # GET / list, POST / seed-protected insert
│       │   └── skills.js                 # GET / all skills
│       ├── scripts/
│       │   └── seedCatalog.js            # Seeds 47 courses + embeddings
│       ├── tests/
│       │   ├── adaptivePathway.test.js   # Pathway generation tests
│       │   └── computeSkillGap.test.js   # Skill gap computation tests
│       ├── middleware/upload.js          # Multer memory storage (10 MB)
│       ├── parsers/extractText.js        # pdf-parse / mammoth + 150-word validation
│       └── utils/
│           ├── retry.js                  # 2 attempts, 1 s delay
│           ├── levelToNum.js             # Level string ↔ number
│           └── cosineSimilarity.js       # Cosine similarity util
│
├── flow.md                               # Data flow docs (3-hop architecture)
└── PLAN-1.md                             # Project planning notes
```

---

## Tech Stack

### Client

| Package | Purpose |
|---|---|
| React 18 + Vite 5 | UI framework and build tooling |
| TailwindCSS 3 | Utility-first styling |
| ReactFlow 11 + @dagrejs/dagre | Interactive graph + automatic DAG layout |
| Framer Motion | Animations and transitions |
| react-dropzone | Drag-and-drop file upload |
| jsPDF + html2canvas | Client-side PDF generation |
| Axios | HTTP client (session retrieval) |
| React Router 6 | Client-side routing |

### Server

| Package | Purpose |
|---|---|
| Express 5 | HTTP server and API routing |
| Groq SDK | LLM inference (Llama 3.3 70B) |
| @google/generative-ai | Gemini embedding API |
| Supabase JS v2 | PostgreSQL + pgvector client |
| Multer 2 | Multipart upload handling |
| pdf-parse 2 + mammoth | PDF and DOCX text extraction |
| Zod 4 | Runtime schema validation for LLM output |
| dotenv + nodemon | Env management and dev auto-restart |

---

## Course Catalog

The seed script provisions **47 courses** across 3 domains:

| Domain | Count | Sample Courses |
|---|---|---|
| **Technical** | 25 | React, Node.js, Docker, Kubernetes, AWS, PostgreSQL, Machine Learning, LLM APIs |
| **Operational** | 11 | Workplace Safety, Forklift Operation, Inventory Management, WMS, Supply Chain |
| **Soft Skills** | 11 | Business Communication, Agile/Scrum, Project Management, Leadership, Strategy |

Each course includes a linked skill, difficulty level, duration in hours, provider, URL, prerequisite chain, and a 768-d Gemini embedding.

---

## Testing & Scripts

### Run Tests

```bash
cd server && npm test
```

Covers: `adaptivePathway.test.js` (phase assignment, topological sort) and `computeSkillGap.test.js` (missing / level gap / already met).

### All Scripts

| Location | Command | Description |
|---|---|---|
| `client/` | `npm run dev` | Start Vite dev server |
| `client/` | `npm run build` | Production build |
| `client/` | `npm run preview` | Preview production build |
| `client/` | `npm run lint` | ESLint check |
| `server/` | `npm run dev` | Start with nodemon |
| `server/` | `npm test` | Run test suite |
| `server/` | `npm run seed` | Seed skills + courses + embeddings |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

ISC License — see [LICENSE](LICENSE) for details.
