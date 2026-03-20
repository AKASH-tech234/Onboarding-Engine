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

    const { data, error } = await supabase.from('skills').select('*').order('name', { ascending: true });

    if (error) {
      throw error;
    }

    return res.json(data || []);
  } catch (error) {
    return next(error);
  }
});

module.exports = router;
