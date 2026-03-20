import { useState, useEffect } from 'react';
import client from '../api/client';

const DEMO_IDS = { tech: 'FILL_AFTER_DEPLOY', ops: 'FILL_AFTER_DEPLOY' };

export function useSession(id, initialData = null) {
  const [data, setData] = useState(initialData);
  const [isLoading, setIsLoading] = useState(!initialData);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    async function fetchSession() {
      if (initialData?.session_id === id) {
        if (active) {
          setData(initialData);
          setIsLoading(false);
          setError(null);
        }
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await client.get(`/sessions/${id}`);
        if (active) {
          setData(response.data);
          setIsLoading(false);
        }
      } catch (err) {
        if (!active) return;
        setIsLoading(false);
        
        if (err.response?.status === 404 && Object.values(DEMO_IDS).includes(id)) {
            console.warn('Demo session expired or not available on this environment');
            setError('Demo session expired. Please use the upload form.');
        } else if (err.response?.status === 404) {
            setError('Session not found');
        } else {
            setError(err.message || 'Failed to load session');
        }
      }
    }

    fetchSession();

    return () => { active = false; };
  }, [id, initialData]);

  return { data, isLoading, error };
}
