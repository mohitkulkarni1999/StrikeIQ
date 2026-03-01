/**
 * Smart Money Bias Field Mapping Layer
 * Maps backend smart money engine output to frontend bias interface
 */

export interface BackendBiasData {
  signal: string;      // BULLISH | BEARISH | NEUTRAL
  confidence: number;  // 0-100
  direction: string;    // UP | DOWN | NONE
  strength: number;    // 0-100
  reason: string;
}

export interface FrontendBiasData {
  score: number;       // Maps to confidence
  label: string;       // Maps to signal
  confidence: number;  // Same as backend
  signal: string;      // Same as backend
  direction: string;    // Same as backend
  strength: number;    // Same as backend
}

/**
 * Maps backend bias data to frontend bias interface
 */
export function mapBiasData(backendData: BackendBiasData): FrontendBiasData {
  return {
    score: backendData.confidence,
    label: backendData.signal,
    confidence: backendData.confidence,
    signal: backendData.signal,
    direction: backendData.direction,
    strength: backendData.strength
  };
}

/**
 * Safe bias data mapping with fallbacks
 */
export function safeMapBiasData(backendData: any): FrontendBiasData {
  if (!backendData || typeof backendData !== 'object') {
    return getFallbackBiasData();
  }

  return {
    score: typeof backendData.confidence === 'number' ? backendData.confidence : 0,
    label: typeof backendData.signal === 'string' ? backendData.signal : 'NEUTRAL',
    confidence: typeof backendData.confidence === 'number' ? backendData.confidence : 0,
    signal: typeof backendData.signal === 'string' ? backendData.signal : 'NEUTRAL',
    direction: typeof backendData.direction === 'string' ? backendData.direction : 'NONE',
    strength: typeof backendData.strength === 'number' ? backendData.strength : 0
  };
}

/**
 * Returns safe fallback bias data
 */
function getFallbackBiasData(): FrontendBiasData {
  return {
    score: 0,
    label: 'NEUTRAL',
    confidence: 0,
    signal: 'NEUTRAL',
    direction: 'NONE',
    strength: 0
  };
}
