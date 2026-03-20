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

router.post('/analyze', async (req, res) => {
  return res.json({ status: 'not implemented' });
});

router.get('/:id', async (req, res, next) => {
  try {
    const supabase = getSupabase();
    if (!supabase) {
      return res.status(503).json({ error: 'Database client not configured yet' });
    }

    const { id } = req.params;

    const { data, error } = await supabase.from('sessions').select('*').eq('id', id).maybeSingle();

    if (error) {
      throw error;
    }

    if (!data) {
      return res.status(404).json({ error: 'Session not found' });
    }

    return res.json(data);
  } catch (error) {
    return next(error);
  }
});

module.exports = router;
