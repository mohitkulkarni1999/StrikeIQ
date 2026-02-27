import { useState, useEffect, useRef } from "react"
import { useWSStore } from "@/core/ws/wsStore"
import { clearWSInitialized } from "@/core/ws/wsInitController"

export interface LiveMarketData {
  symbol: string
  spot: number
  timestamp: string
  optionChain?: {
    symbol: string
    spot: number
    expiry: string
    calls: any[]
    puts: any[]
  } | null
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
    optionChain,
    lastUpdate,
    connected,
    connect
  } = useWSStore()

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
  TRANSFORM STORE DATA → UI DATA
  -------------------------------
  */

  useEffect(() => {

    if (spot === 0) return

    const transformed: LiveMarketData = {

      symbol,

      spot,

      timestamp: new Date(lastUpdate).toISOString(),

      optionChain: optionChain
        ? {
            symbol,
            spot,
            expiry: expiry || "",
            calls: optionChain.calls || [],
            puts: optionChain.puts || []
          }
        : null

    }

    setData(transformed)
    setMode("live")
    setLoading(false)
    setError(null)

  }, [spot, optionChain, lastUpdate])

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