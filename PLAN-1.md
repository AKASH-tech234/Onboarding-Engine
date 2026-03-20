# AI-Adaptive Onboarding Engine — Complete Build Plan
**Hackathon: ARTPARK CodeForge**
**Stack: React + Express + Supabase (PostgreSQL) + pgvector**

---

## 0. Mental Model Before Anything Else

The system does exactly three things:
1. **Understand** where the user is (parse resume → extract skills + levels)
2. **Understand** where they need to go (parse JD → extract required competencies)
3. **Bridge the gap** (diff the two → generate an ordered, personalized learning pathway from a fixed course catalog)

Every architectural decision flows from these three verbs: **Understand → Diff → Bridge**.

The "AI" is not magic — it's a structured pipeline:
- LLM (Gemini 1.5 Flash via API) does the reading/extraction/reasoning
- pgvector does semantic similarity for course matching
- Our own graph/scoring logic does the pathway ordering (this is the "original adaptive logic" the rubric demands)
- Nothing is hallucinated because all course recommendations are grounded strictly in our course catalog (addresses the 15% Grounding criterion)

---

## 1. Tech Stack — Final Decisions + Rationale

### Backend
| Layer | Choice | Why |
|---|---|---|
| Runtime | Node.js + Express | Team familiarity, fast to scaffold |
| Database | Supabase (PostgreSQL + pgvector) | Gives us relational DB + vector search in one place, no separate vector DB needed |
| ORM | Supabase JS client (direct queries) | Avoids Prisma/Drizzle overhead for a hackathon |
| File Parsing | `pdf-parse` (PDF), `mammoth` (DOCX) | Both lightweight, no external service needed |
| LLM | Google Gemini 1.5 Flash (`@google/generative-ai`) | Free tier generous, fast, structured output support |
| Embeddings | Gemini `text-embedding-004` model | Same SDK, no extra dependency |
| Auth | None (out of scope for hackathon MVP) | |

### Frontend
| Layer | Choice | Why |
|---|---|---|
| Framework | React 18 (Vite) | Fast HMR, familiar |
| Styling | Tailwind CSS | Rapid UI without fighting CSS |
| File Upload | react-dropzone | Clean UX for resume/JD upload |
| Roadmap Visualization | React Flow (`reactflow`) + `@dagrejs/dagre` | Purpose-built DAG visualization; dagre computes proper node positions automatically |
| HTTP Client | Axios | |
| State | React useState + useContext | Simple enough, no Redux needed |

### Infrastructure
- **Dev:** Docker Compose (Postgres locally mirrors Supabase schema)
- **Prod:** Supabase hosted Postgres, Express on Railway or Render, React on Vercel
- **Dockerfile:** Multi-stage build (Node backend + Vite build served as static)

---

## 2. Supabase Schema — Every Table, Column, and Constraint

### `skills` table
Canonical skill registry. Single source of truth.
```sql
CREATE TABLE skills (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL UNIQUE,       -- e.g. "React", "SQL", "Docker"
  category    TEXT NOT NULL,              -- e.g. "Frontend", "DevOps", "Soft Skills"
  domain      TEXT NOT NULL,              -- e.g. "Technical", "Operational", "Managerial"
  embedding   vector(768),                -- text-embedding-004 output
  created_at  TIMESTAMPTZ DEFAULT now()
);
```

### `courses` table
The fixed catalog. ALL pathway recommendations must come from here. No hallucinations.
```sql
CREATE TABLE courses (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title         TEXT NOT NULL,
  description   TEXT NOT NULL,
  skill_id      UUID REFERENCES skills(id),   -- primary skill this course teaches
  level         TEXT CHECK (level IN ('beginner', 'intermediate', 'advanced')),
  level_num     INTEGER CHECK (level_num IN (1, 2, 3)),  -- 1=beginner, 2=intermediate, 3=advanced — used for numeric comparisons in SQL, kept in sync with level
  duration_hrs  NUMERIC(4,1),                  -- e.g. 4.5 hours
  domain        TEXT NOT NULL,                 -- mirrors skills.domain
  provider      TEXT,                          -- e.g. "Coursera", "Internal", "Udemy"
  url           TEXT,
  prerequisites UUID[] DEFAULT '{}',           -- array of course UUIDs that should precede this
  embedding     vector(768),                   -- embedding of title + description
  created_at    TIMESTAMPTZ DEFAULT now()
);
```

> **Why `level_num`?** `level` is TEXT. PostgreSQL TEXT comparison sorts alphabetically: "advanced" < "beginner" < "intermediate" — which is semantically wrong. Never use `level >= 'intermediate'` in SQL. Always filter on `level_num` instead. Always set both fields together when inserting: `level='intermediate', level_num=2`.

