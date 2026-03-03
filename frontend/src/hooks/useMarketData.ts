/**
 * Hook to access live market data from WebSocket store
 * Provides persistent access to market_data without closing connection
 */

import { useWSStore } from '../core/ws/wsStore';

export function useMarketData() {
  const marketData = useWSStore((state) => state.marketData);
  const connected = useWSStore((state) => state.connected);
  const error = useWSStore((state) => state.error);

  return {
    data: marketData,
    isConnected: connected,
    error,
    loading: !marketData && connected
  };
}
