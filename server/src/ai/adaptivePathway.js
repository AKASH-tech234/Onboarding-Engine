const { embed } = require('./gemini')
const { levelToNum } = require('../utils/levelToNum')

function scoreCandidate(course, gap) {
  const gap_criticality = gap.required ? 1.0 : 0.5
  const impact_coverage = course.impact ?? 0.5
  const level_fit = 1 - Math.abs(course.level_num - gap.target_num) / 2
  const efficiency = 1 / Math.log(course.duration_hrs + Math.E)
  const total = (gap_criticality * 0.40) + (impact_coverage * 0.30) + (level_fit * 0.20) + (efficiency * 0.10)
  return { total, gap_criticality, impact_coverage, level_fit, efficiency }
}

function assignPhase(course) {
  if (course.level_num === 1) return { phase: 1, phase_label: 'Foundation' }
  if (course.level_num === 2) return { phase: 2, phase_label: 'Core Competency' }
  return course.gap.required
    ? { phase: 3, phase_label: 'Specialization' }
    : { phase: 4, phase_label: 'Stretch Goals' }
}

function topologicalSort(courses) {
  const inDegree = {}
  const graph = {}

  for (const c of courses) {
    inDegree[c.id] = 0
    graph[c.id] = []
  }

  for (const c of courses) {
    for (const prereqId of (c.prerequisites || [])) {
      if (graph[prereqId]) {
        graph[prereqId].push(c.id)
        inDegree[c.id]++
      }
    }
  }

  const queue = courses
    .filter(c => inDegree[c.id] === 0)
    .sort((a, b) => b.score - a.score)

  const result = []

  while (queue.length) {
    const node = queue.shift()
    result.push(node)
    for (const nId of graph[node.id]) {
      inDegree[nId]--
      if (inDegree[nId] === 0) {
        queue.push(courses.find(c => c.id === nId))
        queue.sort((a, b) => b.score - a.score)
      }
    }
  }

  return result
}

async function adaptivePathway(skillGap, supabase) {
  const allGaps = [...skillGap.gaps, ...skillGap.missing]

  if (allGaps.length === 0) {
    return { phases: [], total_training_hrs: 0 }
  }

  const candidateMap = {}

  for (const gapItem of allGaps) {
    const { data: primary } = await supabase
      .from('skill_course_map')
      .select('impact, courses(*)')
      .eq('skill_id', gapItem.skill_id)
      .limit(5)

    const primaryCourses = (primary || [])
      .filter(row => row.courses && row.courses.level_num >= gapItem.current_num)
      .map(row => ({ ...row.courses, impact: row.impact }))
      .sort((a, b) => b.impact - a.impact)
      .slice(0, 3)

    const vec = await embed(gapItem.skill)
    const { data: fallback } = await supabase.rpc('match_courses_by_vector', {
      query_embedding: vec,
      match_threshold: 0.6,
      match_count: 3
    })

    const combined = [...primaryCourses, ...(fallback || [])]

    for (const course of combined) {
      if (!course || !course.id) continue
      if (!candidateMap[course.id] || candidateMap[course.id].score < scoreCandidate(course, gapItem).total) {
        const scoreResult = scoreCandidate(course, gapItem)
        candidateMap[course.id] = {
          ...course,
          gap: gapItem,
          score: scoreResult.total,
          score_breakdown: scoreResult
        }
      }
    }
  }

  const candidates = Object.values(candidateMap)

  if (candidates.length === 0) {
    return { phases: [], total_training_hrs: 0 }
  }

  const sorted = topologicalSort(candidates)

  const phaseGroups = {}
  for (const course of sorted) {
    const { phase, phase_label } = assignPhase(course)
    if (!phaseGroups[phase]) {
      phaseGroups[phase] = { phase, phase_label, courses: [], phase_duration_hrs: 0 }
    }
    phaseGroups[phase].courses.push(course)
    phaseGroups[phase].phase_duration_hrs += course.duration_hrs
  }

  const phases = Object.values(phaseGroups).sort((a, b) => a.phase - b.phase)
  const total_training_hrs = phases.reduce((sum, p) => sum + p.phase_duration_hrs, 0)

  return { phases, total_training_hrs }
}

module.exports = { adaptivePathway }