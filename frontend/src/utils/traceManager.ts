export function getTraceId() {
  return Math.random().toString(36).substring(2, 8).toUpperCase()
}

export function withTraceId<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  context: string
): T {
  return (async (...args: Parameters<T>) => {
    const traceId = getTraceId()
    console.debug(`[${context}] START`, { traceId })
    
    try {
      const result = await fn(...args)
      console.debug(`[${context}] SUCCESS`, { traceId })
      return result
    } catch (error) {
      console.error(`[${context}] ERROR`, { traceId, error })
      throw error
    }
  }) as T
}
