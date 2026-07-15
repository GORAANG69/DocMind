import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search as SearchIcon, FileText, ExternalLink, ChevronDown, ChevronRight,
  Clock, X, Trash2, FileSpreadsheet, Code, Table
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';

// ─── Types ────────────────────────────────────────────────────────────────────

interface PageMatch {
  page_number: number;
  match_count: number;
  snippet: string;
  positions: number[];
}

interface SheetMatch {
  sheet_name: string;
  cell_ref: string;
  match_count: number;
  snippet: string;
  positions: number[];
}

interface GroupedSearchResult {
  doc_id: string;
  filename: string;
  file_type: string;
  original_filename: string;
  total_matches: number;
  pages: PageMatch[];
  sheets: SheetMatch[];
  snippet: string;
}

interface SearchHistoryEntry {
  query: string;
  timestamp: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const SESSION_KEY_QUERY   = 'docmind_search_query';
const SESSION_KEY_RESULTS = 'docmind_search_results';
const SESSION_KEY_SCROLL  = 'docmind_search_scroll';
const SESSION_KEY_EXPANDED = 'docmind_search_expanded';
const LOCAL_KEY_HISTORY   = 'docmind_search_history';
const MAX_HISTORY         = 10;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function loadHistory(): SearchHistoryEntry[] {
  try {
    return JSON.parse(localStorage.getItem(LOCAL_KEY_HISTORY) || '[]');
  } catch {
    return [];
  }
}

function saveHistory(entries: SearchHistoryEntry[]) {
  localStorage.setItem(LOCAL_KEY_HISTORY, JSON.stringify(entries));
}

function pushHistory(query: string) {
  const trimmed = query.trim();
  if (!trimmed) return;
  const entries = loadHistory().filter(e => e.query !== trimmed);
  entries.unshift({ query: trimmed, timestamp: Date.now() });
  saveHistory(entries.slice(0, MAX_HISTORY));
}

function loadSession<T>(key: string, fallback: T): T {
  try {
    const raw = sessionStorage.getItem(key);
    return raw !== null ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

/**
 * Load cached search results, but ONLY if every item in the array has the
 * current grouped shape (doc_id + pages array).  If anything looks like the
 * old flat per-page format (no pages field), discard the whole cache so the
 * component never tries to call .map() on undefined and crash.
 */
function loadGroupedResults(): GroupedSearchResult[] {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY_RESULTS);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    // Validate shape: every entry must have doc_id and pages/sheets arrays
    const isValid = parsed.every(
      (r: any) =>
        r &&
        typeof r.doc_id === 'string' &&
        Array.isArray(r.pages) &&
        Array.isArray(r.sheets)
    );
    if (!isValid) {
      // Stale format — nuke the cache
      sessionStorage.removeItem(SESSION_KEY_RESULTS);
      return [];
    }
    return parsed as GroupedSearchResult[];
  } catch {
    sessionStorage.removeItem(SESSION_KEY_RESULTS);
    return [];
  }
}

// ─── File icon helper ─────────────────────────────────────────────────────────

function getFileIcon(fileType: string, filename?: string) {
  const ext = (fileType || filename?.split('.').pop() || '').replace('.', '').toLowerCase();
  if (ext === 'pdf')                    return <FileText size={16} color="#ef4444" />;
  if (ext === 'docx' || ext === 'doc')  return <FileText size={16} color="#3b82f6" />;
  if (ext === 'xlsx' || ext === 'xls') return <FileSpreadsheet size={16} color="#10b981" />;
  if (ext === 'csv')                    return <Table size={16} color="#14b8a6" />;
  if (ext === 'json')                   return <Code size={16} color="#8b5cf6" />;
  return <FileText size={16} />;
}

// ─── Snippet highlight ────────────────────────────────────────────────────────

function HighlightedSnippet({ snippet, query }: { snippet: string; query: string }) {
  if (!query.trim() || !snippet) return <span>{snippet}</span>;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const parts = snippet.split(new RegExp(`(${escaped})`, 'gi'));
  return (
    <span>
      {parts.map((part, i) =>
        part.toLowerCase() === query.toLowerCase()
          ? <mark key={i} style={{ backgroundColor: 'rgba(99,102,241,0.35)', color: 'inherit', borderRadius: '2px', padding: '0 2px' }}>{part}</mark>
          : part
      )}
    </span>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

const SearchPage = () => {
  const navigate = useNavigate();
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  // Restore from sessionStorage on first mount.
  // loadGroupedResults() validates the cached shape — old flat-format results
  // are discarded rather than crash the render loop.
  const [query,    setQuery]    = useState<string>(() => loadSession(SESSION_KEY_QUERY, ''));
  const [results,  setResults]  = useState<GroupedSearchResult[]>(loadGroupedResults);
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set(loadSession<string[]>(SESSION_KEY_EXPANDED, [])));
  const [searched, setSearched] = useState(() => loadSession(SESSION_KEY_QUERY, '') !== '');
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);

  // History dropdown
  const [history,         setHistory]         = useState<SearchHistoryEntry[]>(loadHistory);
  const [showHistory,     setShowHistory]      = useState(false);
  const [historyFilter,   setHistoryFilter]    = useState('');

  // Persist state to sessionStorage whenever it changes
  useEffect(() => {
    sessionStorage.setItem(SESSION_KEY_QUERY, JSON.stringify(query));
  }, [query]);

  useEffect(() => {
    sessionStorage.setItem(SESSION_KEY_RESULTS, JSON.stringify(results));
  }, [results]);

  useEffect(() => {
    sessionStorage.setItem(SESSION_KEY_EXPANDED, JSON.stringify([...expanded]));
  }, [expanded]);

  // Save scroll position on unmount, restore on mount
  useEffect(() => {
    const savedScroll = loadSession(SESSION_KEY_SCROLL, 0);
    if (savedScroll > 0 && scrollRef.current) {
      // Defer to after paint so the DOM is populated
      requestAnimationFrame(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = savedScroll;
      });
    }

    return () => {
      if (scrollRef.current) {
        sessionStorage.setItem(SESSION_KEY_SCROLL, JSON.stringify(scrollRef.current.scrollTop));
      }
    };
  }, []);

