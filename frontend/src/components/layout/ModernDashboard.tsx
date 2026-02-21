import React, { memo, useMemo, useCallback, useState } from 'react';
import { RefreshCw, Activity, Wifi, WifiOff, Settings, Bell } from 'lucide-react';

// Import optimized components
import ResponsiveLayout from './ResponsiveLayout';
import { Container, Grid, Card, Button, Badge, Metric } from '../ui/DesignSystem';
import PerformanceOptimizedCard from '../ui/PerformanceOptimizedCard';

// Import existing components (will be optimized)
import MarketMetrics from '../MarketMetrics';
import BiasMeter from '../BiasMeter';
import ProbabilityDisplay from '../ProbabilityDisplay';
import ExpectedMoveChart from '../ExpectedMoveChart';
import InstitutionalBias from '../InstitutionalBias';
import SignalCards from '../SignalCards';
import AIInterpretationPanel from '../AIInterpretationPanel';
import OIHeatmap from '../OIHeatmap';

// Import optimized panels
import OptimizedOptionChainPanel from '../intelligence/OptimizedOptionChainPanel';

interface ModernDashboardProps {
  data: any;
  status: any;
  error: string | null;
  loading: boolean;
  onSymbolChange: (symbol: string) => void;
  onExpiryChange: (expiry: string) => void;
  symbol: string;
  expiryList: string[];
  selectedExpiry: string | null;
}

// Memoized status indicator component
const StatusIndicator = memo(({ 
  isConnected, 
  label, 
  type 
}: { 
  isConnected: boolean; 
  label: string; 
  type: 'market' | 'websocket'; 
}) => {
  const statusConfig = useMemo(() => ({
    market: {
      connected: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/40' },
      disconnected: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/40' }
    },
    websocket: {
      connected: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/40' },
      disconnected: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/40' }
    }
  }), []);

  const config = statusConfig[type][isConnected ? 'connected' : 'disconnected'];

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-400">{label}:</span>
      <Badge variant={isConnected ? 'success' : 'danger'} size="sm">
        {isConnected ? 'Connected' : 'Disconnected'}
      </Badge>
    </div>
  );
});

StatusIndicator.displayName = 'StatusIndicator';

// Memoized header component
const DashboardHeader = memo(({
  symbol,
  onSymbolChange,
  status,
  onSettingsClick,
  onNotificationsClick
}: {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
  status: any;
  onSettingsClick: () => void;
  onNotificationsClick: () => void;
}) => {
  const handleSymbolChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    onSymbolChange(e.target.value.toUpperCase());
  }, [onSymbolChange]);

  return (
    <div className="flex items-center justify-between w-full">
      {/* Logo and Symbol Input */}
      <div className="flex items-center gap-4">
        <h1 className="text-2xl lg:text-4xl font-black bg-gradient-to-r from-[#00FF9F] to-[#4F8CFF] bg-clip-text text-transparent">
          StrikeIQ
        </h1>
        
        <input
          type="text"
          value={symbol}
          onChange={handleSymbolChange}
          className="bg-black/50 border border-gray-700 rounded-lg px-4 py-2 text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-24 lg:w-32"
          placeholder="NIFTY"
          aria-label="Trading Symbol"
        />
      </div>

      {/* Status Indicators and Actions */}
      <div className="flex items-center gap-4 lg:gap-6">
        {/* Status Indicators */}
        <div className="hidden lg:flex items-center gap-4">
          <StatusIndicator
            isConnected={status?.market_status === 'OPEN'}
            label="Market"
            type="market"
          />
          <StatusIndicator
            isConnected={status?.websocket_status === 'CONNECTED'}
            label="WebSocket"
            type="websocket"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onNotificationsClick}
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onSettingsClick}
            aria-label="Settings"
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
});

DashboardHeader.displayName = 'DashboardHeader';

