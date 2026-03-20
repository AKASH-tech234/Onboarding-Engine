import os
import re

def fix(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # import X from 'Y' -> const X = require('Y')
    content = re.sub(r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"];?", r"const \1 = require('\2');", content)
    
    # import { X, Y } from 'Z' -> const { X, Y } = require('Z')
    content = re.sub(r"import\s*\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"];?", r"const {\1} = require('\2');", content)
    
    exports = []
    
    def repl_func(m):
        exports.append(m.group(1))
        return f"async function {m.group(1)}"
        
    content = re.sub(r"export\s+async\s+function\s+(\w+)", repl_func, content)
    
    def repl_const(m):
        exports.append(m.group(1))
        return f"const {m.group(1)}"
    
    content = re.sub(r"export\s+const\s+(\w+)", repl_const, content)

    if 'export default router' in content:
        content = content.replace('export default router;', 'module.exports = router;')
        
    if exports:
        # Check if module.exports already exists
        if 'module.exports' not in content:
            content += f"\nmodule.exports = {{ {', '.join(exports)} }};\n"
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

base = "d:/edge download/IISC/Onboarding-Engine/server/src"
files = [
    "index.js", "routes/skills.js", "routes/sessions.js",
    "db/supabaseClient.js", "utils/retry.js", "ai/gemini.js",
    "parsers/extractText.js", "ai/extractResumeSkills.js",
    "ai/extractJDRequirements.js", "ai/normalizeSkills.js",
    "ai/generateReasoningTrace.js"
]

for f in files:
    try:
        fix(os.path.join(base, f))
        print(f"Fixed {f}")
    except Exception as e:
        print(f"Error on {f}: {e}")
