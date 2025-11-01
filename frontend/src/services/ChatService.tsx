import type { ChatResponse } from '../types/Chat';

interface ChatRequestPayload {
  query: string;
  url: string;
  mode: string;
}

export async function sendQueryToBackend(payload: ChatRequestPayload): Promise<ChatResponse> {
  const apiUrl = '/api/chat/rag';
  const baseUrl =
    (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_BACKEND_API_URL) ||
    (globalThis as any).process?.env?.REACT_APP_BACKEND_API_URL ||
    'http://localhost:8000';

    const backendUrl = baseUrl + apiUrl;

  console.log('Envoi de la requête au backend:', backendUrl, payload);

  const response = await fetch(backendUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Erreur réseau: ${response.status}`);
  }

  return await response.json();
}