### `sessions` table
One row per user upload session. Stateless from user perspective (no auth), but lets us retrieve results.
```sql
CREATE TABLE sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resume_text     TEXT,
  jd_text         TEXT,
  extracted_skills JSONB,   -- { "skills": [{ "name": "React", "level": "intermediate", "years": 2 }] }
  required_skills  JSONB,   -- { "skills": [{ "name": "React", "level": "advanced", "required": true }] }
  skill_gap        JSONB,   -- { "gaps": [{ "skill": "React", "current": "intermediate", "target": "advanced" }] }
  pathway          JSONB,   -- ordered array of course objects
  reasoning_trace  JSONB,   -- step-by-step reasoning log (required by rubric)
  created_at      TIMESTAMPTZ DEFAULT now()
);
```

### `skill_course_map` table
Many-to-many: which skills does a course address (beyond its primary skill).
```sql
CREATE TABLE skill_course_map (
  course_id  UUID REFERENCES courses(id),
  skill_id   UUID REFERENCES skills(id),
  impact     NUMERIC(3,2) CHECK (impact BETWEEN 0 AND 1), -- how much does this course improve this skill
  PRIMARY KEY (course_id, skill_id)
);
```

### pgvector index
```sql
CREATE INDEX ON skills USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
CREATE INDEX ON courses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

---

## 3. AI Pipeline — Step by Step with Exact Prompts

This is the heart of the system. Each step is a discrete function in `server/src/ai/`.

### Step 1: Document Text Extraction
**File:** `server/src/parsers/extractText.js`

- If `.pdf`: use `pdf-parse`, get raw text
- If `.docx`: use `mammoth`, get plain text
- Strip excessive whitespace, normalize line breaks
- Return: `{ text: string, wordCount: number }`

No AI involved here. Pure text extraction.

### Step 2: Resume Skill Extraction
**File:** `server/src/ai/extractResumeSkills.js`

Call Gemini with this exact structured prompt:

```
SYSTEM: You are a precise HR data extraction engine. Extract ONLY skills explicitly mentioned or clearly implied by the resume text. Do NOT infer skills not evidenced in the text. Return ONLY valid JSON, no markdown, no explanation.

USER: Extract all skills from this resume. For each skill return:
- name: canonical skill name (e.g. "React" not "ReactJS" or "React.js")  
- level: one of ["beginner", "intermediate", "advanced"] inferred from context (years, role seniority, project complexity)
- years: numeric years of experience (null if not determinable)
- evidence: one-sentence quote or paraphrase from the resume that supports this skill

Return format:
{
  "candidate_name": string | null,
  "total_experience_years": number | null,
  "current_role": string | null,
  "skills": [{ "name": string, "level": string, "years": number|null, "evidence": string }]
}

Resume text:
<RESUME_TEXT>
```

Parse the JSON response. Store in `sessions.extracted_skills`.

### Step 3: JD Requirement Extraction
**File:** `server/src/ai/extractJDRequirements.js`

```
SYSTEM: You are a precise job requirements extraction engine. Extract ONLY skills and competencies explicitly stated in the job description. Return ONLY valid JSON, no markdown, no explanation.

USER: Extract all required and preferred skills from this job description. For each skill return:
- name: canonical skill name
- level: minimum required level ["beginner", "intermediate", "advanced"]
- required: true if mandatory, false if preferred/nice-to-have
- context: the exact phrase from JD that mentions this skill

Return format:
{
  "job_title": string | null,
  "department": string | null,
  "seniority_level": string | null,
  "skills": [{ "name": string, "level": string, "required": boolean, "context": string }]
}

Job Description:
<JD_TEXT>
```

Store in `sessions.required_skills`.

### Step 4: Skill Normalization via Vector Search
**File:** `server/src/ai/normalizeSkills.js`

The LLM may return "ReactJS", "React.js", "React Framework" — all meaning "React". We normalize by:
1. For each extracted skill name, generate its embedding via `text-embedding-004`
2. Run `SELECT id, name FROM skills ORDER BY embedding <=> $1 LIMIT 1` (cosine nearest neighbor)
3. If cosine similarity > 0.85, map to the canonical DB skill
4. If similarity < 0.85, it's a novel skill — insert it into `skills` table dynamically

This is deterministic and grounded. No hallucination possible.

### Step 5: Skill Gap Analysis
**File:** `server/src/ai/computeSkillGap.js`

Pure TypeScript logic. No LLM needed here.

Level ordering: `beginner=1, intermediate=2, advanced=3`

Algorithm:
```javascript
function computeGap(extractedSkills, requiredSkills) {
  const gaps = [];
  const alreadyMet = [];
  const missing = [];

  for (const req of requiredSkills) {
    const current = extractedSkills.find(s => s.normalized_id === req.normalized_id);
    
    if (!current) {
      // Completely missing skill
      missing.push({ skill: req.name, current: null, target: req.level, gap_size: levelToNum(req.level), required: req.required });
    } else if (levelToNum(current.level) < levelToNum(req.level)) {
      // Has the skill but not at required level
      gaps.push({ skill: req.name, current: current.level, target: req.level, gap_size: levelToNum(req.level) - levelToNum(current.level), required: req.required });
    } else {
      // Already meets requirement
      alreadyMet.push({ skill: req.name, current: current.level, target: req.level });
    }
  }

  return { gaps, missing, alreadyMet, total_gaps: gaps.length + missing.length };
}
```

Store result in `sessions.skill_gap`.

### Step 6: Adaptive Pathway Generation (THE CORE ORIGINAL ALGORITHM)
**File:** `server/src/ai/adaptivePathway.js`

This is the "original adaptive logic" the rubric specifically calls out. It's a **Weighted Dependency Graph traversal + Priority Queue** approach.

> **Graph-based vs Knowledge Tracing — why we chose Graph:** The rubric (Slide 4) mentions both "Graph-based" and "Knowledge Tracing" as example algorithms. Knowledge Tracing (e.g. Bayesian Knowledge Tracing, Deep Knowledge Tracing) models the probability that a student has mastered a skill given their response history — it requires interaction data over time (correct/incorrect answers per question). We don't have that data from a one-shot resume+JD upload. A scored dependency graph is the correct choice here: it works from a single snapshot of the candidate's skills, is fully explainable to judges (every weight has a formula), and produces deterministic, auditable results. Mention this explicitly in Slide 4 if asked.

#### 6a. Candidate Course Retrieval
For each gap/missing skill, query the course catalog:
```sql
SELECT c.*, scm.impact
FROM courses c
JOIN skill_course_map scm ON c.id = scm.course_id
WHERE scm.skill_id = $1
  AND c.level_num >= $2  -- $2 is levelToNum(current_level), filters out courses below candidate's current level
