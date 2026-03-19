// React: src/api/analyze.js
const formData = new FormData();
formData.append('resume', resumeFile);          // PDF file object
formData.append('jd_text', jobDescriptionText); // or append('job_description', jdFile)

const res = await fetch('http://localhost:3001/api/analyze', {
  method: 'POST',
  body: formData   // no Content-Type header — browser sets it with boundary
});
const data = await res.json();
```

Node.js receives it in `routes/analyze.js` → `middleware/upload.js` (multer) → `controllers/analyzeController.js`:
```
REQUEST  hitting  backend/routes/analyze.js
─────────────────────────────────────────────
POST /api/analyze
Content-Type: multipart/form-data; boundary=----FormBoundaryXYZ

[PDF binary: resume.pdf]
[text: jd_text = "We need a Full Stack Engineer..."]

AFTER multer processes it  (upload.js):
req.files = {
  resume: [{ originalname: "priya_resume.pdf", path: "./uploads/abc123.pdf", size: 4821 }]
}
req.body = { jd_text: "We need a Full Stack Engineer..." }
```

---

## Hop 2 — `backend/` (Node.js) → `ml_service/` (Python)

`analyzeController.js` calls `mlService.js`, which makes two sequential HTTP calls to Flask:
```
CALL 1 — extract text from PDF
────────────────────────────────────────────────────────
POST http://localhost:5001/extract-text
Content-Type: multipart/form-data

file = <binary stream of ./uploads/abc123.pdf>

RESPONSE:
{ "text": "Priya Sharma\nJunior Frontend Dev...", "char_count": 1842 }

CALL 2 — run full analysis
────────────────────────────────────────────────────────
POST http://localhost:5001/analyze
Content-Type: application/json

{
  "resume_text": "Priya Sharma\nJunior Frontend Dev...",
  "jd_text": "We need a Full Stack Engineer with Node.js, Docker..."
}

RESPONSE (from ml_service/app.py after all 6 pipeline steps):
{
  "success": true,
  "candidate": { "name": "Priya Sharma", "current_role": "Junior Frontend Dev", ... },
  "skill_gaps": [ { "skill": "Node.js", "type": "missing", "priority": 1.0 }, ... ],
  "learning_path": [ { "order": 1, "course_id": "C004", "title": "React.js Modern Frontend", ... }, ... ],
  "reasoning_trace": "Priya brings solid frontend skills but lacks...",
  "total_training_hours": 82,
  "estimated_weeks": 8.2
}
```

---

## Hop 3 — `backend/` sends final response back to React

`analyzeController.js` adds meta fields and returns to React:
```
RESPONSE to React
──────────────────────────────────────────────────────
HTTP 200 OK
Content-Type: application/json

{
  "success": true,
  "candidate": { ... },
  "target_role": "Full Stack Engineer",
  "skill_gaps": [ ... ],
  "learning_path": [ ... ],
  "reasoning_trace": "...",
  "total_training_hours": 82,
  "estimated_weeks": 8.2,
  "meta": {
    "processing_time_seconds": 5.34,
    "resume_filename": "priya_resume.pdf",
    "jd_filename": "text-input"
  }
}
```

React renders the roadmap from `data.learning_path` and skill gap chips from `data.skill_gaps`.

---

## The complete file-to-file map
```
React                      Node.js backend/              Python ml_service/
──────────────────────     ──────────────────────────    ──────────────────────────
src/api/analyze.js    →    routes/analyze.js
                      →    middleware/upload.js  (multer saves PDF to uploads/)
                      →    controllers/analyzeController.js
                      →    services/mlService.js  ──────→  app.py  /extract-text
                                                  ──────→  app.py  /analyze
                                                              extractors/pdf_extractor.py
                                                              analyzers/skill_extractor.py
                                                              models/embeddings.py
                                                              analyzers/gap_analyzer.py
                                                              analyzers/path_generator.py
                                                              utils/validators.py
                      ←    analyzeController.js  ←──────  app.py  (full JSON)
src/components/
  Roadmap.jsx         ←    HTTP 200 JSON response
  SkillGaps.jsx
  ReasoningTrace.jsx