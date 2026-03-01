import { useState, useEffect } from 'react';
import { fetchAvailableExpiries } from '@/api/marketApi';
import { useOptionChainStore } from '@/core/ws/optionChainStore';

export const useExpirySelector = (symbol: string) => {
  const [expiryList, setExpiryList] = useState<string[]>([]);
  const [selectedExpiry, setSelectedExpiry] = useState<string | null>(null);
  const [loadingExpiries, setLoadingExpiries] = useState(false);
  const [expiryError, setExpiryError] = useState<string | null>(null);

  const { connectOptionChain, disconnectOptionChain, optionChainConnected } = useOptionChainStore();

  // Fetch available expiries when symbol changes
  useEffect(() => {
    const loadExpiries = async () => {
      if (!symbol) return;

      setLoadingExpiries(true);
      setExpiryError(null);

      try {
        const expiries = await fetchAvailableExpiries(symbol);
        setExpiryList(expiries);

        // Auto-select the nearest expiry if none is selected
        if (expiries.length > 0 && !selectedExpiry) {
          setSelectedExpiry(expiries[0]);
        }
      } catch (error) {
        setExpiryError('Failed to load expiries');
        console.error('Error loading expiries:', error);
      } finally {
        setLoadingExpiries(false);
      }
    };

    loadExpiries();
  }, [symbol]);

  // Handle expiry change - reconnect option chain WebSocket
  useEffect(() => {
    if (symbol && selectedExpiry) {
      // Disconnect existing connection
      disconnectOptionChain();
      
      // Small delay to ensure clean disconnection
      const timeoutId = setTimeout(() => {
        connectOptionChain(symbol, selectedExpiry);
      }, 100);

      return () => clearTimeout(timeoutId);
    }
  }, [symbol, selectedExpiry, connectOptionChain, disconnectOptionChain]);

  const handleExpiryChange = (expiry: string) => {
    setSelectedExpiry(expiry);
  };

  return {
    expiryList,
    selectedExpiry,
    loadingExpiries,
    expiryError,
    handleExpiryChange,
    optionChainConnected
  };
};
