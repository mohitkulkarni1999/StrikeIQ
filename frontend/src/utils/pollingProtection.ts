/**
 * API Polling Protection Utility
 * Prevents duplicate intervals and excessive polling
 */

interface PollingInterval {
  id: string
  intervalId: NodeJS.Timeout
  createdAt: number
}

const activeIntervals = new Map<string, PollingInterval>()

export function createProtectedInterval(
  id: string,
  callback: () => void,
  ms: number
): NodeJS.Timeout | null {
  // Check if interval already exists
  if (activeIntervals.has(id)) {
    console.warn(`⚠️ Polling interval ${id} already exists, skipping creation`)
    return null
  }

  // Create new interval
  const intervalId = setInterval(callback, ms)
  
  // Store interval info
  activeIntervals.set(id, {
    id,
    intervalId,
    createdAt: Date.now()
  })

  console.log(`✅ Created polling interval ${id} (${ms}ms)`)
  return intervalId
}

export function clearProtectedInterval(id: string): boolean {
  const interval = activeIntervals.get(id)
  if (!interval) {
    console.warn(`⚠️ Polling interval ${id} not found`)
    return false
  }

  clearInterval(interval.intervalId)
  activeIntervals.delete(id)
  console.log(`🗑️ Cleared polling interval ${id}`)
  return true
}

export function clearAllProtectedIntervals(): void {
  activeIntervals.forEach((interval) => {
    clearInterval(interval.intervalId)
  })
  const count = activeIntervals.size
  activeIntervals.clear()
  console.log(`🗑️ Cleared ${count} polling intervals`)
}

export function getActiveIntervals(): string[] {
  return Array.from(activeIntervals.keys())
}

export function hasActiveInterval(id: string): boolean {
  return activeIntervals.has(id)
}

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', clearAllProtectedIntervals)
}
