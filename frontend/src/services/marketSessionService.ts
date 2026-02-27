/**
 * Market Session Service - Prevents duplicate polling
 * Ensures polling starts only once and runs at 10-second intervals
 */

let sessionPollingStarted = false;
let sessionPollingInterval: NodeJS.Timeout | null = null;

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
 * Fetch market session status from backend
 */
async function fetchSession(): Promise<MarketSessionResponse> {
    try {
        const response = await fetch('/api/v1/market/session');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Market session fetch error:', error);
        return {
            status: 'error',
            error: error instanceof Error ? error.message : 'Failed to fetch market session'
        };
    }
}

/**
 * Start market session polling - only once per application lifecycle
 */
export function startMarketSessionPolling(): void {
    if (sessionPollingStarted) {
        console.log('🔒 Market session polling already started - skipping');
        return;
    }

    sessionPollingStarted = true;
    console.log('🚀 Starting market session polling (10s interval)');

    // Initial fetch
    fetchSession();

    // Set up polling every 10 seconds
    sessionPollingInterval = setInterval(fetchSession, 10000);
}

/**
 * Stop market session polling
 */
export function stopMarketSessionPolling(): void {
    if (sessionPollingInterval) {
        clearInterval(sessionPollingInterval);
        sessionPollingInterval = null;
        sessionPollingStarted = false;
        console.log('🛑 Market session polling stopped');
    }
}

/**
 * Get current polling status
 */
export function isSessionPollingActive(): boolean {
    return sessionPollingStarted && sessionPollingInterval !== null;
}

/**
 * Manual fetch without affecting polling
 */
export { fetchSession };
