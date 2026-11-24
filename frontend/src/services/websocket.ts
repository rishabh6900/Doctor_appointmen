type EventCallback = (data: any) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private reconnectTimer: number | null = null;
  private isConnected = false;

  public connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/events`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
        console.log('[WebSocket] Connected to CarePoint real-time events stream');
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const eventType = payload.event;
          const data = payload.data;

          if (eventType && this.listeners.has(eventType)) {
            this.listeners.get(eventType)?.forEach((cb) => {
              try {
                cb(data);
              } catch (err) {
                console.error(`[WebSocket] Listener callback error for event ${eventType}:`, err);
              }
            });
          }
        } catch {
          // Ignore non-json frames (e.g. pong)
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.warn('[WebSocket] Connection error:', err);
        if (this.ws) {
          this.ws.close();
        }
      };
    } catch (e) {
      console.warn('[WebSocket] Failed to initialize WebSocket:', e);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 4000);
  }

  public on(event: string, callback: EventCallback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
    return () => {
      this.listeners.get(event)?.delete(callback);
    };
  }

  public getConnected(): boolean {
    return this.isConnected;
  }
}

export const wsClient = new WebSocketClient();
