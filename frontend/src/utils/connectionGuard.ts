/**
 * FRONTEND CRASH PREVENTION GUARDS
 * 
 * Add guards to prevent UI crashes:
 * - If websocket disconnects: show "reconnecting..."
 * - System reconnects automatically
 * - No UI crash allowed
 */

import React, { useEffect, useState, useRef } from 'react';

export interface ConnectionGuardState {
  isConnected: boolean;
  isReconnecting: boolean;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  lastError: string | null;
  reconnectDelay: number;
}

export interface ConnectionGuardCallbacks {
  onConnectionLost?: () => void;
  onConnectionRestored?: () => void;
  onReconnectAttempt?: (attempt: number) => void;
  onMaxReconnectReached?: () => void;
}

class ConnectionGuard {
  private state: ConnectionGuardState = {
    isConnected: false,
    isReconnecting: false,
    reconnectAttempts: 0,
    maxReconnectAttempts: 10,
    lastError: null,
    reconnectDelay: 3000, // Start with 3 seconds
  };

  private callbacks: ConnectionGuardCallbacks = {};
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private reconnectBackoffMultiplier = 1.5;
  private maxReconnectDelay = 30000; // Max 30 seconds

  /**
   * Set connection guard callbacks
   */
  setCallbacks(callbacks: ConnectionGuardCallbacks) {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  /**
   * Initialize connection guard
   */
  initialize(): void {
    this.state.isConnected = true;
    this.state.reconnectAttempts = 0;
    this.state.lastError = null;
    this.state.reconnectDelay = 3000;
  }

  /**
   * Handle connection loss
   */
  handleConnectionLoss(error?: string): void {
    if (!this.state.isConnected) {
      return; // Already handling disconnection
    }

    console.warn('[ConnectionGuard] Connection lost:', error || 'Unknown error');
    
    this.state.isConnected = false;
    this.state.isReconnecting = true;
    this.state.lastError = error || 'Connection lost';

    this.callbacks.onConnectionLost?.();

    // Start reconnection attempt
    this.startReconnection();
  }

  /**
   * Handle connection restored
   */
  handleConnectionRestored(): void {
    console.log('[ConnectionGuard] Connection restored');
    
    this.state.isConnected = true;
    this.state.isReconnecting = false;
    this.state.reconnectAttempts = 0;
    this.state.lastError = null;
    this.state.reconnectDelay = 3000;

    // Clear any pending reconnection timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.callbacks.onConnectionRestored?.();
  }

  /**
   * Start reconnection process
   */
  private startReconnection(): void {
    if (this.state.reconnectAttempts >= this.state.maxReconnectAttempts) {
      console.error('[ConnectionGuard] Max reconnection attempts reached');
      this.callbacks.onMaxReconnectReached?.();
      return;
    }

    this.state.reconnectAttempts++;
    
    console.log(`[ConnectionGuard] Reconnection attempt ${this.state.reconnectAttempts}/${this.state.maxReconnectAttempts} in ${this.state.reconnectDelay}ms`);
    
    this.callbacks.onReconnectAttempt?.(this.state.reconnectAttempts);

    this.reconnectTimeout = setTimeout(() => {
      this.attemptReconnection();
    }, this.state.reconnectDelay);
  }

  /**
   * Attempt reconnection
   */
  private async attemptReconnection(): Promise<void> {
    try {
      // This would be implemented by the specific connection type
      // For now, we'll emit an event that the connection manager can handle
      const event = new CustomEvent('attemptReconnection', {
        detail: {
          attempt: this.state.reconnectAttempts,
          maxAttempts: this.state.maxReconnectAttempts,
        }
      });
      window.dispatchEvent(event);

      // Increase backoff for next attempt
      this.state.reconnectDelay = Math.min(
        this.state.reconnectDelay * this.reconnectBackoffMultiplier,
        this.maxReconnectDelay
      );

    } catch (error) {
      console.error('[ConnectionGuard] Reconnection attempt failed:', error);
      
      // Schedule next attempt
      this.startReconnection();
    }
  }

  /**
   * Manually trigger reconnection
   */
  manualReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.state.reconnectAttempts = 0;
    this.state.reconnectDelay = 3000;
    this.state.isReconnecting = true;

    this.startReconnection();
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionGuardState {
    return { ...this.state };
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.state.isConnected;
  }

  /**
   * Check if reconnecting
   */
  isReconnecting(): boolean {
    return this.state.isReconnecting;
  }

  /**
   * Reset connection guard
   */
  reset(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.state = {
      isConnected: false,
      isReconnecting: false,
      reconnectAttempts: 0,
      maxReconnectAttempts: 10,
      lastError: null,
      reconnectDelay: 3000,
    };
  }

  /**
   * Set max reconnection attempts
   */
  setMaxReconnectAttempts(maxAttempts: number): void {
    this.state.maxReconnectAttempts = maxAttempts;
  }
}

// Create singleton instance
const connectionGuard = new ConnectionGuard();

export default connectionGuard;
export { ConnectionGuard };

/**
 * React hook for connection guard state
 */
export function useConnectionGuard() {
  const [guardState, setGuardState] = useState<ConnectionGuardState>(connectionGuard.getState());

  useEffect(() => {
    const updateState = () => {
      setGuardState(connectionGuard.getState());
    };

    // Listen for connection guard events
    const handleConnectionLost = () => {
      updateState();
    };

    const handleConnectionRestored = () => {
      updateState();
    };

    const handleReconnectAttempt = () => {
      updateState();
    };

    window.addEventListener('connectionLost', handleConnectionLost);
    window.addEventListener('connectionRestored', handleConnectionRestored);
    window.addEventListener('reconnectAttempt', handleReconnectAttempt);

    // Update state periodically
    const interval = setInterval(updateState, 1000);

    return () => {
      window.removeEventListener('connectionLost', handleConnectionLost);
      window.removeEventListener('connectionRestored', handleConnectionRestored);
      window.removeEventListener('reconnectAttempt', handleReconnectAttempt);
      clearInterval(interval);
    };
  }, []);

  return {
    ...guardState,
    manualReconnect: () => connectionGuard.manualReconnect(),
  };
}
