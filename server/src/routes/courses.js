const express = require('express')
const supabase = require('../db/supabaseClient')

const router = express.Router()

router.get('/', async (req, res, next) => {
  try {
    let query = supabase.from('courses').select('*')

    if (req.query.domain) query = query.eq('domain', req.query.domain)
    if (req.query.level) query = query.eq('level', req.query.level)
    if (req.query.skill_id) query = query.eq('skill_id', req.query.skill_id)

    const { data, error } = await query.order('title', { ascending: true })

    if (error) throw error
    res.json(data || [])
  } catch (err) {
    next(err)
  }
})

router.post('/', async (req, res, next) => {
  try {
    if (req.headers['x-seed-secret'] !== process.env.SEED_SECRET) {
      return res.status(403).json({ error: 'Forbidden' })
    }

    const courses = req.body
    const { data, error } = await supabase
      .from('courses')
      .insert(courses)
      .select()

    if (error) throw error
    res.json({ inserted: data.length })
  } catch (err) {
    next(err)
  }
})

module.exports = router