import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import StructuralBanner from '../components/intelligence/StructuralBannerFinal';
import ConvictionPanel from '../components/intelligence/ConvictionPanelFinal';
import GammaPressurePanel from '../components/intelligence/GammaPressurePanelFinal';
import AlertPanel from '../components/intelligence/AlertPanelFinal';
import InteractionPanel from '../components/intelligence/InteractionPanelFinal';
import RegimeDynamicsPanel from '../components/intelligence/RegimeDynamicsPanelFinal';
import ExpiryPanel from '../components/intelligence/ExpiryPanelFinal';
// import IOHeatmap from '../components/IOHeatmap'; // Existing component - uncomment when path is correct

interface WebSocketData {
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
  alerts: any[];
  gamma_pressure_map: any;
  flow_gamma_interaction: any;
  regime_dynamics: any;
  expiry_magnet_analysis: any;
}

const IntelligenceDashboard: React.FC = () => {
  // Use REST-based market data hook instead of WebSocket
  const marketData = useLiveMarketData('NIFTY', null);
  
  const [regimeHistory, setRegimeHistory] = useState<string[]>([]);
  
  useEffect(() => {
    // Update regime history when market data changes
    if (marketData.data && marketData.data.intelligence) {
      setRegimeHistory(prev => [...prev, marketData.data.intelligence]);
    }
  }, [marketData.data]);
  
  // Loading state
  if (marketData.loading) {
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
  if (marketData.error) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-gray-700 rounded-full mb-4">
            <div className="text-red-500 text-xl mb-2">⚠️ Error</div>
            <div className="text-gray-300">{marketData.error}</div>
          </div>
        </div>
      </div>
    );
  }
  
  // Success state with data
  return (
    <div className="min-h-screen bg-black text-white">
      {/* STRUCTURAL REGIME BANNER (FULL WIDTH) */}
      <div className="p-6 pb-0">
        <StructuralBanner
          regime={marketData.data?.intelligence?.structural_regime || 'unknown'}
          confidence={marketData.data?.intelligence?.regime_confidence || 0}
          stability={marketData.data?.intelligence?.regime_stability || 0}
          acceleration={marketData.data?.intelligence?.acceleration_index || 0}
        />
      </div>
      
      {/* INTELLIGENCE SCORE CARDS */}
      <div className="px-6 pb-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Conviction Panel */}
          <div className="col-span-8">
            <ConvictionPanel conviction={marketData.data?.intelligence?.conviction || 0} />
          </div>
          
          {/* Main Intelligence Display */}
          <div className="col-span-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg border border-gray-700 p-6">
              <div className="text-2xl font-bold text-center mb-4">
                StrikeIQ Intelligence Engine
              </div>
              <div className="text-gray-600 text-center mb-6">
                Analyzing market patterns in real-time
              </div>
              
              {/* Display market data when available */}
              {marketData.data && (
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-400">
                      NIFTY
                    </div>
                    <div className="text-5xl font-bold text-gray-300">
                      {marketData.data.spot?.toLocaleString()}
                    </div>
                    <div className="text-lg text-gray-400">
                      Change: {marketData.data.change?.toFixed(2)}%
                    </div>
                  </div>
                  
                  {/* Key Intelligence Metrics */}
                  <div className="grid grid-cols-2 gap-4 mt-6">
                    <div className="text-center">
                      <div className="text-lg font-semibold text-gray-400">Market Bias</div>
                      <div className="text-2xl font-bold">
                        {marketData.data.intelligence?.market_bias || 'NEUTRAL'}
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-lg font-semibold text-gray-400">Pin Probability</div>
                      <div className="text-2xl font-bold">
                        {(marketData.data.intelligence?.pin_probability * 100)?.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Other Panels */}
          <div className="col-span-4">
            <GammaPressurePanel 
              pressureMap={marketData.data?.intelligence?.gamma_pressure_map || {}}
              spot={marketData.data.spot || 0}
            />
          </div>
          
          <div className="col-span-4">
            <AlertPanel 
              alerts={marketData.data?.intelligence?.alerts || []}
              maxVisible={5}
            />
          </div>
          
          <div className="col-span-4">
            <InteractionPanel 
              interaction={marketData.data?.intelligence?.flow_gamma_interaction || {}}
            />
          </div>
          
          <div className="col-span-4">
            <RegimeDynamicsPanel 
              dynamics={marketData.data?.intelligence?.regime_dynamics || {}}
            />
          </div>
          
          <div className="col-span-4">
            <ExpiryPanel 
              expiryAnalysis={marketData.data?.intelligence?.expiry_magnet_analysis || {}}
            />
          </div>
        </div>
      </div>
      
      {/* Connection Status */}
      <div className="fixed bottom-4 right-4 z-50">
        <div className={`px-3 py-2 rounded-full text-xs font-medium backdrop-blur-sm ${
          marketData.isConnected 
            ? 'bg-green-500/20 border border-green-500/40 text-green-400' 
            : 'bg-red-500/20 border border-red-500/40 text-red-400'
        }`}>
          {marketData.isConnected ? '🟢 LIVE' : '🔴 OFFLINE'}
        </div>
      </div>
    </div>
  );
};

export default IntelligenceDashboard;
