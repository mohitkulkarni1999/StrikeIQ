/**
 * WEBSOCKET HEARTBEAT INDICATOR
 * 
 * When websocket connected:
 * - heartbeat icon must blink every 1 second
 * - indicates live connection
 * 
 * No UI flicker allowed
 */

import { useEffect, useRef, useState } from 'react';

export interface HeartbeatState {
  isConnected: boolean;
  isBeating: boolean;
  lastBeat: number;
  connectionTime: number | null;
  missedBeats: number;
}

export interface HeartbeatCallbacks {
  onConnectionEstablished?: () => void;
  onConnectionLost?: () => void;
  onMissedBeats?: (count: number) => void;
}

class WebSocketHeartbeat {
  private state: HeartbeatState = {
    isConnected: false,
    isBeating: false,
    lastBeat: 0,
    connectionTime: null,
    missedBeats: 0,
  };

  private callbacks: HeartbeatCallbacks = {};
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private beatInterval: NodeJS.Timeout | null = null;
  private readonly HEARTBEAT_INTERVAL = 1000; // 1 second
  private readonly BEAT_BLINK_INTERVAL = 500; // 0.5 second for blink effect
  private readonly MAX_MISSED_BEATS = 3;

  /**
   * Set heartbeat callbacks
   */
  setCallbacks(callbacks: HeartbeatCallbacks) {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  /**
   * Start heartbeat when WebSocket connects
   */
  startHeartbeat(): void {
    if (this.state.isConnected) {
      return; // Already started
    }

    console.log('[WebSocketHeartbeat] Starting heartbeat');
    
    this.state.isConnected = true;
    this.state.connectionTime = Date.now();
    this.state.missedBeats = 0;
    this.state.lastBeat = Date.now();

    // Start the heartbeat pulse
    this.startHeartbeatPulse();
    
    // Start the visual beat effect
    this.startBeatEffect();

    this.callbacks.onConnectionEstablished?.();
  }

  /**
   * Stop heartbeat when WebSocket disconnects
   */
  stopHeartbeat(): void {
    console.log('[WebSocketHeartbeat] Stopping heartbeat');
    
    this.state.isConnected = false;
    this.state.isBeating = false;
    this.state.connectionTime = null;

    // Clear intervals
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.beatInterval) {
      clearInterval(this.beatInterval);
      this.beatInterval = null;
    }

    this.callbacks.onConnectionLost?.();
  }

  /**
   * Update heartbeat when message received
   */
  updateHeartbeat(): void {
    if (!this.state.isConnected) {
      return;
    }

    const now = Date.now();
    this.state.lastBeat = now;
    this.state.missedBeats = 0;
    this.state.isBeating = true;

    // Reset beat effect
    setTimeout(() => {
      this.state.isBeating = false;
    }, this.BEAT_BLINK_INTERVAL);
  }

  /**
   * Start heartbeat pulse monitoring
   */
  private startHeartbeatPulse(): void {
    // Clear existing interval
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    this.heartbeatInterval = setInterval(() => {
      const now = Date.now();
      const timeSinceLastBeat = now - this.state.lastBeat;

      // Check for missed beats
      if (timeSinceLastBeat > this.HEARTBEAT_INTERVAL * 2) {
        this.state.missedBeats++;
        
        console.warn(`[WebSocketHeartbeat] Missed beat ${this.state.missedBeats}/${this.MAX_MISSED_BEATS}`);
        
        this.callbacks.onMissedBeats?.(this.state.missedBeats);

        // If too many missed beats, consider connection lost
        if (this.state.missedBeats >= this.MAX_MISSED_BEATS) {
          console.error('[WebSocketHeartbeat] Too many missed beats, stopping heartbeat');
          this.stopHeartbeat();
        }
      }
    }, this.HEARTBEAT_INTERVAL);
  }

  /**
   * Start visual beat effect
   */
  private startBeatEffect(): void {
    // Clear existing interval
    if (this.beatInterval) {
      clearInterval(this.beatInterval);
    }

    this.beatInterval = setInterval(() => {
      if (this.state.isConnected) {
        this.state.isBeating = true;
        
        // Toggle beat effect for visual indication
        setTimeout(() => {
          this.state.isBeating = false;
        }, this.BEAT_BLINK_INTERVAL);
      }
    }, this.HEARTBEAT_INTERVAL);
  }

  /**
   * Get current heartbeat state
   */
  getState(): HeartbeatState {
    return { ...this.state };
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.state.isConnected;
  }

  /**
   * Check if currently beating (for visual effect)
   */
  isBeating(): boolean {
    return this.state.isBeating;
  }

  /**
   * Get connection duration
   */
  getConnectionDuration(): number {
    if (!this.state.connectionTime) {
      return 0;
    }
    return Date.now() - this.state.connectionTime;
  }

  /**
   * Get time since last beat
   */
  getTimeSinceLastBeat(): number {
    if (this.state.lastBeat === 0) {
      return 0;
    }
    return Date.now() - this.state.lastBeat;
  }

  /**
   * Reset heartbeat state
   */
  reset(): void {
    this.stopHeartbeat();
    this.state.missedBeats = 0;
    this.state.lastBeat = 0;
  }
}

// Create singleton instance
const webSocketHeartbeat = new WebSocketHeartbeat();

export default webSocketHeartbeat;
export { WebSocketHeartbeat };

/**
 * React hook for heartbeat state
 */
export function useWebSocketHeartbeat() {
  const [heartbeatState, setHeartbeatState] = useState<HeartbeatState>(webSocketHeartbeat.getState());
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Update state every 100ms to catch beat changes
    intervalRef.current = setInterval(() => {
      setHeartbeatState(webSocketHeartbeat.getState());
    }, 100);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    isConnected: heartbeatState.isConnected,
    isBeating: heartbeatState.isBeating,
    lastBeat: heartbeatState.lastBeat,
    connectionTime: heartbeatState.connectionTime,
    missedBeats: heartbeatState.missedBeats,
    connectionDuration: webSocketHeartbeat.getConnectionDuration(),
    timeSinceLastBeat: webSocketHeartbeat.getTimeSinceLastBeat(),
  };
}
