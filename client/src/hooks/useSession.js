import { useState, useEffect } from 'react';
import client from '../api/client';
import { mockData } from '../mockData';

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';
const DEMO_IDS = { tech: 'FILL_AFTER_DEPLOY', ops: 'FILL_AFTER_DEPLOY' };

export function useSession(id) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    async function fetchSession() {
      setIsLoading(true);
      setError(null);
      
      if (USE_MOCK) {
        setTimeout(() => {
          if (active) {
            setData(mockData);
            setIsLoading(false);
          }
        }, 800);
        return;
      }

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
  }, [id]);

  return { data, isLoading, error };
}
