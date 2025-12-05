import { useEffect, useState, useRef, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import styles from './MemoryMonitor.module.scss';

interface MemoryStats {
  rss_GB: number;
  vms_GB: number;
  cpu_percent: number;
  threads: number;
  total_RAM_GB: number;
  used_RAM_GB: number;
  ram_percent: number;
  timestamp: string;
}

const MemoryMonitor = () => {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [history, setHistory] = useState<MemoryStats[]>([]);
  const [connected, setConnected] = useState(false);
  const [shouldConnect, setShouldConnect] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const getWebSocketUrl = () => {
      const baseUrl = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';
      const wsUrl = baseUrl.replace(/^http/, 'ws').replace(/^https/, 'wss');
      return `${wsUrl}/ws/memory`;
    };

    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(getWebSocketUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('Connected to memory websocket');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const dataWithTime = { ...data, timestamp: new Date().toLocaleTimeString() };
        
        setStats(dataWithTime);
        setHistory(prev => {
          const newHistory = [...prev, dataWithTime];
          return newHistory.slice(-300); // Keep last 300
        });
      } catch (error) {
        console.error('Error parsing websocket message:', error);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('Disconnected from memory websocket');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  useEffect(() => {
    if (shouldConnect) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [shouldConnect, connect, disconnect]);

  const toggleConnection = () => {
    setShouldConnect(!shouldConnect);
  };

  const maxMemory = history.length > 0 ? Math.max(...history.map(h => Math.max(h.rss_GB, h.vms_GB))) : 3;
  const memoryTicks = [];
  for (let i = 0; i <= maxMemory + 0.5; i += 0.25) {
    memoryTicks.push(Number(i.toFixed(1)));
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Moniteur de Ressources Système</h2>
        <button 
          className={`${styles.button} ${shouldConnect ? styles.disconnectBtn : styles.connectBtn}`}
          onClick={toggleConnection}
        >
          {shouldConnect ? 'Déconnecter' : 'Connecter'}
        </button>
      </div>
      
      <div className={`${styles.status} ${connected ? styles.connected : styles.disconnected}`}>
        {connected ? 'Connecté au serveur' : 'Déconnecté'}
      </div>

      {stats && (
        <>
          <div className={styles.grid}>
            <div className={styles.card}>
              <div className={styles.label}>CPU Usage</div>
              <div className={styles.value}>
                {stats.cpu_percent}
                <span className={styles.unit}>%</span>
              </div>
            </div>

            <div className={styles.card}>
              <div className={styles.label}>RAM Utilisée (Système)</div>
              <div className={styles.value}>
                {stats.used_RAM_GB}
                <span className={styles.unit}>GB</span>
              </div>
              <div className={styles.label} style={{marginTop: '0.5rem'}}>
                sur {stats.total_RAM_GB} GB ({stats.ram_percent}%)
              </div>
            </div>

            <div className={styles.card}>
              <div className={styles.label}>Mémoire Physique (Process)</div>
              <div className={styles.value}>
                {stats.rss_GB}
                <span className={styles.unit}>GB</span>
              </div>
            </div>

            <div className={styles.card}>
              <div className={styles.label}>Mémoire Virtuelle (Process)</div>
              <div className={styles.value}>
                {stats.vms_GB}
                <span className={styles.unit}>GB</span>
              </div>
            </div>

            <div className={styles.card}>
              <div className={styles.label}>Threads Actifs</div>
              <div className={styles.value}>
                {stats.threads}
              </div>
            </div>
          </div>

          <div className={styles.chartsGrid}>
            <div className={styles.chartCard}>
              <h3>Processus en cours (Threads)</h3>
              <div className={styles.chartContainer}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" tick={false} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="threads" stroke="#8884d8" dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className={styles.chartCard}>
              <h3>Utilisation Mémoire (GB)</h3>
              <div className={styles.chartContainer}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" tick={false} />
                    <YAxis ticks={memoryTicks} domain={[0, 'auto']} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="rss_GB" name="RSS (Physique)" stroke="#2bea21ff" dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="vms_GB" name="VMS (Virtuelle)" stroke="#6958ffff" dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MemoryMonitor;
