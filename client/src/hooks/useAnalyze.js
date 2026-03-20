import { useState } from 'react';
import client from '../api/client';

export function useAnalyze() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = async (resumeFile, jdFile, jdText) => {
    setIsLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      if (resumeFile) formData.append('resume', resumeFile);
      
      if (jdFile) {
        formData.append('jd', jdFile);
      } else if (jdText) {
        formData.append('jd_text', jdText);
      }

      const response = await client.post('/sessions/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'An error occurred during analysis');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { analyze, isLoading, error };
}
