const express = require('express')
const supabase = require('../db/supabaseClient')

const router = express.Router()

router.get('/', async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from('skills')
      .select('*')
      .order('name', { ascending: true })

    if (error) throw error
    res.json(data || [])
  } catch (err) {
    next(err)
  }
})

module.exports = router