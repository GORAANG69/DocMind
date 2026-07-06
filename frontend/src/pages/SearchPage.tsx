import React, { useState } from 'react';
import { Search as SearchIcon, FileText, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';

const SearchPage = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    setError(null);

    try {
      // ApiClient.search now returns a plain array directly
      const data = await ApiClient.search(query);
      setResults(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.error('Search error:', err);
      setError(err.message || 'Search failed. Please try again.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenResult = (result: any) => {
    const params = new URLSearchParams({ query });
    if (result.page_number) params.set('page', String(result.page_number));
    navigate(`/viewer/${result.doc_id}?${params.toString()}`);
  };

  const getFileIcon = (fileType: string, filename?: string) => {
    const ext = (fileType || filename?.split('.').pop() || '').replace('.', '').toLowerCase();
    if (ext === 'pdf') return <FileText size={16} color="#ef4444" />;
    if (ext === 'docx' || ext === 'doc') return <FileText size={16} color="#3b82f6" />;
    if (ext === 'xlsx' || ext === 'xls') return <FileText size={16} color="#10b981" />;
    return <FileText size={16} />;
  };

  const highlightSnippet = (snippet: string, q: string) => {
    if (!q.trim() || !snippet) return snippet;
    const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const parts = snippet.split(new RegExp(`(${escaped})`, 'gi'));
    return (
      <span>
        {parts.map((part, i) =>
          part.toLowerCase() === q.toLowerCase()
            ? <mark key={i} style={{ backgroundColor: 'rgba(99,102,241,0.35)', color: 'inherit', borderRadius: '2px', padding: '0 2px' }}>{part}</mark>
            : part
        )}
      </span>
    );
  };

  return (
    <div className="content-area">
      <div className="search-container">
        <h1 className="page-title" style={{ textAlign: 'center', marginBottom: '2rem', fontSize: '2.5rem' }}>
          Full-Text Search
        </h1>

        <form className="search-bar" onSubmit={handleSearch}>
          <div style={{ position: 'relative', flexGrow: 1 }}>
            <div style={{ position: 'absolute', left: '1.25rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }}>
              <SearchIcon size={20} />
            </div>
            <input
              type="text"
              className="input"
              placeholder="Search across all your documents..."
              style={{ paddingLeft: '3rem', fontSize: '1.1rem', padding: '1rem 1.5rem 1rem 3rem', borderRadius: '30px' }}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading || !query.trim()} style={{ borderRadius: '30px', padding: '0 2rem', fontSize: '1.1rem' }}>
            {loading ? <div className="loader" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div> : 'Search'}
          </button>
        </form>

        {error && (
          <div style={{ padding: '1rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius-md)', marginBottom: '2rem', textAlign: 'center' }}>
            {error}
          </div>
        )}

        <div className="search-results">
          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
              <div className="dot-flashing" style={{ margin: '0 auto 1.5rem auto' }}></div>
              <p style={{ color: 'var(--text-secondary)' }}>Searching documents…</p>
            </div>
          ) : searched && results.length === 0 ? (
            <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              <SearchIcon size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
              <p style={{ fontSize: '1.1rem' }}>No results found for "{query}".</p>
              <p>Try different keywords or check your spelling.</p>
            </div>
          ) : (
            <>
              {searched && results.length > 0 && (
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                  {results.length} result{results.length !== 1 ? 's' : ''} for "<strong style={{ color: 'var(--text-primary)' }}>{query}</strong>"
                </p>
              )}
              {results.map((result, idx) => (
                <div key={idx} className="card result-card" style={{ padding: '1.5rem', marginBottom: '1rem', cursor: 'pointer' }} onClick={() => handleOpenResult(result)}>
                  <div className="result-header" style={{ marginBottom: '0.75rem' }}>
                    <h3 className="result-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1rem' }}>
                      {getFileIcon(result.file_type, result.filename)}
                      {result.filename}
                      {result.page_number && (
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 400 }}>— Page {result.page_number}</span>
                      )}
                      {result.sheet_name && (
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 400 }}>— Sheet: {result.sheet_name} {result.cell_ref}</span>
                      )}
                    </h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--success)', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '0.2rem 0.6rem', borderRadius: '4px', fontWeight: 600 }}>
                        {result.match_count} match{result.match_count !== 1 ? 'es' : ''}
                      </span>
                      <ExternalLink size={14} color="var(--text-secondary)" />
                    </div>
                  </div>

                  <div className="result-snippet" style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                    {result.snippet ? highlightSnippet(result.snippet, query) : 'No text preview available.'}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchPage;
