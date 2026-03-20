// client/src/utils/exportRoadmapPDF.js

function parseReasoning(text) {
  if (!text) return null;
  const sections = text.split(/##\s*\d+\.\s*/);
  
  const rawAssessment = sections[1] || "";
  const candidateAssessment = rawAssessment.replace(/^Candidate Assessment\s*/i, "").trim();

  const rawGaps = sections[2] || "";
  const gapLines = rawGaps.replace(/^Gap Identification\s*/i, "").split(/\*\s+\*\*/).filter(Boolean);
  const gaps = gapLines.map(line => {
    const nameMatch = line.match(/^([^*]+)\*\*:/);
    const skill = nameMatch ? nameMatch[1].trim() : "";
    const severityMatch = line.match(/(Severe|Moderate|Minor|Critical)/i);
    const severity = severityMatch ? severityMatch[1] : "Moderate";
    const reasonMatch = line.match(/matters because\s+(.+)/i);
    const reason = reasonMatch ? reasonMatch[1].replace(/\.$/, "").trim() : line.replace(/^[^:]+:\s*/, "").trim();
    return { skill, severity, reason };
  }).filter(g => g.skill.length > 0);

  const rawCourses = sections[3] || "";
  const courseLines = rawCourses.replace(/^Course Selection Rationale\s*/i, "").split(/\*\s+\*\*/).filter(Boolean);
  const courseRationale = courseLines.map(line => {
    const nameMatch = line.match(/^([^*]+)\*\*:/);
    const course = nameMatch ? nameMatch[1].trim() : "";
    const reason = line.replace(/^[^:]+:\s*/, "").trim();
    return { course, reason };
  }).filter(c => c.course.length > 0);

  const rawOrdering = sections[4] || "";
  const orderingLogic = rawOrdering.replace(/^Pathway Ordering Logic\s*/i, "").trim();

  const rawTime = sections[5] || "";
  const timeEstimate = rawTime.replace(/^Estimated Time to Competency\s*/i, "").trim();

  const monthsMatch = timeEstimate.match(/(\d+[-–]\d+)\s*months/i);
  const timeHighlight = monthsMatch ? `${monthsMatch[1]} months` : "See below";

  return { candidateAssessment, gaps, courseRationale, orderingLogic, timeEstimate, timeHighlight };
}

export async function exportRoadmapPDF(rawData) {
  const { default: jsPDF } = await import("jspdf");
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

  const data = {
    userName: rawData.userName,
    targetRole: rawData.targetRole,
    totalGaps: rawData.totalGaps,
    criticalGaps: rawData.criticalGaps,
    met: rawData.met,
    trainingHours: rawData.trainingHours,
    courses: rawData.courses,
    reasoning: parseReasoning(rawData.reasoningRaw) || {}
  };

  const W = 210;
  const H = 297;
  const ML = 16;
  const MR = 16;
  const CW = W - ML - MR;

  const C = {
    bg:         [252, 252, 253],
    white:      [255, 255, 255],
    heading:    [15,  17,  23],
    body:       [55,  65,  81],
    muted:      [107, 114, 128],
    border:     [229, 231, 235],
    blue:       [79,  142, 247],
    blueBg:     [239, 246, 255],
    purple:     [139, 92,  246],
    purpleBg:   [245, 243, 255],
    amber:      [217, 119, 6],
    amberBg:    [255, 251, 235],
    green:      [16,  185, 129],
    greenBg:    [236, 253, 245],
    red:        [239, 68,  68],
    redBg:      [254, 242, 242],
    accent:     [79,  142, 247],
  };

  let y = 0;

  function checkPageBreak(needed = 20) {
    if (y + needed > H - 16) {
      doc.addPage();
      y = 16;
      drawPageBg();
    }
  }

  function drawPageBg() {
    doc.setFillColor(...C.bg);
    doc.rect(0, 0, W, H, "F");
  }

  function drawLine(x1, y1, x2, y2, color = C.border, width = 0.3) {
    doc.setDrawColor(...color);
    doc.setLineWidth(width);
    doc.line(x1, y1, x2, y2);
  }

  function drawRect(x, yy, w, h, fillColor, radius = 3) {
    doc.setFillColor(...fillColor);
    doc.roundedRect(x, yy, w, h, radius, radius, "F");
  }

  function drawText(text, x, yy, opts = {}) {
    const {
      size = 10, color = C.body, weight = "normal",
      align = "left", maxWidth = CW
    } = opts;
    doc.setFontSize(size);
    doc.setTextColor(...color);
    doc.setFont("helvetica", weight);
    doc.text(String(text), x, yy, { align, maxWidth });
  }

  drawPageBg();
  y = 0;

  doc.setFillColor(...C.heading);
  doc.rect(0, 0, W, 38, "F");

  doc.setFillColor(...C.blue);
  doc.rect(0, 0, W, 2, "F");

  drawText(data.userName, ML, 16, { size: 18, color: [255,255,255], weight: "bold" });

  const nameWidth = doc.getTextWidth(data.userName) + 4;
  drawText("->", ML + nameWidth, 16, { size: 18, color: C.blue, weight: "normal" });
  drawText(data.targetRole, ML + nameWidth + 8, 16, { size: 18, color: C.blue, weight: "bold" });

  drawText("Adaptive Learning Roadmap", ML, 26, { size: 9, color: [156,163,175], weight: "normal" });

  const dateStr = new Date().toLocaleDateString("en-US", { year:"numeric", month:"long", day:"numeric" });
  drawText(dateStr, W - MR, 26, { size: 9, color: [156,163,175], align: "right" });

  y = 46;

  checkPageBreak(28);

  const stats = [
    { label: "TOTAL GAPS",    value: data.totalGaps,    color: C.red,    bg: C.redBg },
    { label: "CRITICAL",      value: data.criticalGaps, color: C.amber,  bg: C.amberBg },
    { label: "SKILLS MET",    value: data.met,           color: C.green,  bg: C.greenBg },
    { label: "TRAINING HRS",  value: data.trainingHours + "h", color: C.blue, bg: C.blueBg },
  ];

  const cardW = (CW - 12) / 4;
  stats.forEach((stat, i) => {
    const x = ML + i * (cardW + 4);
    
    drawRect(x, y, cardW, 22, stat.bg, 4);
    
    doc.setFillColor(...stat.color);
    doc.roundedRect(x, y, 2.5, 22, 1, 1, "F");
    
    drawText(stat.label, x + 6, y + 8, { size: 6.5, color: stat.color, weight: "bold" });
    drawText(String(stat.value), x + 6, y + 17, { size: 16, color: C.heading, weight: "bold" });
  });

  y += 30;

  checkPageBreak(16);

  doc.setFillColor(...C.blue);
  doc.rect(ML, y, 3, 7, "F");
  drawText("COURSE ROADMAP", ML + 6, y + 5.5, { size: 10, color: C.heading, weight: "bold" });
  y += 14;

  const phases = {};
  (data.courses || []).forEach(course => {
    const p = course.phase_num || course.phase || 1;
    if (!phases[p]) phases[p] = [];
    phases[p].push(course);
  });

  const phaseColors = {
    1: { label: "FOUNDATION",    color: C.blue,   bg: C.blueBg },
    2: { label: "CORE",          color: C.purple, bg: C.purpleBg },
    3: { label: "ADVANCED",      color: C.amber,  bg: C.amberBg },
    4: { label: "STRETCH GOALS", color: C.green,  bg: C.greenBg },
  };

  Object.entries(phases).forEach(([phaseNum, courses]) => {
    checkPageBreak(20);
    const pc = phaseColors[phaseNum] || phaseColors[1];
    
    drawRect(ML, y, CW, 9, pc.bg, 3);
    doc.setFillColor(...pc.color);
    doc.roundedRect(ML, y, CW, 9, 3, 3, "F");
    doc.setFillColor(...pc.bg);
    doc.roundedRect(ML + 2, y + 0.5, CW - 4, 8, 2, 2, "F");
    
    drawText(`PHASE ${phaseNum}  ·  ${pc.label}`, ML + 6, y + 6, { size: 7.5, color: pc.color, weight: "bold" });
    y += 13;

    const colW = (CW - 6) / 2;
    courses.forEach((course, idx) => {
      if (idx % 2 === 0) {
        checkPageBreak(18);
      }
      const col = idx % 2;
      const cx = ML + col * (colW + 6);

      if (col === 0 && idx > 0) y += 18;

      drawRect(cx, y, colW, 15, C.white, 3);
      doc.setDrawColor(...C.border);
      doc.setLineWidth(0.3);
      doc.roundedRect(cx, y, colW, 15, 3, 3, "S");
      
      doc.setFillColor(...pc.color);
      doc.circle(cx + 5, y + 5, 1.5, "F");
      
      const courseName = course.label || course.name || course.title || "";
      drawText(courseName, cx + 10, y + 6, { size: 8, color: C.heading, weight: "bold", maxWidth: colW - 20 });
      
      const hrs = course.hours || course.duration_hrs || course.duration || "";
      drawText(hrs ? `${hrs}h` : "", cx + colW - 4, y + 6, { size: 7.5, color: C.muted, align: "right" });
      
      const type = course.type || course.category || course.level || "";
      if (type) {
        drawText(String(type).toUpperCase(), cx + 10, y + 12, { size: 6, color: pc.color, weight: "bold" });
      }

      if (col === 1 || idx === courses.length - 1) y += 18;
    });
    
    y += 6;
  });

  checkPageBreak(30);

  doc.setFillColor(...C.purple);
  doc.rect(ML, y, 3, 7, "F");
  drawText("WHY THIS PATHWAY", ML + 6, y + 5.5, { size: 10, color: C.heading, weight: "bold" });
  y += 14;

  if (data.reasoning?.candidateAssessment) {
    checkPageBreak(20);
    drawRect(ML, y, CW, 8, C.blueBg, 3);
    drawText("CANDIDATE ASSESSMENT", ML + 6, y + 5.5, { size: 7, color: C.blue, weight: "bold" });
    y += 11;
    
    const assessLines = doc.splitTextToSize(data.reasoning.candidateAssessment, CW - 4);
    assessLines.forEach(line => {
      checkPageBreak(6);
      drawText(line, ML + 2, y, { size: 8.5, color: C.body });
      y += 5.5;
    });
    y += 6;
  }

  if (data.reasoning?.gaps?.length) {
    checkPageBreak(16);
    drawText("SKILL GAPS IDENTIFIED", ML, y, { size: 7, color: C.muted, weight: "bold" });
    y += 7;

    data.reasoning.gaps.forEach(gap => {
      checkPageBreak(25);
      const severityColor = gap.severity?.toLowerCase() === "severe" ? C.red : gap.severity?.toLowerCase() === "moderate" ? C.amber : C.green;
      const severityBg = gap.severity?.toLowerCase() === "severe" ? C.redBg : gap.severity?.toLowerCase() === "moderate" ? C.amberBg : C.greenBg;

      drawRect(ML, y, CW, 14, severityBg, 3);
      doc.setFillColor(...severityColor);
      doc.roundedRect(ML, y, 2.5, 14, 1, 1, "F");
      
      drawText(gap.skill, ML + 6, y + 5, { size: 8.5, color: C.heading, weight: "bold" });
      
      const sw = doc.getTextWidth(gap.skill) + 10;
      drawRect(ML + sw + 2, y + 2, 18, 5, severityColor, 2);
      drawText(gap.severity || "", ML + sw + 3, y + 5.6, { size: 5.5, color: C.white, weight: "bold" });
      
      const reasonLines = doc.splitTextToSize(gap.reason || "", CW - 10);
      if (reasonLines[0]) drawText(reasonLines[0], ML + 6, y + 9.5, { size: 7.5, color: C.muted });
      if (reasonLines[1]) drawText(reasonLines[1], ML + 6, y + 12.5, { size: 7.5, color: C.muted });
      
      y += 18;
    });
    y += 4;
  }

  if (data.reasoning?.orderingLogic) {
    checkPageBreak(20);
    drawRect(ML, y, CW, 8, C.purpleBg, 3);
    drawText("PATHWAY LOGIC", ML + 6, y + 5.5, { size: 7, color: C.purple, weight: "bold" });
    y += 11;
    
    const logicLines = doc.splitTextToSize(data.reasoning.orderingLogic, CW - 4);
    logicLines.forEach(line => {
      checkPageBreak(6);
      drawText(line, ML + 2, y, { size: 8.5, color: C.body });
      y += 5.5;
    });
    y += 6;
  }

  checkPageBreak(36);

  drawRect(ML, y, CW, 24, C.heading, 4);
  doc.setFillColor(...C.blue);
  doc.roundedRect(ML, y, CW, 24, 4, 4, "F");
  doc.setFillColor(...C.heading);
  doc.roundedRect(ML + 1, y + 1, CW - 2, 22, 3, 3, "F");

  drawText("ESTIMATED TRAINING TIME", ML + 8, y + 9, { size: 7.5, color: [156,163,175], weight: "bold" });
  drawText(`${data.trainingHours}h`, ML + 8, y + 19, { size: 20, color: [255,255,255], weight: "bold" });
  drawText("guided learning path ->", W - MR, y + 19, { size: 9, color: C.blue, weight: "bold", align: "right" });

  y += 32;

  const totalPages = doc.getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    drawText(`${p} / ${totalPages}`, W / 2, H - 6, { size: 7, color: C.muted, align: "center" });
    drawLine(ML, H - 10, W - MR, H - 10, C.border, 0.2);
  }

  const slug = (data.targetRole || "roadmap").toLowerCase().replace(/\s+/g, "-");
  doc.save(`${slug}-roadmap.pdf`);
}
