const { embed } = require('./gemini.js');
const { supabase } = require('../db/supabaseClient.js');

async function normalizeSkills(skillNames) {
  const results = [];

  for (const skillName of skillNames) {
    const vec = await embed(skillName);
    
    // Relies on RPC 'match_skill' returning [{ id, name, similarity }]
    const { data: matches, error } = await supabase.rpc('match_skill', {
      query_embedding: vec,
      match_count: 1
    });

    if (error) {
      console.error(error);
      throw error;
    }

    if (matches && matches.length > 0 && matches[0].similarity >= 0.85) {
      results.push({
        original: skillName,
        normalized_id: matches[0].id,
        normalized_name: matches[0].name,
        matched: true
      });
    } else {
      const { data: newSkill, error: insertError } = await supabase
        .from('skills')
        .insert({
          name: skillName,
          category: 'Unknown',
          domain: 'Unknown',
          embedding: vec
        })
        .select()
        .single();

      results.push({
        original: skillName,
        normalized_id: newSkill?.id,
        normalized_name: skillName,
        matched: false
      });
    }
  }

  return results;
}

module.exports = { normalizeSkills };