// Memoized sidebar component
const DashboardSidebar = memo(({ expiryList, selectedExpiry, onExpiryChange }: {
  expiryList: string[];
  selectedExpiry: string | null;
  onExpiryChange: (expiry: string) => void;
}) => {
  const handleExpiryChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    onExpiryChange(e.target.value);
  }, [onExpiryChange]);

  return (
    <div className="space-y-6">
      {/* Expiry Selection */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-3">Expiry Selection</h3>
        <select
          value={selectedExpiry || ''}
          onChange={handleExpiryChange}
          className="w-full bg-gray-800 border border-gray-700 text-white px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Select Expiry Date"
        >
          <option value="">Select Expiry</option>
          {expiryList.map((exp) => (
            <option key={exp} value={exp}>
              {exp}
            </option>
          ))}
        </select>
      </div>

      {/* Quick Stats */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-3">Quick Stats</h3>
        <div className="space-y-2">
          <div className="p-3 bg-gray-800 rounded-lg">
            <div className="text-xs text-gray-400">Active Symbols</div>
            <div className="text-lg font-bold text-white">3</div>
          </div>
          <div className="p-3 bg-gray-800 rounded-lg">
            <div className="text-xs text-gray-400">Data Points</div>
            <div className="text-lg font-bold text-white">1.2K</div>
          </div>
        </div>
      </div>

      {/* System Health */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-3">System Health</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 bg-gray-800 rounded">
            <span className="text-xs text-gray-400">Latency</span>
            <span className="text-xs text-green-400">12ms</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-800 rounded">
            <span className="text-xs text-gray-400">CPU</span>
            <span className="text-xs text-yellow-400">45%</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-800 rounded">
            <span className="text-xs text-gray-400">Memory</span>
            <span className="text-xs text-blue-400">2.1GB</span>
          </div>
        </div>
      </div>
    </div>
  );
});

DashboardSidebar.displayName = 'DashboardSidebar';

// Main modern dashboard component
const ModernDashboard: React.FC<ModernDashboardProps> = memo(({
  data,
  status,
  error,
  loading,
  onSymbolChange,
  onExpiryChange,
  symbol,
  expiryList,
  selectedExpiry
}) => {
  // State for mobile menu
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Memoized handlers
  const handleSettingsClick = useCallback(() => {
    // Handle settings modal
    console.log('Settings clicked');
  }, []);

  const handleNotificationsClick = useCallback(() => {
    // Handle notifications panel
    console.log('Notifications clicked');
  }, []);

  // Memoized error component
  const ErrorComponent = useMemo(() => {
    if (!error) return null;
    
    return (
      <PerformanceOptimizedCard
        className="bg-red-950/20 border-red-900/50 p-8 m-4"
        dataKey="error-card"
      >
        <div className="flex flex-col items-center text-center">
          <WifiOff className="w-12 h-12 text-red-500 mb-4" />
          <h3 className="text-xl font-bold text-red-400 mb-2">Connection Interrupted</h3>
          <p className="text-red-300/70 max-w-md">{error}</p>
          <Button variant="outline" size="sm" className="mt-4">
            Retry Connection
          </Button>
        </div>
      </PerformanceOptimizedCard>
    );
  }, [error]);

  // Memoized loading component
  const LoadingComponent = useMemo(() => {
    if (!loading) return null;
    
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <RefreshCw className="w-10 h-10 text-[#4F8CFF] animate-spin mb-4" />
        <p className="text-lg font-mono text-[#4F8CFF]/80 tracking-widest uppercase">
          Synchronizing Market Data...
        </p>
      </div>
    );
  }, [loading]);

  // Memoized main content
  const MainContent = useMemo(() => {
    if (loading || error) return null;

    return (
      <Container size="xl">
        <div className="space-y-6">
          {/* Market Metrics Section */}
          <PerformanceOptimizedCard dataKey="market-metrics">
            <MarketMetrics
              analytics={{
                spot: data?.spot ?? 0,
                change: data?.change ?? 0,
                changePercent: data?.change_percent ?? 0,
                high: data?.analytics?.high ?? 0,
                low: data?.analytics?.low ?? 0,
                volume: data?.analytics?.total_volume ?? 0,
                vwap: data?.analytics?.vwap ?? 0
              }}
            />
          </PerformanceOptimizedCard>

          {/* Key Metrics Grid */}
          <Grid cols={3} gap="lg">
            <PerformanceOptimizedCard dataKey="bias-meter">
              <BiasMeter intelligence={data?.intelligence ?? null} />
            </PerformanceOptimizedCard>
            
            <PerformanceOptimizedCard dataKey="expected-move">
              <ExpectedMoveChart
                probability={
                  data?.expected_move_data ??
                  (data?.intelligence as any)?.probability ??
                  null
                }
              />
            </PerformanceOptimizedCard>
            
            <PerformanceOptimizedCard dataKey="pin-probability">
              <div className="p-6 text-center">
                <div className="text-xs text-gray-400 uppercase tracking-widest font-bold mb-4">
                  Pin Probability
                </div>
                <div className="text-5xl font-black text-[#4F8CFF] mb-2">
                  {Math.round(
                    typeof data?.pin_probability === "number"
                      ? data.pin_probability
                      : typeof (data?.pin_probability as any)?.probability === "number"
                        ? (data?.pin_probability as any).probability
                        : 0
                  )}%
                </div>
                <div className="text-[10px] text-gray-500 font-mono tracking-tight uppercase">
                  Statistical Magnet Strength
                </div>
              </div>
            </PerformanceOptimizedCard>
          </Grid>

          {/* Institutional Bias and Smart Money */}
          <Grid cols={2} gap="lg">
            <PerformanceOptimizedCard dataKey="institutional-bias">
              <InstitutionalBias
                intelligence={data?.intelligence ?? null}
                spotPrice={data?.spot}
                marketStatus={status?.market_status || 'OPEN'}
                marketChange={data?.change}
                marketChangePercent={data?.change_percent}
              />
            </PerformanceOptimizedCard>
            
            <PerformanceOptimizedCard dataKey="smart-money">
              <SignalCards intelligence={data?.intelligence ?? null} />
            </PerformanceOptimizedCard>
          </Grid>

          {/* Option Chain */}
          {data?.optionChain && (
            <PerformanceOptimizedCard dataKey="option-chain">
              <OptimizedOptionChainPanel optionChainData={data.optionChain} />
            </PerformanceOptimizedCard>
          )}

          {/* AI Interpretation */}
          <PerformanceOptimizedCard dataKey="ai-interpretation">
            <AIInterpretationPanel intelligence={data?.intelligence ?? null} />
          </PerformanceOptimizedCard>

          {/* OI Heatmap */}
          <PerformanceOptimizedCard dataKey="oi-heatmap">
            <OIHeatmap symbol={symbol} liveData={data?.optionChain ?? null} />
          </PerformanceOptimizedCard>
        </div>
      </Container>
    );
  }, [data, status, symbol, loading, error]);

  return (
    <ResponsiveLayout
      header={
        <DashboardHeader
          symbol={symbol}
          onSymbolChange={onSymbolChange}
          status={status}
          onSettingsClick={handleSettingsClick}
          onNotificationsClick={handleNotificationsClick}
        />
      }
      sidebar={
        <DashboardSidebar
          expiryList={expiryList}
          selectedExpiry={selectedExpiry}
          onExpiryChange={onExpiryChange}
        />
      }
    >
      {ErrorComponent}
      {LoadingComponent}
      {MainContent}
    </ResponsiveLayout>
  );
});

ModernDashboard.displayName = 'ModernDashboard';

export default ModernDashboard;
