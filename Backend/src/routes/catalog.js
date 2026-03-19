const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');

const CATALOG_PATH = path.join(__dirname, '../data/course_catalog.json');

let catalogCache = null;

function getCatalog() {
  if (!catalogCache) {
    catalogCache = JSON.parse(fs.readFileSync(CATALOG_PATH, 'utf8'));
  }
  return catalogCache;
}

router.get('/', (req, res) => {
  try {
    const catalog = getCatalog();
    const { category, level } = req.query;

    let filtered = catalog;
    if (category) filtered = filtered.filter(c => c.category.toLowerCase() === category.toLowerCase());
    if (level) filtered = filtered.filter(c => c.level.toLowerCase() === level.toLowerCase());

    res.json({
      total: filtered.length,
      courses: filtered,
      categories: [...new Set(catalog.map(c => c.category))],
      levels: ['beginner', 'intermediate', 'advanced']
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to load course catalog.' });
  }
});

router.get('/:id', (req, res) => {
  const catalog = getCatalog();
  const course = catalog.find(c => c.id === req.params.id);
  if (!course) return res.status(404).json({ error: `Course ${req.params.id} not found.` });
  res.json(course);
});

module.exports = router;