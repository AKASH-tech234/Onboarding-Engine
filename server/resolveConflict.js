const fs = require('fs')

const path = '../client/src/pages/UploadPage.jsx'
let content = fs.readFileSync(path, 'utf8')

const replacement = `        <main className="grid flex-1 gap-8 xl:grid-cols-[1.15fr_0.9fr]">
          <section className="relative rounded-[36px] border border-white/10 bg-[linear-gradient(180deg,rgba(8,18,33,0.88),rgba(3,8,18,0.96))] p-7 shadow-[0_30px_90px_rgba(2,6,23,0.45)] sm:p-10">
            <div className="max-w-2xl">
              <div className="inline-flex rounded-full border border-indigo-300/20 bg-indigo-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-indigo-100">
                AI-powered onboarding orchestration
              </div>
              <h2 className="mt-6 text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl">
                Turn every resume and job description into a guided learning roadmap.
              </h2>
              <p className="mt-5 max-w-xl text-base leading-8 text-slate-300 sm:text-lg">
                Upload a candidate profile, compare it against a target role, and generate a grounded pathway that closes the most important skill gaps first.
              </p>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              <HeroMetric label="Faster readiness" value="26h" caption="targeted training example" />
              <HeroMetric label="Grounded pathway" value="100%" caption="catalog-backed recommendations" />
              <HeroMetric label="Role aware" value="4 phases" caption="from foundation to specialization" />
            </div>

            <div className="mt-10 grid gap-4 lg:grid-cols-2">
              <FeatureCard title="Resume intelligence" description="Extract current strengths and infer candidate readiness from the uploaded profile." />
              <FeatureCard title="Role-fit analysis" description="Compare required competencies against evidence from the candidate’s background." />
              <FeatureCard title="Adaptive sequencing" description="Order courses by prerequisites, impact, and urgency without changing backend logic." />
              <FeatureCard title="Reasoning visibility" description="Show why each recommendation appears and how the learning path is prioritized." />
            </div>
          </section>

          <section className="glass-panel relative rounded-[36px] p-6 sm:p-8">
            <div className="mb-8">
              <p className="text-[11px] uppercase tracking-[0.28em] text-slate-400">Start analysis</p>
              <h3 className="mt-3 text-2xl font-bold text-white">Build a premium onboarding plan</h3>
              <p className="mt-2 text-sm leading-7 text-slate-300">
                Keep the workflow exactly the same. The UI now gives it a more polished, guided, SaaS-quality feel.
              </p>
            </div>

            <div className="space-y-5">
              <UploadZone type="resume" onFile={setResumeFile} file={resumeFile} />

              <div className="rounded-[28px] border border-white/10 bg-white/5 p-5">
                <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-100">Job description input</p>
                    <p className="mt-1 text-sm text-slate-400">Use a file for formal documents or switch to text for quick testing.</p>
                  </div>
                  <button
                    onClick={() => {
                      setJdMode((mode) => {
                        const nextMode = mode === 'file' ? 'text' : 'file';
                        if (nextMode === 'file') {
                          setJdText('');
                        } else {
                          setJdFile(null);
                        }
                        return nextMode;
                      });
                      setLocalError(null);
                    }}
                    className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-200 transition-colors hover:bg-white/10"
                  >
                    {jdMode === 'file' ? 'Switch to pasted text' : 'Switch to file upload'}
                  </button>
                </div>

                {jdMode === 'file' ? (
                  <UploadZone type="jd" onFile={setJdFile} file={jdFile} />
                ) : (
                  <textarea
                    className="h-40 w-full rounded-[24px] border border-white/12 bg-slate-950/30 px-5 py-4 text-sm leading-7 text-slate-100 outline-none transition-all duration-300 placeholder:text-slate-500 focus:border-indigo-300/40 focus:bg-slate-950/45 focus:ring-4 focus:ring-indigo-400/10"
                    placeholder="Paste the job requirements here..."
                    value={jdText}
                    onChange={(event) => setJdText(event.target.value)}
                  />
                )}
              </div>

              {error && (
                <div className="flex items-start gap-3 rounded-2xl border border-rose-300/15 bg-rose-400/10 px-4 py-4 text-sm text-rose-100">
                  <span className="mt-0.5 h-2.5 w-2.5 rounded-full bg-rose-300" />
                  <span className="flex-1">{error}</span>
                  <button onClick={() => setLocalError(null)} className="rounded-full border border-white/10 px-2 py-0.5 text-xs font-semibold text-rose-100 transition-colors hover:bg-white/8">
                    Dismiss
                  </button>
                </div>
              )}

              {isLoading ? (
                <div className="rounded-[24px] border border-indigo-300/20 bg-indigo-400/10 p-6 space-y-4">
                  <div className="flex items-center gap-3">
                    <svg className="animate-spin h-5 w-5 text-indigo-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <h3 className="font-semibold text-indigo-100">{loadingStatus || "Analyzing..."}</h3>
                  </div>
                  
                  {partialTrace && (
                    <div className="rounded-[20px] bg-slate-950/40 p-5 font-mono text-sm leading-relaxed text-slate-300 h-48 overflow-y-auto border border-white/5 whitespace-pre-wrap">
                      {partialTrace}
                      <span className="animate-pulse inline-block w-2 h-4 ml-1 bg-indigo-400 align-middle"></span>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <AnalyzeButton
                    disabled={!resumeFile || (jdMode === 'file' ? !jdFile : !jdText.trim())}
                    loading={false}
                    onClick={handleSubmit}
                  />
                  <ExampleBadge />
                </>
              )}
            </div>
          </section>
        </main>`

content = content.replace(/<<<<<<< Updated upstream[\s\S]*?>>>>>>> Stashed changes/, replacement)
fs.writeFileSync(path, content)
console.log('Merge conflict resolved.')
