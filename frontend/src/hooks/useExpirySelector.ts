/**
 * useExpirySelector - FINAL PRODUCTION STABILITY PATCH
 * Fetches expiries ONLY when symbol changes from store.
 * Prevents API spam with ref guard and strict dependency array.
 */

import { useState, useEffect, useRef } from 'react';
import { fetchAvailableExpiries } from '@/api/marketApi';
import { useMarketStore } from '@/stores/marketStore';
import { useOptionChainStore } from '@/core/ws/optionChainStore';

export const useExpirySelector = () => {
  const [expiryList, setExpiryList] = useState<string[]>([]);
  const [selectedExpiry, setSelectedExpiry] = useState<string | null>(null);
  const [loadingExpiries, setLoadingExpiries] = useState(false);
  const [expiryError, setExpiryError] = useState<string | null>(null);

  // Read symbol from store - no props needed
  const currentSymbol = useMarketStore(state => state.currentSymbol);
  const { optionChainConnected } = useOptionChainStore();

  const lastFetchedSymbolRef = useRef<string | null>(null)

  useEffect(() => {

    async function loadExpiries() {

      if (lastFetchedSymbolRef.current === currentSymbol) {
        return
      }

      const res = await fetch(`/api/v1/market/expiries?symbol=${currentSymbol}`)

      const data = await res.json()

      setExpiryList(data)

      lastFetchedSymbolRef.current = currentSymbol
    }

    loadExpiries()

  }, [currentSymbol])

  const handleExpiryChange = (expiry: string) => {
    setSelectedExpiry(expiry);
  };

  return {
    expiryList,
    selectedExpiry,
    loadingExpiries,
    expiryError,
    handleExpiryChange,
    optionChainConnected,
    currentSymbol
  };
};
