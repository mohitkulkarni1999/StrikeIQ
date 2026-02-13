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