ORDER BY scm.impact DESC, c.duration_hrs ASC
LIMIT 3;
```

> **Why `level_num` not `level`?** `level` is TEXT. PostgreSQL alphabetical sort gives "advanced" < "beginner" < "intermediate" — completely wrong semantically. `level_num` (integer 1/2/3) is always correct for numeric comparison. `$2` is passed as `levelToNum(gap.current_level)` from JS, e.g. if the candidate already knows React at intermediate (2), we only fetch intermediate+ courses, not beginner ones they've already surpassed.

Also run a vector search fallback for skills not found by exact `skill_id` match:
```sql
SELECT c.*, 1 - (c.embedding <=> $1) AS similarity
FROM courses c
WHERE 1 - (c.embedding <=> $1) > 0.6
ORDER BY c.embedding <=> $1
LIMIT 3;
```
Union and deduplicate. This gives us a candidate pool per skill gap.

#### 6b. Priority Scoring
Each candidate course gets a score:

```
score = (gap_criticality * 0.40) 
      + (impact_coverage * 0.30) 
      + (level_fit * 0.20) 
      + (efficiency * 0.10)
```

Where:
- `gap_criticality`: 1.0 if skill is `required: true`, 0.5 if preferred
- `impact_coverage`: `scm.impact` value (0–1)
- `level_fit`: 1 - |numericLevel(course) - numericLevel(gap_target)| / 2 (penalizes over/under-level)
- `efficiency`: 1 / log(duration_hrs + 1) (shorter courses score higher, normalized)

#### 6c. Dependency-Aware Ordering (DAG Traversal)
Courses have `prerequisites` (UUID array). We build a DAG and do a topological sort:

```javascript
function topologicalSort(courses) {
  // Kahn's algorithm
  const inDegree = {};
  const graph = {};
  
  for (const course of courses) {
    inDegree[course.id] = 0;
    graph[course.id] = [];
  }
  
  for (const course of courses) {
    for (const prereqId of course.prerequisites) {
      if (graph[prereqId]) {
        graph[prereqId].push(course.id);
        inDegree[course.id]++;
      }
    }
  }
  
  const queue = courses.filter(c => inDegree[c.id] === 0).sort((a, b) => b.score - a.score);
  const result = [];
  
  while (queue.length) {
    const node = queue.shift();
    result.push(node);
    for (const neighborId of graph[node.id]) {
      inDegree[neighborId]--;
      if (inDegree[neighborId] === 0) {
        const neighbor = courses.find(c => c.id === neighborId);
        queue.push(neighbor);
        queue.sort((a, b) => b.score - a.score); // re-sort by priority
      }
    }
  }
  
  return result;
}
```

#### 6d. Phase Grouping
After topological sort, assign each course to a phase based purely on `course.level_num`. This is deterministic and unambiguous — phase is a property of the course's difficulty level, not of the gap size.

```javascript
function assignPhase(course) {
  if (course.level_num === 1) return { phase: 1, phase_label: 'Foundation' };
  if (course.level_num === 2) return { phase: 2, phase_label: 'Core Competency' };
  if (course.level_num === 3) {
    return course.gap.required
      ? { phase: 3, phase_label: 'Specialization' }
      : { phase: 4, phase_label: 'Stretch Goals' };
  }
}
```

Phase meanings:
- **Phase 1: Foundation** — `level_num = 1` (beginner). Candidate has zero knowledge of this skill. Start here.
- **Phase 2: Core Competency** — `level_num = 2` (intermediate). Candidate has beginner knowledge but role needs intermediate+.
- **Phase 3: Specialization** — `level_num = 3` (advanced), skill is `required: true`. Must reach this level for the role.
- **Phase 4: Stretch Goals** — `level_num = 3` (advanced), skill is `required: false` (preferred). Nice-to-have after phases 1–3 are done.

> **Why not use `gap_size` for phase assignment?** `gap_size` tells you how far the candidate needs to travel, not where the course sits. A course that teaches Docker at beginner level is always Phase 1 regardless of how large the Docker gap is. Mixing gap_size into phase assignment (as the old plan did) produced contradictory rules like "Phase 1 = beginner AND gap_size 3" — a beginner Docker course doesn't care about the gap_size, it's just a beginner course.

Each phase has an estimated total duration (sum of `duration_hrs` for all courses in that phase) and a completion milestone label.

Store final pathway in `sessions.pathway`.

### Step 7: Reasoning Trace Generation
**File:** `server/src/ai/generateReasoningTrace.js`

The rubric explicitly requires a **reasoning trace feature** (10%). This is a human-readable log of every decision.

Call Gemini one final time with all intermediate data:

```
SYSTEM: You are an expert L&D advisor. Given the analysis below, write a clear, professional reasoning trace explaining WHY each recommendation was made. Be specific, cite the skill gap, and explain the course selection logic. No hallucinations — only reference data provided to you.

