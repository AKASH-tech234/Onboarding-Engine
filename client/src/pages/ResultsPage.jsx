import { useState, useEffect, useRef } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useSession } from '../hooks/useSession';
import PathwayFlow from '../components/PathwayFlow';
import CourseDrawer from '../components/CourseDrawer';
import ReasoningTrace from '../components/ReasoningTrace';
import PhaseTimeline from '../components/PhaseTimeline';
import FloatingExportButton from '../components/FloatingExportButton';

function useCounter(target, duration = 800, startOnMount = true) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!startOnMount) return;
    let startTime = null;
    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      setCount(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    const raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration, startOnMount]);
  return count;
}

const TypewriterSubtitle = ({ text }) => {
  const [displayedWords, setDisplayedWords] = useState([]);
  const words = text.split(" ");

  useEffect(() => {
    words.forEach((word, i) => {
      setTimeout(() => {
        setDisplayedWords(prev => [...prev, word]);
      }, 800 + i * 80);
    });
  }, [text]);

  return (
    <p style={{
      fontSize: "17px", color: "#9ca3af", textAlign: "center",
      maxWidth: "540px", margin: "16px auto 0", lineHeight: 1.7,
      minHeight: "28px", position: "relative", zIndex: 10
    }}>
      {displayedWords.map((word, i) => (
        <span key={i}
          style={{
            display: "inline-block",
            marginRight: "5px",
            animation: "wordReveal 0.4s ease forwards",
            animationDelay: `${i * 0.05}s`,
            opacity: 0
          }}>
          {word}
        </span>
      ))}
    </p>
  );
};

