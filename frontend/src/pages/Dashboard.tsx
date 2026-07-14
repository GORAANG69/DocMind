import { useState, useEffect, useCallback } from 'react';
import { FileText, Database, ArrowRight, LayoutDashboard, FileSpreadsheet, Code, Table, Search, AlertCircle, RefreshCw } from 'lucide-react';
import { ApiClient } from '../api/client';
import { useNavigate } from 'react-router-dom';

interface Stats {
  totalDocuments: number;
  totalSize: number;
  pdfCount: number;
  docxCount: number;
  xlsxCount: number;
  csvCount: number;
  jsonCount: number;
}

const EMPTY_STATS: Stats = {
  totalDocuments: 0,
  totalSize: 0,
  pdfCount: 0,
  docxCount: 0,
  xlsxCount: 0,
  csvCount: 0,
  jsonCount: 0,
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats>(EMPTY_STATS);
  const [loading, setLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setStatsError(null);
    try {
      const data = await ApiClient.getStats();
      setStats({
        totalDocuments: data.totalDocuments ?? data.total_documents ?? 0,
        totalSize:      data.totalSize      ?? data.total_size      ?? 0,
        pdfCount:       data.pdfCount       ?? data.pdf_count       ?? 0,
        docxCount:      data.docxCount      ?? data.docx_count      ?? 0,
        xlsxCount:      data.xlsxCount      ?? data.xlsx_count      ?? 0,
        csvCount:       data.csvCount       ?? data.csv_count       ?? 0,
        jsonCount:      data.jsonCount      ?? data.json_count       ?? 0,
      });
    } catch (error: any) {
      console.error('Failed to fetch stats:', error);
      // Keep previously loaded stats visible — show an error banner instead of zeroing
      setStatsError('Could not refresh statistics. The backend may be unavailable.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();

    // Refresh when Documents page signals an upload / delete
    const handleStatsChanged = () => fetchStats();
    window.addEventListener('docmind:stats-changed', handleStatsChanged);

    // No polling — rely solely on the event and initial fetch
    return () => {
      window.removeEventListener('docmind:stats-changed', handleStatsChanged);
    };
  }, [fetchStats]);

  const formatSize = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="content-area">
      <div className="top-bar" style={{ margin: '-2rem -2rem 2rem -2rem' }}>
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <LayoutDashboard size={22} color="var(--accent-primary)" /> Dashboard
        </h1>
        <button
          className="btn btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}
          onClick={fetchStats}
          disabled={loading}
          title="Refresh statistics"
        >
          <RefreshCw size={14} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {/* Error banner — shown instead of silently zeroing stats */}
      {statsError && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.75rem',
          padding: '0.85rem 1.25rem',
          backgroundColor: 'rgba(239,68,68,0.08)',
          border: '1px solid rgba(239,68,68,0.2)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--danger)',
          fontSize: '0.9rem',
          marginBottom: '1.5rem',
        }}>
          <AlertCircle size={16} />
          <span style={{ flex: 1 }}>{statsError}</span>
          <button
            onClick={fetchStats}
            style={{ color: 'var(--danger)', textDecoration: 'underline', fontSize: '0.85rem' }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Stats Grid */}
      <div className="dashboard-grid" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="stat-card">
            <div className="stat-icon" style={{ backgroundColor: 'rgba(99, 102, 241, 0.12)' }}>
              <FileText size={24} color="var(--accent-primary)" />
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
            <div className="stat-icon" style={{ backgroundColor: 'rgba(99, 102, 241, 0.12)' }}>
              <Database size={24} color="var(--accent-primary)" />
            </div>
            <div className="stat-info">
              <h3>Total Storage Size</h3>
              {loading ? (
                <div className="dot-flashing" style={{ marginTop: '1rem' }}></div>
              ) : (
                <p>{formatSize(stats.totalSize)}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Breakdowns Title */}
      <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '1.25rem' }}>File Formats Breakdown</h2>

      {/* Breakdown Grid */}
      <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '1.25rem', marginBottom: '3rem' }}>
        {/* PDF Card */}
        <div className="card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.5rem', backgroundColor: 'rgba(239, 68, 68, 0.12)', borderRadius: 'var(--radius-md)' }}>
            <FileText size={20} color="#ef4444" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 500 }}>PDFs</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.15rem' }}>
              {loading ? '…' : stats.pdfCount}
            </div>
          </div>
        </div>

        {/* DOCX Card */}
        <div className="card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.5rem', backgroundColor: 'rgba(59, 130, 246, 0.12)', borderRadius: 'var(--radius-md)' }}>
            <FileText size={20} color="#3b82f6" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 500 }}>DOCX</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.15rem' }}>
              {loading ? '…' : stats.docxCount}
            </div>
          </div>
        </div>

        {/* XLSX Card */}
        <div className="card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.5rem', backgroundColor: 'rgba(16, 185, 129, 0.12)', borderRadius: 'var(--radius-md)' }}>
            <FileSpreadsheet size={20} color="#10b981" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 500 }}>XLSX</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.15rem' }}>
              {loading ? '…' : stats.xlsxCount}
            </div>
          </div>
        </div>

        {/* CSV Card */}
        <div className="card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.5rem', backgroundColor: 'rgba(20, 184, 166, 0.12)', borderRadius: 'var(--radius-md)' }}>
            <Table size={20} color="#14b8a6" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 500 }}>CSV</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.15rem' }}>
              {loading ? '…' : stats.csvCount}
            </div>
          </div>
        </div>

        {/* JSON Card */}
        <div className="card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.5rem', backgroundColor: 'rgba(139, 92, 246, 0.12)', borderRadius: 'var(--radius-md)' }}>
            <Code size={20} color="#8b5cf6" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 500 }}>JSON</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.15rem' }}>
              {loading ? '…' : stats.jsonCount}
            </div>
          </div>
        </div>
      </div>

      <h2 style={{ marginBottom: '1.5rem', fontSize: '1.2rem', fontWeight: 600 }}>Quick Actions</h2>
      
      <div className="dashboard-grid">
        <div 
          className="card" 
          style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', transition: 'all 0.2s' }}
          onClick={() => navigate('/documents')}
          onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
          onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
        >
          <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-translucent-accent)', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
            <FileText size={24} color="var(--accent-primary)" />
          </div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Upload Documents</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', flexGrow: 1 }}>
            Add new PDFs, Word docs, Excel sheets, CSV records, or JSON datasets to your workspace.
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
          <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-translucent-accent)', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
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

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default Dashboard;
