import React, { useState, useEffect } from 'react';
import { FileText, Search, Database, ArrowRight } from 'lucide-react';
import { ApiClient } from '../api/client';

import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalDocuments: 0,
    totalIndexed: 0,
    databaseSize: '0 MB'
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await ApiClient.getStats();
        setStats(data || { totalDocuments: 0, totalIndexed: 0, databaseSize: '0 MB' });
      } catch (error) {
        console.error('Failed to fetch stats:', error);
        // Fallback for development if backend isn't ready
        setStats({
          totalDocuments: 12,
          totalIndexed: 12,
          databaseSize: '2.4 MB'
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="content-area">
      <div className="top-bar" style={{ margin: '-2rem -2rem 2rem -2rem' }}>
        <h1 className="page-title">Dashboard</h1>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <div className="stat-card">
            <div className="stat-icon">
              <FileText size={24} />
            </div>
            <div className="stat-info">
              <h3>Total Documents</h3>
              {loading ? (
                <div className="dot-flashing" style={{ marginTop: '1rem' }}></div>
              ) : (
                <p>{stats.totalDocuments}</p>
              )}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="stat-card">
            <div className="stat-icon">
              <Database size={24} />
            </div>
            <div className="stat-info">
              <h3>Indexed Files</h3>
              {loading ? (
                <div className="dot-flashing" style={{ marginTop: '1rem' }}></div>
              ) : (
                <p>{stats.totalIndexed}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <h2 style={{ marginTop: '3rem', marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 600 }}>Quick Actions</h2>
      
      <div className="dashboard-grid">
        <div 
          className="card" 
          style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', transition: 'all 0.2s' }}
          onClick={() => navigate('/documents')}
          onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
          onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
        >
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(99, 102, 241, 0.1)', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
            <FileText size={24} color="var(--accent-primary)" />
          </div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Upload Documents</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', flexGrow: 1 }}>
            Add new PDFs, Word docs, or Excel files to your knowledge base.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-primary)', fontSize: '0.9rem', fontWeight: 500 }}>
            Go to Documents <ArrowRight size={16} />
          </div>
        </div>

        <div 
          className="card" 
          style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', transition: 'all 0.2s' }}
          onClick={() => navigate('/search')}
          onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
          onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
        >
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(99, 102, 241, 0.1)', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
            <Search size={24} color="var(--accent-primary)" />
          </div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Semantic Search</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', flexGrow: 1 }}>
            Search through all your indexed documents instantly.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-primary)', fontSize: '0.9rem', fontWeight: 500 }}>
            Start Searching <ArrowRight size={16} />
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
