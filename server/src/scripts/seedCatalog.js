require('dotenv').config()
const supabase = require('../db/supabaseClient')
const { embed } = require('../ai/gemini')

const courses = [
  // Technical — Frontend
  { title: 'HTML & CSS Fundamentals', description: 'Learn the building blocks of the web. Covers HTML structure, CSS styling, layouts, and responsive design principles.', skill_name: 'HTML & CSS', level: 'beginner', level_num: 1, duration_hrs: 3.0, domain: 'Technical', provider: 'freeCodeCamp', url: 'https://freecodecamp.org', prerequisite_titles: [] },
  { title: 'JavaScript Essentials', description: 'Core JavaScript concepts including variables, functions, arrays, objects, and DOM manipulation. Foundation for all frontend work.', skill_name: 'JavaScript', level: 'beginner', level_num: 1, duration_hrs: 5.0, domain: 'Technical', provider: 'freeCodeCamp', url: 'https://freecodecamp.org', prerequisite_titles: [] },
  { title: 'React Basics', description: 'Introduction to React including components, props, state, and hooks. Build your first React application from scratch.', skill_name: 'React', level: 'intermediate', level_num: 2, duration_hrs: 6.0, domain: 'Technical', provider: 'Udemy', url: 'https://udemy.com', prerequisite_titles: ['JavaScript Essentials'] },
  { title: 'React Advanced Patterns', description: 'Advanced React patterns including context, custom hooks, performance optimization, and component composition strategies.', skill_name: 'React', level: 'advanced', level_num: 3, duration_hrs: 5.0, domain: 'Technical', provider: 'Frontend Masters', url: 'https://frontendmasters.com', prerequisite_titles: ['React Basics'] },
  { title: 'TypeScript Foundations', description: 'Type system fundamentals, interfaces, generics, and integrating TypeScript into existing JavaScript projects.', skill_name: 'TypeScript', level: 'intermediate', level_num: 2, duration_hrs: 4.0, domain: 'Technical', provider: 'Scrimba', url: 'https://scrimba.com', prerequisite_titles: ['JavaScript Essentials'] },
  { title: 'Next.js for Production', description: 'Server-side rendering, static generation, API routes, and deployment strategies using Next.js in production environments.', skill_name: 'Next.js', level: 'advanced', level_num: 3, duration_hrs: 6.0, domain: 'Technical', provider: 'Vercel Docs', url: 'https://nextjs.org/learn', prerequisite_titles: ['React Basics', 'TypeScript Foundations'] },

  // Technical — Backend
  { title: 'Node.js + Express Fundamentals', description: 'Build REST APIs with Node.js and Express. Covers routing, middleware, error handling, and connecting to databases.', skill_name: 'Node.js', level: 'intermediate', level_num: 2, duration_hrs: 5.0, domain: 'Technical', provider: 'Udemy', url: 'https://udemy.com', prerequisite_titles: ['JavaScript Essentials'] },
  { title: 'REST API Design', description: 'Best practices for designing RESTful APIs including resource naming, HTTP methods, status codes, and versioning.', skill_name: 'REST API', level: 'intermediate', level_num: 2, duration_hrs: 3.0, domain: 'Technical', provider: 'Pluralsight', url: 'https://pluralsight.com', prerequisite_titles: [] },
  { title: 'GraphQL Fundamentals', description: 'Introduction to GraphQL schema definition, queries, mutations, and resolvers. Build a GraphQL API from scratch.', skill_name: 'GraphQL', level: 'intermediate', level_num: 2, duration_hrs: 4.0, domain: 'Technical', provider: 'Apollo Docs', url: 'https://apollographql.com/tutorials', prerequisite_titles: ['REST API Design'] },
  { title: 'Python for Backend', description: 'Python fundamentals for backend development including data structures, file I/O, modules, and basic scripting patterns.', skill_name: 'Python', level: 'beginner', level_num: 1, duration_hrs: 6.0, domain: 'Technical', provider: 'Coursera', url: 'https://coursera.org', prerequisite_titles: [] },
  { title: 'FastAPI with Python', description: 'Build high-performance APIs with FastAPI. Covers path operations, data validation with Pydantic, and async endpoints.', skill_name: 'FastAPI', level: 'intermediate', level_num: 2, duration_hrs: 4.0, domain: 'Technical', provider: 'FastAPI Docs', url: 'https://fastapi.tiangolo.com', prerequisite_titles: ['Python for Backend'] },

  // Technical — Databases
  { title: 'SQL Fundamentals', description: 'Core SQL including SELECT, JOIN, GROUP BY, subqueries, and basic database design principles for relational databases.', skill_name: 'SQL', level: 'beginner', level_num: 1, duration_hrs: 4.0, domain: 'Technical', provider: 'Mode Analytics', url: 'https://mode.com/sql-tutorial', prerequisite_titles: [] },
  { title: 'PostgreSQL Advanced', description: 'Advanced PostgreSQL covering indexes, transactions, stored procedures, window functions, and performance tuning.', skill_name: 'PostgreSQL', level: 'intermediate', level_num: 2, duration_hrs: 5.0, domain: 'Technical', provider: 'Udemy', url: 'https://udemy.com', prerequisite_titles: ['SQL Fundamentals'] },
  { title: 'MongoDB Basics', description: 'NoSQL fundamentals with MongoDB including documents, collections, CRUD operations, and aggregation pipelines.', skill_name: 'MongoDB', level: 'beginner', level_num: 1, duration_hrs: 3.0, domain: 'Technical', provider: 'MongoDB University', url: 'https://university.mongodb.com', prerequisite_titles: [] },
  { title: 'Redis Caching Strategies', description: 'Caching patterns with Redis including data structures, expiration policies, pub/sub, and session management.', skill_name: 'Redis', level: 'intermediate', level_num: 2, duration_hrs: 3.0, domain: 'Technical', provider: 'Redis University', url: 'https://university.redis.com', prerequisite_titles: ['SQL Fundamentals'] },

  // Technical — DevOps
  { title: 'Linux Command Line Basics', description: 'Essential Linux commands for file management, permissions, processes, networking, and shell scripting fundamentals.', skill_name: 'Linux', level: 'beginner', level_num: 1, duration_hrs: 3.0, domain: 'Technical', provider: 'The Odin Project', url: 'https://theodinproject.com', prerequisite_titles: [] },
  { title: 'Docker Fundamentals', description: 'Containerization with Docker including images, containers, volumes, networking, and writing Dockerfiles for applications.', skill_name: 'Docker', level: 'intermediate', level_num: 2, duration_hrs: 4.0, domain: 'Technical', provider: 'Docker Docs', url: 'https://docs.docker.com', prerequisite_titles: ['Linux Command Line Basics'] },
  { title: 'Kubernetes Basics', description: 'Container orchestration with Kubernetes including pods, deployments, services, config maps, and scaling strategies.', skill_name: 'Kubernetes', level: 'advanced', level_num: 3, duration_hrs: 6.0, domain: 'Technical', provider: 'CNCF', url: 'https://kubernetes.io/training', prerequisite_titles: ['Docker Fundamentals'] },
  { title: 'CI/CD with GitHub Actions', description: 'Automate build, test, and deployment pipelines using GitHub Actions workflows, triggers, and reusable actions.', skill_name: 'CI/CD', level: 'intermediate', level_num: 2, duration_hrs: 4.0, domain: 'Technical', provider: 'GitHub Docs', url: 'https://docs.github.com/actions', prerequisite_titles: [] },
  { title: 'AWS Core Services', description: 'Foundational AWS services including EC2, S3, RDS, IAM, Lambda, and VPC. Covers the AWS Well-Architected Framework.', skill_name: 'AWS', level: 'intermediate', level_num: 2, duration_hrs: 6.0, domain: 'Technical', provider: 'AWS Skill Builder', url: 'https://skillbuilder.aws', prerequisite_titles: [] },

  // Technical — AI/ML
  { title: 'Python for Data Science', description: 'Data manipulation with NumPy and Pandas, data visualization with Matplotlib, and exploratory data analysis techniques.', skill_name: 'Data Science', level: 'intermediate', level_num: 2, duration_hrs: 6.0, domain: 'Technical', provider: 'Kaggle', url: 'https://kaggle.com/learn', prerequisite_titles: ['Python for Backend'] },
  { title: 'Machine Learning Fundamentals', description: 'Supervised and unsupervised learning algorithms, model evaluation, cross-validation, and scikit-learn implementation.', skill_name: 'Machine Learning', level: 'intermediate', level_num: 2, duration_hrs: 8.0, domain: 'Technical', provider: 'Coursera', url: 'https://coursera.org', prerequisite_titles: ['Python for Data Science'] },
  { title: 'LLM APIs and Prompt Engineering', description: 'Working with large language model APIs, prompt design patterns, few-shot learning, and building AI-powered applications.', skill_name: 'Prompt Engineering', level: 'intermediate', level_num: 2, duration_hrs: 3.0, domain: 'Technical', provider: 'DeepLearning.ai', url: 'https://deeplearning.ai', prerequisite_titles: [] },
  { title: 'Vector Databases', description: 'Embeddings, similarity search, and vector database concepts using tools like Pinecone, pgvector, and Chroma for AI applications.', skill_name: 'Vector Databases', level: 'advanced', level_num: 3, duration_hrs: 3.0, domain: 'Technical', provider: 'Pinecone Docs', url: 'https://docs.pinecone.io', prerequisite_titles: ['Machine Learning Fundamentals'] },
  { title: 'Fine-tuning LLMs', description: 'Fine-tuning pre-trained language models using LoRA, RLHF, and instruction tuning techniques with Hugging Face transformers.', skill_name: 'Fine-tuning', level: 'advanced', level_num: 3, duration_hrs: 5.0, domain: 'Technical', provider: 'Hugging Face', url: 'https://huggingface.co/learn', prerequisite_titles: ['Machine Learning Fundamentals'] },

  // Operational — Warehouse
  { title: 'Workplace Safety Fundamentals', description: 'Core workplace safety principles, hazard identification, PPE usage, and emergency response procedures for industrial environments.', skill_name: 'Workplace Safety', level: 'beginner', level_num: 1, duration_hrs: 2.0, domain: 'Operational', provider: 'OSHA', url: 'https://osha.gov', prerequisite_titles: [] },
  { title: 'OSHA Standards Overview', description: 'Comprehensive review of OSHA standards, compliance requirements, recordkeeping obligations, and inspection procedures.', skill_name: 'OSHA', level: 'intermediate', level_num: 2, duration_hrs: 4.0, domain: 'Operational', provider: 'OSHA', url: 'https://osha.gov/training', prerequisite_titles: ['Workplace Safety Fundamentals'] },
  { title: 'Forklift Operation Basics', description: 'Safe forklift operation including pre-operation inspection, load handling, stability principles, and pedestrian safety.', skill_name: 'Forklift Operation', level: 'beginner', level_num: 1, duration_hrs: 3.0, domain: 'Operational', provider: 'Internal', url: '', prerequisite_titles: [] },
  { title: 'Forklift Certification Prep', description: 'Certification preparation covering advanced forklift maneuvers, narrow aisle operation, racking systems, and evaluation criteria.', skill_name: 'Forklift Operation', level: 'intermediate', level_num: 2, duration_hrs: 2.0, domain: 'Operational', provider: 'Internal', url: '', prerequisite_titles: ['Forklift Operation Basics'] },
  { title: 'Inventory Management Systems', description: 'Principles of inventory control including cycle counting, FIFO/LIFO methods, shrinkage reduction, and inventory software basics.', skill_name: 'Inventory Management', level: 'intermediate', level_num: 2, duration_hrs: 4.0, domain: 'Operational', provider: 'Coursera', url: 'https://coursera.org', prerequisite_titles: [] },
  { title: 'Supply Chain Basics', description: 'Introduction to supply chain concepts including procurement, logistics, distribution networks, and supplier relationship management.', skill_name: 'Supply Chain', level: 'beginner', level_num: 1, duration_hrs: 3.0, domain: 'Operational', provider: 'Coursera', url: 'https://coursera.org', prerequisite_titles: [] },
  { title: 'Quality Control Processes', description: 'Quality management principles, inspection techniques, statistical process control, and root cause analysis methodologies.', skill_name: 'Quality Control', level: 'intermediate', level_num: 2, duration_hrs: 3.0, domain: 'Operational', provider: 'ASQ', url: 'https://asq.org', prerequisite_titles: [] },
  { title: 'Warehouse Management Systems (WMS)', description: 'Using WMS software for receiving, putaway, picking, packing, and shipping operations in modern distribution centers.', skill_name: 'WMS', level: 'intermediate', level_num: 2, duration_hrs: 5.0, domain: 'Operational', provider: 'Internal', url: '', prerequisite_titles: ['Inventory Management Systems'] },

  // Operational — Customer/Service
  { title: 'Customer Service Fundamentals', description: 'Core customer service skills including active listening, empathy, handling complaints, and building positive customer relationships.', skill_name: 'Customer Service', level: 'beginner', level_num: 1, duration_hrs: 2.0, domain: 'Operational', provider: 'LinkedIn Learning', url: 'https://linkedin.com/learning', prerequisite_titles: [] },
  { title: 'Conflict Resolution in the Workplace', description: 'Techniques for de-escalating conflicts, facilitating difficult conversations, and reaching mutually acceptable resolutions.', skill_name: 'Conflict Resolution', level: 'intermediate', level_num: 2, duration_hrs: 2.0, domain: 'Operational', provider: 'LinkedIn Learning', url: 'https://linkedin.com/learning', prerequisite_titles: ['Customer Service Fundamentals'] },
  { title: 'Service Desk Operations', description: 'IT service desk workflows, ticketing systems, SLA management, escalation procedures, and customer communication best practices.', skill_name: 'Service Desk', level: 'intermediate', level_num: 2, duration_hrs: 3.0, domain: 'Operational', provider: 'Internal', url: '', prerequisite_titles: [] },

  // Soft Skills
  { title: 'Business Communication', description: 'Professional written and verbal communication skills including email etiquette, meeting facilitation, and business writing.', skill_name: 'Communication', level: 'beginner', level_num: 1, duration_hrs: 2.0, domain: 'Soft Skills', provider: 'Coursera', url: 'https://coursera.org', prerequisite_titles: [] },
  { title: 'Presentation Skills', description: 'Designing and delivering compelling presentations including slide design, storytelling, handling Q&A, and managing nerves.', skill_name: 'Presentation', level: 'intermediate', level_num: 2, duration_hrs: 2.0, domain: 'Soft Skills', provider: 'Coursera', url: 'https://coursera.org', prerequisite_titles: ['Business Communication'] },
  { title: 'Agile and Scrum Foundations', description: 'Agile principles, Scrum framework, sprint planning, daily standups, retrospectives, and working effectively in Agile teams.', skill_name: 'Agile', level: 'beginner', level_num: 1, duration_hrs: 3.0, domain: 'Soft Skills', provider: 'Scrum.org', url: 'https://scrum.org', prerequisite_titles: [] },
  { title: 'Project Management Fundamentals', description: 'Project lifecycle, scope management, scheduling, risk assessment, stakeholder communication, and project closure techniques.', skill_name: 'Project Management', level: 'intermediate', level_num: 2, duration_hrs: 5.0, domain: 'Soft Skills', provider: 'PMI', url: 'https://pmi.org', prerequisite_titles: ['Agile and Scrum Foundations'] },
  { title: 'PMP Exam Prep', description: 'Comprehensive PMP certification preparation covering all PMBOK knowledge areas, process groups, and exam-style practice questions.', skill_name: 'Project Management', level: 'advanced', level_num: 3, duration_hrs: 10.0, domain: 'Soft Skills', provider: 'PMI', url: 'https://pmi.org', prerequisite_titles: ['Project Management Fundamentals'] },
  { title: 'Data-Driven Decision Making', description: 'Using data to inform business decisions including KPI definition, dashboard reading, A/B testing, and communicating insights.', skill_name: 'Data Analysis', level: 'intermediate', level_num: 2, duration_hrs: 3.0, domain: 'Soft Skills', provider: 'Coursera', url: 'https://coursera.org', prerequisite_titles: [] },
  { title: 'Team Leadership Essentials', description: 'Leadership fundamentals including motivating teams, delegation, giving feedback, performance management, and building trust.', skill_name: 'Leadership', level: 'intermediate', level_num: 2, duration_hrs: 3.0, domain: 'Soft Skills', provider: 'LinkedIn Learning', url: 'https://linkedin.com/learning', prerequisite_titles: [] },
  { title: 'Strategic Thinking', description: 'Frameworks for strategic analysis including SWOT, Porter\'s Five Forces, scenario planning, and translating strategy to execution.', skill_name: 'Strategy', level: 'advanced', level_num: 3, duration_hrs: 4.0, domain: 'Soft Skills', provider: 'Harvard ManageMentor', url: 'https://harvardbusiness.org', prerequisite_titles: ['Team Leadership Essentials'] },
  { title: 'Change Management', description: 'Leading organizational change using ADKAR and Kotter frameworks, managing resistance, and sustaining change over time.', skill_name: 'Change Management', level: 'advanced', level_num: 3, duration_hrs: 4.0, domain: 'Soft Skills', provider: 'Prosci', url: 'https://prosci.com', prerequisite_titles: [] },

  // Cross-domain
  { title: 'Excel for Business', description: 'Business spreadsheet skills including formulas, pivot tables, VLOOKUP, data validation, and creating professional reports.', skill_name: 'Excel', level: 'beginner', level_num: 1, duration_hrs: 3.0, domain: 'Soft Skills', provider: 'Microsoft Learn', url: 'https://learn.microsoft.com', prerequisite_titles: [] },
  { title: 'Power BI Fundamentals', description: 'Data visualization with Power BI including connecting data sources, building dashboards, DAX basics, and sharing reports.', skill_name: 'Power BI', level: 'intermediate', level_num: 2, duration_hrs: 4.0, domain: 'Soft Skills', provider: 'Microsoft Learn', url: 'https://learn.microsoft.com', prerequisite_titles: ['Excel for Business'] },
  { title: 'Cybersecurity Awareness', description: 'Essential cybersecurity concepts including phishing, password hygiene, social engineering, data handling, and incident reporting.', skill_name: 'Cybersecurity', level: 'beginner', level_num: 1, duration_hrs: 2.0, domain: 'Technical', provider: 'SANS', url: 'https://sans.org', prerequisite_titles: [] },
]