USER: Given this onboarding analysis, explain each recommendation:

Candidate Profile: <extracted_skills JSON>
Job Requirements: <required_skills JSON>  
Skill Gaps: <skill_gap JSON>
Recommended Pathway: <pathway JSON>

Write a reasoning trace with these sections:
1. Candidate Assessment (2-3 sentences)
2. Gap Identification (bullet per gap, explain severity)
3. Course Selection Rationale (bullet per course, explain why this specific course)
4. Pathway Ordering Logic (explain why courses are sequenced this way)
5. Estimated Time to Competency (calculate from course durations)
```

Store in `sessions.reasoning_trace`. Display in UI as a collapsible "Why this pathway?" panel.

---

## 4. API Endpoints — Every Route

**Base URL:** `/api/v1`

### `POST /sessions/analyze`
Main endpoint. Accepts multipart form data.

**Request:** `multipart/form-data`
- `resume`: File (PDF or DOCX)
- `jd`: File (PDF or DOCX) OR `jd_text`: plain text string

**Response:**
```json
{
  "session_id": "uuid",
  "candidate": { "name": "...", "current_role": "...", "total_experience_years": 3 },
  "job_title": "...",
  "skill_gap_summary": { "total_gaps": 5, "critical_gaps": 3, "already_met": 7 },
  "pathway": [
    {
      "phase": 1,
      "phase_label": "Foundation",
      "courses": [
        {
          "id": "uuid",
          "title": "...",
          "description": "...",
          "level": "intermediate",
          "duration_hrs": 4.5,
          "provider": "Coursera",
          "url": "...",
          "addresses_skill": "Docker",
          "gap_type": "missing",
          "score": 0.87
        }
      ],
      "phase_duration_hrs": 12
    }
  ],
  "reasoning_trace": { ... },
  "total_training_hrs": 28.5
}
```

**Pipeline inside this handler:**
1. Extract text from both files
2. `extractResumeSkills(resumeText)`
3. `extractJDRequirements(jdText)`
4. `normalizeSkills(extracted, required)` — vector search against DB
5. `computeSkillGap(normalizedExtracted, normalizedRequired)`
6. `adaptivePathway(skillGap)` — retrieves courses, scores, sorts, phases
7. `generateReasoningTrace(all intermediate data)`
8. Write complete session to Supabase
9. Return response

**Error handling:**
- 400 if files missing or unparseable
- 422 if LLM returns invalid JSON (retry once, then return structured error)
- 500 for DB/LLM failures with specific error message

### `GET /sessions/:id`
Retrieve a previously analyzed session by ID. Enables shareable results.

**Response:** Same shape as POST response.

### `GET /courses`
List all courses in the catalog. Used for admin/demo purposes.

**Query params:** `?domain=Technical&level=intermediate&skill_id=uuid`

### `GET /skills`
List all skills in the registry.

### `POST /courses` (seeding endpoint, protected by `SEED_SECRET` env var)
Bulk insert courses into catalog. Used to populate the DB before demo.

---

## 5. Course Catalog — What We Actually Seed

We need a real catalog to avoid hallucinating courses. We seed **at minimum 60 courses** covering:

### Technical Domain
- **Frontend:** HTML/CSS Fundamentals, JavaScript Essentials, React Basics, React Advanced Patterns, TypeScript Foundations, Next.js for Production
- **Backend:** Node.js + Express, REST API Design, GraphQL Fundamentals, Python for Backend, FastAPI with Python
- **Databases:** SQL Fundamentals, PostgreSQL Advanced, MongoDB Basics, Redis Caching Strategies
- **DevOps:** Docker Fundamentals, Kubernetes Basics, CI/CD with GitHub Actions, AWS Core Services, Linux Command Line
- **AI/ML:** Python for Data Science, Machine Learning Fundamentals, LLM APIs and Prompt Engineering, Vector Databases, Fine-tuning LLMs

### Operational Domain (for Cross-Domain Scalability criterion — 10%)
- Warehouse Safety and Compliance
- Forklift Certification Prep
- Inventory Management Systems
- Customer Service Fundamentals
- OSHA Standards Overview
- Supply Chain Basics
- Quality Control Processes

### Soft Skills / Managerial Domain
- Business Communication
- Agile and Scrum Foundations
- Project Management Fundamentals (PMP Prep)
- Presentation Skills
- Conflict Resolution
- Data-Driven Decision Making

Each course entry includes: `title`, `description`, `skill_id`, `level`, `duration_hrs`, `domain`, `provider`, `url` (can be placeholder), `prerequisites`.

Seed script: `server/src/scripts/seedCatalog.js`

---

## 6. Frontend — Page by Page

### Page 1: Upload Page (`/`)
**Purpose:** Entry point. Upload resume + JD.

**Components:**
- `<UploadZone type="resume" />` — dropzone for resume (PDF/DOCX), shows file name on drop
- `<UploadZone type="jd" />` — dropzone for JD, OR a text paste textarea (toggle)
- `<AnalyzeButton />` — disabled until both inputs present, shows spinner on loading
- `<ExampleBadge />` — small button "Try with sample resume/JD" that loads demo files (important for demo video)

**State:** `resumeFile`, `jdFile | jdText`, `isLoading`, `error`

**On submit:** POST to `/api/v1/sessions/analyze`, navigate to `/results/:session_id`

### Page 2: Results Page (`/results/:id`)
**Purpose:** The main output. Three-panel layout.

#### Left Panel: Profile Summary
- Candidate name, current role, years of experience
- Chip list of skills they already have (green chips)
- Chip list of skill gaps (red chips for required, amber for preferred)
- "X gaps identified, Y skills already met" summary stat

#### Center Panel: Learning Pathway (React Flow Visualization)
This is the most important UI component. A DAG where:
- **Nodes** = individual courses, colored by phase (Phase 1 = blue, Phase 2 = purple, Phase 3 = orange, Phase 4 = grey)
- **Edges** = prerequisite relationships (directed arrows)
- Each node shows: course title, duration, level badge, skill it addresses
- Click on a node → right panel shows course detail
- Phase groupings shown as swimlane-style background sections
- Bottom shows total estimated time to competency

React Flow setup with dagre auto-layout (never hardcode positions — with 4+ courses in a phase they will overlap):
```jsx
import dagre from '@dagrejs/dagre';

