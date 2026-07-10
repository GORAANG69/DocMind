import React, { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, AlertCircle, Loader, Search, ChevronUp, ChevronDown, X, CaseSensitive } from 'lucide-react';
import { ApiClient } from '../api/client';

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

const DocumentViewer: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Settings from URL & localStorage defaults
  const queryParam = searchParams.get('query') || '';
  const initialCaseSensitive = localStorage.getItem('search_case_sensitive') === 'true';
  const initialWholeWord = localStorage.getItem('search_whole_word') === 'true';

  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState('');

  // Search input & parameters
  const [searchQuery, setSearchQuery] = useState(queryParam);
  const [caseSensitive, setCaseSensitive] = useState(initialCaseSensitive);
  const [wholeWord, setWholeWord] = useState(initialWholeWord);
  const [matchIndex, setMatchIndex] = useState(-1);

  // Parsed data states
  const [pages, setPages] = useState<string[]>([]);
  const [sheets, setSheets] = useState<{ name: string; rows: string[][] }[]>([]);
  const [activeSheet, setActiveSheet] = useState(0);

  // Matches lists
  const [textMatches, setTextMatches] = useState<{ pageIndex: number; start: number; end: number; globalIndex: number }[]>([]);
  const [excelMatches, setExcelMatches] = useState<{ sheetName: string; rowIndex: number; globalIndex: number }[]>([]);

  const searchInputRef = useRef<HTMLInputElement>(null);

  // Load document metadata and text
  useEffect(() => {
    if (!docId) return;
    setLoading(true);
    
    Promise.all([
      ApiClient.getDocumentMetadata(docId),
      ApiClient.getDocumentText(docId)
    ])
      .then(([metadata, extractedText]) => {
        setDoc(metadata);
        setText(extractedText || '');
        setError(null);
      })
      .catch(e => {
        console.error('Failed to load viewer document:', e);
        setError(e.message || 'Document not found');
      })
      .finally(() => setLoading(false));
  }, [docId]);

  const ext = doc ? (doc.filename.split('.').pop() || '').toLowerCase() : '';
  const isPdf = ext === 'pdf';
  const isExcel = ext === 'xlsx' || ext === 'xls' || ext === 'csv';
  const isCode = ext === 'json' || ext === 'txt' || ext === 'log' || ext === 'text' || ext === 'md';

  // Parse text into pages or sheets
  useEffect(() => {
    if (!text) {
      setPages([]);
      setSheets([]);
      return;
    }

    if (isExcel) {
      const sheetMap: Record<string, string[][]> = {};
      for (const line of text.split('\n')) {
        if (!line.trim()) continue;
        const parts = line.split('\t');
        const sheetName = parts[0] || (ext === 'csv' ? 'CSV' : 'Sheet1');
        if (!sheetMap[sheetName]) sheetMap[sheetName] = [];
        sheetMap[sheetName].push(parts.slice(1));
      }
      setSheets(Object.entries(sheetMap).map(([name, rows]) => ({ name, rows })));
    } else if (isPdf) {
      // Split PDF by form feed
      setPages(text.split('\f'));
    } else {
      // Single page document
      setPages([text]);
    }
  }, [text, isPdf, isExcel, ext]);

  // Compute search matches
  useEffect(() => {
    if (!searchQuery.trim()) {
      setTextMatches([]);
      setExcelMatches([]);
      setMatchIndex(-1);
      return;
    }

    // Escape regex characters
    let escaped = searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (wholeWord) {
      escaped = `\\b${escaped}\\b`;
    }

    let regex: RegExp;
    try {
      regex = new RegExp(escaped, caseSensitive ? 'g' : 'gi');
    } catch (e) {
      console.error('Invalid search regex:', e);
      return;
    }

    if (isExcel) {
      const list: typeof excelMatches = [];
      let globalIndexCounter = 0;
      sheets.forEach((sheet) => {
        sheet.rows.forEach((row, rowIndex) => {
          const cellValue = row[1] || ''; // Row contains [coordinate, cellValue]
          regex.lastIndex = 0;
          if (regex.test(cellValue)) {
            list.push({
              sheetName: sheet.name,
              rowIndex,
              globalIndex: globalIndexCounter++
            });
          }
        });
      });
      setExcelMatches(list);
      setMatchIndex(list.length > 0 ? 0 : -1);
    } else {
      const list: typeof textMatches = [];
      let globalIndexCounter = 0;
      pages.forEach((pageText, pageIndex) => {
        regex.lastIndex = 0;
        let match;
        while ((match = regex.exec(pageText)) !== null) {
          list.push({
            pageIndex,
            start: match.index,
            end: regex.lastIndex,
            globalIndex: globalIndexCounter++
          });
          if (match.index === regex.lastIndex) {
            regex.lastIndex++;
          }
        }
      });
      setTextMatches(list);
      setMatchIndex(list.length > 0 ? 0 : -1);
    }
  }, [searchQuery, caseSensitive, wholeWord, pages, sheets, isExcel]);

  // Jump to match when matchIndex changes
  useEffect(() => {
    if (matchIndex < 0) return;

    if (isExcel) {
      const currentMatch = excelMatches[matchIndex];
      if (currentMatch) {
        // Switch to the correct sheet tab if needed
        const sheetIdx = sheets.findIndex(s => s.name === currentMatch.sheetName);
        if (sheetIdx >= 0 && sheetIdx !== activeSheet) {
          setActiveSheet(sheetIdx);
        }

        // Delay scroll slightly to allow React sheet render
        setTimeout(() => {
          const el = document.getElementById(`excel-match-${currentMatch.globalIndex}`);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }, 50);
      }
    } else {
      const currentMatch = textMatches[matchIndex];
      if (currentMatch) {
        const el = document.getElementById(`match-${currentMatch.globalIndex}`);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }
  }, [matchIndex, isExcel, excelMatches, textMatches, sheets, activeSheet]);

  // Navigation commands
  const handleNext = () => {
    const count = isExcel ? excelMatches.length : textMatches.length;
    if (count <= 0) return;
    setMatchIndex(prev => (prev + 1) % count);
  };

  const handlePrev = () => {
    const count = isExcel ? excelMatches.length : textMatches.length;
    if (count <= 0) return;
    setMatchIndex(prev => (prev - 1 + count) % count);
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (e.shiftKey) {
        handlePrev();
      } else {
        handleNext();
      }
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setTextMatches([]);
    setExcelMatches([]);
    setMatchIndex(-1);
    searchInputRef.current?.focus();
  };

  const handleDownload = () => {
    if (!docId) return;
    const viewUrl = ApiClient.getDocumentViewUrl(docId);
    const a = document.createElement('a');
    a.href = viewUrl;
    a.download = doc?.filename || 'download';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // HTML Highlight Injector for Text
  const renderHighlightedPage = (pageText: string, pageIndex: number) => {
    const pageMatches = textMatches.filter(m => m.pageIndex === pageIndex);
    if (pageMatches.length === 0) return escapeHtml(pageText);

    let html = '';
    let lastIdx = 0;
    pageMatches.forEach(m => {
      const before = pageText.substring(lastIdx, m.start);
      const matched = pageText.substring(m.start, m.end);
      const isActive = m.globalIndex === matchIndex;

      html += escapeHtml(before);
      html += `<mark id="match-${m.globalIndex}" class="doc-highlight ${isActive ? 'active' : ''}">${escapeHtml(matched)}</mark>`;
      lastIdx = m.end;
    });
    html += escapeHtml(pageText.substring(lastIdx));
    return html;
  };

  // cell highlighter for spreadsheet cells
  const renderHighlightedCell = (cellValue: string, rowIndex: number, sheetName: string) => {
    const match = excelMatches.find(m => m.sheetName === sheetName && m.rowIndex === rowIndex);
    if (!match) return escapeHtml(cellValue);

    // If this is the cell containing the match, we highlight all occurrences in it
    let escaped = searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (wholeWord) escaped = `\\b${escaped}\\b`;
    const regex = new RegExp(`(${escaped})`, caseSensitive ? 'g' : 'gi');
    const isActive = match.globalIndex === matchIndex;

    const htmlValue = escapeHtml(cellValue).replace(regex, (m) => {
      return `<mark id="excel-match-${match.globalIndex}" class="doc-highlight ${isActive ? 'active' : ''}">${m}</mark>`;
    });

    return htmlValue;
  };

  if (loading) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-primary)', color: 'var(--text-secondary)' }}>
        <Loader size={48} style={{ animation: 'spin 1s linear infinite' }} />
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-primary)', gap: '1rem' }}>
        <AlertCircle size={48} color="var(--danger)" />
        <p style={{ color: 'var(--danger)' }}>{error || 'Document not found'}</p>
        <button className="btn btn-secondary" onClick={() => navigate(-1)}><ArrowLeft size={16} /> Go Back</button>
      </div>
    );
  }

  const matchesCount = isExcel ? excelMatches.length : textMatches.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* Search & Tool Bar */}
      <div style={{
        display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '1rem', padding: '0.75rem 1.25rem',
        backgroundColor: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)',
        flexShrink: 0, zIndex: 10,
      }}>
        <button className="btn btn-secondary" style={{ padding: '0.4rem 0.75rem' }} onClick={() => navigate(-1)}>
          <ArrowLeft size={16} /> Back
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden', minWidth: '150px', flex: 1 }}>
          <span style={{ fontWeight: 600, fontSize: '0.95rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {doc.filename}
          </span>
        </div>

        {/* Ctrl+F Search Bar Component */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'var(--bg-tertiary)', padding: '0.25rem 0.5rem', borderRadius: '30px', border: '1px solid var(--border-color)' }}>
          <div style={{ paddingLeft: '0.4rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}>
            <Search size={16} />
          </div>
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Find in document..."
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              width: '180px',
              padding: '0.2rem 0'
            }}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
          />
          {searchQuery && (
            <button onClick={clearSearch} style={{ display: 'flex', alignItems: 'center', color: 'var(--text-secondary)' }} title="Clear search">
              <X size={14} />
            </button>
          )}

          <div style={{ borderLeft: '1px solid var(--border-color)', height: '16px', margin: '0 0.25rem' }}></div>

          {/* Matches Counter */}
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', minWidth: '60px', textAlign: 'center', marginRight: '0.25rem' }}>
            {matchesCount > 0 ? `${matchIndex + 1} of ${matchesCount}` : '0 of 0'}
          </span>

          {/* Option Toggles */}
          <button
            onClick={() => setCaseSensitive(prev => !prev)}
            style={{
              padding: '0.2rem 0.4rem',
              borderRadius: '4px',
              color: caseSensitive ? 'var(--accent-primary)' : 'var(--text-secondary)',
              backgroundColor: caseSensitive ? 'var(--bg-translucent-accent)' : 'transparent',
              display: 'flex',
              alignItems: 'center'
            }}
            title="Case sensitive (Aa)"
          >
            <CaseSensitive size={14} />
          </button>
          
          <button
            onClick={() => setWholeWord(prev => !prev)}
            style={{
              padding: '0.2rem 0.4rem',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: 700,
              fontFamily: 'monospace',
              color: wholeWord ? 'var(--accent-primary)' : 'var(--text-secondary)',
              backgroundColor: wholeWord ? 'var(--bg-translucent-accent)' : 'transparent',
              display: 'flex',
              alignItems: 'center'
            }}
            title="Whole word match (\b)"
          >
            \b
          </button>

          <div style={{ borderLeft: '1px solid var(--border-color)', height: '16px', margin: '0 0.25rem' }}></div>

          {/* Navigation Arrows */}
          <button onClick={handlePrev} disabled={matchesCount <= 0} style={{ color: matchesCount > 0 ? 'var(--text-primary)' : 'var(--text-secondary)', opacity: matchesCount > 0 ? 1 : 0.4 }} title="Previous occurrence (Shift+Enter)">
            <ChevronUp size={16} />
          </button>
          <button onClick={handleNext} disabled={matchesCount <= 0} style={{ color: matchesCount > 0 ? 'var(--text-primary)' : 'var(--text-secondary)', opacity: matchesCount > 0 ? 1 : 0.4 }} title="Next occurrence (Enter)">
            <ChevronDown size={16} />
          </button>
        </div>

        <button
          onClick={handleDownload}
          className="btn btn-secondary"
          style={{ padding: '0.4rem 0.75rem', textDecoration: 'none' }}
          title="Download original file"
        >
          <Download size={16} /> Download
        </button>
      </div>

      {/* Document Display Area */}
      <div style={{ flex: 1, overflow: 'auto', padding: isExcel ? 0 : '2rem 1rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {isExcel ? (
          /* Spreadsheet Tabbed Table Render */
          <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
            {sheets.length > 1 && (
              <div style={{ display: 'flex', gap: '4px', padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                {sheets.map((s, i) => (
                  <button key={i} onClick={() => setActiveSheet(i)}
                    style={{
                      padding: '0.35rem 1.25rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', cursor: 'pointer',
                      backgroundColor: i === activeSheet ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                      color: i === activeSheet ? '#ffffff' : 'var(--text-secondary)', fontWeight: i === activeSheet ? 600 : 400
                    }}>
                    {s.name}
                  </button>
                ))}
              </div>
            )}
            <div style={{ overflow: 'auto', flexGrow: 1 }}>
              {sheets[activeSheet] ? (
                <table style={{ borderCollapse: 'collapse', minWidth: '100%', fontSize: '0.85rem' }}>
                  <tbody>
                    {sheets[activeSheet].rows.map((row, ri) => (
                      <tr key={ri} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.4rem 0.75rem', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', fontWeight: 500, width: '60px', backgroundColor: 'var(--bg-secondary)', textAlign: 'center' }}>
                          {row[0]}
                        </td>
                        <td
                          style={{ padding: '0.4rem 0.75rem', border: '1px solid var(--border-color)', whiteSpace: 'pre-wrap', verticalAlign: 'top' }}
                          dangerouslySetInnerHTML={{ __html: renderHighlightedCell(row[1] || '', ri, sheets[activeSheet].name) }}
                        />
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No sheet data loaded.</div>
              )}
            </div>
          </div>
        ) : (
          /* Multi-Page High-Fidelity Text Reader (PDF, DOCX, TXT) */
          <div style={{
            width: '100%', maxWidth: '850px', display: 'flex', flexDirection: 'column', gap: '2rem',
            fontFamily: isCode ? 'Consolas, Monaco, "Andale Mono", monospace' : 'Georgia, serif',
            fontSize: isCode ? '0.9rem' : '1.1rem',
            lineHeight: 1.7
          }}>
            {pages.length > 0 ? (
              pages.map((pageText, pageIdx) => (
                <div
                  key={pageIdx}
                  className="page-container"
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '2.5rem',
                    boxShadow: 'var(--shadow-md)',
                    minHeight: isPdf ? '600px' : 'auto',
                    position: 'relative'
                  }}
                >
                  {isPdf && (
                    <div style={{
                      position: 'absolute', top: '1rem', right: '1.5rem',
                      fontSize: '0.75rem', color: 'var(--text-secondary)',
                      backgroundColor: 'var(--bg-tertiary)', padding: '0.2rem 0.6rem',
                      borderRadius: '4px', border: '1px solid var(--border-color)',
                      fontWeight: 600, userSelect: 'none'
                    }}>
                      Page {pageIdx + 1} of {pages.length}
                    </div>
                  )}
                  <div
                    style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginTop: isPdf ? '1.5rem' : '0' }}
                    dangerouslySetInnerHTML={{ __html: renderHighlightedPage(pageText, pageIdx) }}
                  />
                </div>
              ))
            ) : (
              <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-secondary)', width: '100%' }}>
                <p>No document text content available.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Global CSS styles for active highlights */}
      <style>{`
        .doc-highlight {
          background-color: rgba(99, 102, 241, 0.25);
          color: inherit;
          border-radius: 2px;
          padding: 0 1px;
          transition: background-color 0.2s, box-shadow 0.2s;
        }
        .doc-highlight.active {
          background-color: #f59e0b !important;
          color: #000000 !important;
          box-shadow: 0 0 8px #f59e0b;
        }
        .page-container {
          transition: all 0.2s;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default DocumentViewer;
