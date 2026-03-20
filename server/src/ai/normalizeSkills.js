const supabase = require('../db/supabaseClient')
const { embed } = require('./gemini')

async function normalizeSkills(skillNames) {
  return Promise.all(skillNames.map(async (skillName) => {
    const vec = await embed(skillName)

    const { data, error } = await supabase.rpc('match_skill_by_embedding', {
      query_embedding: vec,
      match_threshold: 0.0,
      match_count: 1
    })

    let topMatch = null
    if (!error && data && data.length > 0) {
      topMatch = data[0]
    }

    if (topMatch && topMatch.similarity >= 0.85) {
      return {
        original: skillName,
        normalized_id: topMatch.id,
        normalized_name: topMatch.name,
        matched: true
      }
    } else {
      const { data: inserted, error: insertError } = await supabase
        .from('skills')
        .insert({ name: skillName, category: 'Unknown', domain: 'Unknown', embedding: vec })
        .select('id')
        .single()

      if (insertError && insertError.code === '23505') {
        const { data: existing } = await supabase
          .from('skills')
          .select('id, name')
          .eq('name', skillName)
          .single()

        return {
          original: skillName,
          normalized_id: existing.id,
          normalized_name: existing.name,
          matched: true
        }
      } else if (insertError) {
        throw insertError
      } else {
        return {
          original: skillName,
          normalized_id: inserted.id,
          normalized_name: skillName,
          matched: false
        }
      }
    }
  }))
}

module.exports = { normalizeSkills }