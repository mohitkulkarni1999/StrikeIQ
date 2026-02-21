export interface MarketData {
  symbol: string;
  spot_price: number | null;
  previous_close: number | null;
  change: number | null;
  change_percent: number | null;
  vwap: number | null;
  timestamp: string;
  market_status: 'OPEN' | 'CLOSED' | 'ERROR';
  exchange_timestamp?: string;
}

export interface AuthRequiredData {
  session_type: 'AUTH_REQUIRED';
  mode: 'AUTH';
  message: string;
  login_url: string;
  timestamp: string;
}

export interface RateLimitData {
  session_type: 'RATE_LIMIT';
  message: string;
  timestamp: string;
}

export interface MarketBiasData {
  symbol: string;
  price_vs_vwap: number;
  vwap: number;
  current_price: number;
  oi_change_5min: number;
  pcr: number;
  divergence_detected: boolean;
  divergence_type: string;
  bias_strength: number;
  timestamp: string;
}

export interface ExpectedMoveData {
  symbol: string;
  spot: number;
  atm_call_premium: number;
  atm_put_premium: number;
  combined_premium: number;
  expected_move_1sd: number;
  expected_move_2sd: number;
  breakout_detected: boolean;
  breakout_direction: string;
  breakout_strength: number;
  implied_volatility: number;
  time_to_expiry: number;
  timestamp: string;
}

export interface SmartMoneyData {
  symbol: string;
  call_writing_detected: boolean;
  put_writing_detected: boolean;
  call_writing_strength: number;
  put_writing_strength: number;
  long_buildup_detected: boolean;
  short_buildup_detected: boolean;
  buildup_strength: number;
  net_smart_money_flow: string;
  institutional_activity_score: number;
  key_observations: string[];
  timestamp: string;
}

export interface OptionChainData {
  calls?: Array<{
    strike: number;
    oi: number;
    ltp: number;
    iv: number;
    open_interest?: number;  // Made optional since not always present
  }>;
  puts?: Array<{
    strike: number;
    oi: number;
    ltp: number;
    iv: number;
    open_interest?: number;  // Made optional since not always present
  }>;
  top_strikes?: Array<{
    strike: number;
    call_oi: number;
    put_oi: number;
    total_oi: number;
    oi_concentration: number;
  }>;
  pcr_summary?: {
    put_call_ratio: number;
    interpretation: string;
    signal: 'bullish' | 'bearish' | 'neutral';
  };
  key_levels?: {
    resistance: number[];
    support: number[];
    max_oi_strike: number;
    max_oi_value: number;
  };
}

export interface MarketStatusData {
  market_status: 'OPEN' | 'CLOSED';
  server_time: string;
  websocket_status: 'CONNECTED' | 'DISCONNECTED';
  symbol_supported: string[];
}

// Unified WebSocket Payload Type
export interface WebSocketPayload {
  status: string;
  symbol: string;
  spot: number;
  expected_move: number;
  net_gamma: number;
  gamma_flip_level: number;
  distance_from_flip: number;
  call_oi_velocity: number;
  put_oi_velocity: number;
  flow_imbalance: number;
  flow_direction: string;
  structural_regime: string;
  regime_confidence: number;
  regime_stability: number;
  acceleration_index: number;
  pin_probability: number;
  alerts: Array<{
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    message: string;
    timestamp: string;
  }>;
  gamma_pressure_map: Record<string, any>;
  flow_gamma_interaction: Record<string, any>;
  regime_dynamics: Record<string, any>;
  expiry_magnet_analysis: Record<string, any>;
  market_bias: MarketBiasData;
  expected_move_data: ExpectedMoveData;
  smart_money_activity: SmartMoneyData;
  option_chain_intelligence: OptionChainData;
  // Backend ATM fields
  rest_spot_price?: number;
  ws_tick_price?: number;
  current_atm_strike?: number;
  atm_last_updated?: string;
  ws_last_update_ts?: string;
  rest_last_update?: string;
}

export type DashboardResponse = MarketData | AuthRequiredData | RateLimitData;

export function isAuthRequired(data: DashboardResponse): data is AuthRequiredData {
  return 'session_type' in data && data.session_type === 'AUTH_REQUIRED';
}

export function isRateLimit(data: DashboardResponse): data is RateLimitData {
  return 'session_type' in data && data.session_type === 'RATE_LIMIT';
}

export function isMarketData(data: DashboardResponse): data is MarketData {
  return !isAuthRequired(data) && !isRateLimit(data);
}
