import React, { useEffect, useState } from 'react';
import LLMTimeline from '../components/LLMTimeline';

const LLMTimelinePage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Try to load from backend API first, fallback to JSON file
        const response = await fetch('/api/llm-timeline') 
          .catch(() => fetch('/data/llm_releases.json'));
        
        if (!response.ok) {
          throw new Error('Failed to load timeline data');
        }

        const jsonData = await response.json();
        setData(jsonData);
      } catch (err) {
        console.error('Error loading timeline data:', err);
        setError('Failed to load timeline data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0e27 0%, #0f1429 100%)',
        color: '#e8e8ee',
        fontFamily: "'Inter', sans-serif"
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '3rem',
            marginBottom: '1rem',
            animation: 'spin 2s linear infinite'
          }}>⏳</div>
          <p>Loading LLM Timeline...</p>
          <style>{`
            @keyframes spin {
              from { transform: rotate(0deg); }
              to { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0e27 0%, #0f1429 100%)',
        color: '#ff6b9d',
        fontFamily: "'Inter', sans-serif"
      }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '1.2rem' }}>⚠️ {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {data && <LLMTimeline data={data} />}
    </div>
  );
};

export default LLMTimelinePage;
