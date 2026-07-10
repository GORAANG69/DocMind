import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, File as FileIcon, FileText, CheckCircle, AlertCircle, RefreshCw, FolderPlus, FilePlus, Eye, Trash2, CheckSquare, Square, AlertTriangle, FileSpreadsheet, Code, Table } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';

const SUPPORTED_EXTENSIONS = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'json'];

const Documents = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Selection states
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [batchDeleting, setBatchDeleting] = useState(false);

  // Upload queue states
  const [uploading, setUploading] = useState(false);
  const [uploadStats, setUploadStats] = useState({ total: 0, completed: 0, successful: 0, failed: 0 });
  const [currentFilename, setCurrentFilename] = useState('');
  const [remainingTimeText, setRemainingTimeText] = useState('');
  const [failedFilesList, setFailedFilesList] = useState<{ name: string; reason: string }[]>([]);
  const [uploadSummary, setUploadSummary] = useState<{ successful: number; failed: number } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const docs = await ApiClient.getDocuments();
      setDocuments(docs || []);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch documents:', err);
      setError('Failed to load documents. Please check the backend connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const isValidFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    return ext && SUPPORTED_EXTENSIONS.includes(ext);
  };

  // Process folder or multiple file uploads via an async queue
  const processUploadsQueue = async (files: File[]) => {
    const validFiles = files.filter(isValidFile);

    if (validFiles.length === 0) {
      setError('No supported files found. Please upload PDF, DOCX, XLSX, CSV, or JSON files.');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadSummary(null);
    setFailedFilesList([]);
    setUploadStats({ total: validFiles.length, completed: 0, successful: 0, failed: 0 });
    
    let successCount = 0;
    let failCount = 0;
    const failures: { name: string; reason: string }[] = [];
    const startTime = Date.now();

    // Process files sequentially to avoid database locking issues in SQLite
    for (let i = 0; i < validFiles.length; i++) {
      const file = validFiles[i];
      setCurrentFilename(file.name);

      // Estimate remaining time
      if (i > 0) {
        const elapsedMs = Date.now() - startTime;
        const avgTimePerFileMs = elapsedMs / i;
        const remainingFiles = validFiles.length - i;
        const remainingMs = avgTimePerFileMs * remainingFiles;
        
        if (remainingMs > 60000) {
          const mins = Math.floor(remainingMs / 60000);
          const secs = Math.round((remainingMs % 60000) / 1000);
          setRemainingTimeText(`~${mins}m ${secs}s remaining`);
        } else {
          const secs = Math.round(remainingMs / 1000);
          setRemainingTimeText(`~${secs}s remaining`);
        }
      } else {
        setRemainingTimeText('Estimating remaining time...');
      }

      try {
        await ApiClient.uploadDocument(file);
        successCount++;
      } catch (err: any) {
        failCount++;
        failures.push({ name: file.name, reason: err.message || 'Upload failed' });
      }

      setUploadStats({
        total: validFiles.length,
        completed: i + 1,
        successful: successCount,
        failed: failCount,
      });
    }

    setFailedFilesList(failures);
    setUploadSummary({ successful: successCount, failed: failCount });
    setUploading(false);
    setSelectedIds(new Set());
    await fetchDocuments();
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files ? Array.from(event.target.files) : [];
    if (files.length > 0) await processUploadsQueue(files);
    if (event.target) event.target.value = '';
  };

  const getFilesFromEntry = async (entry: any): Promise<File[]> => {
    if (entry.isFile) {
      return new Promise((resolve) => {
        entry.file((file: File) => resolve([file]));
      });
    } else if (entry.isDirectory) {
      const dirReader = entry.createReader();
      return new Promise((resolve) => {
        const allFiles: File[] = [];
        const readBatch = () => {
          dirReader.readEntries(async (entries: any[]) => {
            if (entries.length === 0) {
              resolve(allFiles);
              return;
            }
            const batchFiles = await Promise.all(entries.map((e: any) => getFilesFromEntry(e)));
            allFiles.push(...batchFiles.flat());
            readBatch();
          });
        };
        readBatch();
      });
    }
    return [];
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-active');

    let allFiles: File[] = [];

    if (e.dataTransfer.items) {
      const items = Array.from(e.dataTransfer.items);
      const promises = items.map(item => {
        const entry = item.webkitGetAsEntry();
        if (entry) return getFilesFromEntry(entry);
        return Promise.resolve([]);
      });
      const filesArrays = await Promise.all(promises);
      allFiles = filesArrays.flat();
    } else {
      allFiles = Array.from(e.dataTransfer.files);
    }

    if (allFiles.length > 0) await processUploadsQueue(allFiles);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-active');
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-active');
  };

  // Single deletion
  const handleDelete = async (docId: string, filename: string) => {
    if (!window.confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    setDeletingId(docId);
    try {
      await ApiClient.deleteDocument(docId);
      setDocuments(prev => prev.filter(d => d.id !== docId));
      setSelectedIds(prev => {
        const next = new Set(prev);
        next.delete(docId);
        return next;
      });
    } catch (err: any) {
      setError(err.message || 'Failed to delete document.');
    } finally {
      setDeletingId(null);
    }
  };

  // Multi deletion
  const handleDeleteSelected = async () => {
    const count = selectedIds.size;
    if (count === 0) return;
    if (!window.confirm(`Delete ${count} selected files? This cannot be undone.`)) return;

    setBatchDeleting(true);
    setError(null);
    const ids = Array.from(selectedIds);

    try {
      // Run parallel deletions to delete quickly
      await Promise.all(ids.map(id => ApiClient.deleteDocument(id)));
      setDocuments(prev => prev.filter(d => !selectedIds.has(d.id)));
      setSelectedIds(new Set());
    } catch (err: any) {
      setError(err.message || 'Failed to delete some selected documents.');
      // Refresh state to match server DB state
      const docs = await ApiClient.getDocuments();
      setDocuments(docs || []);
    } finally {
      setBatchDeleting(false);
    }
  };

  const handleSelectToggle = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleOpen = (docId: string) => {
    navigate(`/viewer/${docId}`);
  };

  const handleSelectAll = () => {
    const allIds = documents.map(d => d.id);
    setSelectedIds(new Set(allIds));
  };

  const handleDeselectAll = () => {
    setSelectedIds(new Set());
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return <FileText size={18} color="#ef4444" />;
    if (ext === 'docx' || ext === 'doc') return <FileText size={18} color="#3b82f6" />;
    if (ext === 'xlsx' || ext === 'xls') return <FileSpreadsheet size={18} color="#10b981" />;
    if (ext === 'csv') return <Table size={18} color="#14b8a6" />;
    if (ext === 'json') return <Code size={18} color="#8b5cf6" />;
    return <FileIcon size={18} />;
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes) return '—';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '—';
    try { return new Date(dateStr).toLocaleString(); } catch { return dateStr; }
  };

  const allSelected = documents.length > 0 && selectedIds.size === documents.length;

  return (
    <div className="content-area">
      <div className="top-bar" style={{ margin: '-2rem -2rem 2rem -2rem' }}>
        <h1 className="page-title">Documents</h1>
        <button className="btn btn-secondary" onClick={fetchDocuments} disabled={loading || uploading || batchDeleting}>
          <RefreshCw size={18} style={{ border: 'none', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'var(--bg-translucent-danger)', color: 'var(--danger)', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {/* Upload Complete Summary */}
      {uploadSummary && !uploading && (
        <div style={{ padding: '1.25rem', backgroundColor: 'var(--bg-translucent-success)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)', fontWeight: 600, fontSize: '1.05rem', marginBottom: '0.5rem' }}>
            <CheckCircle size={20} />
            Upload Queue Complete
          </div>
          <div style={{ color: 'var(--text-primary)', marginLeft: '1.75rem', fontSize: '0.95rem' }}>
            Successfully indexed <strong>{uploadSummary.successful}</strong> document{uploadSummary.successful !== 1 ? 's' : ''}.
            {uploadSummary.failed > 0 && <span style={{ color: 'var(--danger)', fontWeight: 500 }}> · {uploadSummary.failed} file{uploadSummary.failed !== 1 ? 's' : ''} failed.</span>}
          </div>

          {failedFilesList.length > 0 && (
            <div style={{ marginTop: '1rem', marginLeft: '1.75rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--warning)', fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                <AlertTriangle size={14} /> Failed Files List:
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, maxHeight: '120px', overflowY: 'auto' }}>
                {failedFilesList.map((fail, index) => (
                  <li key={index} style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', display: 'flex', gap: '0.5rem' }}>
                    <span style={{ color: 'var(--danger)' }}>•</span>
                    <strong style={{ color: 'var(--text-primary)' }}>{fail.name}</strong> ({fail.reason})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Upload Zone */}
      <div
        className="upload-zone"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{ cursor: uploading ? 'default' : 'pointer' }}
      >
        <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.json" multiple onChange={handleFileSelect} />
        <input type="file" ref={folderInputRef} style={{ display: 'none' }} accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.json" multiple {...{ webkitdirectory: '', directory: '' } as any} onChange={handleFileSelect} />

        {uploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1rem' }}>
            <div className="loader" style={{ width: '48px', height: '48px', marginBottom: '1.25rem' }}></div>
            <h3 style={{ marginBottom: '0.5rem', fontSize: '1.2rem', fontWeight: 600 }}>Indexing files: {uploadStats.completed} / {uploadStats.total}</h3>
            
            <div style={{ color: 'var(--accent-primary)', fontWeight: 500, fontSize: '0.9rem', marginBottom: '1rem', maxWidth: '80%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              Current: {currentFilename}
            </div>

            <div style={{ width: '100%', maxWidth: '400px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '10px', height: '8px', overflow: 'hidden', marginBottom: '0.75rem' }}>
              <div style={{ height: '100%', backgroundColor: 'var(--accent-primary)', width: `${(uploadStats.completed / uploadStats.total) * 100}%`, transition: 'width 0.2s ease' }}></div>
            </div>

            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 500, marginBottom: '1rem' }}>
              {remainingTimeText}
            </div>

            <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--success)', fontWeight: 500 }}>{uploadStats.successful} successful</span>
              <span style={{ color: 'var(--danger)', fontWeight: 500 }}>{uploadStats.failed} failed</span>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <UploadCloud className="upload-icon" />
            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.4rem', fontWeight: 600 }}>Drag and drop files or folders here</h2>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()} disabled={batchDeleting}>
                <FilePlus size={18} /> Choose Files
              </button>
              <button className="btn btn-secondary" onClick={() => folderInputRef.current?.click()} disabled={batchDeleting}>
                <FolderPlus size={18} /> Choose Folder
              </button>
            </div>
            <p style={{ color: 'var(--text-secondary)', marginTop: '1.5rem', fontSize: '0.9rem' }}>
              Supports PDF, Word (.docx), Excel (.xlsx), CSV, and JSON
            </p>
          </div>
        )}
      </div>

      {/* Files Table Section */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', flexWrap: 'wrap', gap: '1rem', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Indexed Files</h2>
            <span style={{ backgroundColor: 'var(--bg-translucent-accent)', color: 'var(--accent-primary)', padding: '0.25rem 0.75rem', borderRadius: '20px', fontSize: '0.875rem', fontWeight: 600 }}>
              {documents?.length || 0} Total
            </span>
          </div>

          {documents.length > 0 && (
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                onClick={allSelected ? handleDeselectAll : handleSelectAll}
                disabled={uploading || batchDeleting}
              >
                {allSelected ? 'Deselect All' : 'Select All'}
              </button>
              
              {selectedIds.size > 0 && (
                <button
                  className="btn"
                  style={{
                    padding: '0.4rem 0.8rem',
                    fontSize: '0.85rem',
                    backgroundColor: 'var(--bg-translucent-danger)',
                    color: 'var(--danger)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem'
                  }}
                  onClick={handleDeleteSelected}
                  disabled={uploading || batchDeleting}
                >
                  <Trash2 size={14} /> Delete Selected ({selectedIds.size})
                </button>
              )}
            </div>
          )}
        </div>

        {loading && documents.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div className="dot-flashing" style={{ margin: '0 auto 1.5rem auto' }}></div>
            Loading documents…
          </div>
        ) : documents.length === 0 ? (
          <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <FileText size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
            <p style={{ fontSize: '1.1rem' }}>No documents indexed yet.</p>
            <p>Upload a file or a folder above to get started.</p>
          </div>
        ) : (
          <div className="documents-table-wrapper">
            <table className="documents-table">
              <thead>
                <tr>
                  <th style={{ width: '40px', paddingRight: 0 }}>
                    <button 
                      onClick={() => allSelected ? handleDeselectAll() : handleSelectAll()}
                      style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}
                      title={allSelected ? "Deselect all" : "Select all"}
                    >
                      {allSelected ? <CheckSquare size={18} color="var(--accent-primary)" /> : <Square size={18} />}
                    </button>
                  </th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Indexed On</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => {
                  const isChecked = selectedIds.has(doc.id);
                  return (
                    <tr key={doc.id} className={isChecked ? 'selected-row' : ''} style={{ backgroundColor: isChecked ? 'var(--bg-translucent-accent)' : 'transparent' }}>
                      <td style={{ paddingRight: 0 }}>
                        <button
                          onClick={() => handleSelectToggle(doc.id)}
                          style={{ color: isChecked ? 'var(--accent-primary)' : 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}
                        >
                          {isChecked ? <CheckSquare size={18} /> : <Square size={18} />}
                        </button>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          {getFileIcon(doc.filename)}
                          <span style={{ fontWeight: 500 }}>{doc.filename}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`file-type-badge ${doc.file_type?.replace('.', '') || doc.filename.split('.').pop()?.toLowerCase()}`}>
                          {(doc.file_type || doc.filename.split('.').pop())?.replace('.', '').toUpperCase()}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        {formatFileSize(doc.file_size)}
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        {formatDate(doc.created_at || doc.upload_date)}
                      </td>
                      <td>
                        <span className="status-badge">
                          <CheckCircle size={14} /> Indexed
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                            onClick={() => handleOpen(doc.id)}
                            title="Open document"
                            disabled={batchDeleting || uploading}
                          >
                            <Eye size={14} /> Open
                          </button>
                          <button
                            className="btn"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', backgroundColor: 'var(--bg-translucent-danger)', color: 'var(--danger)', border: '1px solid rgba(239,68,68,0.2)' }}
                            onClick={() => handleDelete(doc.id, doc.filename)}
                            disabled={deletingId === doc.id || batchDeleting || uploading}
                            title="Delete document"
                          >
                            <Trash2 size={14} /> {deletingId === doc.id ? '…' : 'Delete'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Documents;
