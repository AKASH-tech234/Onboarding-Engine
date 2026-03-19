# Backend — Complete Setup Guide
## Every terminal command from zero to running

---

## STEP 1 — Clone / scaffold the project

```bash
# If starting fresh:
mkdir onboarding-engine && cd onboarding-engine

# Copy the folder structure that was given to you:
# onboarding-engine/
# ├── backend/
# ├── ml_service/
# ├── frontend/          ← (React app, set up separately)
# └── docker-compose.yml
```

---

## STEP 2 — Set up the Node.js Backend

```bash
# Navigate into backend
cd backend

# Install all dependencies
npm install

# Create your .env file from the template
cp .env.example .env

# Your .env should look like this (edit if needed):
# PORT=3001
# ML_SERVICE_URL=http://localhost:5001
# NODE_ENV=development
# MAX_FILE_SIZE_MB=10
# UPLOAD_DIR=./uploads

# Create the uploads directory (multer needs it)
mkdir -p uploads

# Verify folder structure looks correct
ls -la
# Expected:
# ├── controllers/
# │   └── analyzeController.js
# ├── data/
# │   ├── course_catalog.json
# │   └── sample_result.json
# ├── middleware/
# │   └── upload.js
# ├── routes/
# │   ├── analyze.js
# │   └── catalog.js
# ├── services/
# │   └── mlService.js
# ├── uploads/
# ├── .env
# ├── .env.example
# ├── Dockerfile
# ├── package.json
# └── server.js

# Start the backend (dev mode with auto-reload)
npm run dev

# You should see:
# Backend running on http://localhost:3001
# ML Service:   http://localhost:5001
# Environment:  development

# Test the health endpoint in a NEW terminal tab:
curl http://localhost:3001/api/health
# Expected: {"status":"ok","service":"backend",...}

# Test the catalog endpoint:
curl http://localhost:3001/api/catalog
# Expected: {"total":42,"courses":[...],...}

# Test sample result (no ML needed):
curl http://localhost:3001/api/analyze/sample
# Expected: full JSON with learning_path, skill_gaps, etc.
```

---
