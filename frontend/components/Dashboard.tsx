import React, { useState, useEffect } from 'react';
import { DashboardResponse, isAuthRequired, isMarketData, MarketData } from '../types/dashboard';
import { useAuth } from '../contexts/AuthContext';
import BiasMeter from './BiasMeter';
import ExpectedMoveChart from './ExpectedMoveChart';
import SmartMoneyActivity from './SmartMoneyActivity';
import MarketMetrics from './MarketMetrics';
import OIHeatmap from './OIHeatmap';
import SignalCards from './SignalCards';
import AuthScreen from './AuthScreen';

interface DashboardProps {
  data: DashboardResponse | null;
  symbol: string;
}

function DashboardComponent({ data, symbol }: DashboardProps) {
  const { state: authState, handleAuthRequired } = useAuth();
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // Handle auth required responses
  useEffect(() => {
    // Only call handleAuthRequired if backend returns AUTH_REQUIRED
    if (data && isAuthRequired(data)) {
      handleAuthRequired(data);
      
      // Stop polling
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    }
  }, [data, handleAuthRequired, pollingInterval]);

  // Always render MarketDashboard - let it handle auth state internally
  console.log(`🔍 DashboardComponent: Rendering with symbol=${symbol}, data=${data ? 'exists' : 'null'}`);
  return <MarketDashboard marketData={data} symbol={symbol} authState={authState} />;

  // Setup polling for authenticated state
  useEffect(() => {
    if (!authState.isAuthenticated) return;
    
    const interval = setInterval(() => {
      // Trigger data refresh - this would be handled by parent component
      window.dispatchEvent(new CustomEvent('refreshData'));
    }, 60000); // Poll every 60 seconds
    
    return () => clearInterval(interval);
  }, []); // Empty dependencies - only run once

  // Stop polling listener
  useEffect(() => {
    const handleStopPolling = () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    };

    window.addEventListener('stopPolling', handleStopPolling);
    return () => window.removeEventListener('stopPolling', handleStopPolling);
  }, [pollingInterval]);

  // Show loading state
  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4 animate-spin">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <p className="text-white text-lg">Loading market data...</p>
        </div>
      </div>
    );
  }

  // Show auth screen if authentication required (fallback)
  if (data && isAuthRequired(data)) {
    return <AuthScreen authData={data} />;
  }

  // Show market data if authenticated
  if (data && isMarketData(data)) {
    return <MarketDashboard marketData={data} symbol={symbol} />;
  }

  // Fallback
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="text-center text-white">
        <p>Unknown response format</p>
      </div>
    </div>
  );
}

interface MarketDashboardProps {
  marketData: DashboardResponse | null;
  symbol: string;
  authState: any;
}

function MarketDashboard({ marketData, symbol, authState }: MarketDashboardProps) {
  const [analytics, setAnalytics] = useState<any>(null);
  
  console.log(`🔍 MarketDashboard: Received symbol=${symbol}, marketData.symbol=${marketData?.symbol}`);
  
  // Callback to receive analytics from OIHeatmap
  const handleAnalyticsUpdate = (analyticsData: any) => {
    setAnalytics(analyticsData);
  };
  
  // Show auth button if in AUTH mode (handle auth state here to avoid hooks issues)
  if (authState.mode === 'AUTH' && authState.loginUrl) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          <div className="glass-morphism rounded-2xl p-8 text-center">
            <div className="w-20 h-20 bg-orange-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            
            <h1 className="text-3xl font-bold text-white mb-2">Authentication Required</h1>
            <p className="text-gray-300 mb-8">Please authenticate to access market data</p>
            
            <button
              onClick={() => window.location.href = authState.loginUrl}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-orange-500/25"
            >
              Authenticate to Upstox
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Check if we have valid market data
  if (!marketData || !isMarketData(marketData)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center text-white">
          <p>Loading market data...</p>
        </div>
      </div>
    );
  }

  // Check if market is closed
  const isMarketClosed = marketData.market_status === "CLOSED";
  const hasError = marketData.market_status === "ERROR";
  
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
                Market is currently closed. Trading hours are 9:15 AM - 3:30 PM IST.
              </p>
              <div className="text-sm text-muted-foreground">
                <p>📈 Live data available during:</p>
                <p className="font-semibold">9:15 AM - 3:30 PM (Weekdays)</p>
              </div>
            </div>
          </div>
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
                Unable to fetch live data
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
              {symbol}
            </h2>
            <div className="flex items-center gap-4">
              <span className="text-3xl font-bold">
                {marketData.spot_price ? 
                  `₹${marketData.spot_price.toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}` : 
                  'Loading...'
                }
              </span>
              <div className="text-xs text-muted-foreground">
                Debug: marketData.symbol={marketData.symbol}, marketData.spot_price={marketData.spot_price}
              </div>
              {marketData.change !== null && marketData.change !== undefined && (
                <span
                  className={`text-lg font-medium ${
                    marketData.change >= 0
                      ? 'text-success-500'
                      : 'text-danger-500'
                  }`}
                >
                  {marketData.change >= 0 ? '+' : ''}
                  {marketData.change.toFixed(2)} (
                  {marketData.change_percent >= 0 ? '+' : ''}
                  {(marketData.change_percent * 100).toFixed(2)}%)
                </span>
              )}
            </div>
          </div>

          <div className="text-right">
            <div className="text-sm text-muted-foreground mb-1">Market Status</div>
            <div className="flex items-center gap-2">
              <div
                className={`status-indicator ${
                  marketData.market_status === 'OPEN' ? 'status-online' : 'status-offline'
                }`}
              ></div>
              <span className="capitalize">{marketData.market_status}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bias Meter - Takes 1/3 width */}
        <div className="lg:col-span-1">
          <BiasMeter signals={null} />
        </div>

        {/* Expected Move Chart - Takes 2/3 width */}
        <div className="lg:col-span-2">
          <ExpectedMoveChart signals={null} />
        </div>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Smart Money Activity */}
        <SmartMoneyActivity signals={null} />

        {/* Market Metrics */}
        <MarketMetrics data={marketData} analytics={analytics} />
      </div>

      {/* Third Row - Signal Cards */}
      <SignalCards signals={null} />

      {/* OI Heatmap - Full Width */}
      <OIHeatmap symbol={symbol} onAnalyticsUpdate={handleAnalyticsUpdate} />
      <div className="text-xs text-muted-foreground mt-2">
        Debug: Dashboard component rendering with symbol={symbol}, marketData.symbol={marketData.symbol}
      </div>
    </div>
  );
}

export default React.memo(DashboardComponent);
