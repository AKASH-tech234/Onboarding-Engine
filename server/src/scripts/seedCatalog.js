const path = require("node:path");

let supabase = null;
let embedText = null;

try {
  supabase = require("../db/supabaseClient");
} catch (error) {
  supabase = null;
}

try {
  ({ embed: embedText } = require("../ai/gemini"));
} catch (error) {
  embedText = null;
}

const SKILLS = [
  { name: "HTML", category: "Frontend", domain: "Technical" },
  { name: "CSS", category: "Frontend", domain: "Technical" },
  { name: "JavaScript", category: "Frontend", domain: "Technical" },
  { name: "TypeScript", category: "Frontend", domain: "Technical" },
  { name: "React", category: "Frontend", domain: "Technical" },
  { name: "Node.js", category: "Backend", domain: "Technical" },
  { name: "Express", category: "Backend", domain: "Technical" },
  { name: "Python", category: "Backend", domain: "Technical" },
  { name: "SQL", category: "Data", domain: "Technical" },
  { name: "PostgreSQL", category: "Data", domain: "Technical" },
  { name: "Docker", category: "DevOps", domain: "Technical" },
  { name: "Kubernetes", category: "DevOps", domain: "Technical" },
  { name: "AWS", category: "Cloud", domain: "Technical" },
  { name: "Git", category: "Developer Tools", domain: "Technical" },
  { name: "Testing", category: "Quality", domain: "Technical" },
  { name: "Data Analysis", category: "Analytics", domain: "Operational" },
  { name: "Inventory Management", category: "Operations", domain: "Operational" },
  { name: "Warehouse Management Systems", category: "Operations", domain: "Operational" },
  { name: "OSHA Compliance", category: "Safety", domain: "Operational" },
  { name: "Supply Chain Fundamentals", category: "Operations", domain: "Operational" },
  { name: "Forklift Operation", category: "Operations", domain: "Operational" },
  { name: "Team Leadership", category: "Management", domain: "Operational" },
  { name: "Process Improvement", category: "Management", domain: "Operational" },
  { name: "Communication", category: "Soft Skills", domain: "Operational" },
];

