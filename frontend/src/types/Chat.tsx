export interface Message {
  sender: 'user' | 'ai';
  text: string;
}

export interface ChatResponse {
  response: string;
}