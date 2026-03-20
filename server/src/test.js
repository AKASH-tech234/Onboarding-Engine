require('dotenv').config()
const supabase = require('./src/db/supabaseClient')

async function test() {
  const { data, error } = await supabase
    .from('skills')
    .select('*')
    .limit(1)

  if (error) {
    console.log('ERROR:', error.message)
  } else {
    console.log('SUCCESS — connected to Supabase')
    console.log('Skills table exists, rows:', data.length)
  }}

test()