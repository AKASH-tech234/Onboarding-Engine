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
  const [jdMode, setJdMode] = useState('file'); // 'file' | 'text'
  const [localError, setLocalError] = useState(null);

  const navigate = useNavigate();
  const { analyze, isLoading, error: analyzeError } = useAnalyze();

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
      const data = await analyze(resumeFile, jdFile, jdText);
      navigate(`/results/${data.session_id}`);
    } catch (err) {
      // Error handled by hook
    }
  };

  return (
    <div className="bg-slate-50 min-h-screen p-4">
      <div className="max-w-[640px] mx-auto mt-16 p-8 bg-white rounded-2xl shadow-sm border border-slate-100">
        <h1 className="text-2xl font-bold text-slate-800 mb-6 text-center">AI Onboarding Engine</h1>
        
        <div className="mb-6">
          <UploadZone type="resume" onFile={setResumeFile} file={resumeFile} />
        </div>

        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-slate-700">Job Description</span>
            <button
              onClick={() => {
                setJdMode(m => m === 'file' ? 'text' : 'file');
                setLocalError(null);
              }}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {jdMode === 'file' ? 'Paste JD text instead' : 'Upload JD file instead'}
            </button>
          </div>
          
          {jdMode === 'file' ? (
            <UploadZone type="jd" onFile={setJdFile} file={jdFile} />
          ) : (
            <textarea
              className="w-full h-32 p-4 border-2 border-slate-300 rounded-xl focus:border-blue-400 focus:ring-4 focus:ring-blue-50 outline-none transition-all resize-none"
              placeholder="Paste the job requirements here..."
              value={jdText}
              onChange={e => setJdText(e.target.value)}
            />
          )}
        </div>

        {error && (
          <div className="mt-3 flex items-center gap-2 px-4 py-3 mb-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            <span className="flex-1">{error}</span>
            <button onClick={() => setLocalError(null)} className="text-red-400 hover:text-red-600 text-xl leading-none">&times;</button>
          </div>
        )}

        <AnalyzeButton 
          disabled={!resumeFile || (jdMode === 'file' ? !jdFile : !jdText.trim())}
          loading={isLoading}
          onClick={handleSubmit}
        />
        
        <ExampleBadge />
      </div>
    </div>
  );
}
