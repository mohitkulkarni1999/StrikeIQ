import { useState, useEffect } from 'react';

interface OptionChainResponse {
  symbol: string;
  expiry: string;
  calls: Array<{
    strike: number;
    call_oi: number;
    put_oi: number;
    call_ltp: number;
    put_ltp: number;
    call_volume: number;
    put_volume: number;
    call_iv: number;
    put_iv: number;
    call_change: number;
    put_change: number;
  }>;
  puts: Array<{
    strike: number;
    call_oi: number;
    put_oi: number;
    call_ltp: number;
    put_ltp: number;
    call_volume: number;
    put_volume: number;
    call_iv: number;
    put_iv: number;
    call_change: number;
    put_change: number;
  }>;
  spot?: number;  // Add spot price field
  analytics: {
    total_call_oi: number;
    total_put_oi: number;
    pcr: number;
    strongest_resistance: number;
    strongest_support: number;
    bias_score: number;
    bias_label: string;
    oi_dominance: number;
    position_score: number;
    pcr_strength: number;
  };
  intelligence?: {
    bias: {
      score: number;
      label: string;
      strength: number;
      direction: string;
      confidence: number;
      signal: string;
    };
    volatility: {
      current: string;
      percentile: number;
      trend: string;
      risk: string;
      environment: string;
    };
    liquidity: {
      total_oi: number;
      oi_change_24h: number;
      concentration: number;
      depth_score: number;
      flow_direction: string;
    };
    probability?: {
      expected_move: number;
      upper_1sd: number;
      lower_1sd: number;
      upper_2sd: number;
      lower_2sd: number;
      breach_probability: number;
      range_hold_probability: number;
      volatility_state: string;
    };
    timestamp: string;
    confidence: number;
  } | null;
  timestamp: string;
  total_strikes: number;
}

interface UseMarketDataReturn {
  data: OptionChainResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useMarketData(symbol: string, expiry: string): UseMarketDataReturn {
  const [data, setData] = useState<OptionChainResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // API call with expiry parameter - backend requires it
      const response = await fetch(`/api/v1/options/chain/${symbol}?expiry_date=${expiry}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('🔍 Raw API Response:', result);
      
      // Extract the actual data from the nested response structure
      const actualData = result.data;
      console.log('🔍 Extracted Data:', actualData);
      
      setData(actualData);
    } catch (err) {
      console.error('🔍 API Error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const refetch = () => {
    fetchData();
  };

  useEffect(() => {
    fetchData();
  }, [symbol, expiry]);

  return {
    data,
    loading,
    error,
    refetch
  };
}
