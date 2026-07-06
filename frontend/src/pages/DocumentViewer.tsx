import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, AlertCircle, Loader } from 'lucide-react';
import { ApiClient } from '../api/client';

/* ─────────────────────────────────────────────────────────────────────────
   Helpers
───────────────────────────────────────────────────────────────────────── */

function getExt(filename: string): string {
  return (filename.split('.').pop() || '').toLowerCase();
}

function highlightText(text: string, query: string): string {
  if (!query.trim()) return escapeHtml(text);
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return escapeHtml(text).replace(
    new RegExp(`(${escaped})`, 'gi'),
    '<mark class="doc-highlight">$1</mark>'
  );
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* ─────────────────────────────────────────────────────────────────────────
   Sub-viewers
───────────────────────────────────────────────────────────────────────── */

/** PDF viewer — renders the file in a full-height iframe (browser native / PDF.js) */
const PdfViewer: React.FC<{ url: string }> = ({ url }) => (
  <iframe
    src={url}
    title="PDF Viewer"
    style={{ width: '100%', height: '100%', border: 'none', display: 'block', backgroundColor: '#525659' }}
  />
);

/** Plain-text / DOCX viewer — fetches extracted text and renders with highlighting */
const TextViewer: React.FC<{ docId: string; query: string }> = ({ docId, query }) => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    ApiClient.getDocumentText(docId)
      .then(t => { setText(t); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [docId]);

  if (loading) return <div style={centreStyle}><Loader size={40} style={{ animation: 'spin 1s linear infinite' }} /></div>;
  if (error) return <ErrorBlock msg={error} />;

  const html = highlightText(text, query);
  return (
    <div style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto', lineHeight: 1.8, fontFamily: 'Georgia, serif', whiteSpace: 'pre-wrap', overflowWrap: 'break-word' }}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

/** Excel viewer — parses tab-separated extracted text into an HTML table */
const ExcelViewer: React.FC<{ docId: string; query: string }> = ({ docId, query }) => {
  const [sheets, setSheets] = useState<{ name: string; rows: string[][] }[]>([]);
  const [activeSheet, setActiveSheet] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    ApiClient.getDocumentText(docId)
      .then(raw => {
        // Format: each line → "SheetName\tCellRef\tValue"
        const sheetMap: Record<string, string[][]> = {};
        for (const line of raw.split('\n')) {
          if (!line.trim()) continue;
          const parts = line.split('\t');
          const sheetName = parts[0] || 'Sheet1';
          if (!sheetMap[sheetName]) sheetMap[sheetName] = [];
          sheetMap[sheetName].push(parts.slice(1));
        }
        setSheets(Object.entries(sheetMap).map(([name, rows]) => ({ name, rows })));
        setError(null);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [docId]);

  if (loading) return <div style={centreStyle}><Loader size={40} style={{ animation: 'spin 1s linear infinite' }} /></div>;
  if (error) return <ErrorBlock msg={error} />;
  if (!sheets.length) return <div style={centreStyle}>No spreadsheet data found.</div>;

  const current = sheets[activeSheet];
  const highlight = (s: string) => {
    if (!query.trim()) return s;
    const r = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return s.replace(r, '<mark class="doc-highlight">$1</mark>');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Sheet tabs */}
      {sheets.length > 1 && (
        <div style={{ display: 'flex', gap: '4px', padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
          {sheets.map((s, i) => (
            <button key={i} onClick={() => setActiveSheet(i)}
              style={{ padding: '0.3rem 1rem', borderRadius: '4px 4px 0 0', border: '1px solid var(--border-color)', cursor: 'pointer',
                backgroundColor: i === activeSheet ? 'var(--bg-primary)' : 'var(--bg-tertiary)',
                color: i === activeSheet ? 'var(--accent-primary)' : 'var(--text-secondary)', fontWeight: i === activeSheet ? 600 : 400 }}>
              {s.name}
            </button>
          ))}
        </div>
      )}
      <div style={{ overflowX: 'auto', flexGrow: 1 }}>
        <table style={{ borderCollapse: 'collapse', minWidth: '100%', fontSize: '0.85rem' }}>
          <tbody>
            {current.rows.map((row, ri) => (
              <tr key={ri} style={{ borderBottom: '1px solid var(--border-color)' }}>
                {row.map((cell, ci) => (
                  <td key={ci}
                    style={{ padding: '0.4rem 0.75rem', border: '1px solid var(--border-color)', whiteSpace: 'pre', verticalAlign: 'top', minWidth: '80px' }}
                    dangerouslySetInnerHTML={{ __html: highlight(escapeHtml(cell)) }}
                  />
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

/* ─────────────────────────────────────────────────────────────────────────
   Shared helpers
───────────────────────────────────────────────────────────────────────── */
const centreStyle: React.CSSProperties = { display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' };

const ErrorBlock: React.FC<{ msg: string }> = ({ msg }) => (
  <div style={{ ...centreStyle, flexDirection: 'column', gap: '1rem', color: 'var(--danger)' }}>
    <AlertCircle size={40} />
    <p>{msg}</p>
  </div>
);

/* ─────────────────────────────────────────────────────────────────────────
   Main DocumentViewer page
───────────────────────────────────────────────────────────────────────── */
const DocumentViewer: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const query = searchParams.get('query') || '';

  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!docId) return;
    setLoading(true);
    ApiClient.getDocumentMetadata(docId)
      .then(d => { setDoc(d); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [docId]);

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

  const ext = getExt(doc.filename);
  const isPdf = ext === 'pdf';
  const isExcel = ext === 'xlsx' || ext === 'xls';
  const viewUrl = ApiClient.getDocumentViewUrl(docId!);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: 'var(--bg-primary)' }}>
      {/* ── Toolbar ── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1.25rem',
        backgroundColor: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)',
        flexShrink: 0, zIndex: 10,
      }}>
        <button className="btn btn-secondary" style={{ padding: '0.4rem 0.75rem' }} onClick={() => navigate(-1)}>
          <ArrowLeft size={16} /> Back
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden', flex: 1 }}>
          <span style={{ fontWeight: 600, fontSize: '0.95rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {doc.filename}
          </span>
          {query && (
            <span style={{ backgroundColor: 'rgba(99,102,241,0.2)', color: 'var(--accent-primary)', padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.78rem', whiteSpace: 'nowrap', flexShrink: 0 }}>
              Highlighting: "{query}"
            </span>
          )}
        </div>

        <a
          href={viewUrl}
          download={doc.filename}
          className="btn btn-secondary"
          style={{ padding: '0.4rem 0.75rem', textDecoration: 'none' }}
          title="Download original file"
        >
          <Download size={16} /> Download
        </a>
      </div>

      {/* ── Viewer body ── */}
      <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
        {isPdf ? (
          <PdfViewer url={viewUrl} />
        ) : isExcel ? (
          <ExcelViewer docId={docId!} query={query} />
        ) : (
          <TextViewer docId={docId!} query={query} />
        )}
      </div>

      {/* Inject highlight style once */}
      <style>{`
        .doc-highlight {
          background-color: rgba(99,102,241,0.4);
          color: inherit;
          border-radius: 2px;
          padding: 0 2px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default DocumentViewer;