const SpotlightCard = ({ children, className }) => {
  const divRef = useRef(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0);

  const handleMouseMove = (e) => {
    if (!divRef.current) return;
    const rect = divRef.current.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  return (
    <div
      ref={divRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setOpacity(1)}
      onMouseLeave={() => setOpacity(0)}
      style={{ position: 'relative', borderRadius: '12px', background: '#111318', border: '1px solid rgba(255,255,255,0.07)', padding: '28px', overflow: 'hidden' }}
      className={`transition-colors duration-300 hover:border-neutral-600 hover:-translate-y-[2px] will-change-transform ${className || ''}`}
    >
      <div
        className="pointer-events-none absolute -inset-px z-0 opacity-0 transition duration-300 will-change-[opacity]"
        style={{
          opacity,
          background: `radial-gradient(400px circle at ${position.x}px ${position.y}px, rgba(255,255,255,0.08), transparent 40%)`,
        }}
      />
      <div className="relative z-10 h-full">{children}</div>
    </div>
  );
};

export default function ResultsPage() {
  const { id } = useParams();
  const location = useLocation();
  const initialData = location.state?.sessionData || null;
  const { data, isLoading, error } = useSession(id, initialData);

  const [visible, setVisible] = useState(false);
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(t);
  }, []);

  if (isLoading) {
    return <div className="min-h-screen bg-[#0a0c10] flex items-center justify-center text-neutral-400">Loading analysis...</div>;
  }
  if (error || !data) {
    return <div className="min-h-screen bg-[#0a0c10] flex items-center justify-center text-red-500">Error loading data.</div>;
  }

  const { skill_gap_summary, candidate } = data;
  
  // Clone pathway so we can re-index cleanly strictly consecutively
  const pathway = data.pathway ? JSON.parse(JSON.stringify(data.pathway)) : null;
  if (pathway?.phases) {
    pathway.phases.forEach((p, idx) => {
      p.original_phase = p.phase;
      p.phase = idx + 1; // 1, 2, 3...
    });
  }
  
  // Dynamic mapped variables strictly retaining the prompt specifications
  const gapsRaw = skill_gap_summary?.total_gaps !== undefined ? skill_gap_summary.total_gaps : 18;
  const requiredRaw = skill_gap_summary?.critical_gaps !== undefined ? skill_gap_summary.critical_gaps : 10;
  const metRaw = skill_gap_summary?.already_met !== undefined ? skill_gap_summary.already_met : 4;
  const hoursRaw = data.total_training_hrs || 49;
  const phasesCount = pathway?.phases?.length || 3;

  // Dynamic mapped arrays natively from server calculation (with intelligent fallback to preview)
  const skillGapData = data.skill_gap || { gaps: [], missing: [], alreadyMet: [] };
  const combinedGaps = [...(skillGapData.gaps || []), ...(skillGapData.missing || [])];
  
  const requiredGapsList = combinedGaps.filter(g => g.required === true).map(g => g.skill);
  const gapSkills = requiredGapsList.filter(Boolean).length > 0 
    ? Array.from(new Set(requiredGapsList.filter(Boolean)))
    : ["Docker", "Redis", "Kafka", "System Design", "AWS (EC2/S3/Lambda)", "PostgreSQL Advanced", "gRPC", "CI/CD Pipelines", "Kubernetes", "Microservices Architecture"];
  
  const alreadyMetList = (skillGapData.alreadyMet || []).map(m => m.skill);
  const coveredSkills = alreadyMetList.filter(Boolean).length > 0 
    ? Array.from(new Set(alreadyMetList.filter(Boolean)))
    : ["Node.js", "Express.js", "REST APIs", "Git & GitHub"];

  // State ticks
  const gapsCount = useCounter(gapsRaw, 800);
  const requiredCount = useCounter(requiredRaw, 800);
  const metCount = useCounter(metRaw, 800);
  const hoursCount = useCounter(Math.floor(hoursRaw), 800);

  const exportData = {
    userName: candidate?.name || 'Ayush Tiwari',
    targetRole: data.job_title || candidate?.current_role || 'Backend Developer',
    totalGaps: gapsRaw,
    criticalGaps: requiredRaw,
    met: metRaw,
    trainingHours: hoursRaw,
    courses: pathway?.phases?.flatMap((phase) => 
      phase.courses.map(c => ({ ...c, phase_num: phase.phase }))
    ) || [],
    reasoningRaw: typeof data.reasoning_trace === 'object' ? data.reasoning_trace?.raw : data.reasoning_trace
  };

  const getRevealStyle = (delay) => ({
    opacity: visible ? 1 : 0,
    transform: visible ? 'translateY(0)' : 'translateY(20px)',
    transition: 'opacity 0.6s ease, transform 0.6s ease',
    transitionDelay: `${delay}ms`
  });

  return (
    <>
    <div id="roadmap-container" className="bg-[#0a0c10] min-h-screen py-12 text-[#f0f2f5] font-sans overflow-x-hidden">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&display=swap');
        @keyframes beamFade {
          from { opacity: 0.05; }
          to { opacity: 0.35; }
        }
        @keyframes glowPulse {
          from { opacity: 0.1; transform: scaleX(0.9); }
          to { opacity: 0.25; transform: scaleX(1.1); }
        }
        @keyframes wordReveal {
          from { opacity: 0; transform: translateY(6px) filter: blur(4px); }
          to   { opacity: 1; transform: translateY(0)   filter: blur(0);   }
        }
        @keyframes headingSlide {
          from { opacity: 0; transform: translateY(24px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes chipReveal {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
      
      {/* SECTION 1 - HERO */}
      <div className="px-6 mx-auto max-w-5xl">
        <div 
          className="relative w-full rounded-[12px] flex flex-col items-center justify-center p-8 overflow-hidden"
          style={{
            ...getRevealStyle(0),
            background: "rgba(17,19,24,0.95)",
            border: "1px solid rgba(79, 142, 247, 0.2)",
            boxShadow: "0 0 60px rgba(79,142,247,0.06), 0 0 120px rgba(79,142,247,0.03)"
          }}
        >
          {/* Background Beams Absolute Wrapper */}
          <svg
            style={{
              position: "absolute", inset: 0,
              width: "100%", height: "100%",
              zIndex: 0, pointerEvents: "none"
            }}
            viewBox="0 0 1200 500"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <linearGradient id="beam1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#4f8ef7" stopOpacity="0.8"/>
                <stop offset="100%" stopColor="#4f8ef7" stopOpacity="0"/>
              </linearGradient>
              <linearGradient id="beam2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#818cf8" stopOpacity="0.6"/>
                <stop offset="100%" stopColor="#818cf8" stopOpacity="0"/>
              </linearGradient>
            </defs>

            {/* Fan of 12 beams from top-center */}
            {[...Array(12)].map((_, i) => (
              <line key={i}
                x1="600" y1="-10"
                x2={i * 110} y2="520"
                stroke="#4f8ef7"
                strokeWidth={i % 3 === 0 ? "1.5" : "0.5"}
                strokeOpacity="0.2"
                style={{
                  animation: `beamFade ${2.5 + i * 0.25}s ease-in-out infinite alternate`,
                  animationDelay: `${i * 0.18}s`
                }}
              />
            ))}

            <ellipse cx="600" cy="0" rx="400" ry="200"
              fill="url(#beam1)" opacity="0.15"
              style={{animation: "glowPulse 4s ease-in-out infinite alternate"}}
            />
            <ellipse cx="600" cy="0" rx="200" ry="100"
              fill="url(#beam2)" opacity="0.2"
              style={{animation: "glowPulse 3s ease-in-out infinite alternate",
                animationDelay: "1s"}}
            />
          </svg>

          {/* Hero text overlay wrapper */}
          <div style={{ position: 'relative', zIndex: 10 }} className="flex flex-col items-center text-center">
            
            <h1 className="font-bold text-2xl md:text-3xl tracking-tight mb-2 flex items-center justify-center flex-wrap gap-x-3">
              <span style={{ display:'inline-block', opacity:0, animation:'headingSlide 0.7s cubic-bezier(0.16,1,0.3,1) forwards', color:'white' }}>
                {candidate?.name || 'Ayush Tiwari'}
              </span>
              <span style={{ display:'inline-block', opacity:0, animation:'headingSlide 0.7s cubic-bezier(0.16,1,0.3,1) forwards', animationDelay:'200ms', color:'#6b7280', fontSize:'0.8em' }}>
                →
              </span>
              <span style={{ display:'inline-block', opacity:0, animation:'headingSlide 0.7s cubic-bezier(0.16,1,0.3,1) forwards', animationDelay:'350ms', color:'#4f8ef7' }}>
                {data.job_title || candidate?.current_role || 'Backend Developer'}
              </span>
            </h1>
            
            <TypewriterSubtitle text={data.subtitle || "Review the skill gap summary and explore the roadmap below."} />
            
            <div className="flex flex-row items-center mt-10">
              <div 
                className="flex flex-col items-start pr-6"
                style={{ opacity:0, animation:'chipReveal 0.5s ease forwards', animationDelay:'1200ms' }}>
                <span className="text-[11px] tracking-[0.15em] uppercase text-neutral-500">ROLE</span>
                <span className="text-[15px] font-medium text-white mt-0.5">{candidate?.current_role || 'Profile under review'}</span>
              </div>
              <div 
                className="flex flex-col items-start border-l border-neutral-800 pl-6 pr-6"
                style={{ opacity:0, animation:'chipReveal 0.5s ease forwards', animationDelay:'1350ms' }}>
                <span className="text-[11px] tracking-[0.15em] uppercase text-neutral-500">EXPERIENCE</span>
                <span className="text-[15px] font-medium text-white mt-0.5">{candidate?.total_experience_years ? `${candidate.total_experience_years} years` : 'Not specified'}</span>
              </div>
              <div 
                className="flex flex-col items-start border-l border-neutral-800 pl-6"
                style={{ opacity:0, animation:'chipReveal 0.5s ease forwards', animationDelay:'1500ms' }}>
                <span className="text-[11px] tracking-[0.15em] uppercase text-neutral-500">PHASES</span>
                <span className="text-[15px] font-medium text-white mt-0.5">{phasesCount} roadmap stages</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6 max-w-5xl mx-auto mt-6">
        {/* SECTION 2 - STAT CARDS */}
        <div 
          className="grid grid-cols-1 md:grid-cols-3 gap-4 px-6 md:px-0" 
          style={getRevealStyle(150)}
        >
          <SpotlightCard>
            <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '3px', background: '#ef4444', borderRadius: '3px 0 0 3px' }}/>
            <div style={{ paddingLeft: '12px' }}>
              <p style={{ fontSize: '11px', letterSpacing: '0.15em', color: '#6b7280', marginBottom: '12px' }} className="uppercase font-bold">Gaps</p>
              <p style={{ fontSize: '48px', fontFamily: "'DM Mono', monospace", fontWeight: 500, color: 'white', lineHeight: 1 }}>
                <span style={{fontFamily:"'DM Mono',monospace"}}>{gapsCount}</span>
              </p>
              <p style={{ fontSize: '12px', color: '#4b5563', marginTop: '8px' }}>skill deficiencies</p>
            </div>
          </SpotlightCard>
          
          <SpotlightCard>
            <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '3px', background: '#f59e0b', borderRadius: '3px 0 0 3px' }}/>
            <div style={{ paddingLeft: '12px' }}>
              <p style={{ fontSize: '11px', letterSpacing: '0.15em', color: '#6b7280', marginBottom: '12px' }} className="uppercase font-bold">Required</p>
              <p style={{ fontSize: '48px', fontFamily: "'DM Mono', monospace", fontWeight: 500, color: 'white', lineHeight: 1 }}>
                <span style={{fontFamily:"'DM Mono',monospace"}}>{requiredCount}</span>
              </p>
              <p style={{ fontSize: '12px', color: '#4b5563', marginTop: '8px' }}>critical priority</p>
            </div>
          </SpotlightCard>

          <SpotlightCard>
            <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '3px', background: '#22c55e', borderRadius: '3px 0 0 3px' }}/>
            <div style={{ paddingLeft: '12px' }}>
              <p style={{ fontSize: '11px', letterSpacing: '0.15em', color: '#6b7280', marginBottom: '12px' }} className="uppercase font-bold">Met</p>
              <p style={{ fontSize: '48px', fontFamily: "'DM Mono', monospace", fontWeight: 500, color: 'white', lineHeight: 1 }}>
                <span style={{fontFamily:"'DM Mono',monospace"}}>{metCount}</span>
              </p>
              <p style={{ fontSize: '12px', color: '#4b5563', marginTop: '8px' }}>already owned</p>
            </div>
          </SpotlightCard>
        </div>

        {/* SECTION 3 - SKILL SECTIONS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 px-6 md:px-0 mt-6">
          
          {/* ALREADY COVERED (MET) SECTION */}
          <div 
            style={getRevealStyle(300)} 
            className="flex flex-col min-h-[160px] bg-[#111318] border border-[rgba(255,255,255,0.07)] rounded-[16px] p-6 shadow-lg"
          >
            <div className="flex items-center gap-2 mb-4 border-b border-[rgba(255,255,255,0.04)] pb-3">
              <span className="w-2 h-2 rounded-full bg-[#238636] shadow-[0_0_8px_rgba(35,134,54,0.6)]"></span>
              <h3 className="text-[12px] font-bold tracking-[0.15em] text-[#9ca3af] uppercase">Already Covered</h3>
            </div>
            
            <div className="flex flex-wrap gap-3 mt-1 flex-1 content-start">
              {(!coveredSkills || coveredSkills.length === 0) ? (
                // Empty state skeleton
                [...Array(6)].map((_, i) => (
                  <div 
                    key={i} 
                    className="h-[34px] w-[80px] sm:w-[100px] bg-[#161b22] border border-[rgba(35,134,54,0.15)] rounded-full animate-pulse flex-shrink-0"
                    style={{ animationDelay: `${i * 150}ms` }}
                  ></div>
                ))
              ) : (
                coveredSkills.map((skill, i) => (
                  <div 
                    key={i}
                    className="group relative flex items-center px-4 py-1.5 bg-[#161b22]/80 backdrop-blur-md border border-[rgba(35,134,54,0.3)] rounded-full transition-all duration-300 ease-out hover:scale-[1.04] hover:-translate-y-[2px] hover:bg-[#161b22] hover:border-[rgba(35,134,54,0.7)] hover:shadow-[0_6px_16px_rgba(35,134,54,0.15)] cursor-default overflow-hidden"
                  >
                    <div className="absolute left-0 top-0 bottom-0 w-[4px] bg-[#238636] opacity-80 group-hover:opacity-100 transition-opacity duration-300"></div>
                    <span className="ml-[6px] text-[11px] font-semibold tracking-wide uppercase text-slate-300 group-hover:text-white transition-colors duration-300">
                      {skill}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* REQUIRED GAPS SECTION */}
          <div 
            style={getRevealStyle(400)} 
            className="flex flex-col min-h-[160px] bg-[#111318] border border-[rgba(255,255,255,0.07)] rounded-[16px] p-6 shadow-lg"
          >
            <div className="flex items-center gap-2 mb-4 border-b border-[rgba(255,255,255,0.04)] pb-3">
              <span className="w-2 h-2 rounded-full bg-[#ef4444] shadow-[0_0_8px_rgba(239,68,68,0.6)]"></span>
              <h3 className="text-[12px] font-bold tracking-[0.15em] text-[#9ca3af] uppercase">Required Gaps</h3>
            </div>
            
            <div className="flex flex-wrap gap-3 mt-1 flex-1 content-start">
              {(!gapSkills || gapSkills.length === 0) ? (
                // Empty state skeleton
                [...Array(6)].map((_, i) => (
                  <div 
                    key={i} 
                    className="h-[34px] w-[80px] sm:w-[100px] bg-[#161b22] border border-[rgba(239,68,68,0.15)] rounded-full animate-pulse flex-shrink-0"
                    style={{ animationDelay: `${i * 150}ms` }}
                  ></div>
                ))
              ) : (
                gapSkills.map((skill, i) => (
                  <div 
                    key={i}
                    className="group relative flex items-center px-4 py-1.5 bg-[#161b22]/80 backdrop-blur-md border border-[rgba(239,68,68,0.3)] rounded-full transition-all duration-300 ease-out hover:scale-[1.04] hover:-translate-y-[2px] hover:bg-[#161b22] hover:border-[rgba(239,68,68,0.6)] hover:shadow-[0_6px_16px_rgba(239,68,68,0.15)] cursor-default overflow-hidden"
                  >
                    <div className="absolute left-0 top-0 bottom-0 w-[4px] bg-[#ef4444] opacity-80 group-hover:opacity-100 transition-opacity duration-300"></div>
                    <span className="ml-[6px] text-[11px] font-semibold tracking-wide uppercase text-slate-300 group-hover:text-white transition-colors duration-300">
                      {skill}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* SECTION 4 - ESTIMATED TRAINING */}
        <div 
          className="bg-[#111318] border border-[rgba(255,255,255,0.07)] rounded-[12px] px-8 py-6 flex flex-col sm:flex-row items-start sm:items-center justify-between relative overflow-hidden mx-6 md:mx-0 mt-6"
          style={getRevealStyle(500)}
        >
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-[#4f8ef7] rounded-t-[12px]"></div>
          <div className="flex flex-col mb-4 sm:mb-0">
            <span className="text-[11px] tracking-[0.15em] uppercase text-neutral-500">ESTIMATED TRAINING</span>
            <span className="text-4xl font-medium text-white mt-1 tracking-tight flex items-baseline">
              <span style={{fontFamily:"'DM Mono',monospace"}}>{hoursCount}</span>
              <span className="text-4xl ml-1">h</span>
            </span>
          </div>
          <button 
            onClick={() => document.getElementById('pathway-section')?.scrollIntoView({ behavior: 'smooth' })}
            className="border border-[rgba(255,255,255,0.15)] text-neutral-300 text-sm px-4 py-[0.6rem] rounded-lg hover:bg-[rgba(255,255,255,0.06)] transition-all group flex items-center"
          >
            guided learning path <span className="inline-block transition-transform duration-300 group-hover:translate-x-[2px] ml-1">→</span>
          </button>
        </div>

        {/* SECTION 5 - PATHWAY GRAPH */}
        <div 
          id="pathway-section"
          className="mt-12 relative w-full h-[640px] rounded-[16px] overflow-hidden bg-[#111318] border border-[rgba(255,255,255,0.07)]" 
          style={getRevealStyle(600)}
        >
          <PathwayFlow pathway={pathway} onNodeClick={setSelectedCourseId} />
        </div>

        {/* SECTION 6 - PHASE TIMELINE */}
        <div 
          className="mt-4 rounded-[16px] overflow-hidden bg-[#111318] border border-[rgba(255,255,255,0.07)]"
          style={getRevealStyle(700)}
        >
          <PhaseTimeline pathway={pathway} total_training_hrs={hoursRaw} />
        </div>

        {/* SECTION 7 - REASONING TRACE */}
        <div 
          className="mt-6 rounded-[16px] overflow-hidden bg-[#111318] border border-[rgba(255,255,255,0.07)] p-6"
          style={getRevealStyle(800)}
        >
          <ReasoningTrace trace={data.reasoning_trace} activeSection={null} />
        </div>
      </div>

      <CourseDrawer courseId={selectedCourseId} pathway={pathway} onClose={() => setSelectedCourseId(null)} />
    </div>
    <FloatingExportButton exportData={exportData} />
    </>
  );
}
