# 48-Hour Hackathon Battle Plan
## AI-Adaptive Onboarding Engine — ARTPARK CodeForge

> **Goal:** Win. Ship a working, polished, well-documented product in 48 hours.
> **Stack:** React (frontend) · Node.js (backend API) · Python (NLP/ML microservice) · SQLite (course catalog DB)

---

## Team Roles (Assign Before Starting)

| Role | Responsibility |
|------|---------------|
| **Frontend Dev** | React UI, file upload, roadmap visualization |
| **Backend Dev** | Node.js API, PDF parsing, LLM integration |
| **ML/NLP Dev** | Skill extraction, gap analyzer, DAG path generator |
| **Fullstack/Lead** | Integration, Docker, README, demo video, slides |

---

## Phase Breakdown

```
Hours  0–4   →  Setup & Architecture
Hours  4–16  →  Core Engine (Backend + ML)
Hours 16–28  →  Frontend + Integration
Hours 28–36  →  Polish, Edge Cases, Anti-Hallucination
Hours 36–44  →  Documentation, Demo Video, Slides
Hours 44–48  →  Buffer, Final Testing, Submission
```

---

## Hour 0–4 | Setup & Architecture

### Goals
Lock the architecture. Every team member must finish this block aligned.

### Tasks

**All members (first 30 min)**
- Read the problem statement together
- Finalize the course catalog (hardcode 30–50 courses across 5 domains: Software, Data, DevOps, HR, Operations)
- Define the JSON schema for skill objects and learning paths

**Skill JSON schema (agree on this now)**
```json
{
  "skill": "Docker",
  "category": "DevOps",
  "level": "intermediate",
  "prerequisites": ["Linux Basics", "Networking Fundamentals"]
}
```

**Learning Path JSON schema**
```json
{
  "goal_role": "Backend Engineer",
  "identified_skills": ["Python", "REST APIs"],
  "skill_gaps": ["Docker", "PostgreSQL", "CI/CD"],
  "path": [
    { "order": 1, "course_id": "C012", "title": "Linux Basics", "duration_hrs": 4, "reason": "Prerequisite for Docker" },
    { "order": 2, "course_id": "C019", "title": "Docker Fundamentals", "duration_hrs": 6, "reason": "Gap identified from JD" }
  ],
  "reasoning_trace": "Candidate has Python expertise but lacks containerization skills required by the JD..."
}
```

**Setup (all parallel)**
- Backend Dev: `npm init`, install `express`, `multer`, `pdfplumber` (via Python subprocess), `axios`
- ML Dev: `pip install pdfplumber spacy sentence-transformers scikit-learn networkx`
- Frontend Dev: `npx create-react-app` or `npm create vite@latest`, install `react-flow`, `react-dropzone`, `axios`
- Lead: Create GitHub repo, set up `/frontend`, `/backend`, `/ml_service` folders, create `docker-compose.yml` skeleton

### Deliverable
- Monorepo scaffold committed
- Course catalog JSON file (`/backend/data/course_catalog.json`) with 40+ courses
- Agreed API contracts (endpoints, request/response shapes)

---

## Hour 4–16 | Core Engine (Backend + ML)

> This is the most critical block. The judging criteria weights **Technical Sophistication (20%)** and **Grounding/Reliability (15%)** highest. Win this block, win the hackathon.

### ML Service (Python) — Hours 4–14

**Step 1: PDF Text Extraction (Hour 4–5)**
```python
import pdfplumber

def extract_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
```

**Step 2: LLM Skill Extraction (Hour 5–8)**
- Use OpenAI GPT-4o-mini or Groq (free tier, fast)
- Prompt must return **strict JSON only** — no prose
- Run extraction separately for Resume AND Job Description

```
System: You are a skill extraction engine. Output ONLY valid JSON. No explanation.
User: Extract skills from this resume. Return:
{
  "candidate_name": string,
  "skills": [{ "name": string, "level": "beginner|intermediate|expert", "years": number }],
  "total_experience_years": number,
  "current_role": string
}
Resume text: {text}
```