const COURSE_BLUEPRINTS = [
  ["HTML Foundations", "HTML", "beginner", 3.0],
  ["Semantic HTML in Practice", "HTML", "intermediate", 4.0],
  ["Accessible Interface Markup", "HTML", "advanced", 4.5],
  ["CSS Fundamentals", "CSS", "beginner", 3.5],
  ["Responsive CSS Systems", "CSS", "intermediate", 4.5],
  ["Advanced CSS Architecture", "CSS", "advanced", 5.0],
  ["JavaScript Essentials", "JavaScript", "beginner", 5.0],
  ["Modern JavaScript Patterns", "JavaScript", "intermediate", 6.0],
  ["JavaScript Performance Tuning", "JavaScript", "advanced", 6.5],
  ["TypeScript Foundations", "TypeScript", "beginner", 4.0],
  ["TypeScript for React Apps", "TypeScript", "intermediate", 5.0],
  ["Advanced Type Modeling", "TypeScript", "advanced", 6.0],
  ["React Basics", "React", "beginner", 5.0],
  ["React State and Effects", "React", "intermediate", 6.0],
  ["React Performance and Architecture", "React", "advanced", 7.0],
  ["Node.js Foundations", "Node.js", "beginner", 4.5],
  ["Express API Development", "Express", "intermediate", 5.5],
  ["Backend Reliability with Node.js", "Node.js", "advanced", 6.5],
  ["Python Fundamentals", "Python", "beginner", 4.0],
  ["Applied Python Automation", "Python", "intermediate", 5.5],
  ["Production Python Patterns", "Python", "advanced", 6.5],
  ["SQL Basics", "SQL", "beginner", 4.0],
  ["Relational Query Optimization", "SQL", "intermediate", 5.5],
  ["Advanced Database Design", "SQL", "advanced", 6.0],
  ["PostgreSQL Foundations", "PostgreSQL", "beginner", 4.0],
  ["PostgreSQL for Application Teams", "PostgreSQL", "intermediate", 5.0],
  ["PostgreSQL Scaling Strategies", "PostgreSQL", "advanced", 6.5],
  ["Docker Foundations", "Docker", "beginner", 4.0],
  ["Docker for Team Workflows", "Docker", "intermediate", 5.0],
  ["Container Platform Hardening", "Docker", "advanced", 6.0],
  ["Kubernetes Fundamentals", "Kubernetes", "beginner", 5.0],
  ["Kubernetes Workload Management", "Kubernetes", "intermediate", 6.0],
  ["Advanced Kubernetes Operations", "Kubernetes", "advanced", 7.0],
  ["AWS Cloud Essentials", "AWS", "beginner", 4.0],
  ["AWS Application Deployment", "AWS", "intermediate", 5.5],
  ["AWS Architecture for Scale", "AWS", "advanced", 6.5],
  ["Git Foundations", "Git", "beginner", 3.0],
  ["Collaborative Git Workflows", "Git", "intermediate", 4.0],
  ["Release Management with Git", "Git", "advanced", 4.5],
  ["Testing Fundamentals", "Testing", "beginner", 3.5],
  ["Integration Testing for Teams", "Testing", "intermediate", 4.5],
  ["Quality Strategy and Automation", "Testing", "advanced", 5.0],
  ["Data Analysis Basics", "Data Analysis", "beginner", 4.0],
  ["Operational KPI Analysis", "Data Analysis", "intermediate", 5.0],
  ["Analytics for Process Leaders", "Data Analysis", "advanced", 5.5],
  ["Inventory Management Fundamentals", "Inventory Management", "beginner", 4.0],
  ["Inventory Control Systems", "Inventory Management", "intermediate", 5.0],
  ["Advanced Inventory Optimization", "Inventory Management", "advanced", 5.5],
  ["Warehouse Management Systems Basics", "Warehouse Management Systems", "beginner", 4.0],
  ["WMS Operations in Practice", "Warehouse Management Systems", "intermediate", 5.5],
  ["WMS Implementation Leadership", "Warehouse Management Systems", "advanced", 6.0],
  ["OSHA Safety Essentials", "OSHA Compliance", "beginner", 3.5],
  ["Applied Workplace Safety", "OSHA Compliance", "intermediate", 4.5],
  ["Safety Program Leadership", "OSHA Compliance", "advanced", 5.0],
  ["Supply Chain Basics", "Supply Chain Fundamentals", "beginner", 4.0],
  ["Supply Planning and Fulfillment", "Supply Chain Fundamentals", "intermediate", 5.0],
  ["Strategic Supply Chain Design", "Supply Chain Fundamentals", "advanced", 6.0],
  ["Forklift Operation Safety", "Forklift Operation", "beginner", 3.0],
  ["Advanced Material Handling", "Forklift Operation", "intermediate", 4.0],
  ["Warehouse Equipment Leadership", "Forklift Operation", "advanced", 4.5],
  ["Team Leadership Foundations", "Team Leadership", "beginner", 3.5],
  ["Leading Shift Operations", "Team Leadership", "intermediate", 4.5],
  ["Leadership for Ops Managers", "Team Leadership", "advanced", 5.5],
  ["Process Improvement Basics", "Process Improvement", "beginner", 3.5],
  ["Lean Operations Improvement", "Process Improvement", "intermediate", 4.5],
  ["Continuous Improvement Leadership", "Process Improvement", "advanced", 5.5],
  ["Workplace Communication Essentials", "Communication", "beginner", 3.0],
  ["Cross-Functional Communication", "Communication", "intermediate", 4.0],
  ["Stakeholder Communication Strategy", "Communication", "advanced", 4.5],
];

const LEVEL_TO_NUM = {
  beginner: 1,
  intermediate: 2,
  advanced: 3,
};

const SKILL_DESCRIPTIONS = {
  Technical:
    "Builds role-specific technical capability through applied practice and job-relevant exercises.",
  Operational:
    "Develops execution, safety, and team-readiness skills for operational environments.",
};

