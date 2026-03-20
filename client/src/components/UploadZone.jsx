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
      <div className="border-2 border-slate-400 rounded-xl p-8 mb-4 relative bg-white">
        <p className="font-medium text-slate-800">{file.name}</p>
        <p className="text-slate-400 text-sm">{(file.size / 1024).toFixed(1)} KB</p>
        <button
          onClick={() => onFile(null)}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 text-xl leading-none"
        >
          &times;
        </button>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer mb-4 transition-colors ${
        isDragActive ? 'border-blue-400 bg-blue-50' : 'border-slate-300 hover:bg-slate-50'
      }`}
    >
      <input {...getInputProps()} />
      <div className="text-slate-500 mb-2 text-3xl">📄</div>
      <p className="text-slate-600 font-medium">
        {isResume ? 'Drop your resume (PDF or DOCX)' : 'Drop the job description'}
      </p>
      <p className="text-slate-400 text-sm mt-1">or click to browse</p>
    </div>
  );
}