const NODE_WIDTH = 200;
const NODE_HEIGHT = 80;

function getLayoutedElements(nodes, edges) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', ranksep: 80, nodesep: 40 });

  nodes.forEach(n => g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT }));
  edges.forEach(e => g.setEdge(e.source, e.target));

  dagre.layout(g);

  const layoutedNodes = nodes.map(n => {
    const { x, y } = g.node(n.id);
    return { ...n, position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 } };
  });

  return { nodes: layoutedNodes, edges };
}

// Build raw nodes and edges first, then run layout
const rawNodes = pathway.flatMap(phase =>
  phase.courses.map(course => ({
    id: course.id,
    type: 'courseNode',
    position: { x: 0, y: 0 },  // dagre overwrites these
    data: { course, phase_label: phase.phase_label }
  }))
);

const rawEdges = pathway.flatMap(phase =>
  phase.courses.flatMap(course =>
    (course.prerequisites || []).map(prereqId => ({
      id: `${prereqId}-${course.id}`,
      source: prereqId,
      target: course.id,
      animated: true,
      type: 'smoothstep'
    }))
  )
);

const { nodes, edges } = getLayoutedElements(rawNodes, rawEdges);
```

> **Why dagre?** The naive `x: ci * 220, y: pi * 160` grid breaks immediately when a phase has 4+ courses — nodes either overlap or run off-screen. Dagre is a Sugiyama-style hierarchical layout algorithm that handles arbitrary DAGs cleanly with proper rank assignment, crossing minimization, and coordinate assignment. It's what every serious graph tool (Mermaid, Graphviz) uses internally.

#### Right Panel: Reasoning Trace
- Collapsible sections for each reasoning trace section
- "Why this pathway?" header
- Candidate Assessment, Gap Identification (bullet list), Course Selection Rationale, Ordering Logic, Time to Competency
- This is the Reasoning Trace feature (10% criterion)

### Page 3: Course Detail Drawer (slide-in)
When a node is clicked in React Flow, a right drawer slides in showing:
- Full course title and description
- Provider + link
- Duration
- Level badge
- "Addresses skill gap: X" with gap context
- Prerequisites list with links to those courses
- Score breakdown (gap_criticality, impact, level_fit, efficiency)

### Responsive Behavior
- Desktop: 3-panel layout (25% / 50% / 25%)
- Tablet: Left panel collapses to top summary, full-width React Flow below
- Mobile: Accordion — Summary → Pathway (scrollable horizontal flow) → Reasoning Trace

---

## 7. Reasoning Trace UI — Dedicated Feature

Since the rubric allocates 10% to this specifically, it deserves its own treatment.

The reasoning trace is not just a log — it's rendered as a **step-by-step chain of thought** with:

1. **Step indicator** — "Step 1 of 5: Candidate Assessment"
2. **Data source badge** — "Based on resume text"
3. **Decision text** — the LLM's reasoning paragraph
4. **Evidence quote** — the specific resume/JD text that triggered this decision
5. **Confidence indicator** — derived from the gap_size and impact scores

Component: `<ReasoningTrace trace={sessionData.reasoning_trace} />`

The user can click "Show Reasoning" button on any course card, which highlights the relevant trace step.

---

## 8. File Structure

```
adaptive-onboarding/
├── server/
│   ├── src/
│   │   ├── index.js                    # Express app entry, middleware setup
│   │   ├── routes/
│   │   │   ├── sessions.js             # POST /sessions/analyze, GET /sessions/:id
│   │   │   ├── courses.js              # GET /courses, POST /courses (seed)
│   │   │   └── skills.js              # GET /skills
│   │   ├── parsers/
│   │   │   └── extractText.js          # PDF and DOCX → plain text
│   │   ├── ai/
│   │   │   ├── gemini.js               # Gemini client singleton
│   │   │   ├── extractResumeSkills.js  # Step 2
│   │   │   ├── extractJDRequirements.js# Step 3
│   │   │   ├── normalizeSkills.js      # Step 4 (vector search)
│   │   │   ├── computeSkillGap.js      # Step 5 (pure logic)
│   │   │   ├── adaptivePathway.js      # Step 6 (THE ALGORITHM)
│   │   │   └── generateReasoningTrace.js # Step 7
│   │   ├── db/
│   │   │   ├── supabaseClient.js       # Supabase client init
│   │   │   └── schema.sql              # Full schema (also used for migration)
│   │   ├── scripts/
│   │   │   └── seedCatalog.js          # Bulk seed 60+ courses
│   │   └── utils/
│   │       ├── levelToNum.js           # "beginner"→1, "intermediate"→2, "advanced"→3
│   │       ├── cosineSimilarity.js     # Fallback local cosine calc
│   │       └── retry.js               # Retry wrapper for LLM calls
│   ├── .env.example
│   ├── package.json
│   └── Dockerfile
├── client/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx                     # Router setup
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx
│   │   │   └── ResultsPage.jsx
│   │   ├── components/
│   │   │   ├── UploadZone.jsx
│   │   │   ├── AnalyzeButton.jsx
│   │   │   ├── SkillChips.jsx          # Green/red skill chips
│   │   │   ├── PathwayFlow.jsx         # React Flow canvas
│   │   │   ├── CourseNode.jsx          # Custom React Flow node
│   │   │   ├── CourseDrawer.jsx        # Slide-in detail panel
│   │   │   ├── ReasoningTrace.jsx      # Reasoning trace renderer
│   │   │   ├── GapSummaryCard.jsx      # Left panel profile summary
│   │   │   └── PhaseTimeline.jsx       # Bottom timeline showing phases
│   │   ├── hooks/
│   │   │   ├── useSession.js           # Fetch session data, handle loading/error
│   │   │   └── useAnalyze.js           # POST to analyze endpoint
│   │   ├── api/
│   │   │   └── client.js              # Axios instance with base URL
│   │   └── utils/
│   │       └── formatDuration.js       # 4.5 → "4h 30m"
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
├── docker-compose.yml                  # Local: Express + Postgres
├── Dockerfile                          # Production multi-stage
├── README.md
└── PLAN.md
```

---

## 9. Environment Variables

```env
# server/.env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...            # Service role key (not anon, needed for server-side)
GEMINI_API_KEY=AIza...
PORT=3001
SEED_SECRET=changeme_for_prod          # Required header to POST /courses

