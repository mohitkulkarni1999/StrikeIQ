"use client";

import React, { useState, useEffect } from 'react';
import { useLiveMarketData } from '../hooks/useLiveMarketData';
import MarketMetrics from './MarketMetrics';
import OIHeatmap from './OIHeatmap';
import ProbabilityDisplay from './ProbabilityDisplay';
import AIInterpretationPanel from './AIInterpretationPanel';
import BiasMeter from './BiasMeter';
import ExpectedMoveChart from './ExpectedMoveChart';
import SignalCards from './SignalCards';
import InstitutionalBias from './InstitutionalBias';

// Loading component
function LoadingBlock() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="text-center text-white">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p>Loading market data...</p>
      </div>
    </div>
  );
}

// Error component
function ErrorBlock({ message }: { message: string }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="text-center text-white">
        <div className="text-red-400 mb-4">⚠️ Error</div>
        <p>{message}</p>
      </div>
    </div>
  );
}

function MarketDashboard({ data, symbol }: { data: any; symbol: string }) {
  console.log('🔍 MarketDashboard - Render called');
  console.log('🔍 MarketDashboard - data:', data);
  console.log('🔍 MarketDashboard - symbol:', symbol);
  console.log('🔍 MarketDashboard - data.analytics:', data?.analytics);
  console.log('🔍 MarketDashboard - data.intelligence:', data?.intelligence);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="glass-morphism border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-white">StrikeIQ</h1>
              <div className="flex items-center gap-2 text-sm text-white/70">
                <span>{symbol}</span>
                <span>•</span>
                <span className="text-green-400">LIVE</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* DEBUG SECTION - Temporary */}
      <div className="bg-black/50 border border-red-500/30 rounded-lg p-4 m-4">
        <h3 className="text-red-400 font-bold mb-2">DEBUG: Raw API Data</h3>
        <pre className="text-green-400 text-xs overflow-auto max-h-96">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>

      {/* Main Dashboard Grid - Clean Institutional Layout */}
      <section className="space-y-12 lg:space-y-14">
        
        {/* HERO SECTION - Command Center */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
          {/* Institutional Bias - Main Command Center */}
          <div className="lg:col-span-1">
            <div className="glass-morphism rounded-2xl p-6 border border-white/10 h-full">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white/90">Market Intelligence</h3>
                <div className="text-xs text-white/70">
                  {new Date().toLocaleTimeString()}
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-white/70">Total Call OI</span>
                  <span className="text-sm font-medium text-white">
                    {(data?.analytics?.total_call_oi || 0).toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-white/70">Total Put OI</span>
                  <span className="text-sm font-medium text-white">
                    {(data?.analytics?.total_put_oi || 0).toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-white/70">PCR</span>
                  <span className="text-sm font-medium text-white">
                    {data?.analytics?.pcr?.toFixed(3) || '0.000'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-white/70">Bias Score</span>
                  <span className="text-sm font-medium text-white">
                    {data?.analytics?.bias_score || 0}/100
                  </span>
                </div>
              </div>
              <div className="text-center text-sm text-white/70 mt-6">
                Institutional Bias analysis powered by real-time option chain data
              </div>
            </div>
          </div>
          
          {/* Market Intelligence - Key Metrics */}
          <div className="lg:col-span-1">
            {/* OIHeatmap moved to bottom */}
          </div>
        </div>

        {/* DATA DEEP DIVE - OI Heatmap */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">Option Chain Intelligence</h2>
            <div className="text-xs text-white/70">
              Live data analysis
            </div>
          </div>
        </div>

        {/* SECONDARY ANALYTICS - Market Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
          {/* Market Metrics */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Market Metrics</h2>
              <div className="text-xs text-white/70">
                Real-time market data
              </div>
            </div>
            <MarketMetrics analytics={data?.analytics} />
          </div>
          
          {/* Institutional Bias */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Institutional Bias</h2>
              <div className="text-xs text-white/70">
                Advanced bias analysis
              </div>
            </div>
            <InstitutionalBias 
              intelligence={data?.intelligence} 
              spotPrice={data?.spot}
              marketStatus="OPEN"
            />
          </div>

          {/* Market Bias */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Market Bias</h2>
              <div className="text-xs text-white/70">
                Intelligence bias analysis
              </div>
            </div>
            <BiasMeter intelligence={data?.intelligence} />
          </div>

          {/* Expected Move Chart */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Expected Move Chart</h2>
              <div className="text-xs text-white/70">
                Signal analysis
              </div>
            </div>
            <ExpectedMoveChart probability={data?.intelligence?.probability} />
          </div>
        </div>

        {/* SIGNAL CARDS - Full width */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">Signal Analysis</h2>
            <div className="text-xs text-white/70">
              Multi-signal intelligence
            </div>
          </div>
          <SignalCards intelligence={data?.intelligence} />
        </div>

        {/* AI ANALYSIS - Full width */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">AI Analysis</h2>
            <div className="text-xs text-white/70">
              Interpretive insights
            </div>
          </div>
          <AIInterpretationPanel intelligence={data?.intelligence} />
        </div>

        {/* OI HEATMAP - Bottom Position */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">Open Interest Heatmap</h2>
            <div className="text-xs text-white/70">
              Horizontal OI distribution analysis
            </div>
          </div>
          <OIHeatmap symbol={symbol} liveData={data} />
        </div>

        {/* DEBUG INFO - Remove in production */}
        <div className="text-xs text-white/70 text-center">
          Debug: symbol={symbol}, data.analytics?.total_call_oi={data?.analytics?.total_call_oi}
        </div>
      </section>
    </div>
  );
}

// Export default component
export default function DashboardComponent({ symbol }: { symbol: string }) {
  console.log('🔍 DashboardComponent - Render called with symbol:', symbol);

  // Authentication state protection
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  
  useEffect(() => {
    const handleAuthExpired = () => {
      console.log('🔐 DashboardComponent - Auth expired, setting isAuthenticated to false');
      setIsAuthenticated(false);
    };
    
    window.addEventListener('auth-expired', handleAuthExpired);
    
    return () => {
      window.removeEventListener('auth-expired', handleAuthExpired);
    };
  }, []);

  // Show AuthScreen if authentication expired
  if (!isAuthenticated) {
    console.log('🔐 DashboardComponent - Not authenticated, showing AuthScreen');
    // Import AuthScreen component
    const AuthScreen = require('../components/AuthScreen').default;
    return <AuthScreen />;
  }

  // Static expiry as per requirements
  const selectedExpiry = "2026-02-17"; 
  const { data, loading, error } = useLiveMarketData(symbol, selectedExpiry);

  console.log('🔍 DashboardComponent - useMarketData result:');
  console.log('  - loading:', loading);
  console.log('  - error:', error);
  console.log('  - data:', data);

  // Strict guards
  if (loading) {
    console.log('🔍 DashboardComponent - Still loading, showing LoadingBlock');
    return <LoadingBlock />;
  }
  if (error) {
    console.log('🔍 DashboardComponent - Error occurred:', error);
    return <ErrorBlock message={error} />;
  }
  if (!data) {
    console.log('🔍 DashboardComponent - No data available');
    return null;
  }

  console.log('🔍 DashboardComponent - About to render MarketDashboard with data');
  return <MarketDashboard data={data} symbol={symbol} />;
}
