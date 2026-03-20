import React, { useMemo } from 'react';

function parseReasoning(text) {
  if (!text) return null;

  // Split into sections by ## N. pattern
  const sections = text.split(/##\s*\d+\.\s*/);
  // sections[0] is empty string before first ##
  // sections[1] = "Candidate Assessment ..."
  // sections[2] = "Gap Identification ..."
  // sections[3] = "Course Selection Rationale ..."
  // sections[4] = "Pathway Ordering Logic ..."
  // sections[5] = "Estimated Time to Competency ..."

  // ── SECTION 1: Candidate Assessment ──
  const rawAssessment = sections[1] || "";
  const candidateAssessment = rawAssessment
    .replace(/^Candidate Assessment\s*/i, "")
    .trim();

  // ── SECTION 2: Gap Identification ──
  const rawGaps = sections[2] || "";
  const gapLines = rawGaps
    .replace(/^Gap Identification\s*/i, "")
    .split(/\*\s+\*\*/)          // split on "* **"
    .filter(Boolean);

  const gaps = gapLines.map(line => {
    // line looks like: "Python**: Severe gap ... matters because ..."
    const nameMatch = line.match(/^([^*]+)\*\*:/);
    const skill = nameMatch ? nameMatch[1].trim() : "";

    const severityMatch = line.match(/(Severe|Moderate|Minor|Critical)/i);
    const severity = severityMatch ? severityMatch[1] : "Moderate";

    const reasonMatch = line.match(/matters because\s+(.+)/i);
    const reason = reasonMatch
      ? reasonMatch[1].replace(/\.$/, "").trim()
      : line.replace(/^[^:]+:\s*/, "").trim();

    return { skill, severity, reason };
  }).filter(g => g.skill.length > 0);

  // ── SECTION 3: Course Selection Rationale ──
  const rawCourses = sections[3] || "";
  const courseLines = rawCourses
    .replace(/^Course Selection Rationale\s*/i, "")
    .split(/\*\s+\*\*/)
    .filter(Boolean);

  const courseRationale = courseLines.map(line => {
    const nameMatch = line.match(/^([^*]+)\*\*:/);
    const course = nameMatch ? nameMatch[1].trim() : "";
    const reason = line
      .replace(/^[^:]+:\s*/, "")
      .trim();
    return { course, reason };
  }).filter(c => c.course.length > 0);

  // ── SECTION 4: Pathway Ordering Logic ──
  const rawOrdering = sections[4] || "";
  const orderingLogic = rawOrdering
    .replace(/^Pathway Ordering Logic\s*/i, "")
    .trim();

  // ── SECTION 5: Estimated Time ──
  const rawTime = sections[5] || "";
  const timeEstimate = rawTime
    .replace(/^Estimated Time to Competency\s*/i, "")
    .trim();

  // Extract key number (e.g. "4-6 months")
  const monthsMatch = timeEstimate.match(/(\d+[-–]\d+)\s*months/i);
  const timeHighlight = monthsMatch ? `${monthsMatch[1]} months` : "See below";

  return {
    candidateAssessment,
    gaps,
    courseRationale,
    orderingLogic,
    timeEstimate,
    timeHighlight
  };
}

export default function ReasoningTrace({ trace }) {
  // Extract text from object or fallback
  const rawText = typeof trace === 'object' ? trace?.raw : trace;
  const parsed = useMemo(() => parseReasoning(rawText), [rawText]);

  if (!parsed || !rawText) {
    return (
      <div className="space-y-4 w-full">
        <style>{`
          @keyframes pulseSkeleton {
            from { opacity: 0.4; }
            to { opacity: 0.7; }
          }
          .skeleton {
            background: rgba(255,255,255,0.04);
            border-radius: 10px;
            animation: pulseSkeleton 1.5s ease-in-out infinite alternate;
          }
        `}</style>
        <div className="skeleton" style={{ height: '80px' }}></div>
        <div className="skeleton" style={{ height: '160px' }}></div>
        <div className="skeleton" style={{ height: '200px' }}></div>
        <div className="skeleton" style={{ height: '60px' }}></div>
      </div>
    );
  }

  console.log(parsed);

  return (
    <div style={{
      background: 'rgba(17,19,24,1)',
      borderRadius: '16px',
      border: '1px solid rgba(255,255,255,0.07)',
      padding: '32px'
    }} className="will-change-transform">
      <h2 style={{
        fontSize: '18px', fontWeight: 600, color: '#f0f2f5',
        marginBottom: '28px', borderLeft: '3px solid #4f8ef7', paddingLeft: '14px'
      }}>
        Why this pathway?
      </h2>

      {/* BLOCK 1 - Candidate Assessment */}
      <div style={{
        background: 'rgba(79,142,247,0.06)',
        border: '1px solid rgba(79,142,247,0.15)',
        borderRadius: '12px', padding: '16px 20px',
        marginBottom: '32px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'rgba(79,142,247,0.2)', color: '#60a5fa', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 'bold' }}>👤</div>
          <span style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.12em', color: '#60a5fa', fontWeight: 600 }}>
            Candidate Assessment
          </span>
        </div>
        <p style={{ fontSize: '14px', color: '#9ca3af', lineHeight: 1.7 }}>
          {parsed.candidateAssessment}
        </p>
      </div>

      {/* BLOCK 2 - Gap Identification */}
      <div style={{ marginBottom: '32px' }}>
        <p style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.12em', color: '#6b7280', marginBottom: '14px', fontWeight: 600 }}>
          SKILL GAPS IDENTIFIED
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {parsed.gaps.map((gap, i) => {
            const colors = { Severe: '#ef4444', Moderate: '#f59e0b', Minor: '#22c55e', Critical: '#ef4444' };
            const color = colors[gap.severity] || colors.Moderate;
            
            return (
              <div key={i} style={{
                background: 'rgba(17,19,24,0.8)',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '10px', padding: '12px 16px',
                position: 'relative', overflow: 'hidden'
              }}>
                <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '3px', background: color }} />
                <div style={{ paddingLeft: '4px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 500, color: '#f0f2f5' }}>{gap.skill}</span>
                  <span style={{
                    fontSize: '10px', padding: '2px 8px', borderRadius: '999px',
                    marginLeft: '8px', verticalAlign: 'middle',
                    background: `${color}1A`, color: color, border: `1px solid ${color}33`, fontWeight: 500
                  }}>
                    {gap.severity}
                  </span>
                  <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '6px', lineHeight: 1.5 }}>
                    {gap.reason}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* BLOCK 3 - Course Selection Rationale */}
      <div style={{ marginBottom: '32px' }}>
        <p style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.12em', color: '#6b7280', marginBottom: '14px', fontWeight: 600 }}>
          COURSE SELECTIONS
        </p>
        <div style={{ position: 'relative', marginLeft: '6px', marginTop: '8px' }}>
          <div style={{ position: 'absolute', left: '4px', top: '8px', bottom: '0', width: '1px', background: 'rgba(255,255,255,0.06)' }} />
          
          {parsed.courseRationale.map((course, i) => (
            <div key={i} style={{ paddingLeft: '22px', position: 'relative', marginBottom: '18px' }}>
              <div style={{
                position: 'absolute', left: '0px', top: '5px',
                width: '9px', height: '9px', borderRadius: '50%',
                background: '#4f8ef7', border: '2px solid #0a0c10', boxSizing: 'border-box'
              }} />
              <p style={{ fontSize: '13px', fontWeight: 500, color: '#f0f2f5' }}>{course.course}</p>
              <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px', lineHeight: 1.5 }}>{course.reason}</p>
            </div>
          ))}
        </div>
      </div>

      {/* BLOCK 4 - Pathway Ordering Logic */}
      <div style={{
        background: 'rgba(167,139,250,0.06)',
        border: '1px solid rgba(167,139,250,0.15)',
        borderRadius: '12px', padding: '16px 20px',
        marginBottom: '32px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'rgba(167,139,250,0.2)', color: '#c4b5fd', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 'bold' }}>PL</div>
          <span style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.12em', color: '#c4b5fd', fontWeight: 600 }}>
            PATHWAY LOGIC
          </span>
        </div>
        <p style={{ fontSize: '14px', color: '#9ca3af', lineHeight: 1.7 }}>
          {parsed.orderingLogic}
        </p>
      </div>

      {/* BLOCK 5 - Time Estimate */}
      <div style={{
        background: 'rgba(16,185,129,0.06)',
        border: '1px solid rgba(16,185,129,0.15)',
        borderRadius: '12px', padding: '20px 24px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: '16px'
      }}>
        <div style={{ flex: '1' }}>
          <p style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.15em', color: '#34d399', fontWeight: 600 }}>
            ESTIMATED TIME TO COMPETENCY
          </p>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '6px', maxWidth: '300px', lineHeight: 1.6 }}>
            {parsed.timeEstimate}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '32px', fontFamily: "'DM Mono', monospace", color: '#f0f2f5', lineHeight: 1 }}>
            {parsed.timeHighlight}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
            with 10-15 hrs/week
          </div>
        </div>
      </div>

    </div>
  );
}