async function seed() {
  console.log('Starting seed...')

  // Step A — seed skills
  const skillNameToId = {}
  const uniqueSkillNames = [...new Set(courses.map(c => c.skill_name))]

  console.log(`Seeding ${uniqueSkillNames.length} skills...`)
  for (const skillName of uniqueSkillNames) {
    const vec = await embed(skillName)
    const domain = courses.find(c => c.skill_name === skillName)?.domain || 'Unknown'

    const { data, error } = await supabase
      .from('skills')
      .upsert({ name: skillName, category: 'Unknown', domain, embedding: vec }, { onConflict: 'name' })
      .select('id')
      .single()

    if (error) {
      console.error(`Failed to seed skill: ${skillName}`, error.message)
      continue
    }

    skillNameToId[skillName] = data.id
    console.log(`  ✓ skill: ${skillName}`)
  }

  // Step B — seed courses
  const courseTitleToId = {}

  console.log(`\nSeeding ${courses.length} courses...`)
  for (const course of courses) {
    const vec = await embed(course.title + ' ' + course.description)
    const skill_id = skillNameToId[course.skill_name]

    const { data, error } = await supabase
      .from('courses')
      .upsert({
        title: course.title,
        description: course.description,
        skill_id,
        level: course.level,
        level_num: course.level_num,
        duration_hrs: course.duration_hrs,
        domain: course.domain,
        provider: course.provider,
        url: course.url,
        embedding: vec,
        prerequisites: []
      }, { onConflict: 'title' })
      .select('id')
      .single()

    if (error) {
      console.error(`Failed to seed course: ${course.title}`, error.message)
      continue
    }

    courseTitleToId[course.title] = data.id
    console.log(`  ✓ course: ${course.title}`)
  }

  // Step C — set prerequisites
  console.log('\nSetting prerequisites...')
  for (const course of courses) {
    if (course.prerequisite_titles.length === 0) continue

    const prereqIds = course.prerequisite_titles
      .map(t => courseTitleToId[t])
      .filter(Boolean)

    const courseId = courseTitleToId[course.title]
    if (!courseId) continue

    const { error } = await supabase
      .from('courses')
      .update({ prerequisites: prereqIds })
      .eq('id', courseId)

    if (error) {
      console.error(`Failed to set prereqs for: ${course.title}`, error.message)
    } else {
      console.log(`  ✓ prereqs set: ${course.title}`)
    }
  }

  // Step D — seed skill_course_map
  console.log('\nSeeding skill_course_map...')
  for (const course of courses) {
    const courseId = courseTitleToId[course.title]
    const skillId = skillNameToId[course.skill_name]
    if (!courseId || !skillId) continue

    const { error } = await supabase
      .from('skill_course_map')
      .upsert({ course_id: courseId, skill_id: skillId, impact: 1.0 }, { onConflict: 'course_id,skill_id' })

    if (error) {
      console.error(`Failed to map: ${course.title}`, error.message)
    }
  }

  console.log('\n✓ Seed complete!')
  console.log(`  Skills: ${uniqueSkillNames.length}`)
  console.log(`  Courses: ${courses.length}`)
}

seed().catch(err => {
  console.error('Seed failed:', err)
  process.exit(1)
})