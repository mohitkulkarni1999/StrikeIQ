import { useWSStore } from "@/core/ws/wsStore"

export function useDashboardData() {

  const spot = useWSStore((s) => s.spot)
  const optionChain = useWSStore((s) => s.optionChain)

  const calls = optionChain?.calls ?? []
  const puts = optionChain?.puts ?? []
  const connected = useWSStore((s) => s.connected)

  return {
    spot,
    calls,
    puts,
    connected
  }
}
