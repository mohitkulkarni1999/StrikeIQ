/**
 * WebSocket Adapter Layer
 * Normalizes WS payload into consistent optionChain format
 */

export interface NormalizedOptionChain {
  calls: any[];
  puts: any[];
  spot: number;
  expiry: string;
}

export interface WSPayload {
  strikePrice?: number;
  CE?: any[];
  PE?: any[];
  symbol?: string;
  expiry?: string;
  optionChain?: any;
  spot?: number;
  calls?: any[];
  puts?: any[];
}

export class WebSocketAdapter {
  /**
   * Normalize WebSocket payload to consistent optionChain format
   */
  static normalizePayload(payload: WSPayload): NormalizedOptionChain | null {
    try {
      console.log('🔧 WS Adapter - Normalizing payload:', payload);

      // Handle different payload formats
      if (payload.optionChain) {
        // Already normalized format
        return {
          calls: payload.optionChain.calls || [],
          puts: payload.optionChain.puts || [],
          spot: payload.optionChain.spot || payload.spot || 0,
          expiry: payload.optionChain.expiry || payload.expiry || ''
        };
      }

      // Handle CE/PE format
      if (payload.CE && payload.PE) {
        return {
          calls: payload.CE,
          puts: payload.PE,
          spot: payload.strikePrice || payload.spot || 0,
          expiry: payload.expiry || ''
        };
      }

      // Handle direct calls/puts format
      if (payload.calls && payload.puts) {
        return {
          calls: payload.calls,
          puts: payload.puts,
          spot: payload.spot || 0,
          expiry: payload.expiry || ''
        };
      }

      console.warn('🔧 WS Adapter - Unknown payload format:', payload);
      return null;

    } catch (error) {
      console.error('🔧 WS Adapter - Error normalizing payload:', error);
      return null;
    }
  }

  /**
   * Validate normalized optionChain data
   */
  static validateOptionChain(optionChain: NormalizedOptionChain): boolean {
    return (
      optionChain !== null &&
      Array.isArray(optionChain.calls) &&
      Array.isArray(optionChain.puts) &&
      typeof optionChain.spot === 'number' &&
      optionChain.spot > 0
    );
  }

  /**
   * Extract expiry for Redis key format
   */
  static formatExpiryForRedis(symbol: string, expiry: string): string {
    if (!expiry) return symbol;
    
    // Convert YYYY-MM-DD to DDMMMYYYY format (e.g., "NIFTY:27FEB2026")
    const date = new Date(expiry);
    if (isNaN(date.getTime())) return symbol;
    
    const day = date.getDate();
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                   'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    const month = months[date.getMonth()];
    const year = date.getFullYear();
    
    return `${symbol}:${day}${month}${year}`;
  }

  /**
   * Generate cache key compatible with backend Redis format
   */
  static generateCacheKey(symbol: string, dataType: string, expiry?: string): string {
    const baseKey = `upstox:${dataType}:${symbol.toLowerCase()}`;
    if (expiry) {
      const redisExpiry = this.formatExpiryForRedis(symbol, expiry);
      return `${baseKey}:${redisExpiry}`;
    }
    return baseKey;
  }
}
