import { useEffect, useState } from "react"

export function useWebSocketHeartbeat() {

  const [isConnected, setIsConnected] = useState(false)
  const [lastHeartbeat, setLastHeartbeat] = useState<number | null>(null)

  useEffect(() => {

    const socket = (window as any).STRIKEIQ_WS_INSTANCE

    if (!socket) return

    function handleHeartbeat() {
      setLastHeartbeat(Date.now())
      setIsConnected(true)
    }

    function handleClose() {
      setIsConnected(false)
    }

    socket.addEventListener("message", (event: MessageEvent) => {

      let data

      try {
        data = JSON.parse(event.data)
      } catch {
        return
      }

      if (data.type === "heartbeat") {
        handleHeartbeat()
      }

    })

    socket.addEventListener("close", handleClose)

    return () => {
      socket.removeEventListener("close", handleClose)
    }

  }, [])

  return {
    isConnected,
    lastHeartbeat
  }
}
