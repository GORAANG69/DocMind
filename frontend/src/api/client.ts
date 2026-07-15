export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getSessionId() {
  let sessionId = sessionStorage.getItem('docmind_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    sessionStorage.setItem('docmind_session_id', sessionId);
  }
  return sessionId;
}

const fetchWithSession = (url: string, options: RequestInit = {}) => {
  const headers = new Headers(options.headers || {});
  headers.append('X-Session-Id', getSessionId());
  return fetch(url, { ...options, headers });
};


export interface TaskProgress {
  id: string;
  status: 'pending' | 'running' | 'done';
  total_files: number;
  completed: number;
  successful: number;
  skipped: number;
  failed: number;
  files: Array<{ original_filename: string; status: string; error: string }>;
}

export class ApiClient {
  static async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetchWithSession(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let detail = 'Failed to upload document';
      try { detail = (await response.json()).detail || detail; } catch {}
      throw new Error(detail);
    }

    return response.json();
  }

  /** Returns a plain array of document objects. */
  static async getDocuments(): Promise<any[]> {
    const response = await fetchWithSession(`${API_BASE_URL}/api/documents`);
    if (!response.ok) {
      throw new Error('Failed to fetch documents');
    }
    const data = await response.json();
    // Backend returns a raw JSON array — NOT { documents: [] }
    return Array.isArray(data) ? data : (data.documents ?? []);
  }

  /** Returns a plain array of grouped search result objects. */
  static async search(query: string): Promise<any[]> {
    const url = `${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}`;
    const response = await fetchWithSession(url);
    if (!response.ok) {
      let detail = 'Search failed';
      try { detail = (await response.json()).detail || detail; } catch {}
      throw new Error(detail);
    }
    const data = await response.json();
    return Array.isArray(data) ? data : (data.results ?? []);
  }


  static async deleteAllDocuments(): Promise<void> {
    const response = await fetchWithSession(`${API_BASE_URL}/api/documents`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      let detail = 'Failed to delete all documents';
      try { detail = (await response.json()).detail || detail; } catch {}
      throw new Error(detail);
    }
  }

  static async deleteDocument(docId: string): Promise<void> {
    const response = await fetchWithSession(`${API_BASE_URL}/api/document/${docId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      let detail = 'Failed to delete document';
      try { detail = (await response.json()).detail || detail; } catch {}
      throw new Error(detail);
    }
  }

  /** Returns the inline-view URL for embedding in an iframe or PDF.js. */
  static getDocumentViewUrl(docId: string): string {
    return `${API_BASE_URL}/api/document/${docId}/view`;
  }

  static async getDocumentText(docId: string): Promise<string> {
    const response = await fetchWithSession(`${API_BASE_URL}/api/document/${docId}/text`);
    if (!response.ok) throw new Error('Failed to fetch document text');
    const data = await response.json();
    return data.text ?? '';
  }

  static async getDocumentMetadata(docId: string): Promise<any> {
    const response = await fetchWithSession(`${API_BASE_URL}/api/document/${docId}`);
    if (!response.ok) throw new Error('Document not found');
    return response.json();
  }

  static async getStats(): Promise<any> {
    const response = await fetchWithSession(`${API_BASE_URL}/api/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  }

  static async rebuildIndex(): Promise<any> {
    const response = await fetchWithSession(`${API_BASE_URL}/api/settings/rebuild`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to rebuild search index');
    return response.json();
  }

  static async clearSearchCache(): Promise<any> {
    const response = await fetchWithSession(`${API_BASE_URL}/api/settings/clear-cache`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to clear search cache');
    return response.json();
  }

  /**
   * Async batch upload — saves files server-side immediately and returns a
   * task_id for progress polling. Does NOT block until indexing completes.
   *
   * For folder uploads, pass the webkitRelativePath as the x-relative-path
   * header on each file so the backend can store folder-relative metadata.
   */
  static async uploadAsync(
    files: File[],
    onProgress?: (saved: number, total: number) => void,
  ): Promise<{ task_id: string; total_files: number; status: string }> {
    const formData = new FormData();

    files.forEach((file, idx) => {
      // Use the relative path from webkitdirectory uploads when available
      const relativePath = (file as any).webkitRelativePath || '';
      // We cannot set custom headers per FormData part, so embed the
      // relative path as a companion field name pattern: file_rel_{idx}
      formData.append('files', file, file.name);
      if (relativePath) {
        formData.append(`rel_${idx}`, relativePath);
      }
      if (onProgress) onProgress(idx + 1, files.length);
    });

    const response = await fetchWithSession(`${API_BASE_URL}/api/upload/async`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let detail = 'Async upload failed';
      try { detail = (await response.json()).detail || detail; } catch {}
      throw new Error(detail);
    }

    return response.json();
  }

  /** Poll the progress of an async indexing task. */
  static async getTaskProgress(taskId: string): Promise<TaskProgress> {
    const response = await fetchWithSession(`${API_BASE_URL}/api/task/${taskId}`);
    if (!response.ok) throw new Error('Task not found');
    return response.json();
  }
}
