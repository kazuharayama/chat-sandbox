interface ChatRequest {
  message: string;
  language?: string;
  hasAttachment?: boolean;
  use_rag?: boolean;
}

interface ChatResponse {
  response: string;
  sources?: string[];
}

interface DocumentUploadRequest {
  file: File;
  document_type: string;
}

interface DocumentResponse {
  document_id: string;
  filename: string;
  status: string;
}

interface Document {
  document_id: string;
  filename: string;
  size: number;
  last_modified: number;
}

interface DocumentListResponse {
  documents: Document[];
}

interface QueryRequest {
  query: string;
  language?: string;
  use_rag?: boolean;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = 'http://localhost:8000';
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: request.message,
          language: request.language || '日本語',
          hasAttachment: request.hasAttachment || false,
          use_rag: request.use_rag !== undefined ? request.use_rag : true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending message:', error);
      throw new Error('メッセージの送信中にエラーが発生しました');
    }
  }

  async uploadDocument(request: DocumentUploadRequest): Promise<DocumentResponse> {
    try {
      const formData = new FormData();
      formData.append('file', request.file);
      formData.append('document_type', request.document_type);

      const response = await fetch(`${this.baseUrl}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading document:', error);
      throw new Error('ドキュメントのアップロード中にエラーが発生しました');
    }
  }

  async getDocuments(): Promise<DocumentListResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/documents`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting documents:', error);
      throw new Error('ドキュメント一覧の取得中にエラーが発生しました');
    }
  }

  async queryDocuments(request: QueryRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: request.query,
          language: request.language || '日本語',
          use_rag: request.use_rag !== undefined ? request.use_rag : true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error querying documents:', error);
      throw new Error('ドキュメントの検索中にエラーが発生しました');
    }
  }

  async speechToText(audioFile: File): Promise<{ text: string }> {
    try {
      const formData = new FormData();
      formData.append('audio', audioFile);

      const response = await fetch(`${this.baseUrl}/speech-to-text`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error converting speech to text:', error);
      throw new Error('音声のテキスト変換中にエラーが発生しました');
    }
  }
}

export const apiService = new ApiService();
export type { 
  ChatRequest, 
  ChatResponse, 
  DocumentUploadRequest,
  DocumentResponse, 
  Document,
  DocumentListResponse,
  QueryRequest 
};