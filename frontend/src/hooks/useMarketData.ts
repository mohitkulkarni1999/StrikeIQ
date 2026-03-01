/**
 * Hook to access live market data from WebSocket store
 * Provides persistent access to market_data without closing connection
 */

import { useWSStore } from '../core/ws/wsStore';

export function useMarketData() {
  const marketData = useWSStore((state) => state.marketData);
  const isConnected = useWSStore((state) => state.isConnected);
  const error = useWSStore((state) => state.error);

  return {
    data: marketData,
    isConnected,
    error,
    loading: !marketData && isConnected
  };
}
