/**
 * API Throttling Utility for StrikeIQ Frontend
 * 
 * Prevents excessive API calls by implementing rate limiting
 * across all components that poll market session endpoints.
 */

class APIThrottler {
  private static instance: APIThrottler;
  private lastCallTime: Map<string, number> = new Map();
  private minInterval: number = 10000; // 10 seconds minimum interval

  private constructor() {}

  static getInstance(): APIThrottler {
    if (!APIThrottler.instance) {
      APIThrottler.instance = new APIThrottler();
    }
    return APIThrottler.instance;
  }

  /**
   * Check if an API call can be made based on rate limiting
   * @param endpoint - API endpoint identifier
   * @param customInterval - Optional custom interval in milliseconds
   * @returns boolean - True if call can be made
   */
  canMakeCall(endpoint: string, customInterval?: number): boolean {
    const now = Date.now();
    const lastCall = this.lastCallTime.get(endpoint) || 0;
    const interval = customInterval || this.minInterval;
    
    if (now - lastCall >= interval) {
      this.lastCallTime.set(endpoint, now);
      return true;
    }
    
    return false;
  }

  /**
   * Get time until next allowed call
   * @param endpoint - API endpoint identifier
   * @param customInterval - Optional custom interval in milliseconds
   * @returns number - Milliseconds until next call
   */
  getTimeUntilNextCall(endpoint: string, customInterval?: number): number {
    const now = Date.now();
    const lastCall = this.lastCallTime.get(endpoint) || 0;
    const interval = customInterval || this.minInterval;
    const timeSinceLastCall = now - lastCall;
    
    return Math.max(0, interval - timeSinceLastCall);
  }

  /**
   * Reset throttling for a specific endpoint
   * @param endpoint - API endpoint identifier
   */
  reset(endpoint: string): void {
    this.lastCallTime.delete(endpoint);
  }

  /**
   * Set custom minimum interval
   * @param interval - Minimum interval in milliseconds
   */
  setMinInterval(interval: number): void {
    this.minInterval = Math.max(1000, interval); // Minimum 1 second
  }
}

// Export singleton instance
export const apiThrottler = APIThrottler.getInstance();

// Export specific endpoint constants
export const API_ENDPOINTS = {
  MARKET_SESSION: 'market_session',
  MARKET_DATA: 'market_data',
  WEBSOCKET_INIT: 'websocket_init',
} as const;

// Export interval constants
export const API_INTERVALS = {
  FAST: 5000,      // 5 seconds - for critical real-time data
  NORMAL: 10000,   // 10 seconds - for regular polling
  SLOW: 30000,     // 30 seconds - for background updates
  BACKOFF: 60000,  // 60 seconds - for error recovery
} as const;
