import { useState } from 'react';

export function useAnalyze() {
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [partialTrace, setPartialTrace] = useState('');
  const [error, setError] = useState(null);

  const analyze = async (resumeFile, jdFile, jdText) => {
    setIsLoading(true);
    setLoadingStatus('Initializing AI Engine...');
    setPartialTrace('');
    setError(null);
    
    try {
      const formData = new FormData();
      if (resumeFile) formData.append('resume', resumeFile);
      if (jdFile) formData.append('jd', jdFile);
      else if (jdText) formData.append('jd_text', jdText);

      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:3001/api/v1';
      
      const response = await fetch(`${baseUrl}/sessions/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let msg = 'An error occurred during analysis';
        try {
          const errData = await response.json();
          msg = errData.error || msg;
        } catch(e) {}
        throw new Error(msg);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let finalData = null;
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        
        // Keep the last partial event in the buffer
        buffer = events.pop() || '';

        for (const eventBlock of events) {
          if (!eventBlock.trim()) continue;
          
          const eventMatch = eventBlock.match(/event: (.*?)\n/);
          const dataMatch = eventBlock.match(/data: (.*)/);
          
          if (eventMatch && dataMatch) {
            const eventType = eventMatch[1].trim();
            const payloadStr = dataMatch[1].trim();
            
            let payload;
            try { payload = JSON.parse(payloadStr); } catch (e) { payload = payloadStr; }

            if (eventType === 'status') {
              setLoadingStatus(payload.message || 'Processing...');
            } else if (eventType === 'trace_chunk') {
              setPartialTrace(prev => prev + payload);
            } else if (eventType === 'pathway_ready') {
              setLoadingStatus('Building Visuals...');
            } else if (eventType === 'complete') {
              finalData = payload;
            } else if (eventType === 'error') {
              throw new Error(payload.error || 'Server error');
            }
          }
        }
      }

      if (!finalData) throw new Error('Stream closed prematurely');
      return finalData;

    } catch (err) {
      setError(err.message || 'An error occurred during analysis');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { analyze, isLoading, loadingStatus, partialTrace, error };
}
