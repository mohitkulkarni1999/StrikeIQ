import { useState, useEffect, useRef } from "react"
import { useWSStore } from "@/core/ws/wsStore"
import { useOptionChainStore } from "@/core/ws/optionChainStore"
import { clearWSInitialized } from "@/core/ws/wsInitController"
import { throttle } from "@/utils/throttle"

export interface LiveMarketData {
  symbol: string
  spot: number
  timestamp: string
  change?: number
  change_percent?: number
  available_expiries?: string[]
  optionChain?: {
    symbol: string
    spot: number
    expiry: string
    calls: any[]
    puts: any[]
  } | null
  intelligence?: {
    interpretation: {
      narrative: string | null;
      risk_context: string | null;
      positioning_context: string | null;
      contradiction_flags: string[];
      confidence_tone: 'high' | 'medium' | 'cautious';
      interpreted_at?: string;
      fallback?: boolean;
    };
  };
}

export const WS_BACKEND_ONLINE_EVENT = "strikeiq:backend-online"

export function useLiveMarketData(symbol: string, expiry: string | null) {

  const initializedRef = useRef(false)
  const connectedRef = useRef(false)

  const [data, setData] = useState<LiveMarketData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [mode, setMode] = useState<"loading" | "snapshot" | "live" | "error">("loading")

  const {
    spot,
    lastUpdate,
    connected,
    connect
  } = useWSStore()

  const {
    optionChainData,
    optionChainLastUpdate,
    optionChainConnected
  } = useOptionChainStore()

  /*
  -------------------------------
  CONNECT WEBSOCKET
  -------------------------------
  */

  useEffect(() => {

    if (connectedRef.current) return
    connectedRef.current = true

    if (symbol && expiry) {
      connect(symbol, expiry)
    }

  }, [symbol, expiry])

  /*
  -------------------------------
  TRANSFORM STORE DATA → UI DATA (THROTTLED)
  -------------------------------
  */

  // Create throttled update function (100ms delay)
  const throttledSetData = useRef(
    throttle((transformedData: LiveMarketData) => {
      setData(transformedData);
      setMode("live");
      setLoading(false);
      setError(null);
    }, 100)
  ).current;

  useEffect(() => {

    if (spot === 0 && !optionChainData) return

    const transformed: LiveMarketData = {

      symbol,

      spot: spot || optionChainData?.spot || 0,

      timestamp: new Date(lastUpdate || optionChainLastUpdate).toISOString(),

      available_expiries: [],

      optionChain: optionChainData
        ? {
            symbol: optionChainData.symbol || symbol,
            spot: optionChainData.spot || spot,
            expiry: optionChainData.expiry || expiry || "",
            calls: optionChainData.calls || [],
            puts: optionChainData.puts || []
          }
        : null

    }

    // Use throttled update instead of direct setState
    throttledSetData(transformed)

  }, [spot, optionChainData, lastUpdate, optionChainLastUpdate, symbol, expiry])

  /*
  -------------------------------
  CONNECTION STATUS
  -------------------------------
  */

  useEffect(() => {

    if (!connected) {

      setLoading(true)
      setMode("loading")

    }

  }, [connected])

  /*
  -------------------------------
  BACKEND RESTART HANDLER
  -------------------------------
  */

  useEffect(() => {

    const handleBackendOnline = () => {

      const store = useWSStore.getState()

      store.disconnect()

      clearWSInitialized()

      setMode("loading")
      setLoading(true)
      setError(null)

      if (symbol && expiry) {
        connect(symbol, expiry)
      }

    }

    window.addEventListener(WS_BACKEND_ONLINE_EVENT, handleBackendOnline)

    return () => {
      window.removeEventListener(WS_BACKEND_ONLINE_EVENT, handleBackendOnline)
    }

  }, [symbol, expiry])

  /*
  -------------------------------
  RETURN DATA
  -------------------------------
  */

  return {

    data,

    loading,

    error,

    mode,

    connected,

    symbol,

    lastUpdate: data?.timestamp || new Date().toISOString(),

    availableExpiries: []

  }

}