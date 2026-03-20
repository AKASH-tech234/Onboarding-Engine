# Team Division — Technical Work Only
**4 People | P1 = 30% · P2 = 30% · P3 = 20% · P4 = 20%**
**Soft work (README, slides, demo video, example files) is excluded entirely from this document.**

Every file is owned by exactly one person. Every technical task is assigned. Zero overlap.

---

## File Ownership Map

| File / Module | Owner |
|---|---|
| `server/src/db/schema.sql` | P1 |
| `server/src/db/supabaseClient.js` | P1 |
| `server/src/parsers/extractText.js` | P1 |
| `server/src/ai/gemini.js` | P1 |
| `server/src/utils/retry.js` | P1 |
| `server/src/ai/extractResumeSkills.js` | P1 |
| `server/src/ai/extractJDRequirements.js` | P1 |
| `server/src/ai/normalizeSkills.js` | P1 |
| `server/src/ai/generateReasoningTrace.js` | P1 |
| `server/src/utils/levelToNum.js` | P3 |
| `server/src/utils/cosineSimilarity.js` | P3 |
| `server/src/ai/computeSkillGap.js` | P3 |
| `server/src/ai/adaptivePathway.js` | P3 |
| `server/src/scripts/seedCatalog.js` | P3 |
| All `server/src/tests/` files | P3 |
| `server/src/index.js` | P4 |
| `server/src/routes/sessions.js` | P4 |
| `server/src/routes/courses.js` | P4 |
| `server/src/routes/skills.js` | P4 |
| `Dockerfile` | P4 |
| `docker-compose.yml` | P4 |
| `client/src/App.jsx` + routing | P2 |
| `client/src/api/client.js` | P2 |
| `client/src/mockData.js` | P2 |
| `client/src/pages/UploadPage.jsx` | P2 |
| `client/src/pages/ResultsPage.jsx` | P2 |
| `client/src/components/UploadZone.jsx` | P2 |
| `client/src/components/AnalyzeButton.jsx` | P2 |
| `client/src/components/ExampleBadge.jsx` | P2 |
| `client/src/components/GapSummaryCard.jsx` | P2 |
| `client/src/components/SkillChips.jsx` | P2 |
| `client/src/components/PathwayFlow.jsx` | P2 |
| `client/src/components/CourseNode.jsx` | P2 |
| `client/src/components/CourseDrawer.jsx` | P2 |
| `client/src/components/ReasoningTrace.jsx` | P2 |
| `client/src/components/PhaseTimeline.jsx` | P2 |
| `client/src/hooks/useAnalyze.js` | P2 |
| `client/src/hooks/useSession.js` | P2 |
| `client/src/utils/formatDuration.js` | P2 |

---

## Coordination Checkpoints

| # | When | Deliverable | From → To |
|---|---|---|---|
| **CP-1** | End of Day 1 | `supabaseClient.js` live, `gemini.js` tested, `.env` values shared | P1 → P3, P4 |
| **CP-2** | End of Day 3 | `computeSkillGap.js` + `adaptivePathway.js` confirmed importable | P3 → P4 |
| **CP-3** | End of Day 3 | `POST /sessions/analyze` fully wired and returning correct JSON | P4 → P2 (P2 switches from mock to live) |
| **CP-4** | End of Day 7 | Railway URL live | P4 → P2 (Vercel deploy needs the URL) |

---

---

# P1 — AI Pipeline + Database (30%)

**Owns:** Everything that touches the LLM or the database directly — schema, Supabase client, text parsing, Gemini calls, all five AI step files. This is the deepest, most serial work. Nothing else works until P1's foundation is done.

---

## Day 1 — P1

### 1.1 Monorepo + Server Init
- [ ] Create root folder `adaptive-onboarding/`, subfolders `/server` and `/client`
- [ ] `cd server && npm init -y`
- [ ] Install dependencies: `express multer cors dotenv pdf-parse mammoth @google/generative-ai @supabase/supabase-js zod`
- [ ] Install dev dependencies: `nodemon`
- [ ] Create `server/.env.example`:
  ```
  SUPABASE_URL=
  SUPABASE_SERVICE_KEY=
  GEMINI_API_KEY=
  PORT=3001
  SEED_SECRET=
  ```
- [ ] Create `server/src/` directory structure: `ai/`, `db/`, `parsers/`, `routes/`, `scripts/`, `utils/`
- [ ] Init git repo at root, create `.gitignore` covering `node_modules`, `.env`, `dist`, `client/dist`
- [ ] First commit: push to GitHub, set repo public
- [ ] Share real `.env` values with all team members via secure channel (never commit)

### 1.2 Supabase Schema + Client
- [ ] Create Supabase project (free tier), copy `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` to `.env`
- [ ] In Supabase SQL editor: `CREATE EXTENSION IF NOT EXISTS vector;`
- [ ] Write `server/src/db/schema.sql`:
  ```sql
  CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    domain TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT now()
  );

  CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    skill_id UUID REFERENCES skills(id),
    level TEXT CHECK (level IN ('beginner','intermediate','advanced')),
    level_num INTEGER CHECK (level_num IN (1,2,3)),
    duration_hrs NUMERIC(4,1),
    domain TEXT NOT NULL,
    provider TEXT,
    url TEXT,
    prerequisites UUID[] DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT now()
  );

  CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_text TEXT,
    jd_text TEXT,
    extracted_skills JSONB,
    required_skills JSONB,
    skill_gap JSONB,
    pathway JSONB,
    reasoning_trace JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
  );

  CREATE TABLE skill_course_map (
    course_id UUID REFERENCES courses(id),
    skill_id UUID REFERENCES skills(id),
    impact NUMERIC(3,2) CHECK (impact BETWEEN 0 AND 1),
    PRIMARY KEY (course_id, skill_id)
  );

  CREATE INDEX ON skills USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
  CREATE INDEX ON courses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
  ```
- [ ] Run `schema.sql` in Supabase SQL editor — verify all 4 tables created, both indexes exist, no errors
- [ ] Write `server/src/db/supabaseClient.js`:
  - Import `createClient` from `@supabase/supabase-js`
  - Init with `process.env.SUPABASE_URL` and `process.env.SUPABASE_SERVICE_KEY`
  - Export singleton `supabase`
- [ ] Verify connection: `node -e` test that inserts one row into `skills`, reads it back, deletes it — confirm works
- [ ] **CP-1:** confirm to P3 and P4 that schema is live and credentials shared

