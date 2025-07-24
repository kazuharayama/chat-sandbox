interface ChatRequest {
  message: string;
  language?: string;
  hasAttachment?: boolean;
}

interface ChatResponse {
  response: string;
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
      throw new Error('音声認識中にエラーが発生しました');
    }
  }
}

export const apiService = new ApiService();
export type { ChatRequest, ChatResponse }; 