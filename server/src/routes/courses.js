const express = require('express');

const router = express.Router();

function getSupabase() {
  try {
    return require('../db/supabaseClient');
  } catch (error) {
    if (error.code === 'MODULE_NOT_FOUND') {
      return null;
    }
    throw error;
  }
}

router.get('/', async (req, res, next) => {
  try {
    const supabase = getSupabase();
    if (!supabase) {
      return res.status(503).json({ error: 'Database client not configured yet' });
    }

    const { domain, level, skill_id: skillId } = req.query;

    let query = supabase.from('courses').select('*').order('title', { ascending: true });

    if (domain) {
      query = query.eq('domain', domain);
    }
    if (level) {
      query = query.eq('level', level);
    }
    if (skillId) {
      query = query.eq('skill_id', skillId);
    }

    const { data, error } = await query;
    if (error) {
      throw error;
    }

    return res.json(data || []);
  } catch (error) {
    return next(error);
  }
});

router.post('/', async (req, res, next) => {
  try {
    if (req.headers['x-seed-secret'] !== process.env.SEED_SECRET) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const supabase = getSupabase();
    if (!supabase) {
      return res.status(503).json({ error: 'Database client not configured yet' });
    }

    const incoming = Array.isArray(req.body) ? req.body : req.body.courses;
    if (!Array.isArray(incoming) || incoming.length === 0) {
      return res.status(400).json({ error: 'Body must be a non-empty array of course objects' });
    }

    const courseRows = incoming.map((item) => {
      const { skill_mappings: skillMappings, ...course } = item;
      return course;
    });

    const { data: insertedCourses, error: insertCoursesError } = await supabase
      .from('courses')
      .insert(courseRows)
      .select('id, title');

    if (insertCoursesError) {
      throw insertCoursesError;
    }

    const titleToId = Object.fromEntries((insertedCourses || []).map((course) => [course.title, course.id]));

    const mappingRows = incoming.flatMap((item) => {
      const skillMappings = Array.isArray(item.skill_mappings) ? item.skill_mappings : [];
      const resolvedCourseId = item.course_id || titleToId[item.title];
      if (!resolvedCourseId || skillMappings.length === 0) {
        return [];
      }

      return skillMappings
        .filter((mapping) => mapping && mapping.skill_id)
        .map((mapping) => ({
          course_id: resolvedCourseId,
          skill_id: mapping.skill_id,
          impact: typeof mapping.impact === 'number' ? mapping.impact : 1,
        }));
    });

    let insertedMappings = 0;
    if (mappingRows.length > 0) {
      const { data: mappingData, error: insertMapError } = await supabase
        .from('skill_course_map')
        .insert(mappingRows)
        .select('course_id');

      if (insertMapError) {
        throw insertMapError;
      }
      insertedMappings = (mappingData || []).length;
    }

    return res.status(201).json({
      inserted: (insertedCourses || []).length,
      mappings_inserted: insertedMappings,
    });
  } catch (error) {
    return next(error);
  }
});

module.exports = router;