function slugify(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function buildCourseBlueprints() {
  return COURSE_BLUEPRINTS.map(([title, skillName, level, duration]) => {
    const skill = SKILLS.find((item) => item.name === skillName);
    const levelNum = LEVEL_TO_NUM[level];
    const prerequisites = [];

    if (level === "intermediate") {
      prerequisites.push(`${slugify(skillName)}-beginner`);
    }

    if (level === "advanced") {
      prerequisites.push(`${slugify(skillName)}-intermediate`);
    }

    if (skillName === "React" && level !== "beginner") {
      prerequisites.push("javascript-intermediate");
    }

    if (skillName === "Express" && level === "intermediate") {
      prerequisites.push("node-js-beginner");
    }

    if (skillName === "Kubernetes") {
      prerequisites.push("docker-intermediate");
    }

    if (skillName === "AWS" && level !== "beginner") {
      prerequisites.push("docker-beginner");
    }

    return {
      seed_key: `${slugify(skillName)}-${level}`,
      title,
      description: `${title} helps learners progress in ${skillName}. ${SKILL_DESCRIPTIONS[skill.domain]}`,
      skill_name: skillName,
      level,
      level_num: levelNum,
      duration_hrs: duration,
      domain: skill.domain,
      provider: skill.domain === "Technical" ? "Coursera" : "Internal Academy",
      url: `https://example.com/courses/${slugify(title)}`,
      prerequisite_keys: prerequisites,
    };
  });
}

async function maybeEmbed(text) {
  if (typeof embedText !== "function") {
    return null;
  }

  try {
    return await embedText(text);
  } catch (error) {
    return null;
  }
}

async function upsertSkills(skillRows) {
  const rows = [];

  for (const skill of skillRows) {
    rows.push({
      name: skill.name,
      category: skill.category,
      domain: skill.domain,
      embedding: await maybeEmbed(skill.name),
    });
  }

  const { data, error } = await supabase
    .from("skills")
    .upsert(rows, { onConflict: "name" })
    .select("id, name, domain, category");

  if (error) {
    throw error;
  }

  return data;
}

async function upsertCourses(courseBlueprints, skillIdByName) {
  const insertedCourses = [];

  for (const course of courseBlueprints) {
    const embeddingText = `${course.title}\n${course.description}`;
    const row = {
      title: course.title,
      description: course.description,
      skill_id: skillIdByName.get(course.skill_name),
      level: course.level,
      level_num: course.level_num,
      duration_hrs: course.duration_hrs,
      domain: course.domain,
      provider: course.provider,
      url: course.url,
      prerequisites: [],
      embedding: await maybeEmbed(embeddingText),
    };

    const { data, error } = await supabase
      .from("courses")
      .upsert(row, { onConflict: "title" })
      .select("id, title")
      .single();

    if (error) {
      throw error;
    }

    insertedCourses.push({
      ...data,
      seed_key: course.seed_key,
      skill_name: course.skill_name,
      level: course.level,
      prerequisite_keys: course.prerequisite_keys,
      duration_hrs: course.duration_hrs,
      domain: course.domain,
    });
  }

  return insertedCourses;
}

async function updateCoursePrerequisites(insertedCourses) {
  const courseIdBySeedKey = new Map(
    insertedCourses.map((course) => [course.seed_key, course.id])
  );

  for (const course of insertedCourses) {
    const prerequisites = course.prerequisite_keys
      .map((key) => courseIdBySeedKey.get(key))
      .filter(Boolean);

    const { error } = await supabase
      .from("courses")
      .update({ prerequisites })
      .eq("id", course.id);

    if (error) {
      throw error;
    }
  }
}

async function upsertSkillCourseMap(insertedCourses, skillIdByName) {
  const rows = insertedCourses.map((course) => ({
    course_id: course.id,
    skill_id: skillIdByName.get(course.skill_name),
    impact: course.level === "beginner" ? 0.75 : course.level === "intermediate" ? 0.88 : 0.96,
  }));

  const { error } = await supabase
    .from("skill_course_map")
    .upsert(rows, { onConflict: "course_id,skill_id" });

  if (error) {
    throw error;
  }
}

async function main() {
  if (!supabase) {
    throw new Error(
      `Missing Supabase client. Expected ../db/supabaseClient from ${path.resolve(__dirname)}`
    );
  }

  const courseBlueprints = buildCourseBlueprints();
  const skills = await upsertSkills(SKILLS);
  const skillIdByName = new Map(skills.map((skill) => [skill.name, skill.id]));
  const insertedCourses = await upsertCourses(courseBlueprints, skillIdByName);

  await updateCoursePrerequisites(insertedCourses);
  await upsertSkillCourseMap(insertedCourses, skillIdByName);

  process.stdout.write(
    JSON.stringify(
      {
        skills_seeded: skills.length,
        courses_seeded: insertedCourses.length,
      },
      null,
      2
    ) + "\n"
  );
}

if (require.main === module) {
  main().catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exit(1);
  });
}

module.exports = {
  SKILLS,
  buildCourseBlueprints,
  main,
};