### 1.3 Text Extraction
- [ ] Write `server/src/parsers/extractText.js`:
  - `async function extractText({ buffer, mimetype })`
  - PDF (`application/pdf`): `await pdfParse(buffer)` → `.text`
  - DOCX (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`): `await mammoth.extractRawText({ buffer })` → `.value`
  - Any other mimetype: `throw new Error('UNSUPPORTED_FORMAT')`
  - Normalize: replace `/\n{3,}/g` with `\n\n`, `.trim()`
  - `wordCount = text.split(/\s+/).filter(Boolean).length`
  - If `wordCount < 50`: `throw new Error('SCANNED_PDF')`
  - Return `{ text, wordCount }`
- [ ] Test manually: run with one PDF resume, one DOCX resume, one PDF JD — log first 300 chars + wordCount each, confirm correct text extracted

### 1.4 Gemini Client + Retry Utility
- [ ] Write `server/src/ai/gemini.js`:
  - `const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY)`
  - `async function complete(systemPrompt, userPrompt)`:
    - Call `gemini-1.5-flash` with `[{ role: 'user', parts: [{ text: systemPrompt + '\n\n' + userPrompt }] }]`
    - Strip code fences: `.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim()`
    - Return cleaned string
  - `async function embed(text)`:
    - Call `text-embedding-004` with `{ content: { parts: [{ text }] } }`
    - Return `result.embedding.values` (float array, length 768)
  - Export `{ complete, embed }`
- [ ] Write `server/src/utils/retry.js`:
  - `async function withRetry(fn, maxAttempts = 2)`:
    - Call `await fn()`
    - If throws and `attempt < maxAttempts`: wait `1000ms`, retry
    - If still throws: re-throw
  - Export `{ withRetry }`
- [ ] Test: `complete('You are helpful.', 'Return {"ok":true}')` — log result, verify no fences, parseable JSON

### 1.5 Resume Skill Extraction
- [ ] Write `server/src/ai/extractResumeSkills.js`:
  - `async function extractResumeSkills(resumeText)`:
  - System prompt: `"You are a precise HR data extraction engine. Extract ONLY skills explicitly mentioned or clearly implied by the resume text. Do NOT infer skills not evidenced in the text. Return ONLY valid JSON, no markdown, no explanation."`
  - User prompt:
    ```
    Extract all skills from this resume. For each skill return:
    - name: canonical skill name (e.g. "React" not "ReactJS")
    - level: one of ["beginner","intermediate","advanced"] inferred from context
    - years: numeric years or null
    - evidence: one sentence from resume supporting this skill

    Return format:
    {"candidate_name":string|null,"total_experience_years":number|null,"current_role":string|null,"skills":[{"name":string,"level":string,"years":number|null,"evidence":string}]}

    Resume:
    <resumeText>
    ```
  - Call `withRetry(() => complete(system, user))`
  - `JSON.parse(response)` — throws → `throw new Error('LLM_JSON_INVALID')`
  - Validate with zod:
    ```js
    z.object({
      candidate_name: z.string().nullable(),
      total_experience_years: z.number().nullable(),
      current_role: z.string().nullable(),
      skills: z.array(z.object({
        name: z.string(),
        level: z.enum(['beginner','intermediate','advanced']),
        years: z.number().nullable(),
        evidence: z.string()
      }))
    })
    ```
  - Return validated object
- [ ] Test with 2 real resumes — verify canonical names (no "ReactJS", "Node.JS"), sensible level inferences, no hallucinated skills

---

## Day 2 — P1

### 2.1 JD Requirement Extraction
- [ ] Write `server/src/ai/extractJDRequirements.js`:
  - `async function extractJDRequirements(jdText)`:
  - System prompt: `"You are a precise job requirements extraction engine. Extract ONLY skills and competencies explicitly stated in the job description. Return ONLY valid JSON, no markdown, no explanation."`
  - User prompt: extract `name`, `level`, `required` (true if mandatory, false if preferred), `context` (exact JD phrase). Return `{ job_title, department, seniority_level, skills: [{name, level, required, context}] }`
  - Same call + parse + retry pattern as `extractResumeSkills.js`
  - Zod:
    ```js
    z.object({
      job_title: z.string().nullable(),
      department: z.string().nullable(),
      seniority_level: z.string().nullable(),
      skills: z.array(z.object({
        name: z.string(),
        level: z.enum(['beginner','intermediate','advanced']),
        required: z.boolean(),
        context: z.string()
      }))
    })
    ```
  - Return validated object
- [ ] Test with 2 real JDs — verify `required: true` for "must have", `required: false` for "nice to have"

### 2.2 Skill Normalization
- [ ] Write `server/src/ai/normalizeSkills.js`:
  - `async function normalizeSkills(skillNames)` — `skillNames: string[]`
  - For each name:
    1. `const vec = await embed(skillName)`
    2. Query Supabase:
       ```sql
       SELECT id, name, 1 - (embedding <=> $1) AS similarity
       FROM skills ORDER BY embedding <=> $1 LIMIT 1
       ```
       (use `supabase.rpc` or raw query via `supabase` client with the vector as parameter)
    3. If `similarity >= 0.85`: return `{ original: skillName, normalized_id: row.id, normalized_name: row.name, matched: true }`
    4. If `similarity < 0.85`: `INSERT INTO skills (name, category, domain, embedding) VALUES ($1,'Unknown','Unknown',$2)` → return `{ original: skillName, normalized_id: newId, normalized_name: skillName, matched: false }`
  - Return array, one result per input skill
- [ ] Test: pass `['ReactJS','React.js','Node.JS','K8s','Kubernetes']` — all React variants must resolve to same UUID, Node variants same UUID, K8s + Kubernetes same UUID

---

## Day 3 — P1

### 3.1 Reasoning Trace Generation
- [ ] Write `server/src/ai/generateReasoningTrace.js`:
  - `async function generateReasoningTrace({ extractedSkills, requiredSkills, skillGap, pathway })`
  - System: `"You are an expert L&D advisor. Write a clear reasoning trace explaining WHY each recommendation was made. Cite specific skill gaps. Only reference data provided — never invent course names or skills."`
  - User: inject all four blobs as JSON strings, request 5 numbered sections:
    ```
    1. Candidate Assessment (2–3 sentences on the candidate's current profile)
    2. Gap Identification (one bullet per gap: skill name, severity, why it matters)
    3. Course Selection Rationale (one bullet per recommended course: why this course for this gap)
    4. Pathway Ordering Logic (why the sequence is ordered this way)
    5. Estimated Time to Competency (sum durations, state total hrs and realistic timeline)
    ```
  - Call `withRetry(() => complete(system, user))` — response is free text, not JSON
  - Parse sections by splitting on `\n1.`, `\n2.`, `\n3.`, `\n4.`, `\n5.`:
    ```js
    {
      candidate_assessment: string,
      gap_identification: string,
      course_selection_rationale: string,
      pathway_ordering_logic: string,
      estimated_time_to_competency: string,
      raw: string
    }
    ```
  - If parse fails (LLM didn't use numbered format): return `{ raw: fullText }` — UI falls back gracefully
- [ ] Test: call with hardcoded mock data for all 4 params — verify response parses into 5 sections correctly

---

## Day 7 — P1

### 7.1 Clean Up + Final Verification
- [ ] Remove all `console.log` debug statements from every P1 file
- [ ] Run `extractResumeSkills` + `extractJDRequirements` + `normalizeSkills` + `generateReasoningTrace` sequentially on one real resume+JD pair — verify each returns correct shape
- [ ] Verify Supabase `skills` table has no orphaned rows from test runs that shouldn't be there
- [ ] Confirm `server/.env.example` has all required keys, no real values

---

## Day 8 — P1

### 8.1 Final Pipeline Checks
- [ ] Run the full pipeline end-to-end via `POST /sessions/analyze` on production (P4's Railway deployment) — verify complete response shape
- [ ] Verify `generateReasoningTrace` returns at minimum `{ raw: string }` on production (never crashes)
- [ ] Confirm `extractResumeSkills` and `extractJDRequirements` both handle the ops-domain resume+JD without returning Technical skills
- [ ] `grep -r "console.log" server/src/ai/ server/src/parsers/ server/src/db/` — fix any found

---

---

# P2 — Frontend (30%)

**Owns:** The entire `client/src/` directory — every page, component, hook, utility. Uses `mockData.js` for Days 4–5, switches to live backend when P4 confirms `POST /sessions/analyze` is wired (end of Day 3 / start of Day 5).

---

## Day 4 — P2

### 4.1 Client Scaffold
- [ ] `npm create vite@latest client -- --template react` from repo root
- [ ] `cd client && npm install tailwindcss postcss autoprefixer axios react-router-dom react-dropzone reactflow @dagrejs/dagre`
- [ ] `npx tailwindcss init -p` — set `content: ['./src/**/*.{js,jsx}']` in `tailwind.config.js`
- [ ] Add to `src/index.css`: `@tailwind base; @tailwind components; @tailwind utilities;`
- [ ] Write `src/App.jsx`:
  - `BrowserRouter` wrapping `Routes`
  - `<Route path="/" element={<UploadPage />} />`
  - `<Route path="/results/:id" element={<ResultsPage />} />`
- [ ] Write `src/api/client.js`:
  - Axios instance: `baseURL: import.meta.env.VITE_API_URL`
  - Export as default
- [ ] Write `client/.env`: `VITE_API_URL=http://localhost:3001/api/v1`
- [ ] Write `src/mockData.js` — hardcoded object matching the exact shape of `POST /sessions/analyze` response from plan Section 4:
  - `session_id`: fake UUID
  - `candidate`: `{ name: 'Alex Chen', current_role: 'Junior Dev', total_experience_years: 3 }`
  - `skill_gap_summary`: `{ total_gaps: 4, critical_gaps: 3, already_met: 5 }`
  - `pathway.phases`: 3 phases, 5 courses total, each course has `id`, `title`, `description`, `level`, `level_num`, `duration_hrs`, `provider`, `url`, `addresses_skill`, `gap_type`, `score`, `score_breakdown`, `prerequisites: []`
  - `reasoning_trace`: `{ candidate_assessment: '...', gap_identification: '...', course_selection_rationale: '...', pathway_ordering_logic: '...', estimated_time_to_competency: '...', raw: '...' }`
  - `total_training_hrs`: 24.5

### 4.2 Upload Page
- [ ] Write `src/pages/UploadPage.jsx`:
  - State: `resumeFile` (File|null), `jdFile` (File|null), `jdText` (string), `jdMode` ('file'|'text'), `isLoading` (bool), `error` (string|null)
  - Layout: centered card `max-w-[640px] mx-auto mt-16 p-8` on `bg-slate-50 min-h-screen`
  - Title: "AI Onboarding Engine" heading
  - Two `<UploadZone>` components stacked
  - Toggle button: "Upload JD file" / "Paste JD text" — switches between `<UploadZone>` and `<textarea>` for JD input
  - `<AnalyzeButton>` at bottom
  - `<ExampleBadge>` below button
  - Error banner below button: only visible when `error !== null`, dismissible
  - On submit: `const data = await analyze(resumeFile, jdFile, jdText)` → `navigate('/results/' + data.session_id)`
- [ ] Write `src/components/UploadZone.jsx`:
  - Props: `type` ('resume'|'jd'), `onFile` (callback receiving File), `file` (File|null)
  - `useDropzone({ accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] }, onDrop: files => onFile(files[0]) })`
  - Three visual states:
    - Empty: dashed border `border-2 border-dashed border-slate-300 rounded-xl p-8`, upload icon SVG, label text
    - Has file: solid border `border-slate-400`, filename in `font-medium`, file size in `text-slate-400 text-sm`, `×` remove button that calls `onFile(null)`
    - Dragover (`isDragActive`): `border-blue-400 bg-blue-50`
  - Labels: resume → "Drop your resume (PDF or DOCX)", jd → "Drop the job description"
- [ ] Write `src/components/AnalyzeButton.jsx`:
  - Props: `disabled` (bool), `loading` (bool), `onClick`
  - `disabled` = `!resumeFile || (!jdFile && !jdText.trim())`
  - Loading: spinning SVG (4 lines, `animate-spin`) + "Analyzing..." text
  - Active: "Generate Pathway →"
  - Tailwind: `w-full py-3 rounded-lg font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors`
- [ ] Write `src/hooks/useAnalyze.js`:
  - Returns `{ analyze, isLoading, error }`
  - `analyze(resumeFile, jdFile, jdText)`:
    - Build `FormData`: append `resume` file, append `jd` file OR `jd_text` string (check which is present)
    - `POST /sessions/analyze` via axios client
    - Return `response.data`
  - `isLoading`: true from start of request until completion
  - Error: `err.response?.data?.error || err.message`

### 4.3 Results Page Skeleton
- [ ] Write `src/pages/ResultsPage.jsx` (data-flow verification only — not the real layout):
  - `const { id } = useParams()`
  - `const { data, isLoading, error } = useSession(id)`
  - Loading → full-screen spinner `<div className="flex h-screen items-center justify-center"><svg className="animate-spin h-8 w-8 text-blue-600" ...></svg></div>`
  - Error → `<div className="flex h-screen items-center justify-center flex-col gap-4"><p>{error}</p><a href="/">← Start Over</a></div>`
  - Data → `<pre className="p-4 text-xs overflow-auto h-screen">{JSON.stringify(data, null, 2)}</pre>`
- [ ] Write `src/hooks/useSession.js`:
  - Returns `{ data, isLoading, error }`
  - `useEffect`: `GET /sessions/${id}` via axios client on mount
  - 404 → `setError('Session not found')`
  - Network error → `setError(err.message)`
  - Success → `setData(response.data)`

### 4.4 ExampleBadge Component
- [ ] Write `src/components/ExampleBadge.jsx`:
  - Hardcoded constants at top (filled in after Day 7 deployment):
    ```js
    const DEMO_SESSIONS = { tech: 'FILL_AFTER_DEPLOY', ops: 'FILL_AFTER_DEPLOY' }
    ```
  - `useNavigate` from react-router-dom
  - Render: `<div className="flex items-center gap-3 mt-4 text-sm text-slate-500">or try a sample →` + two badge buttons
  - Tech badge: `"💼 Tech Role"` — `onClick={() => navigate('/results/' + DEMO_SESSIONS.tech)}`
  - Ops badge: `"🏭 Ops Role"` — `onClick={() => navigate('/results/' + DEMO_SESSIONS.ops)}`
  - If either `=== 'FILL_AFTER_DEPLOY'`: disable that badge, add `title="Available after deployment"`
  - Tailwind badges: `inline-flex items-center px-3 py-1 bg-slate-100 hover:bg-slate-200 rounded-full cursor-pointer disabled:opacity-40`
- [ ] Day 7: update `DEMO_SESSIONS` constants with real UUIDs once P4 runs pre-computed sessions

---

## Day 5 — P2

### 5.1 Results Page Real Layout
- [ ] Replace raw JSON display in `ResultsPage.jsx` with the 3-panel layout:
  - Desktop: `<div className="grid grid-cols-[280px_1fr_320px] h-screen overflow-hidden">`
  - Left panel: `<div className="overflow-y-auto border-r border-slate-200 p-4">` → `<GapSummaryCard />`
  - Center panel: `<div className="overflow-hidden relative flex flex-col">` → `<PathwayFlow />` fills flex-1, `<PhaseTimeline />` at bottom
  - Right panel: `<div className="overflow-y-auto border-l border-slate-200 p-4">` → `<ReasoningTrace />`
  - State in `ResultsPage`: `selectedCourseId` (string|null) — passed to `PathwayFlow` as `onNodeClick` setter, and to `CourseDrawer` as `courseId`
  - Tablet (`md:` < 1024px): `grid-cols-1`, left panel `max-h-52 overflow-y-auto border-b`, center full width, right panel below
  - Mobile (< 768px): single column, all panels stacked, each with own scroll

### 5.2 Gap Summary Card + Skill Chips
- [ ] Write `src/components/GapSummaryCard.jsx`:
  - Props: `candidate`, `skillGapSummary`, `pathway`
  - Derive from `pathway.phases`: `alreadyMet` list (not in pathway + from `skill_gap_summary`), critical gaps (required), preferred gaps (not required)
  - Sections in order:
    - Candidate header: `candidate.name` (`text-lg font-semibold`), `candidate.current_role` (`text-slate-500 text-sm`), `candidate.total_experience_years + " yrs exp"` badge
    - Stats row: three inline chips — `total_gaps + " gaps"` (red), `critical_gaps + " required"` (orange), `already_met + " met"` (green)
    - "Already have" label + `<SkillChips items={...} color="green" />`
    - "Missing (required)" label + `<SkillChips items={...} color="red" />`
    - "Missing (preferred)" label + `<SkillChips items={...} color="amber" />`
    - Bottom: `"Est. training: " + total_training_hrs + "h"` in `text-sm text-slate-500`
- [ ] Write `src/components/SkillChips.jsx`:
  - Props: `items` (array of `{ skill, current, target }`), `color` ('green'|'red'|'amber')
  - Render each as `<span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium mr-1 mb-1 ..." title="${current || 'none'} → ${target}">{skill}</span>`
  - Color map: `green → bg-green-100 text-green-800`, `red → bg-red-100 text-red-800`, `amber → bg-amber-100 text-amber-800`

### 5.3 React Flow Visualization
- [ ] Write `src/components/PathwayFlow.jsx`:
  - Imports: `ReactFlow, Background, Controls, MiniMap` from `reactflow`; `dagre` from `@dagrejs/dagre`; `CourseNode`
  - Constants: `NODE_WIDTH = 200`, `NODE_HEIGHT = 80`
  - `function getLayoutedElements(nodes, edges)`:
    ```js
    const g = new dagre.graphlib.Graph()
    g.setDefaultEdgeLabel(() => ({}))
    g.setGraph({ rankdir: 'TB', ranksep: 80, nodesep: 40 })
    nodes.forEach(n => g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT }))
    edges.forEach(e => g.setEdge(e.source, e.target))
    dagre.layout(g)
    const layoutedNodes = nodes.map(n => {
      const { x, y } = g.node(n.id)
      return { ...n, position: { x: x - NODE_WIDTH/2, y: y - NODE_HEIGHT/2 } }
    })
    return { nodes: layoutedNodes, edges }
    ```
  - Build `rawNodes` from `pathway.phases.flatMap(phase => phase.courses.map(course => ({ id: course.id, type: 'courseNode', position: {x:0,y:0}, data: { course, phase_label: phase.phase_label } })))`
  - Build `rawEdges` from each `course.prerequisites.map(prereqId => ({ id: prereqId+'-'+course.id, source: prereqId, target: course.id, animated: true, type: 'smoothstep' }))`
  - `const { nodes, edges } = getLayoutedElements(rawNodes, rawEdges)`
  - Render `<div className="w-full h-full"><ReactFlow nodes={nodes} edges={edges} nodeTypes={{ courseNode: CourseNode }} fitView onNodeClick={(_, node) => onNodeClick(node.id)}><Background variant="dots" gap={16} /><Controls /><MiniMap className="hidden sm:block" /></ReactFlow></div>`
  - If `rawNodes.length === 0`: render centered empty state inside a `w-full h-full flex items-center justify-center` div — icon + "No pathway required" + "This candidate meets all requirements"
  - Props: `pathway` (phases array), `onNodeClick` (callback with course id)
- [ ] Write `src/components/CourseNode.jsx`:
  - Must be exactly `NODE_WIDTH × NODE_HEIGHT` (200px × 80px) — set `style={{ width: 200, height: 80 }}`
  - Props: React Flow passes `data: { course, phase_label }`
  - Layout (use absolute positioning within the fixed box):
    - Top-left: course title — `text-xs font-medium leading-tight line-clamp-2 w-[140px]`
    - Top-right: level badge — `B`/`I`/`A` in a `w-5 h-5 rounded text-xs flex items-center justify-center` — grey/blue/purple by `level_num`
    - Bottom-left: skill pill — `text-xs px-1 py-0.5 bg-slate-100 rounded`
    - Bottom-right: `formatDuration(course.duration_hrs)` in `text-xs text-slate-400`
  - Container: `border border-slate-200 rounded-lg bg-white shadow-sm hover:shadow-md cursor-pointer transition-shadow p-2`
  - Left border accent 3px by phase: `border-l-4` — Phase 1 `border-l-blue-500`, Phase 2 `border-l-purple-500`, Phase 3 `border-l-orange-500`, Phase 4 `border-l-slate-400`
  - React Flow handles: `<Handle type="target" position={Position.Top} style={{ opacity: 0 }} />` and `<Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />`

### 5.4 Course Drawer
- [ ] Write `src/components/CourseDrawer.jsx`:
  - Props: `courseId` (string|null), `pathway` (to look up the course object), `onClose`
  - Derive `course = pathway.phases.flatMap(p => p.courses).find(c => c.id === courseId)` — if null, render nothing
  - Render as fixed right-side panel `fixed top-0 right-0 h-full w-80 bg-white shadow-2xl z-20 overflow-y-auto`
  - Slide animation: `transition-transform duration-200 ${courseId ? 'translate-x-0' : 'translate-x-full'}`
  - Header: `course.title` in `font-semibold text-base` + `×` button `onClick={onClose}` top-right
  - Row: level badge (`Beginner`/`Intermediate`/`Advanced` full text) + duration pill
  - Provider: if `course.url` → `<a href={course.url} target="_blank" rel="noreferrer">{course.provider} ↗</a>` else plain text
  - Description: `<p className="text-sm text-slate-600 mt-3">{course.description}</p>`
  - "Addresses gap" section: `<p className="text-sm mt-3">Addresses gap: <strong>{course.addresses_skill}</strong> — {course.gap_type === 'missing' ? 'not on resume' : 'level upgrade needed'}</p>`
  - Score breakdown: heading "Why this course?" + 4 rows, each:
    ```jsx
    <div className="flex items-center gap-2 text-xs">
      <span className="w-36 text-slate-500">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full">
        <div className="h-1.5 bg-blue-500 rounded-full" style={{ width: value * 100 + '%' }} />
      </div>
      <span className="w-8 text-right text-slate-600">{(value * 100).toFixed(0)}%</span>
    </div>
    ```
  - Prerequisites: if `course.prerequisites.length > 0` → list them as `text-sm text-blue-600 underline cursor-pointer` items, clicking calls `onPrereqClick(prereqId)` prop (parent scrolls React Flow)

### 5.5 Utilities
- [ ] Write `src/utils/formatDuration.js`:
  - `export function formatDuration(hrs)`:
    - `hrs === 0` → `"0m"`
    - `hrs < 1` → `` `${Math.round(hrs * 60)}m` ``
    - `Number.isInteger(hrs)` → `` `${hrs}h` ``
    - else → `` `${Math.floor(hrs)}h ${Math.round((hrs % 1) * 60)}m` ``
- [ ] Update `useSession.js`: add a `DEMO_IDS` constant (same values as `ExampleBadge`) — if `GET /sessions/${id}` returns 404 AND `id === DEMO_IDS.tech || id === DEMO_IDS.ops`, instead of showing error, log a warning and return a specific "demo session expired" error message that tells the user to use the upload form instead

---

## Day 6 — P2

### 6.1 Reasoning Trace Component
- [ ] Write `src/components/ReasoningTrace.jsx`:
  - Props: `trace` (reasoning trace object), `activeSection` (string|null)
  - Section labels map: `{ candidate_assessment: 'Candidate Assessment', gap_identification: 'Gap Identification', course_selection_rationale: 'Course Selection', pathway_ordering_logic: 'Ordering Logic', estimated_time_to_competency: 'Time to Competency' }`
  - Each section: accordion item — header `flex justify-between items-center cursor-pointer py-2 border-b` + chevron SVG rotating `transition-transform duration-200 ${open ? 'rotate-180' : ''}`
  - Body: text split on `\n\n` → `<p>` tags; lines starting with `-` → `<li>` in `<ul className="list-disc pl-4 space-y-1 text-sm">`
  - Default open: `candidate_assessment` only
  - `activeSection` prop: if matches a section key → `ref.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })` and open it
  - Fallback: if only `trace.raw` exists → one panel "Reasoning" rendering `trace.raw` as paragraphs

### 6.2 Phase Timeline
- [ ] Write `src/components/PhaseTimeline.jsx`:
  - Props: `pathway` (phases array), `total_training_hrs`
  - Filter to phases with `phase.courses.length > 0`
  - Render horizontal strip: `flex items-center gap-0 px-6 py-3 border-t border-slate-200 bg-white text-xs`
  - Each phase step: colored circle `w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold` colored by phase number (blue-500/purple-500/orange-500/slate-400) + label below + duration below label
  - Between steps: `flex-1 h-px bg-slate-200`
  - After last step: `font-semibold text-slate-700 ml-4 whitespace-nowrap` showing `"Total: " + total_training_hrs + "h"`

### 6.3 All Error States
- [ ] `UploadPage.jsx` error banner: `{error && <div className="mt-3 flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm"><span className="flex-1">{error}</span><button onClick={() => setError(null)} className="text-red-400 hover:text-red-600">×</button></div>}`
- [ ] `ResultsPage.jsx` zero-gaps state: if `data.skill_gap_summary.total_gaps === 0`, replace center panel content with:
  ```jsx
  <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
    <div className="text-green-500 text-5xl">✓</div>
    <h2 className="text-xl font-semibold">No Skill Gaps Found</h2>
    <p className="text-slate-500 text-center">This candidate already meets all requirements for this role.</p>
  </div>
  ```
- [ ] `ResultsPage.jsx` 404 state: `<div className="flex h-screen items-center justify-center flex-col gap-3"><p className="text-slate-600">Session not found.</p><a href="/" className="text-blue-600 underline">Start New Analysis</a></div>`
- [ ] `ResultsPage.jsx` 500 state: `<div className="flex h-screen items-center justify-center flex-col gap-3"><p className="text-slate-600">Something went wrong.</p><button onClick={() => setRetry(r => r+1)} className="text-blue-600 underline">Try again</button></div>` — increment `retryCount` state to re-trigger `useEffect` in `useSession`
- [ ] `PathwayFlow.jsx` empty pathway: already handled in 5.3 above

### 6.4 Responsive Layout Audit
- [ ] Test at 1440px: 3 columns render, nothing overflows, React Flow fills center with proper dagre layout
- [ ] Test at 1024px: left panel collapses to top summary bar, center fills full width
- [ ] Test at 768px: single column, all panels stacked and individually scrollable
- [ ] Test at 375px: left panel accordion (collapsed by default, tap to expand), React Flow wrapped in `overflow-x-auto` with `min-w-[600px]` inner div, `<Controls>` and `<MiniMap>` hidden via `className="hidden sm:block"`
- [ ] Fix every overflow, layout break, and truncation found — no skipping

---

## Day 7 — P2

### 7.1 Integration Test
- [ ] Switch `VITE_API_URL` to P4's Railway URL (received via CP-4)
- [ ] Upload real tech resume + JD — verify results page renders with real data
- [ ] Click every course node — verify drawer opens with correct course data
- [ ] Verify `score_breakdown` bars render correctly in drawer (all values between 0 and 1)
- [ ] Expand all 5 reasoning trace sections — verify content in each
- [ ] Verify phase timeline shows correct durations summing to `total_training_hrs`
- [ ] Fix any field name mismatches between `mockData.js` shape and real API response shape

### 7.2 Vercel Deployment
- [ ] Create Vercel project, set root directory to `client/`
- [ ] Add env var: `VITE_API_URL = <Railway URL from P4>`
- [ ] Deploy — verify production URL loads upload page with no errors
- [ ] Run one full analysis on production (Vercel → Railway → Supabase) — confirm end-to-end
- [ ] Update `DEMO_SESSIONS` constants in `ExampleBadge.jsx` with real session UUIDs (provided by whoever runs the pre-computed sessions)
- [ ] Commit + push → Vercel redeploys automatically
- [ ] Verify "Try Tech Role" and "Try Ops Role" buttons navigate to correct results on production

---

## Day 8 — P2

### 8.1 Final Frontend Checks
- [ ] Lighthouse audit on production Vercel URL — fix any Performance score below 70 (lazy-load `reactflow` with `React.lazy` if needed)
- [ ] Verify Tailwind purge is not removing needed classes: check 5 components on production URL, confirm styling is correct
- [ ] Smoke test on Chrome, Firefox, Safari — log and fix any browser-specific CSS bug
- [ ] Confirm no `mockData.js` import is active in production (all real data flows through `useSession`)
- [ ] `grep -r "console.log" client/src/` — remove every debug log

---

---

# P3 — Algorithm + Data (20%)

**Owns:** The two core algorithm files, all utility functions, the seed catalog (60+ courses), and all unit tests. Must deliver `computeSkillGap.js` and `adaptivePathway.js` by end of Day 3 (CP-2).

---

## Day 1 — P3

### 1.1 Utility Functions
- [ ] Write `server/src/utils/levelToNum.js`:
  - `function levelToNum(level)`: `'beginner'→1`, `'intermediate'→2`, `'advanced'→3`, anything else → `throw new Error('Invalid level: ' + level)`
  - `function numToLevel(n)`: `1→'beginner'`, `2→'intermediate'`, `3→'advanced'`, anything else → throw
  - Export both named
- [ ] Write `server/src/utils/cosineSimilarity.js`:
  - `function cosineSimilarity(a, b)`:
    - `dot = a.reduce((sum, v, i) => sum + v * b[i], 0)`
    - `magA = Math.sqrt(a.reduce((s, x) => s + x*x, 0))`
    - `magB = Math.sqrt(b.reduce((s, x) => s + x*x, 0))`
    - If `magA === 0 || magB === 0` → return `0`
    - Return `dot / (magA * magB)`
  - Export named
- [ ] Write `server/src/tests/utils.test.js` and run with `node`:
  - `levelToNum('beginner') === 1` ✓
  - `levelToNum('intermediate') === 2` ✓
  - `levelToNum('advanced') === 3` ✓
  - `levelToNum('expert')` throws ✓
  - `numToLevel(2) === 'intermediate'` ✓
  - `cosineSimilarity([1,0,0],[1,0,0]) === 1` ✓
  - `cosineSimilarity([1,0],[0,1]) === 0` ✓
  - `cosineSimilarity([0,0],[1,0]) === 0` (zero vector guard) ✓

### 1.2 Seed Catalog Data Design
- [ ] Write the full course data array in `server/src/scripts/seedCatalog.js` — every course as a JS object `{ title, description, skill_name, level, level_num, duration_hrs, domain, provider, url, prerequisite_titles }`. All 63 courses listed here:

  **Technical — Frontend (6):**
  - `HTML & CSS Fundamentals` | beginner | 1 | 3.0 | freeCodeCamp | prereqs: none
  - `JavaScript Essentials` | beginner | 1 | 5.0 | freeCodeCamp | prereqs: none
  - `React Basics` | intermediate | 2 | 6.0 | Udemy | prereqs: [`JavaScript Essentials`]
  - `React Advanced Patterns` | advanced | 3 | 5.0 | Frontend Masters | prereqs: [`React Basics`]
  - `TypeScript Foundations` | intermediate | 2 | 4.0 | Scrimba | prereqs: [`JavaScript Essentials`]
  - `Next.js for Production` | advanced | 3 | 6.0 | Vercel Docs | prereqs: [`React Basics`, `TypeScript Foundations`]

  **Technical — Backend (5):**
  - `Node.js + Express Fundamentals` | intermediate | 2 | 5.0 | Udemy | prereqs: [`JavaScript Essentials`]
  - `REST API Design` | intermediate | 2 | 3.0 | Pluralsight | prereqs: none
  - `GraphQL Fundamentals` | intermediate | 2 | 4.0 | Apollo Docs | prereqs: [`REST API Design`]
  - `Python for Backend` | beginner | 1 | 6.0 | Coursera | prereqs: none
  - `FastAPI with Python` | intermediate | 2 | 4.0 | FastAPI Docs | prereqs: [`Python for Backend`]

  **Technical — Databases (4):**
  - `SQL Fundamentals` | beginner | 1 | 4.0 | Mode Analytics | prereqs: none
  - `PostgreSQL Advanced` | intermediate | 2 | 5.0 | Udemy | prereqs: [`SQL Fundamentals`]
  - `MongoDB Basics` | beginner | 1 | 3.0 | MongoDB University | prereqs: none
  - `Redis Caching Strategies` | intermediate | 2 | 3.0 | Redis University | prereqs: [`SQL Fundamentals`]

  **Technical — DevOps (5):**
  - `Linux Command Line Basics` | beginner | 1 | 3.0 | The Odin Project | prereqs: none
  - `Docker Fundamentals` | intermediate | 2 | 4.0 | Docker Docs | prereqs: [`Linux Command Line Basics`]
  - `Kubernetes Basics` | advanced | 3 | 6.0 | CNCF | prereqs: [`Docker Fundamentals`]
  - `CI/CD with GitHub Actions` | intermediate | 2 | 4.0 | GitHub Docs | prereqs: none
  - `AWS Core Services` | intermediate | 2 | 6.0 | AWS Skill Builder | prereqs: none

  **Technical — AI/ML (5):**
  - `Python for Data Science` | intermediate | 2 | 6.0 | Kaggle | prereqs: [`Python for Backend`]
  - `Machine Learning Fundamentals` | intermediate | 2 | 8.0 | Coursera | prereqs: [`Python for Data Science`]
  - `LLM APIs and Prompt Engineering` | intermediate | 2 | 3.0 | DeepLearning.ai | prereqs: none
  - `Vector Databases` | advanced | 3 | 3.0 | Pinecone Docs | prereqs: [`Machine Learning Fundamentals`]
  - `Fine-tuning LLMs` | advanced | 3 | 5.0 | Hugging Face | prereqs: [`Machine Learning Fundamentals`]

  **Operational — Warehouse/Logistics (7):**
  - `Workplace Safety Fundamentals` | beginner | 1 | 2.0 | OSHA | prereqs: none
  - `OSHA Standards Overview` | intermediate | 2 | 4.0 | OSHA | prereqs: [`Workplace Safety Fundamentals`]
  - `Forklift Operation Basics` | beginner | 1 | 3.0 | Internal | prereqs: none
  - `Forklift Certification Prep` | intermediate | 2 | 2.0 | Internal | prereqs: [`Forklift Operation Basics`]
  - `Inventory Management Systems` | intermediate | 2 | 4.0 | Coursera | prereqs: none
  - `Supply Chain Basics` | beginner | 1 | 3.0 | Coursera | prereqs: none
  - `Quality Control Processes` | intermediate | 2 | 3.0 | ASQ | prereqs: none

  **Operational — Customer/Service (3):**
  - `Customer Service Fundamentals` | beginner | 1 | 2.0 | LinkedIn Learning | prereqs: none
  - `Conflict Resolution in the Workplace` | intermediate | 2 | 2.0 | LinkedIn Learning | prereqs: [`Customer Service Fundamentals`]
  - `Service Desk Operations` | intermediate | 2 | 3.0 | Internal | prereqs: none

  **Soft Skills / Managerial (9):**
  - `Business Communication` | beginner | 1 | 2.0 | Coursera | prereqs: none
  - `Presentation Skills` | intermediate | 2 | 2.0 | Coursera | prereqs: [`Business Communication`]
  - `Agile and Scrum Foundations` | beginner | 1 | 3.0 | Scrum.org | prereqs: none
  - `Project Management Fundamentals` | intermediate | 2 | 5.0 | PMI | prereqs: [`Agile and Scrum Foundations`]
  - `PMP Exam Prep` | advanced | 3 | 10.0 | PMI | prereqs: [`Project Management Fundamentals`]
  - `Data-Driven Decision Making` | intermediate | 2 | 3.0 | Coursera | prereqs: none
  - `Team Leadership Essentials` | intermediate | 2 | 3.0 | LinkedIn Learning | prereqs: none
  - `Strategic Thinking` | advanced | 3 | 4.0 | Harvard ManageMentor | prereqs: [`Team Leadership Essentials`]
  - `Change Management` | advanced | 3 | 4.0 | Prosci | prereqs: none

  **Cross-domain extras (4):**
  - `Warehouse Management Systems (WMS)` | intermediate | 2 | 5.0 | Internal | prereqs: [`Inventory Management Systems`]
  - `Excel for Business` | beginner | 1 | 3.0 | Microsoft Learn | prereqs: none
  - `Power BI Fundamentals` | intermediate | 2 | 4.0 | Microsoft Learn | prereqs: [`Excel for Business`]
  - `Cybersecurity Awareness` | beginner | 1 | 2.0 | SANS | prereqs: none

---

## Day 2 — P3

### 2.1 Skill Gap Analysis
- [ ] Write `server/src/ai/computeSkillGap.js`:
  - `function computeSkillGap(extractedSkills, requiredSkills)` — both arrays have `normalized_id`, `name`, `level`, `required`
  - For each `req` in `requiredSkills`:
    - `const current = extractedSkills.find(s => s.normalized_id === req.normalized_id)`
    - No match → push to `missing`: `{ skill: req.name, skill_id: req.normalized_id, current: null, current_num: 0, target: req.level, target_num: levelToNum(req.level), gap_size: levelToNum(req.level), required: req.required }`
    - Match but `levelToNum(current.level) < levelToNum(req.level)` → push to `gaps`: `{ skill: req.name, skill_id: req.normalized_id, current: current.level, current_num: levelToNum(current.level), target: req.level, target_num: levelToNum(req.level), gap_size: target_num - current_num, required: req.required }`
    - Match and sufficient → push to `alreadyMet`: `{ skill: req.name, current: current.level, target: req.level }`
  - Return: `{ gaps, missing, alreadyMet, total_gaps: gaps.length + missing.length, critical_gaps: [...gaps, ...missing].filter(g => g.required).length }`
  - Export named
- [ ] Write `server/src/tests/computeSkillGap.test.js` — 5 unit tests:
  1. All required skills met → `total_gaps === 0`, `alreadyMet.length === requiredSkills.length`
  2. All required skills missing → `missing.length === requiredSkills.length`, `gaps.length === 0`
  3. Skills present at wrong level → correct `current_num`, `target_num`, `gap_size`
  4. Mix required + preferred → `critical_gaps` counts only `required: true` items
  5. Candidate has extra skills not in JD → ignored, don't appear in any output array
- [ ] Run all 5 tests — all must pass before moving on

### 2.2 Seed Catalog Execution
- [ ] Complete `seedCatalog.js` with the seeding logic (data array from Day 1):
  - **Step A — Seed skills:** collect all unique `skill_name` values. For each: `await embed(skill_name)` → `INSERT INTO skills (name, category, domain, embedding) VALUES ($1, 'Unknown', <domain from course>, $2) ON CONFLICT (name) DO NOTHING RETURNING id`. Store `{ skill_name → id }` in `skillNameToId` map.
  - **Step B — Seed courses:** for each course, resolve `skill_id = skillNameToId[course.skill_name]`. `INSERT INTO courses (title, description, skill_id, level, level_num, duration_hrs, domain, provider, url, embedding) VALUES (..., $embedding) ON CONFLICT (title) DO NOTHING RETURNING id`. Get embedding by `await embed(course.title + ' ' + course.description)`. Store `{ title → id }` in `courseTitleToId` map.
  - **Step C — Set prerequisites:** for each course with `prerequisite_titles.length > 0`: resolve UUIDs via `courseTitleToId`. `UPDATE courses SET prerequisites = $1 WHERE id = $2`.
  - **Step D — Seed skill_course_map:** for each course: `INSERT INTO skill_course_map (course_id, skill_id, impact) VALUES ($courseId, $primarySkillId, 1.0) ON CONFLICT DO NOTHING`. Also insert secondary mappings where a course clearly addresses multiple skills (e.g. `Node.js + Express Fundamentals` → also insert for `Express` skill with `impact = 0.9`).
- [ ] Run: `node server/src/scripts/seedCatalog.js` — verify in Supabase:
  - `SELECT count(*) FROM courses` → 63 (or more)
  - `SELECT count(*) FROM courses WHERE embedding IS NULL` → 0
  - `SELECT count(*) FROM courses WHERE level_num IS NULL` → 0
  - `SELECT count(*) FROM skill_course_map` → ≥ 63
  - Spot-check 3 courses: `Docker Fundamentals` has `Linux Command Line Basics` UUID in its `prerequisites` array, `Kubernetes Basics` has `Docker Fundamentals` UUID, `React Basics` has `JavaScript Essentials` UUID

---

## Day 3 — P3

### 3.1 Adaptive Pathway Algorithm
- [ ] Write `server/src/ai/adaptivePathway.js`:
  - `async function adaptivePathway(skillGap, supabaseClient)`
  - Import `levelToNum`, `numToLevel` from utils

  **Step A — Course retrieval:** for each item in `[...skillGap.gaps, ...skillGap.missing]`:
  ```js
  // Primary: exact skill_id match
  const primary = await supabaseClient.rpc('match_courses_by_skill', {
    p_skill_id: gapItem.skill_id,
    p_min_level_num: gapItem.current_num
  })
  // Equivalent raw SQL:
  // SELECT c.*, scm.impact FROM courses c
  // JOIN skill_course_map scm ON c.id = scm.course_id
  // WHERE scm.skill_id = $1 AND c.level_num >= $2
  // ORDER BY scm.impact DESC, c.duration_hrs ASC LIMIT 3

  // Fallback: vector similarity
  const vec = await embed(gapItem.skill)
  const fallback = await supabaseClient.rpc('match_courses_by_vector', { query_embedding: vec, threshold: 0.6 })
  // Equivalent raw SQL:
  // SELECT c.*, 1-(c.embedding<=>$1) AS similarity FROM courses c
  // WHERE 1-(c.embedding<=>$1) > 0.6 ORDER BY c.embedding<=>$1 LIMIT 3
  ```
  Union + deduplicate by `course.id`; attach `candidate.gap = gapItem`. If zero results for a gap: log `[WARN] No courses found for gap: ${gapItem.skill}`, continue.

  **Step B — Score:**
  ```js
  function scoreCandidate(course, gap) {
    const gap_criticality = gap.required ? 1.0 : 0.5
    const impact_coverage = course.impact ?? 0.5
    const level_fit = 1 - Math.abs(course.level_num - gap.target_num) / 2
    const efficiency = 1 / Math.log(course.duration_hrs + Math.E)
    const total = gap_criticality*0.40 + impact_coverage*0.30 + level_fit*0.20 + efficiency*0.10
    return { total, gap_criticality, impact_coverage, level_fit, efficiency }
  }
  ```
  Attach `course.score = result.total` and `course.score_breakdown = result`

  **Step C — Deduplicate across gaps:** keep only highest-scoring instance per `course.id`

  **Step D — Kahn's topological sort:**
  ```js
  function topologicalSort(courses) {
    const inDegree = {}, graph = {}
    for (const c of courses) { inDegree[c.id] = 0; graph[c.id] = [] }
    for (const c of courses) {
      for (const prereqId of (c.prerequisites || [])) {
        if (graph[prereqId]) {           // prereq IS in selected set
          graph[prereqId].push(c.id)
          inDegree[c.id]++
        }
        // prereq not in set means candidate already has it — skip the edge
      }
    }
    const queue = courses.filter(c => inDegree[c.id] === 0).sort((a,b) => b.score - a.score)
    const result = []
    while (queue.length) {
      const node = queue.shift()
      result.push(node)
      for (const nId of graph[node.id]) {
        if (--inDegree[nId] === 0) {
          queue.push(courses.find(c => c.id === nId))
          queue.sort((a,b) => b.score - a.score)
        }
      }
    }
    return result
  }
  ```

  **Step E — Phase assignment:**
  ```js
  function assignPhase(course) {
    if (course.level_num === 1) return { phase: 1, phase_label: 'Foundation' }
    if (course.level_num === 2) return { phase: 2, phase_label: 'Core Competency' }
    return course.gap.required
      ? { phase: 3, phase_label: 'Specialization' }
      : { phase: 4, phase_label: 'Stretch Goals' }
  }
  ```

  **Step F — Group + durations:**
  - Group sorted courses by `phase` number
  - `phase_duration_hrs = phase.courses.reduce((s, c) => s + c.duration_hrs, 0)`
  - `total_training_hrs = all courses summed`

  **Step G — Return:**
  ```js
  return { phases: [...], total_training_hrs }
  ```

- [ ] Write `server/src/tests/adaptivePathway.test.js` with mock data:
  - Phases assigned correctly: `level_num 1 → Foundation`, `level_num 2 → Core Competency`
  - Topological order respected: Docker before Kubernetes, JavaScript before React
  - `score_breakdown` attached to every course with all 4 fields
  - `total_training_hrs` equals sum of all `duration_hrs`
  - External prereq edge (prereq not in selected set) does NOT block its dependent
  - Zero gaps input → `{ phases: [], total_training_hrs: 0 }`
- [ ] All tests pass
- [ ] **CP-2:** confirm to P4 that both files are ready and importable

---

## Day 7 — P3

### 7.1 Seed Validation + Idempotency
- [ ] Run `seedCatalog.js` a second time on the production Supabase DB — `SELECT count(*) FROM courses` must be identical to before (all INSERTs use `ON CONFLICT DO NOTHING`)
- [ ] Verify `SELECT count(*) FROM courses WHERE prerequisites = '{}'` and spot-check that courses with defined prereqs actually have non-empty `prerequisites` arrays
- [ ] Verify `SELECT count(*) FROM courses WHERE embedding IS NULL` = 0 on production

### 7.2 Algorithm Final Checks
- [ ] `grep -r "console.log" server/src/ai/computeSkillGap.js server/src/ai/adaptivePathway.js server/src/utils/` — remove every debug log
- [ ] Run all unit tests one final time — all must pass on the production-equivalent data
- [ ] Manually trace one pathway result from production: pick a course from a response, verify its `score_breakdown` values are in [0, 1], verify phase assignment matches `level_num`

---

## Day 8 — P3

### 8.1 Final Algorithm Validation
- [ ] Run full pipeline on production via `POST /sessions/analyze` with tech pair — manually verify: ≥ 4 gaps detected, pathway has Technical domain courses only, Docker appears before Kubernetes in sorted order
- [ ] Run full pipeline with ops pair — verify: pathway has Operational domain courses, no Technical courses appear
- [ ] Edge case — zero gaps: submit a resume listing all skills from a simple JD — verify `total_gaps === 0`, `phases === []`, `total_training_hrs === 0`
- [ ] Edge case — niche skill: submit JD requiring "COBOL programming" — verify no server crash, gap recorded, graceful empty courses array for that gap

---

---

# P4 — Routes + Wiring + Deployment + Integration Testing (20%)

**Owns:** All Express routes, `index.js`, the full `POST /sessions/analyze` pipeline wiring (calling P1 and P3 functions in the correct order), Docker, Railway deployment, and all integration/edge-case testing.

**Critical path:** P4 cannot wire `POST /sessions/analyze` until P1 delivers AI functions (CP-1) AND P3 delivers the algorithm (CP-2). Both must be done by end of Day 3.

---

## Day 1 — P4

### 1.1 Express App Entry Point
- [ ] After P1 creates `server/src/` folder structure (coordinate morning of Day 1): write `server/src/index.js`:
  - `const app = express()`
  - Middleware: `app.use(cors())`, `app.use(express.json())`, `app.use(express.urlencoded({ extended: true }))`
  - Multer setup: `const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10 * 1024 * 1024 } })` — 10MB limit, memory storage (files come in as buffers)
  - Export `upload` for use in routes
  - Health check: `app.get('/health', (req, res) => res.json({ status: 'ok', timestamp: new Date().toISOString() }))`
  - Route mounts (add as routes are written):
    - `app.use('/api/v1/sessions', require('./routes/sessions'))`
    - `app.use('/api/v1/courses', require('./routes/courses'))`
    - `app.use('/api/v1/skills', require('./routes/skills'))`
  - Static files conditional: `if (process.env.EXPRESS_STATIC === 'true') app.use(express.static(path.join(__dirname, '../public')))`
  - Global error handler (add last, after all routes):
    ```js
    app.use((err, req, res, next) => {
      console.error(err.stack)
      res.status(err.status || 500).json({ error: err.message || 'Internal server error' })
    })
    ```
  - `app.listen(process.env.PORT || 3001, () => console.log('Server running on port', process.env.PORT || 3001))`
- [ ] Verify: `node server/src/index.js` starts without errors, `GET /health` returns `{ status: 'ok' }`

### 1.2 Skeleton Routes
- [ ] Write `server/src/routes/skills.js`:
  - Import `supabaseClient`
  - `GET /` → `SELECT * FROM skills ORDER BY name` → return array
  - Export router
- [ ] Write `server/src/routes/courses.js`:
  - `GET /` → query `courses` with optional filters: `?domain=`, `?level=`, `?skill_id=` — build query conditionally, return array
  - `POST /` → check `req.headers['x-seed-secret'] === process.env.SEED_SECRET` (else `403`). Body is array of course objects. Bulk insert into `courses` + `skill_course_map`. Return `{ inserted: n }`.
- [ ] Write `server/src/routes/sessions.js` (skeleton only — full wiring on Day 3):
  - `POST /analyze` → `res.json({ status: 'not implemented' })` placeholder
  - `GET /:id` → `SELECT * FROM sessions WHERE id = $1` → return row or `404 { error: 'Session not found' }`
- [ ] Test all skeleton routes with curl:
  - `GET /api/v1/health` → `{ status: 'ok' }` ✓
  - `GET /api/v1/skills` → `[]` (empty, seed not run yet) ✓
  - `GET /api/v1/courses` → `[]` ✓
  - `GET /api/v1/sessions/fake-id` → `404` ✓
  - `POST /api/v1/sessions/analyze` → `{ status: 'not implemented' }` ✓

---

## Day 2 — P4

### 2.1 Courses Route Finalization
- [ ] Test `GET /api/v1/courses` with query params after P3 runs `seedCatalog.js`:
  - `?domain=Technical` → returns only Technical domain courses ✓
  - `?level=intermediate` → returns only intermediate courses ✓
  - `?skill_id=<uuid>` → returns courses for that skill ✓
- [ ] Test `POST /api/v1/courses` seeding endpoint:
  - Without header → `403` ✓
  - With correct `x-seed-secret` header and valid body → inserts and returns count ✓
- [ ] Verify `GET /api/v1/sessions/:id` with a real session UUID (insert one manually via Supabase dashboard) → returns the row correctly

### 2.2 Multer Configuration Testing
- [ ] Test file upload handling: POST a multipart form with a PDF file to `/api/v1/sessions/analyze` — verify `req.files.resume` is populated with `{ buffer, mimetype, originalname, size }`
- [ ] Test with a DOCX file — verify same
- [ ] Test with no file — verify `req.files` is empty (not undefined)
- [ ] Test with file > 10MB — verify multer rejects with appropriate error
- [ ] Fix any multer field name mismatches (field names must be `resume` and `jd` exactly)

---

## Day 3 — P4

### 3.1 Wire POST /sessions/analyze — Full Implementation
This is the most complex task P4 owns. Implement after CP-2 confirms P3 functions are ready.

- [ ] In `server/src/routes/sessions.js`, replace placeholder with full implementation:

  ```js
  const { upload } = require('../index')                    // multer instance
  const { extractText } = require('../parsers/extractText')
  const { extractResumeSkills } = require('../ai/extractResumeSkills')
  const { extractJDRequirements } = require('../ai/extractJDRequirements')
  const { normalizeSkills } = require('../ai/normalizeSkills')
  const { computeSkillGap } = require('../ai/computeSkillGap')
  const { adaptivePathway } = require('../ai/adaptivePathway')
  const { generateReasoningTrace } = require('../ai/generateReasoningTrace')
  const supabase = require('../db/supabaseClient')

  router.post('/analyze', upload.fields([{ name: 'resume', maxCount: 1 }, { name: 'jd', maxCount: 1 }]), async (req, res, next) => {
    try {
      // 1. Validate inputs
      if (!req.files?.resume) return res.status(400).json({ error: 'Resume file is required' })
      if (!req.files?.jd && !req.body.jd_text) return res.status(400).json({ error: 'Job description is required' })

      // 2. Extract text from resume
      let resumeText
      try {
        const result = await extractText({ buffer: req.files.resume[0].buffer, mimetype: req.files.resume[0].mimetype })
        resumeText = result.text
      } catch (e) {
        if (e.message === 'SCANNED_PDF') return res.status(400).json({ error: 'Resume appears to be a scanned image. Please upload a text-based PDF.' })
        if (e.message === 'UNSUPPORTED_FORMAT') return res.status(400).json({ error: 'Resume format not supported. Please use PDF or DOCX.' })
        throw e
      }

      // 3. Extract text from JD
      let jdText
      if (req.body.jd_text) {
        jdText = req.body.jd_text
      } else {
        try {
          const result = await extractText({ buffer: req.files.jd[0].buffer, mimetype: req.files.jd[0].mimetype })
          jdText = result.text
        } catch (e) {
          if (e.message === 'SCANNED_PDF') return res.status(400).json({ error: 'Job description appears to be a scanned image. Please upload a text-based PDF.' })
          throw e
        }
      }

      // 4. LLM extraction
      let resumeResult, jdResult
      try { resumeResult = await extractResumeSkills(resumeText) }
      catch (e) {
        if (e.message === 'LLM_JSON_INVALID') return res.status(422).json({ error: 'Could not parse resume skills. Please try again.' })
        throw e
      }
      try { jdResult = await extractJDRequirements(jdText) }
      catch (e) {
        if (e.message === 'LLM_JSON_INVALID') return res.status(422).json({ error: 'Could not parse job description. Please try again.' })
        throw e
      }

      // 5. Normalize all skill names against canonical DB
      const allSkillNames = [
        ...resumeResult.skills.map(s => s.name),
        ...jdResult.skills.map(s => s.name)
      ]
      const normResults = await normalizeSkills(allSkillNames)
      const normMap = Object.fromEntries(normResults.map(r => [r.original, r]))

      // Attach normalized_id to each skill
      resumeResult.skills = resumeResult.skills.map(s => ({ ...s, normalized_id: normMap[s.name]?.normalized_id }))
      jdResult.skills = jdResult.skills.map(s => ({ ...s, normalized_id: normMap[s.name]?.normalized_id }))

      // 6. Compute skill gap
      const skillGap = computeSkillGap(resumeResult.skills, jdResult.skills)

      // 7. Generate adaptive pathway
      const pathwayResult = await adaptivePathway(skillGap, supabase)

      // 8. Generate reasoning trace
      const reasoningTrace = await generateReasoningTrace({
        extractedSkills: resumeResult.skills,
        requiredSkills: jdResult.skills,
        skillGap,
        pathway: pathwayResult
      })

      // 9. Build response
      const response = {
        session_id: null,  // filled after DB insert
        candidate: {
          name: resumeResult.candidate_name,
          current_role: resumeResult.current_role,
          total_experience_years: resumeResult.total_experience_years
        },
        job_title: jdResult.job_title,
        skill_gap_summary: {
          total_gaps: skillGap.total_gaps,
          critical_gaps: skillGap.critical_gaps,
          already_met: skillGap.alreadyMet.length
        },
        pathway: pathwayResult,
        reasoning_trace: reasoningTrace,
        total_training_hrs: pathwayResult.total_training_hrs
      }

      // 10. Persist session
      const { data: sessionRow, error: dbError } = await supabase
        .from('sessions')
        .insert({
          resume_text: resumeText,
          jd_text: jdText,
          extracted_skills: resumeResult,
          required_skills: jdResult,
          skill_gap: skillGap,
          pathway: pathwayResult,
          reasoning_trace: reasoningTrace
        })
        .select('id')
        .single()
      if (dbError) throw dbError

      response.session_id = sessionRow.id
      res.status(201).json(response)

    } catch (err) {
      next(err)  // passes to global error handler
    }
  })
  ```

- [ ] Test: POST with real tech resume + JD (PDF files) — verify `201` response with all required fields: `session_id` (real UUID), `candidate.name`, `skill_gap_summary.total_gaps > 0`, `pathway.phases` array non-empty, `reasoning_trace` has at least `raw` field
- [ ] Test: POST with `jd_text` instead of JD file — verify same 201 response
- [ ] Test: POST with missing resume → `400`
- [ ] Test: POST with missing JD → `400`
- [ ] **CP-3:** confirm to P2 that `POST /sessions/analyze` is live and returning correct shape

### 3.2 Error Middleware Verification
- [ ] Verify the global error handler in `index.js` catches errors from async route handlers (confirm `next(err)` is called correctly in `sessions.js`)
- [ ] Deliberately throw inside the analyze handler to confirm `500` comes back as `{ error: '...' }` JSON, not HTML
- [ ] Test that a database error (disconnect Supabase temporarily) returns `500` with the error message, not a crash

---

## Day 7 — P4

### 7.1 Docker Build
- [ ] Write `Dockerfile` at repo root (multi-stage):
  ```dockerfile
  FROM node:20-alpine AS builder
  WORKDIR /app

  # Build server
  COPY server/package*.json ./server/
  WORKDIR /app/server
  RUN npm ci

  # Build client
  WORKDIR /app
  COPY client/package*.json ./client/
  WORKDIR /app/client
  RUN npm ci
  COPY client/ .
  RUN npm run build

  # Production image
  FROM node:20-alpine AS runner
  WORKDIR /app
  COPY --from=builder /app/server ./server
  COPY --from=builder /app/client/dist ./server/public
  WORKDIR /app/server
  ENV EXPRESS_STATIC=true
  ENV NODE_ENV=production
  EXPOSE 3001
  CMD ["node", "src/index.js"]
  ```
- [ ] Write `docker-compose.yml` at repo root:
  ```yaml
  version: '3.8'
  services:
    db:
      image: postgres:15
      environment:
        POSTGRES_DB: adaptive_onboarding
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: postgres
      volumes:
        - ./server/src/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      ports:
        - "5432:5432"

    server:
      build: ./server
      depends_on:
        - db
      env_file:
        - ./server/.env
      ports:
        - "3001:3001"
      # Note: for production, remove db service and point SUPABASE_URL at hosted Supabase
  ```
- [ ] Run `docker build -t adaptive-onboarding .` — build must succeed with no errors
- [ ] Run `docker run --env-file server/.env -p 3001:3001 adaptive-onboarding`
- [ ] Verify: `curl localhost:3001/health` → `{"status":"ok","timestamp":"..."}` ✓
- [ ] Verify: `POST localhost:3001/api/v1/sessions/analyze` with real files works inside Docker

### 7.2 Railway Deployment
- [ ] Create Railway project → New Service → Deploy from GitHub repo → set root directory to `/server`
- [ ] Set all environment variables in Railway dashboard: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`, `PORT=3001`, `SEED_SECRET`
- [ ] Deploy — Railway builds and starts
- [ ] Verify: `GET https://<railway-url>/health` → `{"status":"ok"}` ✓
- [ ] Verify Supabase accepts connections from Railway: `GET https://<railway-url>/api/v1/skills` returns the seeded skill list
- [ ] Run one `POST /sessions/analyze` via Postman against the Railway URL with real files — verify full response
- [ ] Share Railway URL with P2 (**CP-4**)

### 7.3 Cross-Domain + Edge Case Testing
- [ ] Tech pair test: POST tech resume + tech JD to production Railway URL — verify ≥ 4 gaps, all pathway courses from Technical domain, phase order sensible
- [ ] Ops pair test: POST ops resume + ops JD — verify pathway has Operational courses (OSHA, WMS, Supply Chain), zero Technical courses
- [ ] Zero-gaps test: construct a resume that lists all skills from a simple 3-skill JD, POST → verify `total_gaps: 0`, `phases: []`
- [ ] Scanned PDF test: rename a 1-word `.txt` file to `.pdf`, POST as resume → verify `400` with SCANNED_PDF error message
- [ ] Niche skill test: POST JD requiring "COBOL programming" → verify no server crash, 201 response, gap recorded, empty courses array for that gap in pathway

---

## Day 8 — P4

### 8.1 Final Integration Checks
- [ ] Run full end-to-end one final time on production: tech pair + ops pair — verify both return correct responses
- [ ] Verify `GET /sessions/:id` works on production with a real session_id from one of the Day 7 test runs
- [ ] Check all error codes on production: missing resume file → 400, bad session id → 404, confirm no 500s on valid inputs
- [ ] `grep -r "console.log" server/src/routes/ server/src/index.js` — remove every debug log
- [ ] Confirm `server/.env.example` is committed and no `.env` file appears in `git log --all -- server/.env`
- [ ] Verify Docker build still works after all Day 8 changes: `docker build -t adaptive-onboarding . && docker run --env-file server/.env -p 3001:3001 adaptive-onboarding` → health check passes

---

*Every technical task is assigned. Every file has one owner. Nothing is left unassigned.*