  // Close history dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('[data-search-container]')) {
        setShowHistory(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSearch = useCallback(async (searchQuery: string) => {
    const q = searchQuery.trim();
    if (!q) return;

    setShowHistory(false);
    setLoading(true);
    setSearched(true);
    setError(null);

    try {
      const data = await ApiClient.search(q);
      const grouped: GroupedSearchResult[] = Array.isArray(data) ? data : [];
      setResults(grouped);
      setExpanded(new Set()); // collapse all cards on new search
      // Persist to history
      pushHistory(q);
      setHistory(loadHistory());
      // Reset scroll
      sessionStorage.setItem(SESSION_KEY_SCROLL, '0');
      if (scrollRef.current) scrollRef.current.scrollTop = 0;
    } catch (err: any) {
      console.error('Search error:', err);
      setError(err.message || 'Search failed. Please try again.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    handleSearch(query);
  };

  const handleHistorySelect = (q: string) => {
    setQuery(q);
    setShowHistory(false);
    handleSearch(q);
  };

  const handleRemoveHistory = (e: React.MouseEvent, q: string) => {
    e.stopPropagation();
    const updated = loadHistory().filter(h => h.query !== q);
    saveHistory(updated);
    setHistory(updated);
  };

  const handleClearHistory = () => {
    saveHistory([]);
    setHistory([]);
    setShowHistory(false);
  };

  const toggleExpanded = (docId: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(docId)) next.delete(docId);
      else next.add(docId);
      return next;
    });
  };

  const handleOpenResult = (docId: string, pageNumber?: number) => {
    const params = new URLSearchParams({ query, from: 'search' });
    if (pageNumber) params.set('page', String(pageNumber));
    navigate(`/viewer/${docId}?${params.toString()}`);
  };

  const filteredHistory = history.filter(h =>
    h.query.toLowerCase().includes(historyFilter.toLowerCase())
  );

  const totalResults = results.length;

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="content-area" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '2rem', paddingTop: '1rem' }}>
        <h1 className="page-title" style={{ fontSize: '2.25rem', marginBottom: '0.5rem' }}>
          Full-Text Search
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Search across all indexed documents instantly
        </p>
      </div>

      {/* Search bar + history dropdown */}
      <div data-search-container style={{ position: 'relative', maxWidth: '700px', margin: '0 auto 2rem auto', width: '100%' }}>
        <form className="search-bar" onSubmit={handleSubmit} style={{ position: 'relative' }}>
          <div style={{ position: 'relative', flexGrow: 1 }}>
            <div style={{ position: 'absolute', left: '1.25rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)', zIndex: 1 }}>
              <SearchIcon size={20} />
            </div>
            <input
              ref={inputRef}
              type="text"
              className="input"
              placeholder="Search across all your documents..."
              style={{ paddingLeft: '3.25rem', paddingRight: query ? '2.5rem' : '1.5rem', fontSize: '1.05rem', padding: '0.9rem 1.5rem 0.9rem 3.25rem', borderRadius: '30px' }}
              value={query}
              onChange={e => {
                setQuery(e.target.value);
                setHistoryFilter(e.target.value);
              }}
              onFocus={() => setShowHistory(true)}
              autoFocus
            />
            {query && (
              <button
                type="button"
                onClick={() => { setQuery(''); setHistoryFilter(''); inputRef.current?.focus(); }}
                style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}
                title="Clear"
              >
                <X size={16} />
              </button>
            )}
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !query.trim()}
            style={{ borderRadius: '30px', padding: '0 2rem', fontSize: '1.05rem' }}
          >
            {loading
              ? <div className="loader" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div>
              : 'Search'}
          </button>
        </form>

        {/* History dropdown */}
        {showHistory && filteredHistory.length > 0 && (
          <div style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            right: 0,
            zIndex: 100,
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-lg)',
            overflow: 'hidden',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem 1rem', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Recent Searches
              </span>
              <button
                onClick={handleClearHistory}
                style={{ fontSize: '0.75rem', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
              >
                <Trash2 size={11} /> Clear all
              </button>
            </div>
            {filteredHistory.map((entry, i) => (
              <div
                key={i}
                onClick={() => handleHistorySelect(entry.query)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.6rem 1rem',
                  cursor: 'pointer',
                  borderBottom: i < filteredHistory.length - 1 ? '1px solid var(--border-color)' : 'none',
                  transition: 'background-color 0.15s',
                }}
                onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--bg-translucent-hover)')}
                onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
              >
                <Clock size={14} color="var(--text-secondary)" style={{ flexShrink: 0 }} />
                <span style={{ flex: 1, fontSize: '0.9rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {entry.query}
                </span>
                <button
                  onClick={e => handleRemoveHistory(e, entry.query)}
                  style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', flexShrink: 0 }}
                  title="Remove from history"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Error banner */}
      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'rgba(239,68,68,0.1)', color: 'var(--danger)', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', textAlign: 'center', maxWidth: '700px', margin: '0 auto 1.5rem auto', width: '100%' }}>
          {error}
        </div>
      )}

      {/* Results area */}
      <div ref={scrollRef} className="search-results" style={{ flex: 1, overflowY: 'auto' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <div className="dot-flashing" style={{ margin: '0 auto 1.5rem auto' }}></div>
            <p style={{ color: 'var(--text-secondary)' }}>Searching documents…</p>
          </div>
        ) : searched && results.length === 0 ? (
          <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <SearchIcon size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
            <p style={{ fontSize: '1.1rem' }}>No results found for "<strong>{query}</strong>"</p>
            <p style={{ marginTop: '0.5rem' }}>Try different keywords or check your spelling.</p>
          </div>
        ) : (
          <>
            {searched && results.length > 0 && (
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                <strong style={{ color: 'var(--text-primary)' }}>{totalResults}</strong> document{totalResults !== 1 ? 's' : ''} matched{' '}
                "<strong style={{ color: 'var(--text-primary)' }}>{query}</strong>"
              </p>
            )}

            {results.map(result => {
              // Always treat pages/sheets as arrays — guards against any
              // residual cache entries that slipped through loadGroupedResults.
              const pages   = Array.isArray(result.pages)  ? result.pages  : [];
              const sheets  = Array.isArray(result.sheets) ? result.sheets : [];
              const isExpanded = expanded.has(result.doc_id);
              const isPdf = result.file_type === '.pdf';
              const isSpreadsheet = ['.xlsx', '.xls', '.csv'].includes(result.file_type);
              const hasSubItems = pages.length > 0 || sheets.length > 0;

              return (
                <div
                  key={result.doc_id}
                  className="card result-card"
                  style={{ padding: 0, marginBottom: '1rem', overflow: 'hidden' }}
                >
                  {/* Card Header — always visible */}
                  <div
                    style={{
                      padding: '1.25rem 1.5rem',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '1rem',
                      cursor: hasSubItems ? 'pointer' : 'default',
                    }}
                    onClick={() => hasSubItems ? toggleExpanded(result.doc_id) : handleOpenResult(result.doc_id)}
                  >
                    {/* Expand arrow for multi-page docs */}
                    {hasSubItems && (
                      <div style={{ paddingTop: '2px', color: 'var(--text-secondary)', flexShrink: 0 }}>
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </div>
                    )}

                    <div style={{ flex: 1, minWidth: 0 }}>
                      {/* Filename row */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
                        {getFileIcon(result.file_type, result.filename)}
                        <span style={{ fontWeight: 600, fontSize: '1rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {result.filename || result.original_filename}
                        </span>
                      </div>

                      {/* Match stats row */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <span style={{
                          fontSize: '0.8rem', color: 'var(--success)',
                          backgroundColor: 'rgba(16,185,129,0.12)',
                          padding: '0.2rem 0.6rem', borderRadius: '4px', fontWeight: 600
                        }}>
                          {result.total_matches} match{result.total_matches !== 1 ? 'es' : ''}
                        </span>
                        {isPdf && pages.length > 0 && (
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            across {pages.length} page{pages.length !== 1 ? 's' : ''}
                          </span>
                        )}
                        {isSpreadsheet && sheets.length > 0 && (
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            in {sheets.length} cell{sheets.length !== 1 ? 's' : ''}
                          </span>
                        )}
                      </div>

                      {/* Snippet for non-paged docs */}
                      {!hasSubItems && result.snippet && (
                        <div style={{ marginTop: '0.75rem', fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                          <HighlightedSnippet snippet={result.snippet} query={query} />
                        </div>
                      )}
                    </div>

                    {/* Open button — always on the right */}
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', flexShrink: 0, display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                      onClick={e => { e.stopPropagation(); handleOpenResult(result.doc_id); }}
                      title="Open document"
                    >
                      <ExternalLink size={13} /> Open
                    </button>
                  </div>

                  {/* Expanded Page/Sheet matches */}
                  {isExpanded && hasSubItems && (
                    <div style={{ borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-primary)' }}>
                      {/* PDF pages */}
                      {pages.map((page, i) => (
                        <div
                          key={i}
                          onClick={() => handleOpenResult(result.doc_id, page.page_number)}
                          style={{
                            padding: '0.85rem 1.5rem 0.85rem 3.25rem',
                            borderBottom: i < pages.length - 1 || sheets.length > 0 ? '1px solid var(--border-color)' : 'none',
                            cursor: 'pointer',
                            transition: 'background-color 0.15s',
                          }}
                          onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--bg-translucent-hover)')}
                          onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
                            <span style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 600, minWidth: '60px' }}>
                              Page {page.page_number}
                            </span>
                            <span style={{
                              fontSize: '0.75rem', color: 'var(--success)',
                              backgroundColor: 'rgba(16,185,129,0.12)',
                              padding: '0.15rem 0.5rem', borderRadius: '4px', fontWeight: 600
                            }}>
                              {page.match_count} match{page.match_count !== 1 ? 'es' : ''}
                            </span>
                          </div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                            <HighlightedSnippet snippet={page.snippet ?? ''} query={query} />
                          </div>
                        </div>
                      ))}

                      {/* Spreadsheet cells */}
                      {sheets.map((sheet, i) => (
                        <div
                          key={i}
                          onClick={() => handleOpenResult(result.doc_id)}
                          style={{
                            padding: '0.85rem 1.5rem 0.85rem 3.25rem',
                            borderBottom: i < sheets.length - 1 ? '1px solid var(--border-color)' : 'none',
                            cursor: 'pointer',
                            transition: 'background-color 0.15s',
                          }}
                          onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--bg-translucent-hover)')}
                          onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
                            <span style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                              {sheet.sheet_name}
                            </span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                              {sheet.cell_ref}
                            </span>
                            <span style={{
                              fontSize: '0.75rem', color: 'var(--success)',
                              backgroundColor: 'rgba(16,185,129,0.12)',
                              padding: '0.15rem 0.5rem', borderRadius: '4px', fontWeight: 600
                            }}>
                              {sheet.match_count} match{sheet.match_count !== 1 ? 'es' : ''}
                            </span>
                          </div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                            <HighlightedSnippet snippet={sheet.snippet ?? ''} query={query} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
