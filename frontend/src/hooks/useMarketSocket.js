import { useEffect, useRef } from 'react';
import { useWSStore } from '@/core/ws/wsStore';

export function useMarketSocket() {
  const { connectToMarket, disconnect, handleMessage } = useWSStore((s) => s);
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) {
      return;
    }

    // Connect to market WebSocket (not live-options)
    connectToMarket('market', 'market');
    
    console.log('WS CONNECTED');
    initializedRef.current = true;

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, []);

  return {
    getConnectionStatus: () => {
      const state = useWSStore.getState();
      return state.connected;
    }
  };
}
