/**
 * Market Session Service - DISABLED
 * Market status now comes via WebSocket only
 * This service is kept for emergency fallback only
 */

import api from '../api/axios';

let pollingStarted = false;
let pollingInterval: NodeJS.Timeout | null = null;

export interface MarketSessionData {
    market_status: 'OPEN' | 'CLOSED' | 'PRE_OPEN' | 'OPENING_END' | 'CLOSING' | 'CLOSING_END' | 'HALTED' | 'UNKNOWN';
    engine_mode: 'LIVE' | 'SNAPSHOT' | 'HALTED' | 'OFFLINE';
    data_source: 'websocket_stream' | 'rest_snapshot';
    last_check?: string;
    is_polling?: boolean;
}

export interface MarketSessionResponse {
    status: 'success' | 'error';
    data?: MarketSessionData;
    error?: string;
}

/**
 * Fetch market session status from backend - DISABLED
 * Components must NEVER call this directly
 * Market status now comes via WebSocket messages
 */
async function fetchSession(): Promise<void> {
    console.warn("⚠️ Market session polling is disabled - using WebSocket only");
    return;
}

/**
 * Start market session polling - DISABLED
 * Market status now comes via WebSocket messages
 */
export function startMarketPolling(): void {
    console.warn("⚠️ Market session polling is disabled - using WebSocket only");
    return;
}

/**
 * Stop market session polling - DISABLED
 */
export function stopMarketPolling(): void {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        pollingStarted = false;
        console.log('🛑 Market session polling stopped (was disabled anyway)');
    }
}

/**
 * Get current polling status - ALWAYS FALSE
 */
export function isSessionPollingActive(): boolean {
    return false; // Polling is disabled
}

// Export fetchSession for testing only - components should NOT use this
export { fetchSession };
