export interface PipelineProgressEvent {
  step: "initializing" | "crawling" | "embedding" | "indexing" | "pipeline";
  status: "start" | "done" | "failed" | "in_progress";
  value?: number;
  message?: string;
  error?: string;
}

type ProgressCallback = (data: PipelineProgressEvent) => void;

const baseUrl =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_BACKEND_API_URL_WS) ||
  (globalThis as any).process?.env?.REACT_APP_BACKEND_API_URL_WS ||
  "ws://localhost:8000";

function wsUrlFor(path: string) {
  const p = path.startsWith('/') ? path : `/${path}`;

  // Normalize baseUrl to a ws:// or wss:// scheme. The environment variable
  // may contain http(s)://; convert to ws(s):// so WebSocket constructor works.
  let u = baseUrl;
  if (u.startsWith('http://')) {
    u = 'ws://' + u.slice('http://'.length);
  } else if (u.startsWith('https://')) {
    u = 'wss://' + u.slice('https://'.length);
  } else if (!u.startsWith('ws://') && !u.startsWith('wss://')) {
    u = 'wss://' + u;
  }

  if (u.endsWith('/')) u = u.slice(0, -1);

  return u + p;
}

const DEFAULT_TIMEOUT = 1000 * 60 * 5;

export class PipelineService {
  private sockets: Record<string, WebSocket | undefined> = {};
  private static inFlightRuns: Record<string, Promise<Record<string, PipelineProgressEvent>> | undefined> = {};
  private static globalClientId: string | undefined;

  private static getClientId(): string {
    const lsKey = `pipelineClientId`;
    try {
      const existing = typeof window !== 'undefined' ? window.localStorage.getItem(lsKey) : null;
      if (existing) {
        PipelineService.globalClientId = existing;
        return existing;
      }
    } catch {}

    if (!PipelineService.globalClientId) {
      const uuid = ([1e7] as any + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, (c: string) => (
        (Number(c) ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (Number(c) / 4))))
      ).toString(16));
      PipelineService.globalClientId = `fe-${uuid}`;

      try {
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(lsKey, PipelineService.globalClientId);
        }
      } catch {}
    }
    return PipelineService.globalClientId;
  }

  private openPipelineSocket(
    path: string,
    payload: any,
    onProgress?: ProgressCallback,
    timeoutMs = DEFAULT_TIMEOUT,
  ): Promise<Record<string, PipelineProgressEvent>> {

    return new Promise<Record<string, PipelineProgressEvent>>((resolve, reject) => {
      const url = wsUrlFor(path);
      let settled = false;
      let timer: number | undefined;
      const results: Record<string, PipelineProgressEvent> = {};

      try {
        const ws = new WebSocket(url);
        this.sockets[path] = ws;

        const cleanup = () => {
          if (timer) {
            clearTimeout(timer as any);
            timer = undefined;
          }
          try {
            if (ws && ws.readyState === WebSocket.OPEN) ws.close();
          } catch {}
          if (this.sockets[path] === ws) this.sockets[path] = undefined;
        };

        ws.onopen = () => {
          try {
            if (onProgress) onProgress({ step: 'initializing', status: 'start' });
            ws.send(JSON.stringify(payload));
          } catch (err) {
            if (!settled) {
              settled = true;
              cleanup();
              reject(err);
            }
          }
        };

        ws.onmessage = (ev) => {
          try {
            const data: PipelineProgressEvent = JSON.parse(ev.data);
            console.log('PipelineService received:', data);
            // Forward raw event to UI
            if (onProgress) onProgress(data);
            // Track last event per step
            results[data.step] = data;

            if (data.step === 'pipeline' && data.status === 'done') {
              settled = true;
              cleanup();
              resolve(results);
              return;
            }
            if (data.step === 'pipeline' && data.status === 'failed') {
              settled = true;
              cleanup();
              reject(new Error(data.error || 'Pipeline failed'));
              return;
            }
          } catch (err) {
            if (!settled) {
              settled = true;
              cleanup();
              reject(err);
            }
          }
        };

        ws.onerror = (err) => {
          if (!settled) {
            settled = true;
            cleanup();
            reject(err);
          }
        };

        ws.onclose = () => {
          if (!settled) {
            settled = true;
            cleanup();
            reject(new Error('Socket closed before completion'));
          }
        };

        timer = setTimeout(() => {
          if (!settled) {
            settled = true;
            cleanup();
            reject(new Error('Timeout waiting for pipeline completion'));
          }
        }, timeoutMs) as unknown as number;
      } catch (err) {
        reject(err);
      }
    });
  }

  // run all steps sequentially; each step waits for the other's done status
  async runFullPipeline(
    perStepProgress: (step: string, data: PipelineProgressEvent) => void,
    url: string,
    maxDepth: number,
    timeoutMs?: number,
  ) {
    // If a full run is already in-flight for this URL, return the existing promise
    const existing = PipelineService.inFlightRuns[url];
    if (existing) return existing;

    const resultsPromise = this.openPipelineSocket(
      '/api/pipeline',
      { url, max_depth: maxDepth, client_id: PipelineService.getClientId() },
      (ev) => {
        if (perStepProgress) perStepProgress(ev.step, ev);
      },
      timeoutMs ?? DEFAULT_TIMEOUT,
    );

    PipelineService.inFlightRuns[url] = resultsPromise;
    resultsPromise.finally(() => {
      if (PipelineService.inFlightRuns[url] === resultsPromise) PipelineService.inFlightRuns[url] = undefined;
    });

    return resultsPromise;
  }

  // run all admin steps sequentially; each step waits for the other's done status
  async runAdminPipeline(
    perStepProgress: (step: string, data: PipelineProgressEvent) => void,
    url: string,
    dataFolder: string,
    maxDepth: number,
    timeoutMs?: number,
  ) {
    const existing = PipelineService.inFlightRuns[url];
    if (existing) return existing;

    const resultsPromise = this.openPipelineSocket(
      '/admin/api/pipeline',
      { url, data_folder: dataFolder, max_depth: maxDepth, client_id: PipelineService.getClientId() },
      (ev) => {
        if (perStepProgress) perStepProgress(ev.step, ev);
      },
      timeoutMs ?? DEFAULT_TIMEOUT,
    );

    PipelineService.inFlightRuns[url] = resultsPromise;
    resultsPromise.finally(() => {
      if (PipelineService.inFlightRuns[url] === resultsPromise) PipelineService.inFlightRuns[url] = undefined;
    });

    return resultsPromise;
  }

  // Close all open sockets
  closeAll() {
    Object.keys(this.sockets).forEach((k) => {
      const ws = this.sockets[k];
      try {
        if (ws && ws.readyState === WebSocket.OPEN) ws.close();
      } catch (e) {}
      this.sockets[k] = undefined;
    });
  }
}