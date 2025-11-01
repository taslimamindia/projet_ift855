export interface PipelineProgressEvent {
  step: "initializing" | "crawling" | "embedding" | "indexing" | "pipeline";
  status: "start" | "done" | "failed" | "in_progress";
  error?: string;
}

type ProgressCallback = (data: PipelineProgressEvent) => void;

const baseUrl =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_BACKEND_API_URL_WS) ||
  (globalThis as any).process?.env?.REACT_APP_BACKEND_API_URL_WS ||
  "ws://localhost:8000";

function wsUrlFor(path: string) {
  // ensure path starts with /
  const p = path.startsWith('/') ? path : `/${path}`;

  // Normalize baseUrl to a ws:// or wss:// scheme. The environment variable
  // may contain http(s)://; convert to ws(s):// so WebSocket constructor works.
  let u = baseUrl;
  if (u.startsWith('http://')) {
    u = 'ws://' + u.slice('http://'.length);
  } else if (u.startsWith('https://')) {
    u = 'wss://' + u.slice('https://'.length);
  } else if (!u.startsWith('ws://') && !u.startsWith('wss://')) {
    // if no scheme, assume ws
    u = 'wss://' + u;
  }

  // remove trailing slash to avoid double slashes when joining with path
  if (u.endsWith('/')) u = u.slice(0, -1);

  return u + p;
}

const DEFAULT_TIMEOUT = 1000 * 60 * 5; // 5 minutes

export class PipelineService {
  // expose per-step web socket references only if needed for debugging
  private sockets: Record<string, WebSocket | undefined> = {};
  // cache in-flight runFullPipeline per-url to avoid duplicate full runs
  private static inFlightRuns: Record<string, Promise<Record<string, PipelineProgressEvent>> | undefined> = {};
  // cache pending step promises per path+payload key to avoid duplicate WS for same step
  private pendingStepPromises: Record<string, Promise<PipelineProgressEvent> | undefined> = {};