**Step 3: Skill DB Matching (Hour 8–10)**
- Use `sentence-transformers` (`all-MiniLM-L6-v2`) to embed extracted skills
- Match against your course catalog skills using cosine similarity (threshold: 0.75)
- This prevents hallucinated course names — you only ever return courses from the catalog

```python
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

def match_skills_to_catalog(extracted_skills, catalog_skills):
    extracted_embs = model.encode(extracted_skills)
    catalog_embs = model.encode(catalog_skills)
    scores = util.cos_sim(extracted_embs, catalog_embs)
    # return best match per extracted skill if score > 0.75
```

**Step 4: Gap Analyzer — YOUR ORIGINAL LOGIC (Hour 10–12)**

The gap analyzer is your core original algorithm. It must:
1. Identify skills in the JD not present (or below required level) in the Resume
2. Weight gaps by frequency/importance in the JD
3. Output an ordered list of skill gaps with priority scores

```python
def analyze_gap(resume_skills: list, jd_skills: list) -> list:
    resume_skill_names = {s['name'].lower() for s in resume_skills}
    gaps = []
    for skill in jd_skills:
        name = skill['name'].lower()
        required_level = skill.get('level', 'intermediate')
        if name not in resume_skill_names:
            gaps.append({ "skill": skill['name'], "priority": skill.get('weight', 1.0), "type": "missing" })
        else:
            # Check level gap
            resume_level = next((s['level'] for s in resume_skills if s['name'].lower() == name), None)
            if level_rank(resume_level) < level_rank(required_level):
                gaps.append({ "skill": skill['name'], "priority": 0.7, "type": "level_upgrade" })
    return sorted(gaps, key=lambda x: -x['priority'])
```

**Step 5: DAG Path Generator (Hour 12–14)**
- Build a Directed Acyclic Graph using `networkx`
- Nodes = courses from your catalog
- Edges = prerequisite relationships
- Use topological sort to generate the learning order

```python
import networkx as nx

def generate_path(skill_gaps: list, course_catalog: list) -> list:
    G = nx.DiGraph()
    # Add all courses as nodes
    for course in course_catalog:
        G.add_node(course['id'], **course)
    # Add prerequisite edges
    for course in course_catalog:
        for prereq in course.get('prerequisites', []):
            G.add_edge(prereq, course['id'])
    
    # Find courses covering the skill gaps
    target_courses = find_courses_for_gaps(skill_gaps, course_catalog)
    
    # Get all ancestors (prerequisites) of target courses
    required = set()
    for course_id in target_courses:
        required.update(nx.ancestors(G, course_id))
        required.add(course_id)
    
    # Topological sort gives correct learning order
    subgraph = G.subgraph(required)
    ordered = list(nx.topological_sort(subgraph))
    return [course_catalog_by_id[cid] for cid in ordered]
```

**Step 6: Reasoning Trace LLM Call (Hour 14)**
- After the path is generated, make ONE final LLM call
- Input: candidate profile + JD + gap list + generated path
- Output: 3–4 sentence human-readable explanation
- Prompt must include: "Do NOT invent course names. Only reference courses from the provided list."

### Backend API (Node.js) — Hours 6–16

Build these 3 endpoints:

```
POST /api/analyze
  Body: multipart/form-data { resume: File, job_description: File|string }
  → calls Python ML service
  → returns full learning path JSON

GET /api/catalog
  → returns all courses (for frontend display)

GET /api/health
  → returns { status: "ok" }
```

Python ML service runs on port 5001, Node.js on port 3001. Node proxies to Python.

---

## Hour 16–28 | Frontend + Integration

### Hour 16–20 | File Upload UI

Build the upload screen first. It has two parts:
1. **Resume drop zone** — drag-and-drop PDF upload with preview of filename
2. **Job Description input** — either paste text OR upload a PDF

Use `react-dropzone` for the drop zones. Keep it clean. Add a prominent "Analyze" button that is disabled until both inputs are filled.