# client/.env
VITE_API_URL=http://localhost:3001/api/v1
```

---

## 10. Build Sequence (Day by Day)

### Day 1: Foundation
- [ ] Init monorepo (`/server`, `/client`)
- [ ] Set up Supabase project, run `schema.sql`, enable pgvector extension
- [ ] Implement `extractText.js` (PDF + DOCX parsing) — test with 3 sample files
- [ ] Implement `gemini.js` client (basic completion call working)
- [ ] Implement `extractResumeSkills.js` — test with 2 sample resumes, verify JSON output

### Day 2: AI Pipeline Core
- [ ] Implement `extractJDRequirements.js` — test with 2 sample JDs
- [ ] Implement `normalizeSkills.js` (generate embeddings, vector search in Supabase)
- [ ] Implement `computeSkillGap.js` — unit test with mock data
- [ ] Run `seedCatalog.js` — seed all 60+ courses with embeddings

### Day 3: Adaptive Algorithm
- [ ] Implement full `adaptivePathway.js` — scoring, topological sort, phase grouping
- [ ] Implement `generateReasoningTrace.js`
- [ ] Wire up `POST /sessions/analyze` end-to-end
- [ ] Test full pipeline with 3 different resume+JD combinations

### Day 4: Frontend Foundation
- [ ] Scaffold Vite React app, Tailwind, react-router-dom
- [ ] Build `UploadPage.jsx` with `react-dropzone` 
- [ ] Build `useAnalyze.js` hook (POST + loading states)
- [ ] Implement basic `ResultsPage.jsx` showing raw JSON (not styled yet, just verify data flows)

### Day 5: Visualization
- [ ] Implement `PathwayFlow.jsx` using React Flow
- [ ] Build `CourseNode.jsx` custom node component
- [ ] Build `CourseDrawer.jsx` slide-in panel
- [ ] Wire click → drawer open

### Day 6: Polish UI + Reasoning Trace
- [ ] Build `GapSummaryCard.jsx` left panel
- [ ] Build `ReasoningTrace.jsx` with collapsible sections
- [ ] Add `PhaseTimeline.jsx` at bottom
- [ ] Responsive layout (tablet/mobile)
- [ ] Error states (failed parse, LLM error, no gaps found)

### Day 7: Cross-Domain Testing + README + Slide Deck
- [ ] Test with Operational role (e.g. Warehouse Manager JD + non-tech resume) — verify it works
- [ ] Test edge cases: resume with no matching skills, JD for very niche role
- [ ] Write `README.md` (setup instructions, architecture overview, dependency list, logic explanation)
- [ ] Write `Dockerfile`, test Docker build
- [ ] Add sample resume + JD files to `/examples` folder in repo (tech pair + ops pair — see Section 16)
- [ ] **Draft all 5 slides** — content only, no polish needed yet (this moves off Day 8 to avoid crunch)

### Day 8: Buffer + Polish + Submit
- [ ] Fix any bugs surfaced during Day 7 testing — this is why Day 8 is intentionally light
- [ ] Polish slide deck visuals (add diagrams, clean up layout)
- [ ] Record 2–3 min demo video (use pre-saved session IDs from Section 16 as fallback if pipeline is slow)
- [ ] Final deployment check: Railway/Render + Vercel + Supabase all live
- [ ] Verify public GitHub repo: no leaked `.env` files, README complete, Dockerfile builds cleanly
- [ ] Submit

> **Why slide deck on Day 7, not Day 8?** Doing the deck, demo video, deployment verification, and Docker testing in a single day leaves zero buffer for anything that goes wrong. Moving the deck draft to Day 7 means Day 8 is: fix issues → polish → record → submit. Much safer.

---

## 11. How Each Rubric Criterion is Addressed

| Criterion | Weight | Our Approach |
|---|---|---|
| Technical Sophistication | 20% | Vector-based skill normalization, scored DAG traversal, multi-step LLM pipeline with structured output |
| Communication & Documentation | 20% | Complete README, Dockerfile, demo video, clean 5-slide deck |
| Grounding and Reliability | 15% | ALL course recommendations pulled from seeded catalog only — LLM cannot invent courses. Prompts explicitly say "use only provided data" |
| User Experience | 15% | React Flow DAG visualization, course detail drawer, phase grouping, responsive layout |
| Reasoning Trace | 10% | Dedicated LLM step that generates structured reasoning; rendered as interactive step-by-step UI component |
| Product Impact | 10% | Show "Training time saved" stat: (all possible courses - recommended courses) * average duration |
| Cross-Domain Scalability | 10% | Operational domain courses in catalog; domain field in schema; demo video shows both a tech hire and an operational hire |

---

## 12. Grounding Strategy — Zero Hallucinations

This is explicitly called out as a criterion. Our approach:

1. **The LLM never names courses.** The LLM only extracts skills from documents and generates reasoning text. Course names always come from the DB query results.

2. **Course retrieval is deterministic.** We query by `skill_id` (exact match) then by vector similarity against the catalog. The LLM sees the course list and writes reasoning about it — it does not invent the list.

3. **Prompts include explicit anti-hallucination instructions:** "Only reference data provided to you. Do not suggest courses, tools, or resources not in the provided catalog."

4. **JSON schema enforcement:** Gemini structured output (or manual parsing with schema validation) ensures the LLM response always matches our expected shape. Use `zod` for response validation on the server.

---

## 13. Slide Deck Outline (Slide by Slide)

**Slide 1: Solution Overview**
- Headline: "From Resume to Ready: Personalized Onboarding in 60 Seconds"
- The problem (one sentence, stat on wasted onboarding hours)
- Our solution (one diagram: Resume + JD → Gap Engine → Pathway)
- Value prop: reduces redundant training, accelerates competency

**Slide 2: Architecture & Workflow**
- Data flow diagram: Upload → Text Extraction → LLM (skills) → Vector Normalization → Gap Analysis → Adaptive Algorithm → React Flow UI
- Label each stage with the component name from our codebase
- Show Supabase at center (stores skills, courses, sessions)

**Slide 3: Tech Stack & Models**
- LLM: Gemini 1.5 Flash (extraction, reasoning trace generation)
- Embeddings: Gemini text-embedding-004
- Vector DB: Supabase pgvector
- Frontend: React + React Flow
- Backend: Node.js + Express
- Why each choice was made (one phrase per tool)

**Slide 4: Algorithms & Training**
- Two sub-sections: Skill Extraction Logic, Adaptive Pathing Algorithm
- Skill Extraction: multi-turn structured prompt → JSON → vector normalization
- Adaptive Pathing: Priority scoring formula (show the weights), Kahn's topological sort, phase grouping
- Code snippet or pseudocode of the scoring function

**Slide 5: Datasets & Metrics**
- Datasets: O*NET (skill taxonomy reference for catalog), Kaggle Resume Dataset (used for testing/validation), Kaggle Jobs & JD Dataset (used for testing)
- Internal metrics: Skill extraction accuracy (test against labeled resumes), pathway relevance score (manual eval on 10 test cases), avg courses per pathway, avg training hours saved vs generic onboarding
- Hallucination rate: 0% (enforced by catalog-grounded retrieval)

---

## 14. Key Risks and Mitigations

| Risk | Mitigation |
|---|---|
| LLM returns malformed JSON | `retry.js` wrapper retries once with stricter prompt; falls back to empty skills array with error message |
| Gemini rate limit during demo | Cache responses in `sessions` table; demo uses pre-computed session IDs as fallback |
| Resume text extraction fails (scanned PDF) | Detect low word count (<50 words) and show "Please upload a text-based PDF" error |
| No courses found for a skill gap | Vector search fallback with lower similarity threshold (0.6); if still none, show "No catalog entry yet" gracefully |
| pgvector extension not enabled | `schema.sql` includes `CREATE EXTENSION IF NOT EXISTS vector;` as first line |
| Demo video: pathway looks confusing | React Flow auto-layout (use `dagre` layout algorithm for clean top-down graph) |

---

## 15. Demo Video Script (2–3 min)

**0:00–0:20** — Problem statement voiceover while showing static "generic onboarding checklist" screenshot  
**0:20–0:40** — Upload a software engineer resume (3 years exp, knows React/Python, missing Docker/Kubernetes/TypeScript)  
**0:40–1:00** — Upload a Senior Full-Stack Engineer JD (requires Docker, Kubernetes, TypeScript, AWS)  
**1:00–1:20** — Hit Analyze, show loading state, result appears  
**1:20–1:50** — Walk through left panel (gap summary: 4 gaps found), center panel (React Flow DAG, 4 phases, 6 courses), click one course node to show drawer  
**1:50–2:10** — Expand Reasoning Trace, read one section aloud  
**2:10–2:30** — **Second demo:** Upload warehouse operations resume + Warehouse Manager JD → completely different pathway (cross-domain scalability proof)  
**2:30–2:50** — Show GitHub repo, README, Docker command  
**2:50–3:00** — Close with stat: "28 hours of targeted training vs 80 hours of generic onboarding"

---

## 16. Demo Fallback — Pre-Computed Sessions

If the pipeline is slow or breaks during judging, you need to be able to navigate directly to pre-computed results without re-running the full analysis. Do this on Day 7 after the system is stable.

### What to prepare
1. Create two real example file pairs and commit them to `/examples/`:
   - `examples/tech/resume.pdf` — Software engineer, 3 yrs exp, skills: React, Python, Node.js, PostgreSQL. Missing: Docker, Kubernetes, TypeScript, AWS
   - `examples/tech/jd.pdf` — Senior Full-Stack Engineer role requiring Docker, Kubernetes, TypeScript, AWS, React (advanced)
   - `examples/ops/resume.pdf` — Warehouse associate, 2 yrs exp, skills: Forklift Operation, Manual Inventory. Missing: WMS software, OSHA certification, Supply Chain basics
   - `examples/ops/jd.pdf` — Warehouse Operations Manager requiring WMS, OSHA, Supply Chain, Team Leadership

2. Run the full pipeline on both pairs manually once the system is stable. Note the returned `session_id` for each.

3. Store these in a `examples/session_ids.json` file (committed to repo, never in `.env`):
```json
{
  "tech": "pre-computed-uuid-here",
  "ops": "pre-computed-uuid-here"
}
```

4. Add a "Load Demo" button on the upload page that navigates directly to `/results/<session_id>` for the selected pair. This is the demo fallback — if the LLM is rate-limited or slow during live judging, you click "Load Demo" and results appear instantly.

### Demo video strategy
Record the video using the pre-computed sessions, not a live run. This means the video always shows a clean, fast result regardless of network conditions on demo day. The live system still works for judges who want to test it themselves.

---

*Last updated: March 2026. This document is the single source of truth for the entire build.*