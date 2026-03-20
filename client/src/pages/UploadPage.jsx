import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import UploadZone from '../components/UploadZone';
import AnalyzeButton from '../components/AnalyzeButton';
import ExampleBadge from '../components/ExampleBadge';
import { useAnalyze } from '../hooks/useAnalyze';

export default function UploadPage() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [jdMode, setJdMode] = useState('file');
  const [localError, setLocalError] = useState(null);

  const navigate = useNavigate();
  const { analyze, isLoading, loadingStatus, partialTrace, error: analyzeError } = useAnalyze();

  const error = localError || analyzeError;

  const handleSubmit = async () => {
    if (!resumeFile) {
      setLocalError('Please upload a resume.');
      return;
    }
    if (jdMode === 'file' && !jdFile) {
      setLocalError('Please upload a job description file.');
      return;
    }
    if (jdMode === 'text' && !jdText.trim()) {
      setLocalError('Please paste a job description.');
      return;
    }

    setLocalError(null);
    try {
      const activeJdFile = jdMode === 'file' ? jdFile : null;
      const activeJdText = jdMode === 'text' ? jdText : '';
      const data = await analyze(resumeFile, activeJdFile, activeJdText);
      navigate(`/results/${data.session_id}`, {
        state: {
          sessionData: data,
        },
      });
    } catch (err) {
      // Error handled by hook.
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0c10] text-slate-300 font-sans selection:bg-indigo-500/30 selection:text-indigo-100 overflow-x-hidden">
      
      {/* Subtle Background Radial Glows */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none flex justify-center z-0">
        <div className="absolute -top-[20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px]" />
        <div className="absolute top-[20%] right-[-10%] w-[40%] h-[40%] rounded-full bg-violet-600/10 blur-[120px]" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 lg:py-14">
        
        {/* Header */}
        <header className="mb-14 lg:mb-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-[0_0_20px_rgba(99,102,241,0.3)]">
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-sm font-bold tracking-wide text-white">Pathway AI</span>
          </div>
          <div className="hidden items-center gap-6 text-xs font-semibold uppercase tracking-widest text-slate-400 md:flex">
            <span>Powered by Gemini</span>
            <div className="h-4 w-px bg-white/10" />
            <span className="flex items-center gap-2 text-indigo-300">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-500"></span>
              </span>
              Engine Online
            </span>
          </div>
        </header>

        <main className="grid grid-cols-1 gap-12 lg:grid-cols-12 lg:gap-12">
          
          {/* LEFT COLUMN: Hero & Features */}
          <section className="lg:col-span-7 flex flex-col justify-center">
            
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.2em] text-indigo-300 backdrop-blur-sm w-fit mb-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]">
              <span className="flex h-1.5 w-1.5 rounded-full bg-indigo-400 shadow-[0_0_8px_rgba(129,140,248,0.8)]" />
              Intelligent Onboarding
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-[56px] font-extrabold tracking-tight text-white leading-[1.15] mb-6">
              Turn resumes into <br className="hidden sm:block"/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-400">
                guided roadmaps.
              </span>
            </h1>
            
            <p className="text-base sm:text-lg leading-relaxed text-slate-400 max-w-[540px] mb-10">
              Upload a candidate's profile and target role to generate a grounded, role-aware training pathway that automatically prioritizes critical skill gaps.
            </p>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 mb-12">
              <HeroMetric label="Faster readiness" value="26h" caption="Avg. targeted training" />
              <HeroMetric label="Grounded path" value="100%" caption="Catalog-backed output" />
              <HeroMetric label="Role aware" value="4 Phases" caption="Foundation to expert" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FeatureCard 
                icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
                title="Resume intelligence" 
                description="Extract current strengths and infer readiness from documents." 
              />
              <FeatureCard 
                icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>}
                title="Role-fit analysis" 
                description="Compare requirements against candidate evidence." 
              />
              <FeatureCard 
                icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>}
                title="Adaptive sequencing" 
                description="Order courses by prerequisites, impact, and urgency." 
              />
              <FeatureCard 
                icon={<svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                title="Reasoning visibility" 
                description="Show why each recommendation appears and how it's prioritized." 
              />
            </div>
          </section>

          {/* RIGHT COLUMN: Upload Panel */}
          <section className="lg:col-span-5 relative lg:sticky lg:top-10 h-fit">
            
            {/* Ambient Background Glow for Card */}
            <div className="absolute -inset-1 rounded-[32px] bg-gradient-to-b from-indigo-500/20 to-transparent blur-2xl pointer-events-none opacity-50" />
            
            <div className="relative rounded-[28px] border border-white/10 bg-[#111318] p-6 shadow-2xl sm:p-8 backdrop-blur-xl">
              
              <div className="mb-8 border-b border-white/5 pb-6">
                <div className="flex items-center justify-between mb-1.5">
                  <h3 className="text-xl font-bold text-white tracking-tight">Generate Pathway</h3>
                  <span className="text-[10px] uppercase tracking-widest text-indigo-400 font-bold bg-indigo-500/10 px-2 py-1 rounded-md">Step 1</span>
                </div>
                <p className="text-sm text-slate-400 leading-relaxed">Securely upload documents to trigger the adaptive matching engine.</p>
              </div>

              <div className="space-y-6">
                
                {/* Resume Upload */}
                <div>
                  <label className="mb-2.5 block text-[11px] font-bold uppercase tracking-widest text-slate-300">Candidate Profile</label>
                  <UploadZone type="resume" onFile={setResumeFile} file={resumeFile} />
                </div>

                <div className="flex items-center gap-4 py-1">
                  <div className="h-px flex-1 bg-white/5"></div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Target Role</span>
                  <div className="h-px flex-1 bg-white/5"></div>
                </div>

                {/* JD Input */}
                <div>
                  <div className="mb-2.5 flex items-center justify-between">
                    <label className="block text-[11px] font-bold uppercase tracking-widest text-slate-300">Job Description</label>
                    <button
                      onClick={() => {
                        setJdMode((m) => {
                          const mode = m === 'file' ? 'text' : 'file';
                          if (mode === 'text') setJdFile(null);
                          else setJdText('');
                          return mode;
                        });
                        setLocalError(null);
                      }}
                      className="text-[11px] font-bold uppercase tracking-widest text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      {jdMode === 'file' ? 'Paste text instead' : 'Upload file'}
                    </button>
                  </div>

                  {jdMode === 'file' ? (
                    <UploadZone type="jd" onFile={setJdFile} file={jdFile} />
                  ) : (
                    <textarea
                      className="h-32 w-full rounded-xl border border-white/10 bg-[#0a0c10]/50 p-4 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600 focus:border-indigo-500/50 focus:bg-[#0a0c10] focus:ring-4 focus:ring-indigo-500/10 resize-none shadow-inner"
                      placeholder="Paste the target job requirements or responsibilities here..."
                      value={jdText}
                      onChange={(e) => setJdText(e.target.value)}
                    />
                  )}
                </div>

                {/* Errors */}
                {error && (
                  <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-200 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] animate-in slide-in-from-top-2 duration-300">
                    <svg className="h-5 w-5 shrink-0 text-rose-400 mt-0.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>
                    <span className="flex-1 leading-relaxed">{error}</span>
                  </div>
                )}

                {/* Submit / Loading */}
                <div className="pt-2">
                  {isLoading ? (
                    <div className="rounded-2xl border border-indigo-500/30 bg-indigo-500/10 p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                      <div className="flex items-center gap-4 mb-4 border-b border-indigo-500/20 pb-4">
                        <div className="relative flex h-8 w-8 items-center justify-center shrink-0">
                          <svg className="absolute h-full w-full animate-spin text-indigo-500/20" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" /></svg>
                          <svg className="absolute h-full w-full animate-spin text-indigo-400" viewBox="0 0 24 24" fill="none"><path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor" /></svg>
                        </div>
                        <div>
                          <h3 className="text-sm font-bold tracking-wide text-white">{loadingStatus || "Analyzing profile..."}</h3>
                          <p className="text-[11px] font-medium uppercase tracking-wider text-indigo-300/80 mt-1">Extracting competencies</p>
                        </div>
                      </div>

                      {partialTrace && (
                        <div className="relative h-[110px] overflow-hidden rounded-xl bg-[#0a0c10] border border-white/5 p-4 shadow-inner">
                          <div className="font-mono text-[10px] leading-[1.8] text-slate-400 whitespace-pre-wrap flex flex-col justify-end min-h-full">
                            <div>{partialTrace.slice(-250)}<span className="animate-pulse inline-block w-1.5 h-3 ml-1 bg-indigo-400 align-middle" /></div>
                          </div>
                          <div className="absolute inset-x-0 top-0 h-8 bg-gradient-to-b from-[#0a0c10] to-transparent pointer-events-none" />
                        </div>
                      )}
                    </div>
                  ) : (
                    <button
                      disabled={!resumeFile || (jdMode === 'file' ? !jdFile : !jdText.trim())}
                      onClick={handleSubmit}
                      className="group relative flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-b from-indigo-500 to-violet-600 px-4 py-4 text-sm font-bold tracking-wide text-white shadow-[0_2px_10px_rgba(99,102,241,0.3),inset_0_1px_0_rgba(255,255,255,0.2)] transition-all duration-300 hover:opacity-90 active:scale-[0.98] disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 disabled:shadow-none disabled:cursor-not-allowed"
                    >
                      Generate Learning Roadmap
                      <svg className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1 disabled:group-hover:translate-x-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                    </button>
                  )}
                  
                  {!isLoading && (
                    <div className="mt-4 flex justify-center">
                      <ExampleBadge />
                    </div>
                  )}
                </div>

              </div>
            </div>
          </section>

        </main>
      </div>
    </div>
  );
}

function HeroMetric({ label, value, caption }) {
  return (
    <div className="flex flex-col border-l-2 border-indigo-500/30 pl-4 py-1 transition-colors hover:border-indigo-400">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold tracking-tight text-white">{value}</p>
      <p className="mt-1 text-[11px] font-medium text-slate-400">{caption}</p>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="group relative rounded-2xl border border-white/5 bg-white/[0.02] p-5 transition-all duration-300 hover:scale-[1.02] hover:bg-white/[0.04] hover:shadow-[0_8px_24px_rgba(0,0,0,0.2)]">
      <div className="mb-4 flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500/20 group-hover:text-indigo-300 transition-colors">
        {icon}
      </div>
      <p className="text-sm font-bold tracking-wide text-slate-200">{title}</p>
      <p className="mt-2 text-[13px] leading-relaxed text-slate-400">{description}</p>
    </div>
  );
}
