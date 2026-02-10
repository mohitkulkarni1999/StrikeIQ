import { MarketData } from '../types/market';
import BiasMeter from './BiasMeter';
import ExpectedMoveChart from './ExpectedMoveChart';
import SmartMoneyActivity from './SmartMoneyActivity';
import MarketMetrics from './MarketMetrics';
import OIHeatmap from './OIHeatmap';
import SignalCards from './SignalCards';

interface DashboardProps {
  data: MarketData | null;
}

export default function Dashboard({ data }: DashboardProps) {
  if (!data) {
    return (
      <div className="text-center text-muted-foreground">
        No market data available
      </div>
    );
  }

  // Check if market is closed
  const isMarketClosed = data.current_market?.market_status === "CLOSED";
  const hasError = data.current_market?.market_status === "ERROR";

  if (isMarketClosed) {
    return (
      <div className="space-y-6">
        {/* Market Closed Banner */}
        <div className="glass-morphism rounded-xl p-6 border-2 border-orange-500/20">
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-semibold text-orange-400 mb-2">
                Market Closed
              </h2>
              <p className="text-muted-foreground mb-4">
                {data.current_market?.message || "Market is currently closed"}
              </p>
              <div className="text-sm text-muted-foreground">
                <p>📈 Live data available during:</p>
                <p className="font-semibold">9:15 AM - 3:30 PM (Weekdays)</p>
              </div>
            </div>
          </div>
        </div>

        {/* Symbol Header */}
        <div className="glass-morphism rounded-xl p-6">
          <h2 className="text-2xl font-semibold mb-2">
            {data.current_market.symbol}
          </h2>
          <p className="text-muted-foreground">
            Waiting for market to open...
          </p>
        </div>
      </div>
    );
  }

  if (hasError) {
    return (
      <div className="space-y-6">
        {/* Error Banner */}
        <div className="glass-morphism rounded-xl p-6 border-2 border-red-500/20">
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h2 className="text-2xl font-semibold text-red-400 mb-2">
                Data Unavailable
              </h2>
              <p className="text-muted-foreground">
                {data.current_market?.message || "Unable to fetch live data"}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Market Status */}
      <div className="glass-morphism rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold mb-2">
              {data.current_market.symbol}
            </h2>
            <div className="flex items-center gap-4">
              <span className="text-3xl font-bold">
                {data.current_market.spot_price ? 
                  `₹${data.current_market.spot_price.toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}` : 
                  'Loading...'
                }
              </span>
              {data.current_market.change !== null && data.current_market.change !== undefined && (
                <span
                  className={`text-lg font-medium ${
                    data.current_market.change >= 0
                      ? 'text-success-500'
                      : 'text-danger-500'
                  }`}
                >
                  {data.current_market.change >= 0 ? '+' : ''}
                  {data.current_market.change.toFixed(2)} (
                  {data.current_market.change_percent >= 0 ? '+' : ''}
                  {(data.current_market.change_percent * 100).toFixed(2)}%)
                </span>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground mb-1">Market Status</div>
            <div className="flex items-center gap-2">
              <div
                className={`status-indicator ${
                  data.market_status === 'open' ? 'status-online' : 'status-offline'
                }`}
              ></div>
              <span className="capitalize">{data.market_status}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bias Meter - Takes 1/3 width */}
        <div className="lg:col-span-1">
          <BiasMeter signals={data.real_time_signals} />
        </div>

        {/* Expected Move Chart - Takes 2/3 width */}
        <div className="lg:col-span-2">
          <ExpectedMoveChart signals={data.real_time_signals} />
        </div>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Smart Money Activity */}
        <SmartMoneyActivity signals={data.real_time_signals} />

        {/* Market Metrics */}
        <MarketMetrics data={data} />
      </div>

      {/* Third Row - Signal Cards */}
      <SignalCards signals={data.real_time_signals} />

      {/* OI Heatmap - Full Width */}
      <OIHeatmap symbol={data.current_market.symbol} />
    </div>
  );
}
