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
      <div className="group relative flex items-center justify-between rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-4 transition-all hover:bg-indigo-500/10 hover:border-indigo-500/40">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#0a0c10] border border-white/10 text-indigo-400 shadow-[0_2px_8px_rgba(0,0,0,0.4)]">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
          </div>
          <div className="min-w-0 pr-4">
            <p className="truncate text-sm font-semibold text-slate-200">{file.name}</p>
            <p className="mt-1 text-xs text-indigo-300">
              {(file.size / 1024).toFixed(1)} KB • Ready for analysis
            </p>
          </div>
        </div>
        <button
          onClick={() => onFile(null)}
          className="shrink-0 rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
          title="Remove file"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`group relative flex cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed p-8 text-center transition-all duration-300 ${
        isDragActive
          ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01]'
          : 'border-white/10 bg-[#0a0c10]/50 hover:border-indigo-500/40 hover:bg-indigo-500/5 hover:scale-[1.01]'
      }`}
    >
      <input {...getInputProps()} />
      <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-full transition-colors duration-300 ${isDragActive ? 'bg-indigo-500/20 text-indigo-400' : 'bg-white/5 text-slate-400 group-hover:bg-indigo-500/20 group-hover:text-indigo-400'}`}>
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
      </div>
      <p className="text-sm font-semibold text-white">
        {isResume ? 'Upload candidate resume' : 'Upload job description'}
      </p>
      <p className="mt-1.5 text-xs text-slate-400 max-w-[200px] leading-relaxed">
        Drag and drop your file here, or click to browse
      </p>
      <div className="mt-5 rounded-full border border-white/5 bg-white/5 px-3 py-1 text-[10px] font-medium tracking-wider text-slate-400 uppercase">
        PDF or DOCX max 5MB
      </div>
    </div>
  );
}
