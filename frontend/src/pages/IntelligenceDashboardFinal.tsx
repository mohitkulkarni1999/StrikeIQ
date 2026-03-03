import React, { useState, useEffect } from 'react';
import StructuralBanner from '../components/intelligence/StructuralBannerFinal';
import ConvictionPanel from '../components/intelligence/ConvictionPanelFinal';
import GammaPressurePanel from '../components/intelligence/GammaPressurePanelFinal';
import AlertPanel from '../components/intelligence/AlertPanelFinal';
import InteractionPanel from '../components/intelligence/InteractionPanelFinal';
import RegimeDynamicsPanel from '../components/intelligence/RegimeDynamicsPanelFinal';
import ExpiryPanel from '../components/intelligence/ExpiryPanelFinal';
import { MarketDataDisplay } from '../components/MarketDataDisplay';
import { useLiveMarketData } from '../hooks/useLiveMarketData';

const IntelligenceDashboard: React.FC = () => {
  // Use the optimized market data hook
  const { data: marketData, connected: isConnected, loading, error } = useLiveMarketData('NIFTY', null);

  const [regimeHistory, setRegimeHistory] = useState<any[]>([]);

  useEffect(() => {
    // Update regime history when market data changes
    if (marketData?.intelligence) {
      setRegimeHistory(prev => [...prev, marketData.intelligence]);
    }
  }, [marketData]);

  const wsData = marketData?.intelligence as any;

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-gray-700 border-t-red-500 rounded-full animate-spin mb-4"></div>
          <div className="text-xl font-semibold mb-2">Loading market analytics...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-2">⚠️ Error</div>
          <div className="text-gray-300">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* STRUCTURAL REGIME BANNER (FULL WIDTH) */}
      <div className="p-6 pb-0">
        <StructuralBanner
          regime={wsData?.structural_regime || 'unknown'}
          confidence={wsData?.regime_confidence || 0}
          stability={wsData?.regime_stability || 0}
          acceleration={wsData?.acceleration_index || 0}
        />
      </div>

      {/* INTELLIGENCE SCORE CARDS */}
      <div className="px-6 pb-6 mt-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Market Data Display */}
          <div className="col-span-12">
            <MarketDataDisplay />
          </div>

          {/* Conviction Panel */}
          <div className="col-span-12 lg:col-span-8">
            <ConvictionPanel
              conviction={wsData?.conviction || 0}
              directionalPressure={wsData?.flow_imbalance ? wsData.flow_imbalance * 100 : 0}
              instabilityIndex={wsData?.regime_dynamics?.transition_probability || 0}
            />
          </div>

          {/* Main Intelligence Display */}
          <div className="col-span-12 lg:col-span-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg border border-gray-700 p-6">
              <div className="text-2xl font-bold text-center mb-4 text-[#00E5FF]">
                StrikeIQ Intelligence
              </div>
              <div className="text-gray-400 text-center mb-6 text-sm">
                Real-time algorithmic market analysis
              </div>

              {marketData && (
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-400">
                      {marketData.symbol}
                    </div>
                    <div className="text-5xl font-black text-white my-2 tracking-tighter">
                      {marketData.spot?.toLocaleString()}
                    </div>
                  </div>

                  {/* Key Intelligence Metrics */}
                  <div className="grid grid-cols-2 gap-4 mt-6">
                    <div className="text-center p-3 bg-white/5 rounded-xl">
                      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">Market Bias</div>
                      <div className="text-xl font-bold text-white">
                        {wsData?.market_bias || 'NEUTRAL'}
                      </div>
                    </div>

                    <div className="text-center p-3 bg-white/5 rounded-xl">
                      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">Pin Prob.</div>
                      <div className="text-xl font-bold text-[#00FF9F]">
                        {((wsData?.pin_probability || 0) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Analysis Panels Grid */}
          <div className="col-span-12 lg:col-span-4">
            <GammaPressurePanel
              pressureMap={wsData?.gamma_pressure_map || {}}
              spot={marketData?.spot || 0}
            />
          </div>

          <div className="col-span-12 lg:col-span-4">
            <AlertPanel
              alerts={wsData?.alerts || []}
              maxVisible={5}
            />
          </div>

          <div className="col-span-12 lg:col-span-4">
            <InteractionPanel
              interaction={wsData?.flow_gamma_interaction || {}}
            />
          </div>

          <div className="col-span-12 lg:col-span-6">
            <RegimeDynamicsPanel
              dynamics={wsData?.regime_dynamics || {}}
            />
          </div>

          <div className="col-span-12 lg:col-span-6">
            <ExpiryPanel
              expiryAnalysis={wsData?.expiry_magnet_analysis || {}}
            />
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <div className="fixed bottom-4 right-4 z-50">
        <div className={`px-3 py-2 rounded-full text-xs font-medium border backdrop-blur-sm ${isConnected
          ? 'bg-green-500/10 border-green-500/40 text-green-400'
          : 'bg-red-500/10 border-red-500/40 text-red-400'
          }`}>
          {isConnected ? '🟢 LIVE' : '🔴 OFFLINE'}
        </div>
      </div>
    </div>
  );
};

export default IntelligenceDashboard;