```jsx
// Key state shape
const [resume, setResume] = useState(null);
const [jdText, setJdText] = useState('');
const [jdFile, setJdFile] = useState(null);
const [loading, setLoading] = useState(false);
const [result, setResult] = useState(null);
```

### Hour 20–26 | Roadmap Visualization (Most Important UI)

This is what the judges see. Use `react-flow` for the DAG visualization.

Each node in the roadmap should show:
- Course title
- Duration in hours
- Skill category (color-coded badge)
- "Why this course?" tooltip showing the gap it addresses

Color code by category:
- 🔵 Blue = Technical / Software
- 🟢 Green = Data / Analytics
- 🟠 Orange = DevOps / Infrastructure
- 🟣 Purple = Soft Skills / Leadership
- ⚫ Gray = Foundational

Also build a **timeline view** (simpler fallback) — a vertical list of ordered courses with progress indicators.

### Hour 26–28 | Skill Gap Summary Panel

Left sidebar showing:
- Candidate's identified skills (green chips)
- Target role skills (from JD)
- Gap skills (red chips with priority score)
- AI reasoning trace (collapsible text block)
- Estimated total training time

---

## Hour 28–36 | Polish, Edge Cases, Anti-Hallucination

### Anti-Hallucination (Critical — 15% of score)

This is explicitly judged. Implement these guardrails:

1. **Catalog lock:** The path generator ONLY returns courses with IDs that exist in `course_catalog.json`. Enforce this with a whitelist check after every LLM response.

2. **LLM output validation:**
```python
def validate_path(generated_path, catalog_ids):
    for course in generated_path:
        if course['course_id'] not in catalog_ids:
            raise ValueError(f"Hallucinated course: {course['course_id']}")
    return True
```

3. **Confidence threshold:** If skill matching score < 0.6, mark as "low confidence" instead of forcing a match.

4. **Fallback path:** If LLM fails or produces invalid JSON, fall back to a rule-based path using only catalog data.

### Edge Cases to Handle
- Resume has no extractable text (scanned PDF) → show friendly error
- JD and Resume are in the same domain → show "minimal gap" message
- Very senior candidate with all JD skills covered → show "role-ready" state
- Network timeout on LLM call → retry once, then fail gracefully

### Polish Checklist
- [ ] Loading skeleton while analysis runs (show step-by-step progress: "Extracting skills... Analyzing gaps... Building path...")
- [ ] Responsive layout (tablet at minimum)
- [ ] Error states for all failure modes
- [ ] "Download as PDF" button for the roadmap
- [ ] "Try a sample" button that loads pre-filled demo data (critical for demo video)

---

## Hour 36–44 | Documentation, Demo Video, Slides

### README.md (Hour 36–39)

Must include (per submission requirements):

```markdown
# AI-Adaptive Onboarding Engine

## Overview
One paragraph explaining the value proposition.

## Setup Instructions
### Prerequisites
- Node.js 18+, Python 3.10+, npm

### Installation
git clone ...
cd backend && npm install
cd ml_service && pip install -r requirements.txt
cd frontend && npm install

### Running
docker-compose up   # recommended
# OR manually:
python ml_service/app.py &
node backend/server.js &
npm start --prefix frontend

## Architecture
[Include a simple ASCII diagram of the pipeline]

## Skill Gap Analysis Logic
Explain your gap analyzer algorithm here.
Explain your DAG path generator here.
Explain your anti-hallucination strategy here.

## Datasets Used
- O*NET Database (skill taxonomy)
- Kaggle Resume Dataset (testing)
- Custom course catalog (40+ courses, handcrafted)

## Models Used
- LLM: [GPT-4o-mini / Groq Llama3] for skill extraction + reasoning trace
- Embeddings: sentence-transformers/all-MiniLM-L6-v2 for skill matching

## Evaluation Metrics
- Skill extraction accuracy (tested against 10 sample resumes)
- Path validity rate (% of paths with no prerequisite violations)
- Anti-hallucination rate (% of courses matched to catalog)
```

