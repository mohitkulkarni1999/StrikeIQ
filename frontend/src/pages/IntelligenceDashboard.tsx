import React, { useState, useEffect } from 'react';
import { useLiveMarketData } from '../hooks/useLiveMarketData';
import StructuralBanner from '../components/intelligence/StructuralBanner';
import ConvictionPanel from '../components/intelligence/ConvictionPanel';
import GammaPressurePanel from '../components/intelligence/GammaPressurePanel';
import AlertPanel from '../components/intelligence/AlertPanel';
import InteractionPanel from '../components/intelligence/InteractionPanel';
import RegimeDynamicsPanel from '../components/intelligence/RegimeDynamicsPanel';
import ExpiryPanel from '../components/intelligence/ExpiryPanel';

const IntelligenceDashboard: React.FC = () => {
  // Use the optimized market data hook
  const { data: marketData, connected: isConnected } = useLiveMarketData('NIFTY', null);

  const [regimeHistory, setRegimeHistory] = useState<any[]>([]);

  useEffect(() => {
    // Update regime history when market data changes
    if (marketData?.intelligence) {
      setRegimeHistory(prev => [...prev, marketData.intelligence]);
    }
  }, [marketData]);

  // Use intelligence data directly from the processed market data
  const wsData = marketData?.intelligence as any;

  // Derived metrics for conviction panel
  const conviction = wsData?.regime_confidence || 0;
  const directionalPressure = wsData?.flow_imbalance ? wsData.flow_imbalance * 100 : 0;
  const instabilityIndex = wsData?.regime_dynamics?.transition_probability || 0;

  const handleRegimeChange = (newRegime: string) => {
    console.log('Regime changed to:', newRegime);
  };

  if (!isConnected) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-gray-700 border-t-blue-500 rounded-full animate-spin mb-4"></div>
          <div className="text-xl font-semibold mb-2">Connecting to StrikeIQ</div>
          <div className="text-gray-400">Establishing secure connection...</div>
        </div>
      </div>
    );
  }

  if (!wsData) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-800 rounded-full animate-pulse mb-4"></div>
          <div className="text-xl font-semibold mb-2">Initializing Intelligence Engine</div>
          <div className="text-gray-400">Loading market analytics...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Structural Regime Banner - Full Width */}
      <div className="p-6 pb-0">
        <StructuralBanner
          regime={wsData.structural_regime}
          confidence={wsData.regime_confidence}
          stability={wsData.regime_dynamics?.stability_score || 0}
          acceleration={wsData.regime_dynamics?.acceleration_index || 0}
          onRegimeChange={handleRegimeChange}
        />
      </div>

      {/* Intelligence Score Cards - Full Width */}
      <div className="px-6 pb-6">
        <ConvictionPanel
          conviction={conviction}
          directionalPressure={directionalPressure}
          instabilityIndex={instabilityIndex}
        />
      </div>

      {/* Main Grid Layout */}
      <div className="px-6 pb-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Gamma Pressure Map - Left 8 columns */}
          <div className="col-span-12 lg:col-span-8">
            <GammaPressurePanel
              pressureMap={wsData.gamma_pressure_map || {}}
              spot={marketData?.spot || 0}
            />
          </div>

          {/* Alerts Panel - Right 4 columns */}
          <div className="col-span-12 lg:col-span-4">
            <AlertPanel
              alerts={wsData.alerts || []}
              maxVisible={5}
            />
          </div>
        </div>
      </div>

      {/* Second Row */}
      <div className="px-6 pb-6">
        <InteractionPanel
          interaction={wsData.flow_gamma_interaction || {}}
        />
      </div>

      {/* Third Row */}
      <div className="px-6 pb-6">
        <RegimeDynamicsPanel
          dynamics={wsData.regime_dynamics || {}}
        />
      </div>

      {/* Fourth Row - Expiry Intelligence */}
      <div className="px-6 pb-6">
        <ExpiryPanel
          expiryAnalysis={wsData.expiry_magnet_analysis || {}}
        />
      </div>

      {/* IOHeatmap - Unchanged placeholder */}
      <div className="px-6 pb-6">
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6 text-center text-gray-400">
          IOHeatmap Component (Placeholder)
        </div>
      </div>

      {/* Connection Status Indicator */}
      <div className="fixed bottom-4 right-4 z-50">
        <div className={`px-3 py-2 rounded-full text-xs font-medium backdrop-blur-sm ${isConnected
            ? 'bg-green-500/20 border border-green-500/40 text-green-400'
            : 'bg-red-500/20 border border-red-500/40 text-red-400'
          }`}>
          {isConnected ? '🟢 LIVE' : '🔴 OFFLINE'}
        </div>
      </div>
    </div>
  );
};

export default IntelligenceDashboard;
