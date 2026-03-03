import { useEffect, useState } from "react"

export function useConnectionGuard() {

  const [isConnected, setIsConnected] = useState(true)
  const [isReconnecting, setIsReconnecting] = useState(false)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [lastError, setLastError] = useState<string | null>(null)

  useEffect(() => {

    function handleOnline() {
      console.log("🌐 Browser online")
      setIsConnected(true)
      setIsReconnecting(false)
      setLastError(null)
    }

    function handleOffline() {
      console.log("🚫 Browser offline")
      setIsConnected(false)
      setLastError("Browser offline")
    }

    window.addEventListener("online", handleOnline)
    window.addEventListener("offline", handleOffline)

    return () => {
      window.removeEventListener("online", handleOnline)
      window.removeEventListener("offline", handleOffline)
    }

  }, [])

  return {
    isConnected,
    isReconnecting,
    reconnectAttempts,
    lastError
  }
}
