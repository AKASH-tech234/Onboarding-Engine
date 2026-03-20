import SkillChips from './SkillChips';
import { TypewriterEffectSmooth } from './TypewriterEffectSmooth';
import { BackgroundGradient } from './BackgroundGradient';

export default function GapSummaryCard({ candidate, skillGapSummary, pathway }) {
  const phases = pathway?.phases || [];
  const allGaps = phases.flatMap((phase) =>
    phase.courses.map((course) => ({
      skill: course.addresses_skill,
      current: course.gap_type === 'missing' ? 'none' : 'lower level',
      target: course.level,
      required: course.score_breakdown?.gap_criticality === 1.0,
    }))
  );

  const uniqueGaps = Array.from(new Set(allGaps.map((item) => item.skill))).map((skill) =>
    allGaps.find((item) => item.skill === skill)
  );

  const requiredGaps = uniqueGaps.filter((item) => item.required);
  const preferredGaps = uniqueGaps.filter((item) => !item.required);
  const alreadyMet = Array(skillGapSummary?.already_met || 0).fill({
    skill: 'Assumed skill',
    current: 'various',
    target: 'various',
  });

  const totalHours = phases.reduce((sum, phase) => sum + phase.phase_duration_hrs, 0);

  const nameWords = String(candidate?.name || 'Ayush Tiwari').split(" ").map(w => ({ text: w, className: "text-white" }));
  const roleWords = String(candidate?.current_role || 'Backend Developer').split(" ").map(w => ({ text: w, className: "text-blue-500" }));
  const typeWriterWords = [...nameWords, { text: "-", className: "text-white" }, ...roleWords];

  return (
    <div className="flex h-full flex-col isolate-layer gap-6">
      <div className="flex flex-col items-center justify-center p-8 bg-zinc-950 rounded-[28px] border border-white/5 shadow-2xl text-center">
        <TypewriterEffectSmooth words={typeWriterWords} />
        <p className="mt-2 text-sm text-slate-400">
          Review the skill gap summary and explore the roadmap below.
        </p>

        <div className="mt-8 grid w-full grid-cols-3 gap-3">
          <div className="group rounded-[20px] bg-white/5 border border-white/10 p-4 transition-all will-change-transform duration-300 hover:border-indigo-400/40 hover:drop-shadow-[0_0_20px_rgba(129,140,248,0.15)] text-left flex flex-col justify-center">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">ROLE</p>
            <p className="mt-1 text-sm font-medium text-white">{candidate?.current_role || 'Profile under review'}</p>
          </div>
          <div className="group rounded-[20px] bg-white/5 border border-white/10 p-4 transition-all will-change-transform duration-300 hover:border-indigo-400/40 hover:drop-shadow-[0_0_20px_rgba(129,140,248,0.15)] text-left flex flex-col justify-center">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">EXPERIENCE</p>
            <p className="mt-1 text-sm font-medium text-white">{candidate?.total_experience_years ? `${candidate.total_experience_years} years` : 'Not specified'}</p>
          </div>
          <div className="group rounded-[20px] bg-white/5 border border-white/10 p-4 transition-all will-change-transform duration-300 hover:border-indigo-400/40 hover:drop-shadow-[0_0_20px_rgba(129,140,248,0.15)] text-left flex flex-col justify-center">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">PHASES</p>
            <p className="mt-1 text-sm font-medium text-white">{phases.length} roadmap stages</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <BackgroundGradient glowClass="bg-gradient-to-r from-red-500 to-rose-600">
          <div className="flex flex-col items-center justify-center h-full py-5 text-center bg-zinc-900 rounded-[22px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] focus:outline-none z-10 relative">
            <p className="text-[10px] font-bold tracking-widest text-zinc-500 uppercase">GAPS</p>
            <p className="mt-1 text-3xl font-extrabold text-white">{skillGapSummary?.total_gaps !== undefined ? skillGapSummary.total_gaps : '18'}</p>
          </div>
        </BackgroundGradient>
        
        <BackgroundGradient glowClass="bg-gradient-to-r from-yellow-400 to-amber-600">
          <div className="flex flex-col items-center justify-center h-full py-5 text-center bg-zinc-900 rounded-[22px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] focus:outline-none z-10 relative">
            <p className="text-[10px] font-bold tracking-widest text-zinc-500 uppercase">REQUIRED</p>
            <p className="mt-1 text-3xl font-extrabold text-white">{skillGapSummary?.critical_gaps !== undefined ? skillGapSummary.critical_gaps : '10'}</p>
          </div>
        </BackgroundGradient>
        
        <BackgroundGradient glowClass="bg-gradient-to-r from-teal-400 to-emerald-600">
          <div className="flex flex-col items-center justify-center h-full py-5 text-center bg-zinc-900 rounded-[22px] shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] focus:outline-none z-10 relative">
            <p className="text-[10px] font-bold tracking-widest text-zinc-500 uppercase">MET</p>
            <p className="mt-1 text-3xl font-extrabold text-white">{skillGapSummary?.already_met !== undefined ? skillGapSummary.already_met : '4'}</p>
          </div>
        </BackgroundGradient>
      </div>

      <div className="rounded-[26px] border border-white/10 bg-white/5 p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-300">Already covered</h3>
        <SkillChips items={alreadyMet} color="green" />
      </div>

      {requiredGaps.length > 0 && (
        <div className="rounded-[26px] border border-white/10 bg-white/5 p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-300">Required gaps</h3>
          <SkillChips items={requiredGaps} color="red" />
        </div>
      )}

      {preferredGaps.length > 0 && (
        <div className="rounded-[26px] border border-white/10 bg-white/5 p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-300">Stretch skills</h3>
          <SkillChips items={preferredGaps} color="amber" />
        </div>
      )}

      <div className="mt-auto rounded-[26px] border border-indigo-300/15 bg-gradient-to-br from-indigo-400/10 to-cyan-400/10 p-5 shadow-[0_18px_40px_rgba(15,23,42,0.25)]">
        <p className="text-[11px] uppercase tracking-[0.24em] text-slate-400">Estimated training</p>
        <div className="mt-2 flex items-end justify-between">
          <span className="text-3xl font-extrabold text-white">{totalHours.toFixed(1)}h</span>
          <span className="text-sm text-slate-300">guided learning path</span>
        </div>
      </div>
    </div>
  );
}
