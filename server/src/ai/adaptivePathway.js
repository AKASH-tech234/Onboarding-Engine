const { levelToNum } = require("../utils/levelToNum");

let embedText = null;

try {
  ({ embed: embedText } = require("./gemini"));
} catch (error) {
  embedText = null;
}

function scoreCandidate(course, gap) {
  const gapCriticality = gap.required ? 1.0 : 0.5;
  const impactCoverage = Number.isFinite(Number(course.impact))
    ? Number(course.impact)
    : 0.5;
  const levelFit = 1 - Math.abs(Number(course.level_num) - gap.target_num) / 2;
  const duration = Number(course.duration_hrs);
  const safeDuration = Number.isFinite(duration) && duration > 0 ? duration : 1;
  const efficiency = 1 / Math.log(safeDuration + Math.E);
  const total =
    gapCriticality * 0.4 +
    impactCoverage * 0.3 +
    levelFit * 0.2 +
    efficiency * 0.1;

  return {
    total,
    gap_criticality: gapCriticality,
    impact_coverage: impactCoverage,
    level_fit: levelFit,
    efficiency,
  };
}

function topologicalSort(courses) {
  const inDegree = {};
  const graph = {};
  const courseById = new Map();

  for (const course of courses) {
    inDegree[course.id] = 0;
    graph[course.id] = [];
    courseById.set(course.id, course);
  }

  for (const course of courses) {
    for (const prerequisiteId of course.prerequisites || []) {
      if (!graph[prerequisiteId]) {
        continue;
      }

      graph[prerequisiteId].push(course.id);
      inDegree[course.id] += 1;
    }
  }

  const queue = courses
    .filter((course) => inDegree[course.id] === 0)
    .sort((left, right) => right.score - left.score);

  const sorted = [];

  while (queue.length > 0) {
    const node = queue.shift();
    sorted.push(node);

    for (const neighborId of graph[node.id]) {
      inDegree[neighborId] -= 1;

      if (inDegree[neighborId] === 0) {
        queue.push(courseById.get(neighborId));
        queue.sort((left, right) => right.score - left.score);
      }
    }
  }

  if (sorted.length === courses.length) {
    return sorted;
  }

  const remaining = courses
    .filter((course) => !sorted.some((item) => item.id === course.id))
    .sort((left, right) => right.score - left.score);

  return [...sorted, ...remaining];
}

function assignPhase(course) {
  if (course.level_num === 1) {
    return { phase: 1, phase_label: "Foundation" };
  }

  if (course.level_num === 2) {
    return { phase: 2, phase_label: "Core Competency" };
  }

  return course.gap.required
    ? { phase: 3, phase_label: "Specialization" }
    : { phase: 4, phase_label: "Stretch Goals" };
}

function normalizeCourse(gap, course) {
  const levelNum =
    Number(course.level_num) ||
    levelToNum(course.level || gap.target || "beginner");
  const scoring = scoreCandidate({ ...course, level_num: levelNum }, gap);

  return {
    ...course,
    level_num: levelNum,
    duration_hrs: Number(course.duration_hrs) || 0,
    prerequisites: Array.isArray(course.prerequisites) ? course.prerequisites : [],
    gap,
    addresses_skill: gap.skill,
    gap_type: gap.current ? "gap" : "missing",
    score: scoring.total,
    score_breakdown: scoring,
  };
}

async function fetchPrimaryCourses(supabaseClient, gap) {
  if (!supabaseClient?.rpc || !gap.skill_id) {
    return [];
  }

  const { data, error } = await supabaseClient.rpc("match_courses_by_skill", {
    p_skill_id: gap.skill_id,
    p_min_level_num: gap.current_num,
  });

  if (error) {
    return [];
  }

  return Array.isArray(data) ? data : [];
}

async function fetchVectorCourses(supabaseClient, gap) {
  if (!supabaseClient?.rpc || typeof embedText !== "function") {
    return [];
  }

  try {
    const embedding = await embedText(gap.skill);
    const { data, error } = await supabaseClient.rpc("match_courses_by_vector", {
      query_embedding: embedding,
      threshold: 0.6,
    });

    if (error) {
      return [];
    }

    return Array.isArray(data) ? data : [];
  } catch (error) {
    return [];
  }
}

function dedupeCourses(courses) {
  const bestCourseById = new Map();

  for (const course of courses) {
    const existing = bestCourseById.get(course.id);

    if (!existing || course.score > existing.score) {
      bestCourseById.set(course.id, course);
    }
  }

  return Array.from(bestCourseById.values());
}

function groupIntoPhases(sortedCourses) {
  const phaseMap = new Map();

  for (const course of sortedCourses) {
    const phaseInfo = assignPhase(course);
    const existing = phaseMap.get(phaseInfo.phase) || {
      phase: phaseInfo.phase,
      phase_label: phaseInfo.phase_label,
      courses: [],
      phase_duration_hrs: 0,
    };

    existing.courses.push(course);
    existing.phase_duration_hrs += course.duration_hrs;
    phaseMap.set(phaseInfo.phase, existing);
  }

  return Array.from(phaseMap.values()).sort((left, right) => left.phase - right.phase);
}

async function adaptivePathway(skillGap, supabaseClient) {
  const gapItems = [
    ...(Array.isArray(skillGap?.gaps) ? skillGap.gaps : []),
    ...(Array.isArray(skillGap?.missing) ? skillGap.missing : []),
  ];

  if (gapItems.length === 0) {
    return {
      phases: [],
      total_training_hrs: 0,
    };
  }

  const scoredCandidates = [];

  for (const gapItem of gapItems) {
    const primaryCourses = await fetchPrimaryCourses(supabaseClient, gapItem);
    const vectorCourses = await fetchVectorCourses(supabaseClient, gapItem);

    const mergedCourses = [...primaryCourses, ...vectorCourses]
      .filter((course) => course && course.id)
      .map((course) => normalizeCourse(gapItem, course));

    scoredCandidates.push(...mergedCourses);
  }

  const dedupedCourses = dedupeCourses(scoredCandidates);
  const sortedCourses = topologicalSort(dedupedCourses);
  const phases = groupIntoPhases(sortedCourses);
  const totalTrainingHours = phases.reduce(
    (sum, phase) => sum + phase.phase_duration_hrs,
    0
  );

  return {
    phases,
    total_training_hrs: totalTrainingHours,
  };
}

module.exports = {
  adaptivePathway,
  assignPhase,
  scoreCandidate,
  topologicalSort,
};
