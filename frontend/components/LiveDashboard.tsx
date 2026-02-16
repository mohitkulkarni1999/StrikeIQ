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
      <div className="text-white text-xl">Connecting to live market data...</div>
    </div>
  );
}

// Error component
function ErrorBlock({ message }: { message: string }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="text-white text-xl text-center px-8">
        <div className="text-red-400 mb-4">❌ Connection Error</div>
        <div>{message}</div>
        <div className="text-sm text-gray-400 mt-4">Please refresh the page to try again</div>
      </div>
    </div>
  );
}

// Mode indicator component
function ModeIndicator({ mode }: { mode: string }) {
  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'loading':
        return 'text-yellow-400';
      case 'snapshot':
        return 'text-blue-400';
      case 'live':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getModeText = (mode: string) => {
    switch (mode) {
      case 'loading':
        return 'Connecting...';
      case 'snapshot':
        return 'REST Mode';
      case 'live':
        return 'LIVE STREAMING';
      case 'error':
        return 'Connection Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 glass-morphism rounded-lg px-4 py-2">
      <div className="flex items-center space-x-2">
        <div className={`text-sm font-medium ${getModeColor(mode)}`}>
          {getModeText(mode)}
        </div>
        {mode === 'live' && (
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
        )}
      </div>
    </div>
  );
}

// Main Live Dashboard component
function LiveMarketDashboard({ symbol }: { symbol: string }) {
  const { data, loading, error, mode, websocket } = useLiveMarketData(symbol, "2026-02-17");

  console.log('🔌 LiveMarketDashboard - useLiveMarketData result:');
  console.log('  - mode:', mode);
  console.log('  - loading:', loading);
  console.log('  - error:', error);
  console.log('  - data:', data);

  // Debug controls
  const [showDebug, setShowDebug] = useState(false);

  // Strict guards
  if (loading) {
    console.log('🔌 LiveMarketDashboard - Still loading, showing LoadingBlock');
    return <LoadingBlock />;
  }

  if (error) {
    console.log('❌ LiveMarketDashboard - Error occurred:', error);
    return <ErrorBlock message={error} />;
  }

  if (!data) {
    console.log('🔌 LiveMarketDashboard - No data available');
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">No market data available</div>
      </div>
    );
  }

  console.log('🔌 LiveMarketDashboard - About to render LiveMarketDashboard with data');
  console.log('🔌 LiveMarketDashboard - data.analytics:', data?.analytics);
  console.log('🔌 LiveMarketDashboard - data.intelligence:', data?.intelligence);

  return (
    <>
      <ModeIndicator mode={mode} />
      
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
        <div className="max-w-7xl mx-auto">
          {/* Debug Panel */}
          {showDebug && (
            <div className="glass-morphism rounded-xl p-4 mb-6">
              <h3 className="text-white text-lg font-semibold mb-4">🔍 Live Debug Panel</h3>
              <div className="text-gray-300 text-sm space-y-2">
                <div><strong>Mode:</strong> {mode}</div>
                <div><strong>WebSocket State:</strong> {websocket ? 'Connected' : 'Disconnected'}</div>
                <div><strong>Symbol:</strong> {symbol}</div>
                <div><strong>Spot:</strong> {data?.spot}</div>
                <div><strong>Last Update:</strong> {data?.timestamp}</div>
              </div>
              <button 
                onClick={() => setShowDebug(false)}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Hide Debug
              </button>
            </div>
          )}

          {/* Main Dashboard Content */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Market Metrics */}
            <div className="space-y-6">
              <MarketMetrics analytics={data.analytics} />
              
              {/* Connection Controls */}
              <div className="glass-morphism rounded-xl p-6">
                <h3 className="text-white text-lg font-semibold mb-4">🔌 Connection Controls</h3>
                <div className="space-y-3">
                  <div className="text-gray-300 text-sm">
                    <div className="flex justify-between items-center">
                      <span>Status:</span>
                      <span className={`font-medium ${
                        mode === 'live' ? 'text-green-400' : 
                        mode === 'snapshot' ? 'text-blue-400' : 
                        mode === 'error' ? 'text-red-400' : 'text-yellow-400'
                      }`}>
                        {mode.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>WebSocket:</span>
                      <span className={websocket ? 'text-green-400' : 'text-red-400'}>
                        {websocket ? 'Connected' : 'Disconnected'}
                      </span>
                    </div>
                  </div>
                  
                  {/* Manual Reconnect Button */}
                  <button
                    onClick={() => {
                      if (websocket) {
                        websocket.close();
                      }
                      window.location.reload();
                    }}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Reconnect
                  </button>
                </div>
              </div>
            </div>

            {/* Middle Column - Charts and Analysis */}
            <div className="space-y-6">
              <ExpectedMoveChart probability={data.probability} />
              <BiasMeter intelligence={data.intelligence} />
              <SignalCards intelligence={data.intelligence} />
            </div>

            {/* Right Column - Heatmap and AI */}
            <div className="space-y-6">
              <OIHeatmap symbol={symbol} />
              <AIInterpretationPanel intelligence={data.intelligence} />
              <InstitutionalBias intelligence={data.intelligence} />
            </div>
          </div>
        </div>

        {/* Debug Toggle */}
        {!showDebug && (
          <button
            onClick={() => setShowDebug(true)}
            className="fixed bottom-4 right-4 z-50 px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700"
          >
            Show Debug
          </button>
        )}
      </div>
    </>
  );
}

export default LiveMarketDashboard;
