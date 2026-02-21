import React, { useState, useEffect } from 'react';
import { Clock, Wifi, WifiOff } from 'lucide-react';
import api from '../../lib/api';

// Inline type — MarketStatusData not exported from types/dashboard
interface MarketStatusData {
  market_status: 'OPEN' | 'CLOSED' | 'ERROR';
  websocket_status: 'CONNECTED' | 'DISCONNECTED';
  server_time: string;
  symbol_supported: string[];
}

const MarketStatusBanner: React.FC = () => {
  const [marketStatus, setMarketStatus] = useState<MarketStatusData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMarketStatus = async () => {
      try {
        const response = await api.get('/api/v1/market/status');
        if (response.data && response.data.status === 'success') {
          setMarketStatus(response.data.data as MarketStatusData);
        }
      } catch (error) {
        console.error('Error fetching market status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMarketStatus();
    const interval = setInterval(fetchMarketStatus, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-3 h-3 bg-gray-500 rounded-full animate-pulse"></div>
            <span className="text-gray-400 text-sm">Loading market status...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!marketStatus) {
    return (
      <div className="bg-red-900/20 border-b border-red-800/50 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-red-400 text-sm">Market status unavailable</span>
          </div>
        </div>
      </div>
    );
  }

  const isMarketOpen = marketStatus.market_status === 'OPEN';
  const isWebSocketConnected = marketStatus.websocket_status === 'CONNECTED';

  // Use current time as fallback if server_time is missing or invalid
  const rawTime = marketStatus.server_time ? new Date(marketStatus.server_time) : new Date();
  const serverTime = isNaN(rawTime.getTime())
    ? new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' })
    : rawTime.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour12: true,
      hour: '2-digit',
      minute: '2-digit'
    });

  const symbols = Array.isArray(marketStatus.symbol_supported)
    ? marketStatus.symbol_supported.join(', ')
    : 'NIFTY, BANKNIFTY';

  return (
    <div className={`${isMarketOpen ? 'bg-green-900/20 border-green-800/50' : 'bg-red-900/20 border-red-800/50'} border-b px-6 py-3`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          {/* Market Status */}
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isMarketOpen ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className={`text-sm font-medium ${isMarketOpen ? 'text-green-400' : 'text-red-400'}`}>
              {isMarketOpen ? '🟢 MARKET OPEN' : '🔴 MARKET CLOSED'}
            </span>
          </div>

          {/* Server Time */}
          <div className="flex items-center space-x-2 text-gray-400">
            <Clock className="w-4 h-4" />
            <span className="text-sm">{serverTime} IST</span>
          </div>

          {/* Supported Symbols */}
          <div className="text-gray-400">
            <span className="text-sm">Symbols: {symbols}</span>
          </div>
        </div>

        {/* WebSocket Status */}
        <div className="flex items-center space-x-2">
          {isWebSocketConnected ? (
            <Wifi className="w-4 h-4 text-green-400" />
          ) : (
            <WifiOff className="w-4 h-4 text-red-400" />
          )}
          <span className={`text-sm ${isWebSocketConnected ? 'text-green-400' : 'text-red-400'}`}>
            {isWebSocketConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MarketStatusBanner;