  private openStepSocket(
    path: string,
    expectedStep: PipelineProgressEvent['step'],
    payload: any,
    onProgress?: ProgressCallback,
    timeoutMs = DEFAULT_TIMEOUT,
    setCurrentStep?: (step: PipelineProgressEvent['step']) => void,
  ): Promise<PipelineProgressEvent> {
    // create a stable key for this step + payload to dedupe identical concurrent calls
    const key = `${path}::${JSON.stringify(payload)}`;

    // if there is already a pending promise for this exact step+payload, return it
    const existing = this.pendingStepPromises[key];
    if (existing) return existing;

    const promise = new Promise<PipelineProgressEvent>((resolve, reject) => {
      const url = wsUrlFor(path);
      
      console.log('Connecting to WebSocket:', url
        , 'with payload:', payload);
      let settled = false;
      let timer: number | undefined;

      try {
        var ws: WebSocket;
        if (this.sockets[path] && this.sockets[path]?.readyState === WebSocket.OPEN) {
          ws = this.sockets[path];
        } else {
          ws = new WebSocket(url);
        }

        this.sockets[path] = ws;
        const cleanup = () => {
          if (timer) {
            clearTimeout(timer as any);
            timer = undefined;
          }

          try {
            if (ws && ws.readyState === WebSocket.OPEN) ws.close();
          } catch (e) {}

          if (this.sockets[path] === ws) this.sockets[path] = undefined;
          // remove pending promise entry for this key
          if (this.pendingStepPromises[key] === promise) this.pendingStepPromises[key] = undefined;
        };

        ws.onopen = () => {
          // notify backend to start this step
          // update UI state before attempting to open websocket
          try {
            if (setCurrentStep) setCurrentStep(expectedStep);
          } catch (e) {
            // swallow errors from external setter
          }

          try {
            // Inform caller immediately that this step has started (backend accepted connection)
            // Only emit the onopen 'start' event if caller did not already emit it.
            console.log('WebSocket opened for step:', expectedStep);
            if (onProgress) {
              onProgress({ step: expectedStep, status: 'start' });
              console.log('Emitted onProgress start for step:', expectedStep);
            }
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
            if (onProgress) onProgress(data);

            // Accept either the expected step completion OR a global pipeline completion
            const isExpected = data.step === expectedStep;
            const isPipelineDone = data.step === 'pipeline' && data.status === 'done';

            if (isExpected && data.status === 'done') {
              settled = true;
              cleanup();
              resolve(data);
              return;
            }

            if (isPipelineDone) {
              // If backend signals the overall pipeline is done, treat as success as well
              settled = true;
              cleanup();
              resolve(data);
              return;
            }

            if (isExpected && data.status === 'failed') {
              settled = true;
              cleanup();
              reject(new Error(data.error || `Step ${expectedStep} failed`));
              return;
            }
            // otherwise continue listening (in_progress, other steps, etc.)
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

        // set timeout
        timer = setTimeout(() => {
          if (!settled) {
            settled = true;
            cleanup();
            reject(new Error('Timeout waiting for step completion'));
          }
        }, timeoutMs) as unknown as number;
      } catch (err) {
        reject(err);
      }
    });

    // store pending promise so concurrent callers reuse it
    this.pendingStepPromises[key] = promise;
    return promise;
  }

  // Each step uses its own endpoint path and sends the same payload { url }
  initialize(url: string, onProgress?: ProgressCallback, timeoutMs?: number, setCurrentStep?: (step: PipelineProgressEvent['step']) => void) {
    return this.openStepSocket('/api/pipeline/initializing', 'initializing', { url }, onProgress, timeoutMs, setCurrentStep);
  }

  crawling(url: string, onProgress?: ProgressCallback, timeoutMs?: number, setCurrentStep?: (step: PipelineProgressEvent['step']) => void) {
    return this.openStepSocket('/api/pipeline/crawling', 'crawling', { url }, onProgress, timeoutMs, setCurrentStep);
  }

  embedding(url: string, onProgress?: ProgressCallback, timeoutMs?: number, setCurrentStep?: (step: PipelineProgressEvent['step']) => void) {
    return this.openStepSocket('/api/pipeline/embedding', 'embedding', { url }, onProgress, timeoutMs, setCurrentStep);
  }

  indexing(url: string, onProgress?: ProgressCallback, timeoutMs?: number, setCurrentStep?: (step: PipelineProgressEvent['step']) => void) {
    return this.openStepSocket('/api/pipeline/indexing', 'indexing', { url }, onProgress, timeoutMs, setCurrentStep);
  }

  // run all steps sequentially; each step waits for the other's done status
  async runFullPipeline(
    url: string,
    perStepProgress?: (step: string, data: PipelineProgressEvent) => void,
    timeoutMs?: number,
    setCurrentStep?: (step: PipelineProgressEvent['step']) => void,
    setIsPipelineDone?: (done: boolean) => void,
  ) {
    // If a full run is already in-flight for this URL, return the existing promise
    const existing = PipelineService.inFlightRuns[url];
    if (existing) return existing;

    const resultsPromise = (async (): Promise<Record<string, PipelineProgressEvent>> => {
      const results: Record<string, PipelineProgressEvent> = {};

      const handle = (stepLabel: PipelineProgressEvent['step']) => (data: PipelineProgressEvent) => {
        if (perStepProgress) perStepProgress(stepLabel, data);
      };

      try {
        // initialize (notify UI immediately that initializing is starting, backend may be slow)
  if (perStepProgress) perStepProgress('initializing', { step: 'initializing', status: 'start' });
  if (setCurrentStep) setCurrentStep('initializing');
  results.initialize = await this.initialize(url, handle('initializing'), timeoutMs, setCurrentStep);
        // crawling
  if (perStepProgress) perStepProgress('crawling', { step: 'crawling', status: 'start' });
  if (setCurrentStep) setCurrentStep('crawling');
  results.crawling = await this.crawling(url, handle('crawling'), timeoutMs, setCurrentStep);
        // embedding
  if (perStepProgress) perStepProgress('embedding', { step: 'embedding', status: 'start' });
  if (setCurrentStep) setCurrentStep('embedding');
  results.embedding = await this.embedding(url, handle('embedding'), timeoutMs, setCurrentStep);
        // indexing
  if (perStepProgress) perStepProgress('indexing', { step: 'indexing', status: 'start' });
  if (setCurrentStep) setCurrentStep('indexing');
  results.indexing = await this.indexing(url, handle('indexing'), timeoutMs, setCurrentStep);

  // After all steps completed successfully, emit a final pipeline done event
  if (perStepProgress) perStepProgress('pipeline', { step: 'pipeline', status: 'done' });
  if (setCurrentStep) setCurrentStep('pipeline');
  if (setIsPipelineDone) setIsPipelineDone(true);
        return results;
      } catch (err: any) {
        // In case any step failed, emit a pipeline failed event for consumers
        if (perStepProgress) {
          const message = err?.message || String(err) || 'Erreur pipeline';
          perStepProgress('pipeline', { step: 'pipeline', status: 'failed', error: message });
        }
        throw err;
      }
    })();

    // store in-flight run and ensure it's removed when settled
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