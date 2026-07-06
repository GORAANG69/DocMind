export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiClient {
  static async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/upload`, {
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
    const response = await fetch(`${API_BASE_URL}/api/documents`);
    if (!response.ok) {
      throw new Error('Failed to fetch documents');
    }
    const data = await response.json();
    // Backend returns a raw JSON array — NOT { documents: [] }
    return Array.isArray(data) ? data : (data.documents ?? []);
  }

  /** Returns a plain array of search result objects. */
  static async search(query: string): Promise<any[]> {
    const url = `${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}`;
    const response = await fetch(url);
    if (!response.ok) {
      let detail = 'Search failed';
      try { detail = (await response.json()).detail || detail; } catch {}
      throw new Error(detail);
    }
    const data = await response.json();
    // Backend returns a raw JSON array — NOT { results: [] }
    return Array.isArray(data) ? data : (data.results ?? []);
  }

  static async deleteDocument(docId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/document/${docId}`, {
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
    const response = await fetch(`${API_BASE_URL}/api/document/${docId}/text`);
    if (!response.ok) throw new Error('Failed to fetch document text');
    const data = await response.json();
    return data.text ?? '';
  }

  static async getDocumentMetadata(docId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/document/${docId}`);
    if (!response.ok) throw new Error('Document not found');
    return response.json();
  }

  static async getStats(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  }
}
