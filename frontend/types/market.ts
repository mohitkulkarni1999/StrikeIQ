export interface OptionChainData {
  strike_price: number;
  expiry_date: string;
  call_oi: number;
  put_oi: number;
  call_volume: number;
  put_volume: number;
  call_change_oi: number;
  put_change_oi: number;
  call_iv: number;
  put_iv: number;
  call_ltp: number;
  put_ltp: number;
}

export interface MarketBias {
  bias: 'Bullish' | 'Bearish' | 'Neutral';
  confidence: number;
  components: {
    price_vs_vwap: {
      signal: number;
      direction: string;
    };
    oi_change: {
      signal: number;
      direction: string;
    };
    pcr: {
      signal: number;
      direction: string;
    };
    divergence: {
      detected: boolean;
      strength: number;
    };
  };
  scores: {
    bullish: number;
    bearish: number;
    net: number;
  };
}

export interface ExpectedMove {
  spot_price: number;
  expected_move: number;
  upper_range: number;
  lower_range: number;
  upper_percentage: number;
  lower_percentage: number;
  straddle_premium: number;
  atm_strikes: {
    call_strike: number;
    put_strike: number;
    atm_strike: number;
  };
  call_premium: number;
  put_premium: number;
  days_to_expiry: number;
}

export interface BreakoutConditions {
  breakout_detected: boolean;
  breakout_type: string | null;
  breakout_strength: number;
  risk_level: string;
  upper_distance: number;
  lower_distance: number;
  range_utilization: number;
}

export interface SmartMoneyActivity {
  type: string;
  strike_price: number;
  expiry_date: string;
  oi_change?: number;
  volume?: number;
  signal_strength: number;
  premium?: number;
  confidence: string;
  [key: string]: any;
}

export interface SmartMoneyAnalysis {
  overall_activity: 'low' | 'medium' | 'high';
  dominant_activity: string | null;
  risk_level: string;
  activities: SmartMoneyActivity[];
  activity_counts: {
    call_writing: number;
    put_writing: number;
    long_buildup: number;
    short_buildup: number;
    trap_zones: number;
  };
  total_strength: number;
  summary: string;
}

export interface CurrentMarket {
  symbol: string;
  spot_price: number | null;
  vwap: number | null;
  change: number | null;
  change_percent: number | null;
  volume: number | null;
  timestamp: string;
  market_status?: 'OPEN' | 'CLOSED' | 'ERROR';
  message?: string;
}

export interface RealTimeSignals {
  timestamp: string;
  bias_signal: {
    action: string;
    strength: string;
    confidence: number;
  };
  expected_move_signal: {
    signal: string;
    action: string;
    distance: number;
  };
  smart_money_signal: {
    signal: string;
    action: string;
    activities?: string[];
  };
  overall_signal: {
    action: string;
    strength: string;
    confidence: number;
    reasoning: string;
  };
}

export interface HistoricalData {
  timestamp: string;
  bias: string;
  confidence: number;
  price_vs_vwap: number;
  oi_change_5min: number;
  pcr: number;
  expected_move: number;
  expected_move_upper: number;
  expected_move_lower: number;
}

export interface MarketData {
  current_market: CurrentMarket;
  real_time_signals: RealTimeSignals;
  historical_analysis: HistoricalData[];
  market_status: string;
  message?: string;
}
