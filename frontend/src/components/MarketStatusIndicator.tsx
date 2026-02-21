import React, { useState, useEffect } from 'react';
import { Clock, Wifi, WifiOff, AlertCircle } from 'lucide-react';

interface MarketSession {
  market_status: 'OPEN' | 'CLOSED' | 'PRE_OPEN' | 'OPENING_END' | 'CLOSING' | 'CLOSING_END' | 'HALTED' | 'UNKNOWN';
  engine_mode: 'LIVE' | 'SNAPSHOT' | 'HALTED' | 'OFFLINE';
  last_check?: string;
  is_polling?: boolean;
}

interface MarketStatusIndicatorProps {
  className?: string;
}

const MarketStatusIndicator: React.FC<MarketStatusIndicatorProps> = ({ className = "" }) => {
  const [session, setSession] = useState<MarketSession>({
    market_status: 'UNKNOWN',
    engine_mode: 'OFFLINE'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMarketStatus = async () => {
      try {
        const response = await fetch('/api/v1/market/session');
        const result = await response.json();
        
        if (result.status === 'success') {
          setSession(result.data);
          setError(null);
        } else {
          setError('Failed to fetch market status');
        }
      } catch (err) {
        setError('Network error');
        console.error('Market status fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchMarketStatus();

    // Poll every 30 seconds
    const interval = setInterval(fetchMarketStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN':
        return 'bg-green-500/20 text-green-400 border-green-500/40';
      case 'PRE_OPEN':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';
      case 'OPENING_END':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
      case 'CLOSING':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/40';
      case 'CLOSING_END':
        return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/40';
      case 'CLOSED':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'HALTED':
        return 'bg-red-600/20 text-red-500 border-red-600/40';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/40';
    }
  };

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'LIVE':
        return <Wifi className="w-3 h-3" />;
      case 'SNAPSHOT':
        return <Clock className="w-3 h-3" />;
      case 'HALTED':
        return <AlertCircle className="w-3 h-3" />;
      default:
        return <WifiOff className="w-3 h-3" />;
    }
  };

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'LIVE':
        return 'text-green-400';
      case 'SNAPSHOT':
        return 'text-blue-400';
      case 'HALTED':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center gap-2 px-2 py-1 bg-card border border-border rounded ${className}`}>
        <div className="w-3 h-3 border border-text-secondary border-t-transparent rounded-full animate-spin"></div>
        <span className="text-xs text-text-secondary">Loading...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center gap-2 px-2 py-1 bg-red-500/20 text-red-400 border border-red-500/40 rounded ${className}`}>
        <AlertCircle className="w-3 h-3" />
        <span className="text-xs font-mono">ERROR</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Market Status */}
      <div className={`flex items-center gap-2 px-2 py-1 border rounded font-mono text-xs ${getStatusColor(session.market_status)}`}>
        <span>{session.market_status}</span>
      </div>
      
      {/* Engine Mode */}
      <div className={`flex items-center gap-1 ${getModeColor(session.engine_mode)}`}>
        {getModeIcon(session.engine_mode)}
        <span className="text-xs font-mono">{session.engine_mode}</span>
      </div>
    </div>
  );
};

export default MarketStatusIndicator;
