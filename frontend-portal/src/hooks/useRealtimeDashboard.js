import { useState, useEffect, useRef, useCallback } from 'react';

const WS_AUTH_TOKEN = import.meta.env.VITE_WS_AUTH_TOKEN || 'CHANGE_ME_SUPER_SECRET_TOKEN';
const WS_URL = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws'}?token=${WS_AUTH_TOKEN}`;

/**
 * Real-time WebSocket hook — Admin Dashboard uchun
 * Backend bilan jonli bog'liq bo'ladi va avtomatik qayta ulanadi
 */
export function useRealtimeDashboard() {
  const [connected, setConnected] = useState(false);
  const [newOrders, setNewOrders] = useState([]);
  const [messages, setMessages] = useState([]);
  const [statsUpdate, setStatsUpdate] = useState(null);
  const [workerLocations, setWorkerLocations] = useState({});
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setConnected(true);
        console.log('🔌 WebSocket ulandi (Real-Time Dashboard)');
        // Ping har 30 soniyada
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);
        ws._pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'pong') return;

          switch (msg.type) {
            case 'new_order':
              setNewOrders(prev => [msg.data, ...prev.slice(0, 49)]);
              // Browser notification
              if (Notification.permission === 'granted') {
                new Notification('🔔 Yangi buyurtma!', {
                  body: `${msg.data.service} — ${msg.data.address}`,
                  icon: '/favicon.ico',
                });
              }
              break;
            case 'order_update':
              setNewOrders(prev =>
                prev.map(o => o.order_id === msg.data.order_id
                  ? { ...o, status: msg.data.status }
                  : o
                )
              );
              break;
            case 'new_message':
              setMessages(prev => [msg.data, ...prev.slice(0, 99)]);
              break;
            case 'worker_location':
              setWorkerLocations(prev => ({
                ...prev,
                [msg.data.worker_id]: {
                  lat: msg.data.lat,
                  lon: msg.data.lon,
                  name: msg.data.worker_name,
                  updatedAt: msg.timestamp,
                }
              }));
              break;
            case 'stats_update':
              setStatsUpdate(msg.data);
              break;
            case 'init':
              if (msg.data.stats) setStatsUpdate(msg.data.stats);
              break;
            default:
              break;
          }
        } catch (e) {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        setConnected(false);
        clearInterval(ws._pingInterval);
        // 5 soniyadan keyin qayta ulanish
        reconnectTimer.current = setTimeout(() => {
          console.log('🔄 WebSocket qayta ulanmoqda...');
          connect();
        }, 5000);
      };

      ws.onerror = (err) => {
        console.warn('WebSocket xatosi (offline rejimida ishlaydi):', err.message);
        ws.close();
      };

      wsRef.current = ws;
    } catch (err) {
      console.warn('WebSocket ulana olmadi — mock ma\'lumotlar ishlatiladi');
    }
  }, []);

  useEffect(() => {
    // Browser notification ruxsatini so'rash
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    connected,
    newOrders,
    messages,
    statsUpdate,
    workerLocations,
  };
}
