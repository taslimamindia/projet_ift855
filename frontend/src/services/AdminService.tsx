export interface AdminConfig {
  default_folder?: string;
}

const httpBaseUrl =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_BACKEND_API_URL) ||
  (globalThis as any).process?.env?.REACT_APP_BACKEND_API_URL ||
  'http://localhost:8000';

const wsBaseEnv =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_BACKEND_API_URL_WS) ||
  (globalThis as any).process?.env?.REACT_APP_BACKEND_API_URL_WS ||
  undefined;

function normalizeHttpBase(url: string) {
  let u = url || 'http://localhost:8000';
  if (u.endsWith('/')) u = u.slice(0, -1);
  return u;
}

function joinUrl(base: string, path: string) {
  const b = normalizeHttpBase(base);
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${b}${p}`;
}

function wsUrlFor(path: string) {
  const p = path.startsWith('/') ? path : `/${path}`;
  let base = wsBaseEnv;

  if (!base) {
    // Derive WS base from HTTP base if explicit WS base is not provided
    base = httpBaseUrl.startsWith('https://')
      ? 'wss://' + httpBaseUrl.slice('https://'.length)
      : httpBaseUrl.startsWith('http://')
      ? 'ws://' + httpBaseUrl.slice('http://'.length)
      : httpBaseUrl;
  }

  if (!base.startsWith('ws://') && !base.startsWith('wss://')) {
    base = 'wss://' + base;
  }
  if ((base as string).endsWith('/')) base = (base as string).slice(0, -1);

  return `${base}${p}`;
}

export class AdminService {
  static getHttpBaseUrl(): string {
    return normalizeHttpBase(httpBaseUrl);
  }

  static apiUrl(path: string): string {
    return joinUrl(AdminService.getHttpBaseUrl(), path);
  }

  static async getConfig(): Promise<AdminConfig> {
    const res = await fetch(AdminService.apiUrl('/admin/api/config'));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  static async listFolders(): Promise<string[]> {
    const res = await fetch(AdminService.apiUrl('/admin/api/folders/list'));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (!Array.isArray(data)) throw new Error('Invalid server response');
    return data as string[];
  }

  static async deleteFolders(folders: string[]): Promise<string> {
    const res = await fetch(AdminService.apiUrl('/admin/api/folders/delete'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(folders),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const txt = await res.text();
    console.log('Deletion response:', txt);
    return txt || 'Deletion successful';
  }

  static getMemoryWsUrl(): string {
    return wsUrlFor('/admin/ws/memory');
  }
}
