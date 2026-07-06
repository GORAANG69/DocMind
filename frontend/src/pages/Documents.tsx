import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, File as FileIcon, FileText, CheckCircle, AlertCircle, RefreshCw, FolderPlus, FilePlus, Eye, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ApiClient } from '../api/client';

const SUPPORTED_EXTENSIONS = ['pdf', 'doc', 'docx', 'xls', 'xlsx'];

const Documents = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadStats, setUploadStats] = useState({ total: 0, completed: 0, successful: 0, failed: 0 });
  const [uploadSummary, setUploadSummary] = useState<{successful: number, failed: number} | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

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

  const processUploads = async (files: File[]) => {
    const validFiles = files.filter(isValidFile);

    if (validFiles.length === 0) {
      setError('No supported files found. Please upload PDF, DOCX, or XLSX files.');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadSummary(null);
    setUploadStats({ total: validFiles.length, completed: 0, successful: 0, failed: 0 });

    let successCount = 0;
    let failCount = 0;

    const uploadPromises = validFiles.map(async (file) => {
      try {
        await ApiClient.uploadDocument(file);
        successCount++;
      } catch {
        failCount++;
      } finally {
        setUploadStats(prev => ({
          ...prev,
          completed: prev.completed + 1,
          successful: successCount,
          failed: failCount,
        }));
      }
    });

    await Promise.allSettled(uploadPromises);

    setUploadSummary({ successful: successCount, failed: failCount });
    setUploading(false);
    await fetchDocuments();
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files ? Array.from(event.target.files) : [];
    if (files.length > 0) await processUploads(files);
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
            readBatch(); // read next batch (directories may return entries in batches)
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

    if (allFiles.length > 0) await processUploads(allFiles);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-active');
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-active');
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!window.confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    setDeletingId(docId);
    try {
      await ApiClient.deleteDocument(docId);
      setDocuments(prev => prev.filter(d => d.id !== docId));
    } catch (err: any) {
      setError(err.message || 'Failed to delete document.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleOpen = (docId: string) => {
    navigate(`/viewer/${docId}`);
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return <FileText size={18} color="#ef4444" />;
    if (ext === 'docx' || ext === 'doc') return <FileText size={18} color="#3b82f6" />;
    if (ext === 'xlsx' || ext === 'xls') return <FileText size={18} color="#10b981" />;
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

  return (
    <div className="content-area">
      <div className="top-bar" style={{ margin: '-2rem -2rem 2rem -2rem' }}>
        <h1 className="page-title">Documents</h1>
        <button className="btn btn-primary" onClick={fetchDocuments} disabled={loading || uploading}>
          <RefreshCw size={18} style={{ border: 'none', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {uploadSummary && !uploading && (
        <div style={{ padding: '1rem', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--success)', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)', fontWeight: 600 }}>
            <CheckCircle size={20} />
            Upload Complete
          </div>
          <div style={{ color: 'var(--text-secondary)', marginLeft: '1.75rem' }}>
            {uploadSummary.successful} uploaded successfully
            {uploadSummary.failed > 0 && <span style={{ color: 'var(--danger)' }}> · {uploadSummary.failed} failed</span>}
          </div>
        </div>
      )}

      <div
        className="upload-zone"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept=".pdf,.doc,.docx,.xls,.xlsx" multiple onChange={handleFileSelect} />
        <input type="file" ref={folderInputRef} style={{ display: 'none' }} accept=".pdf,.doc,.docx,.xls,.xlsx" multiple {...{ webkitdirectory: '', directory: '' } as any} onChange={handleFileSelect} />

        {uploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1rem' }}>
            <div className="loader" style={{ width: '48px', height: '48px', marginBottom: '1rem' }}></div>
            <h3 style={{ marginBottom: '1rem' }}>Uploading {uploadStats.completed} of {uploadStats.total}…</h3>
            <div style={{ width: '100%', maxWidth: '400px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '10px', height: '8px', overflow: 'hidden', marginBottom: '1rem' }}>
              <div style={{ height: '100%', backgroundColor: 'var(--accent-primary)', width: `${Math.max(5, (uploadStats.completed / uploadStats.total) * 100)}%`, transition: 'width 0.3s ease' }}></div>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--success)' }}>{uploadStats.successful} successful</span>
              <span style={{ color: 'var(--danger)' }}>{uploadStats.failed} failed</span>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <UploadCloud className="upload-icon" />
            <h2 style={{ marginBottom: '1.5rem' }}>Drag and drop files or folders here</h2>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()}>
                <FilePlus size={18} /> Choose Files
              </button>
              <button className="btn btn-secondary" onClick={() => folderInputRef.current?.click()}>
                <FolderPlus size={18} /> Choose Folder
              </button>
            </div>
            <p style={{ color: 'var(--text-secondary)', marginTop: '1.5rem', fontSize: '0.9rem' }}>
              Supports PDF, Word (.docx), and Excel (.xlsx) files
            </p>
          </div>
        )}
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Indexed Files</h2>
          <span style={{ backgroundColor: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-primary)', padding: '0.25rem 0.75rem', borderRadius: '20px', fontSize: '0.875rem', fontWeight: 600 }}>
            {documents?.length || 0} Total
          </span>
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
            <p>Upload a file above to get started.</p>
          </div>
        ) : (
          <div className="documents-table-wrapper">
            <table className="documents-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Indexed On</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id}>
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
                        >
                          <Eye size={14} /> Open
                        </button>
                        <button
                          className="btn"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', backgroundColor: 'rgba(239,68,68,0.1)', color: 'var(--danger)', border: '1px solid rgba(239,68,68,0.3)' }}
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          disabled={deletingId === doc.id}
                          title="Delete document"
                        >
                          <Trash2 size={14} /> {deletingId === doc.id ? '…' : 'Delete'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Documents;