### Docker Setup (Hour 39–40)
```dockerfile
# docker-compose.yml
version: '3.8'
services:
  ml_service:
    build: ./ml_service
    ports: ["5001:5001"]
  backend:
    build: ./backend
    ports: ["3001:3001"]
    depends_on: [ml_service]
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
```

### Demo Video Script (Hour 40–42)
**Duration: exactly 2.5 minutes. Use "Try a sample" button for speed.**

```
[0:00–0:20]  Hook — state the problem in one sentence. Show the blank UI.
[0:20–0:50]  Upload a junior developer resume + a senior backend JD. Hit Analyze.
[0:50–1:30]  Walk through the skill gap panel — show identified gaps, priority scores.
[1:30–2:00]  Show the DAG roadmap — point out prerequisite chains and color coding.
[2:00–2:20]  Show the reasoning trace — one click to expand.
[2:20–2:30]  Upload a DIFFERENT resume (senior dev) — show the path shrinks. Proves adaptivity.
```

Record with Loom or OBS. One clean take. No edits needed if you practice twice.

### 5-Slide Deck (Hour 42–44)
Use the required structure exactly:

**Slide 1 — Solution Overview**
- Problem: Static onboarding wastes 40% of training time
- Solution: AI engine that personalizes the path in <30 seconds
- Key differentiator: DAG-based prerequisite chaining + zero hallucination guarantee

**Slide 2 — Architecture & Workflow**
- System diagram of the pipeline (copy your flowchart)
- Highlight: React → Node.js → Python ML service → LLM → Course Catalog DB

**Slide 3 — Tech Stack & Models**
- Frontend: React, react-flow, react-dropzone
- Backend: Node.js, Express, pdfplumber
- ML: sentence-transformers, networkx, spaCy
- LLM: GPT-4o-mini (extraction + reasoning trace)

**Slide 4 — Algorithms & Training**
- Skill extraction: LLM → JSON → embedding-based catalog matching
- Gap analyzer: level-aware diff algorithm with priority weighting
- Adaptive pathing: Topological sort on prerequisite DAG (explain with a mini-diagram)

**Slide 5 — Datasets & Metrics**
- Datasets: O*NET, Kaggle Resume Dataset, custom catalog
- Metrics: extraction accuracy, path validity rate, hallucination rate, time-to-path

---

## Hour 44–48 | Final Testing & Submission

### Final Checklist
- [ ] End-to-end flow works with 3 different resume+JD pairs
- [ ] No hallucinated courses appear in any output
- [ ] README is complete and renders correctly on GitHub
- [ ] Demo video is uploaded (YouTube unlisted or Google Drive)
- [ ] Docker compose starts cleanly with `docker-compose up`
- [ ] All 3 deliverables (GitHub, Video, Slides) are ready
- [ ] GitHub repo is public
- [ ] All datasets and models cited in README and Slide 5

### Submission
Push final commit. Submit links. Done.

---

## Scoring Optimization Summary

| Criterion | Weight | How to Win It |
|-----------|--------|---------------|
| Technical Sophistication | 20% | DAG path generator + embedding-based matching |
| Communication & Docs | 20% | Polished README + clean slides + good video |
| Grounding & Reliability | 15% | Whitelist validation, never return off-catalog courses |
| User Experience | 15% | react-flow roadmap, progress steps, sample data button |
| Product Impact | 10% | Show side-by-side: junior vs senior — different paths |
| Reasoning Trace | 10% | Collapsible LLM explanation panel in the UI |
| Cross-Domain Scalability | 10% | Include courses from 5+ domains in catalog |

---

## Emergency Cuts (If Falling Behind)

**Cut first (low-value):**
- PDF download of roadmap
- Docker setup
- Fancy animations

**Never cut (judged explicitly):**
- Reasoning trace feature
- Anti-hallucination validation
- README with setup instructions
- Demo video
- 5-slide deck

---

*Start Hour 0 now. Lock architecture in the first 30 minutes. Everything else follows.*