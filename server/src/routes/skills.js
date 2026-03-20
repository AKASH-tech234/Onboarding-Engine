const express = require('express');
const { supabase } = require('../db/supabaseClient.js');

const router = express.Router();

router.get('/', async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from('skills')
      .select('*')
      .order('name');
      
    if (error) throw error;
    res.json(data);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
