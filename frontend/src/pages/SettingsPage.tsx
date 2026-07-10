import { useState, useEffect } from 'react';
import { Settings, Shield, Search, Upload, RefreshCw, Trash2, Info, CheckCircle2, AlertCircle } from 'lucide-react';
import { ApiClient } from '../api/client';

const SettingsPage = () => {
  // Appearance settings
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'system');
  
  // Search settings
  const [caseSensitive, setCaseSensitive] = useState(() => localStorage.getItem('search_case_sensitive') === 'true');
  const [wholeWord, setWholeWord] = useState(() => localStorage.getItem('search_whole_word') === 'true');
  const [autoHighlight, setAutoHighlight] = useState(() => localStorage.getItem('search_auto_highlight') !== 'false'); // Default to true

  // Upload settings
  const [autoIndex, setAutoIndex] = useState(() => localStorage.getItem('upload_auto_index') !== 'false'); // Default to true
  const [deleteOriginal, setDeleteOriginal] = useState(() => localStorage.getItem('upload_delete_original') === 'true');

  // Stats settings
  const [stats, setStats] = useState({ totalDocuments: 0, totalSize: 0 });
  const [loadingStats, setLoadingStats] = useState(true);

  // Operation states
  const [rebuilding, setRebuilding] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Fetch stats from backend
  const fetchStats = async () => {
    try {
      const data = await ApiClient.getStats();
      setStats({
        totalDocuments: data.totalDocuments ?? 0,
        totalSize: data.totalSize ?? 0,
      });
    } catch (error) {
      console.error('Failed to load settings stats:', error);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  // Update theme setting
  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    window.dispatchEvent(new Event('theme-changed'));
  };

  // Sync checkboxes to localStorage
  useEffect(() => {
    localStorage.setItem('search_case_sensitive', String(caseSensitive));
  }, [caseSensitive]);

  useEffect(() => {
    localStorage.setItem('search_whole_word', String(wholeWord));
  }, [wholeWord]);

  useEffect(() => {
    localStorage.setItem('search_auto_highlight', String(autoHighlight));
  }, [autoHighlight]);

  useEffect(() => {
    localStorage.setItem('upload_auto_index', String(autoIndex));
  }, [autoIndex]);

  useEffect(() => {
    localStorage.setItem('upload_delete_original', String(deleteOriginal));
  }, [deleteOriginal]);

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleRebuildIndex = async () => {
    if (!window.confirm('Are you sure you want to rebuild the search index? This will scan and re-extract all text from your documents.')) return;
    setRebuilding(true);
    setNotification(null);
    try {
      const res = await ApiClient.rebuildIndex();
      showNotification('success', res.message || 'Search index rebuilt successfully.');
      await fetchStats();
    } catch (err: any) {
      showNotification('error', err.message || 'Failed to rebuild search index.');
    } finally {
      setRebuilding(false);
    }
  };

  const handleClearCache = async () => {
    if (!window.confirm('Clear all search history and chat histories? This cannot be undone.')) return;
    setClearing(true);
    setNotification(null);
    try {
      await ApiClient.clearSearchCache();
      showNotification('success', 'Search cache and histories cleared successfully.');
    } catch (err: any) {
      showNotification('error', err.message || 'Failed to clear search cache.');
    } finally {
      setClearing(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="content-area" style={{ maxWidth: '850px', margin: '0 auto' }}>
      <div className="top-bar" style={{ margin: '-2rem -2rem 2rem -2rem' }}>
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Settings size={22} className="text-primary" /> Settings
        </h1>
      </div>

      {notification && (
        <div style={{
          padding: '1rem',
          borderRadius: 'var(--radius-md)',
          marginBottom: '1.5rem',
          backgroundColor: notification.type === 'success' ? 'var(--bg-translucent-success)' : 'var(--bg-translucent-danger)',
          color: notification.type === 'success' ? 'var(--success)' : 'var(--danger)',
          border: `1px solid ${notification.type === 'success' ? 'var(--success)' : 'var(--danger)'}40`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.95rem'
        }}>
          {notification.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          {notification.message}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {/* Appearance Settings */}
        <section className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Shield size={18} color="var(--accent-primary)" /> Appearance
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Theme</label>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              {['dark', 'light', 'system'].map((t) => (
                <button
                  key={t}
                  onClick={() => handleThemeChange(t)}
                  className="btn"
                  style={{
                    flex: 1,
                    padding: '0.6rem',
                    textTransform: 'capitalize',
                    border: '1px solid var(--border-color)',
                    backgroundColor: theme === t ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                    color: theme === t ? '#ffffff' : 'var(--text-primary)',
                    fontWeight: theme === t ? 600 : 400,
                    borderRadius: 'var(--radius-md)'
                  }}
                >
                  {t === 'system' ? 'System Default' : t + ' Mode'}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Search Options */}
        <section className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Search size={18} color="var(--accent-primary)" /> Search Defaults
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={caseSensitive}
                onChange={(e) => setCaseSensitive(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
              />
              <span style={{ fontSize: '0.95rem' }}>Case Sensitive Search</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={wholeWord}
                onChange={(e) => setWholeWord(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
              />
              <span style={{ fontSize: '0.95rem' }}>Whole Word Search</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={autoHighlight}
                onChange={(e) => setAutoHighlight(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
              />
              <span style={{ fontSize: '0.95rem' }}>Auto Highlight Matches</span>
            </label>
          </div>
        </section>

        {/* Upload Settings */}
        <section className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Upload size={18} color="var(--accent-primary)" /> Upload Settings
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={autoIndex}
                onChange={(e) => setAutoIndex(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
              />
              <span style={{ fontSize: '0.95rem' }}>Automatically index uploaded documents</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={deleteOriginal}
                onChange={(e) => setDeleteOriginal(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
              />
              <span style={{ fontSize: '0.95rem' }}>Delete original uploaded file after indexing</span>
            </label>
          </div>
        </section>

        {/* Application Stats & Data */}
        <section className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Info size={18} color="var(--accent-primary)" /> Application Info & Data
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Version</div>
              <div style={{ fontSize: '1rem', fontWeight: 600 }}>v1.0.0</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Build Number</div>
              <div style={{ fontSize: '1rem', fontWeight: 600 }}>2026.07.10.01</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Storage Used</div>
              <div style={{ fontSize: '1rem', fontWeight: 600 }}>{loadingStats ? 'Loading...' : formatSize(stats.totalSize)}</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Total Indexed Documents</div>
              <div style={{ fontSize: '1rem', fontWeight: 600 }}>{loadingStats ? 'Loading...' : stats.totalDocuments}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
            <button
              onClick={handleRebuildIndex}
              disabled={rebuilding}
              className="btn btn-secondary"
              style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', padding: '0.65rem' }}
            >
              <RefreshCw size={16} className={rebuilding ? 'spin' : ''} style={{ animation: rebuilding ? 'spin 1.5s linear infinite' : 'none' }} />
              {rebuilding ? 'Rebuilding Index...' : 'Rebuild Search Index'}
            </button>
            <button
              onClick={handleClearCache}
              disabled={clearing}
              className="btn"
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                padding: '0.65rem',
                backgroundColor: 'var(--bg-translucent-danger)',
                color: 'var(--danger)',
                border: '1px solid rgba(239, 68, 68, 0.3)'
              }}
            >
              <Trash2 size={16} />
              {clearing ? 'Clearing Cache...' : 'Clear Search Cache'}
            </button>
          </div>
        </section>

        {/* About Card */}
        <section className="card" style={{ padding: '1.5rem', backgroundColor: 'var(--bg-tertiary)', border: 'none' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.75rem' }}>About DocMind</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '0.5rem' }}>
            DocMind is a state-of-the-art local document intelligence workspace. Built for instant searching, cataloging, and analyzing large document libraries.
          </p>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <strong>Supported File Formats:</strong>
            <span>PDF, DOC, DOCX, XLS, XLSX, CSV, JSON</span>
          </div>
        </section>
      </div>
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default SettingsPage;
