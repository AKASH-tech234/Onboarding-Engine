CREATE TABLE skills (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL UNIQUE,
  category    TEXT NOT NULL,
  domain      TEXT NOT NULL,
  embedding   vector(768),
  created_at  TIMESTAMPTZ DEFAULT now()
);

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

CREATE TABLE sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resume_text     TEXT,
  jd_text         TEXT,
  extracted_skills JSONB,
  required_skills  JSONB,
  skill_gap        JSONB,
  pathway          JSONB,
  reasoning_trace  JSONB,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE skill_course_map (
  course_id  UUID REFERENCES courses(id),
  skill_id   UUID REFERENCES skills(id),
  impact     NUMERIC(3,2) CHECK (impact BETWEEN 0 AND 1),
  PRIMARY KEY (course_id, skill_id)
);

CREATE INDEX ON skills USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
CREATE INDEX ON courses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
