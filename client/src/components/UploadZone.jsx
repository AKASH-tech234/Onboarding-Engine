import { useDropzone } from 'react-dropzone';

export default function UploadZone({ type, onFile, file }) {
  const isResume = type === 'resume';
  const accept = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept,
    onDrop: (files) => {
      if (files?.length) onFile(files[0]);
    },
  });

  if (file) {
    return (
      <div className="relative overflow-hidden rounded-[28px] border border-white/15 bg-white/8 p-5 shadow-[0_20px_50px_rgba(2,6,23,0.32)] backdrop-blur-xl">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(109,125,255,0.18),transparent_38%)]" />
        <div className="relative flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-slate-950/40 text-sm font-bold text-indigo-100">
            {isResume ? 'CV' : 'JD'}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-100">{file.name}</p>
            <p className="mt-1 text-xs text-slate-400">
              {(file.size / 1024).toFixed(1)} KB uploaded successfully
            </p>
          </div>
        </div>
        <button
          onClick={() => onFile(null)}
          className="absolute right-4 top-4 rounded-full border border-white/10 bg-white/6 px-2.5 py-1 text-sm font-semibold text-slate-300 transition-colors hover:bg-white/12 hover:text-white"
        >
          Remove
        </button>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`group relative overflow-hidden rounded-[28px] border p-6 text-left transition-all duration-300 ${
        isDragActive
          ? 'border-indigo-300/60 bg-indigo-400/10 shadow-[0_18px_50px_rgba(99,102,241,0.2)]'
          : 'border-white/12 bg-white/6 hover:border-white/22 hover:bg-white/8'
      }`}
    >
      <input {...getInputProps()} />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(109,125,255,0.18),transparent_34%)] opacity-90" />
      <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-slate-950/35 text-lg font-bold text-indigo-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
            {isResume ? 'R' : 'J'}
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-100">
              {isResume ? 'Upload resume' : 'Upload job description'}
            </p>
            <p className="mt-1 text-sm text-slate-400">
              {isResume ? 'PDF or DOCX, parsed directly into skills.' : 'Drop a file or switch to pasted text for faster analysis.'}
            </p>
          </div>
        </div>
        <div className="rounded-full border border-white/12 bg-white/6 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-300 transition-transform duration-300 group-hover:-translate-y-0.5">
          {isDragActive ? 'Release to upload' : 'Browse file'}
        </div>
      </div>
    </div>
  );
}
