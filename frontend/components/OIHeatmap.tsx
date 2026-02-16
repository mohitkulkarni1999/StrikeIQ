import { useState, useEffect, useRef } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import api from '../src/lib/api';

interface OIData {
  strike: number;
  oi: number;
  change: number;
  ltp: number;
  volume: number;
  iv: number;
  put_oi: number;
  put_change: number;
  put_ltp: number;
  put_volume: number;
  put_iv: number;
}

interface ExpiryDate {
  date: string;
  label: string;
  isCurrent: boolean;
}

interface OIHeatmapProps {
  symbol: string;
  liveData?: any; // Live option chain data from useLiveMarketData
}

export default function OIHeatmap({ symbol, liveData }: OIHeatmapProps) {
  const [oiData, setOiData] = useState<OIData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [spotPrice, setSpotPrice] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expiryLoading, setExpiryLoading] = useState<boolean>(false);
  const [availableExpiries, setAvailableExpiries] = useState<ExpiryDate[]>([]);
  const [selectedExpiry, setSelectedExpiry] = useState<string>('');
  
  const tableRef = useRef<HTMLDivElement>(null);
  const atmRowRef = useRef<HTMLTableRowElement>(null);

  // Fetch available expiry dates
  const fetchAvailableExpiries = async () => {
    try {
      setExpiryLoading(true);
      const response = await api.get(`/api/v1/options/contract/${symbol}`);
      
      let expiryDates: string[] = [];
      if (response.data && response.data.data && Array.isArray(response.data.data)) {
        expiryDates = response.data.data;
      } else if (response.data && Array.isArray(response.data)) {
        expiryDates = response.data;
      }
      
      const expiries: ExpiryDate[] = expiryDates.map((date: string) => {
        const expiryDate = new Date(date);
        const today = new Date();
        
        const daysUntilExpiry = Math.ceil((expiryDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
        const isCurrent = daysUntilExpiry >= 0 && daysUntilExpiry <= 7;
        
        return {
          date,
          label: formatExpiryDate(date),
          isCurrent
        };
      });
      
      setAvailableExpiries(expiries);
      
      if (!selectedExpiry && expiries.length > 0) {
        const currentExpiry = expiries.find(e => e.isCurrent);
        const nearestExpiry = currentExpiry || expiries[0];
        setSelectedExpiry(nearestExpiry.date);
      }
      
    } catch (err) {
      console.error('Error fetching expiries:', err);
      setError('Failed to fetch expiry dates');
    } finally {
      setExpiryLoading(false);
    }
  };

  // Format expiry date for display
  const formatExpiryDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    
    const daysUntilExpiry = Math.ceil((date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === new Date(today.getTime() + 24 * 60 * 60 * 1000).toDateString()) {
      return 'Tomorrow';
    } else if (daysUntilExpiry > 0 && daysUntilExpiry <= 7) {
      return `${daysUntilExpiry} days`;
    } else if (daysUntilExpiry > 7 && daysUntilExpiry <= 14) {
      const weeks = Math.floor(daysUntilExpiry / 7);
      return `${weeks} week${weeks > 1 ? 's' : ''}`;
    } else {
      return date.toLocaleDateString('en-IN', { 
        day: 'numeric', 
        month: 'short', 
        year: '2-digit'
      });
    }
  };

  // Handle expiry selection
  const handleExpiryChange = (expiry: string) => {
    const date = new Date(expiry);
    const today = new Date();
    
    if (!isNaN(date.getTime()) && date >= today) {
      setSelectedExpiry(expiry);
    }
  };

  // Auto-scroll to ATM row when data loads
  useEffect(() => {
    if (atmRowRef.current && tableRef.current && oiData.length > 0) {
      const tableContainer = tableRef.current;
      const atmRow = atmRowRef.current;
      
      // Calculate position to center ATM row in view (show 7 rows total)
      const rowHeight = atmRow.offsetHeight;
      const containerHeight = tableContainer.clientHeight;
      const targetScrollTop = atmRow.offsetTop - (containerHeight / 2) + (rowHeight / 2);
      
      // Smooth scroll to center ATM row
      tableContainer.scrollTo({
        top: targetScrollTop,
        behavior: 'smooth'
      });
    }
  }, [oiData, spotPrice]);

  // Process live data from WebSocket when available
  useEffect(() => {
    if (liveData && liveData.calls && liveData.puts) {
      console.log('🔥 OIHeatmap - Processing live WebSocket data');
      
      // Use spot price from live data
      setSpotPrice(liveData.spot);
      
      // Transform live data for heatmap
      const transformedData = liveData.calls.map((call: any) => {
        const matchingPut = liveData.puts.find((p: any) => p.strike === call.strike);
        
        return {
          strike: call.strike,
          oi: call.oi || 0,
          change: call.change || 0,
          ltp: call.ltp || 0,
          volume: call.volume || 0,
          iv: call.iv || 0,
          put_oi: matchingPut?.oi || 0,
          put_change: matchingPut?.change || 0,
          put_ltp: matchingPut?.ltp || 0,
          put_volume: matchingPut?.volume || 0,
          put_iv: matchingPut?.iv || 0,
        };
      });
      
      setOiData(transformedData);
      setLoading(false);
      setError(null);
      
      console.log('🔥 OIHeatmap - Live data processed:', transformedData.length, 'strikes');
    }
  }, [liveData]);

  // Fetch expiries on component mount (REST - cached)
  useEffect(() => {
    fetchAvailableExpiries();
  }, [symbol]);

  // Fetch option chain data
  useEffect(() => {
    if (selectedExpiry) {
      const fetchOptionChain = async () => {
        try {
          setLoading(true);
          setError(null);
          
          const response = await api.get(
            `/api/v1/options/chain/${symbol}?expiry_date=${selectedExpiry}`
          );
        
          const chain = response.data;
          const calls = chain?.data?.calls || [];
          const puts = chain?.data?.puts || [];
          
          // Use the actual spot price from API response instead of calculating it
          let currentSpotPrice = chain?.data?.spot || null;
          
          console.log('🔍 OIHeatmap - Raw API Response:', chain);
          console.log('🔍 OIHeatmap - Extracted spot price:', currentSpotPrice);
          
          // Fallback calculation only if spot price is not available
          if (!currentSpotPrice && calls.length > 0) {
            console.log('🔍 OIHeatmap - Spot price not found, calculating from options');
            // Find strike closest to spot (ATM) - this is usually current spot
            const sortedCalls = [...calls].sort((a, b) => Math.abs(a.strike - (spotPrice || 0)) - Math.abs(b.strike - (spotPrice || 0)));
            const atmCall = sortedCalls[0];
            
            // Estimate spot from ATM strike and option prices
            if (atmCall && atmCall.ltp > 0) {
              const matchingPut = puts.find((p: any) => p.strike === atmCall.strike);
              if (matchingPut && matchingPut.ltp > 0) {
                // Spot ≈ Strike + Call LTP - Put LTP (put-call parity approximation)
                currentSpotPrice = atmCall.strike + atmCall.ltp - matchingPut.ltp;
                console.log('🔍 OIHeatmap - Calculated spot price:', currentSpotPrice);
              }
            }
          }
          
          setSpotPrice(currentSpotPrice);
        
          const transformedData = calls.map((call: any) => {
            const matchingPut = puts.find((p: any) => p.strike === call.strike);
        
            return {
              strike: call.strike,
              oi: call.oi || 0,
              change: call.change || 0,
              ltp: call.ltp || 0,
              volume: call.volume || 0,
              iv: call.iv || 0,
              put_oi: matchingPut?.oi || 0,
              put_change: matchingPut?.change || 0,
              put_ltp: matchingPut?.ltp || 0,
              put_volume: matchingPut?.volume || 0,
              put_iv: matchingPut?.iv || 0
            };
          });
        
          setOiData(transformedData);
        
        } catch (err: any) {
          console.error("Error fetching option chain:", err);
          
          // Check if it's a 401 error - axios interceptor will handle redirect
          if (err.response?.status === 401) {
            console.log('🔐 401 detected in OIHeatmap - axios interceptor will handle redirect');
            return; // Don't set error state, let interceptor handle
          }
          
          if (err?.response?.status === 429) {
            setError("Rate limit exceeded - please wait");
          } else {
            setError("Failed to fetch option chain data");
          }
        } finally {
          setLoading(false);
        }
      };
      
      fetchOptionChain();
    }
  }, [symbol, selectedExpiry]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="metric-card">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <h3 className="text-xl font-semibold text-danger-500">Error</h3>
            <p className="text-muted-foreground">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="metric-card min-h-screen">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold">OI Heatmap - {symbol}</h3>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 text-base">
            <div className="w-4 h-4 bg-danger-500 rounded"></div>
            <span className="text-muted-foreground">Call OI</span>
          </div>
          <div className="flex items-center gap-3 text-base">
            <div className="w-4 h-4 bg-success-500 rounded"></div>
            <span className="text-muted-foreground">Put OI</span>
          </div>
        </div>
      </div>

      {/* Current Price Indicator */}
      {spotPrice && (
        <div className="mb-4 p-3 glass-morphism rounded-lg border-l-4 border-l-green-500">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Current Spot Price</span>
            <div className="text-right">
              <span className="text-lg font-bold text-green-400">
                ₹{spotPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <div className="text-xs text-muted-foreground">
                Expected: ₹25,471.10
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* DEBUG SECTION - Temporary */}
      <div className="mb-4 bg-black/50 border border-red-500/30 rounded-lg p-3">
        <h4 className="text-red-400 font-bold mb-2">DEBUG: OIHeatmap Spot Price</h4>
        <div className="text-green-400 text-xs space-y-1">
          <div>Current: ₹{spotPrice?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || 'null'}</div>
          <div>Expected: ₹25,471.10</div>
          <div>Difference: {spotPrice ? (spotPrice - 25471.10).toFixed(2) : 'N/A'}</div>
        </div>
      </div>

      {/* Expiry Selector */}
      <div className="mb-4 p-3 glass-morphism rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Expiry Date</span>
          </div>
          <div className="flex items-center gap-2">
            {expiryLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm text-blue-500">Loading expiries...</span>
              </div>
            ) : availableExpiries.length > 0 ? (
              <select
                value={selectedExpiry}
                onChange={(e) => handleExpiryChange(e.target.value)}
                className="bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-32"
                disabled={loading}
              >
                {availableExpiries.map((expiry) => (
                  <option key={expiry.date} value={expiry.date}>
                    {expiry.label} {expiry.isCurrent && '(Current)'}
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-sm text-muted-foreground">No expiries available</span>
            )}
          </div>
        </div>
      </div>

      {/* OI Heatmap Table */}
      <div className="relative">
        {/* Fixed Header */}
        <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-white/10">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-muted-foreground">
                <th className="py-3 px-2 text-center min-w-[90px]">Call OI</th>
                <th className="py-3 px-2 text-center min-w-[70px]">Call Chg</th>
                <th className="py-3 px-2 text-center min-w-[90px]">Call LTP</th>
                <th className="py-3 px-2 text-center min-w-[80px]">Strike</th>
                <th className="py-3 px-2 text-center min-w-[90px]">Put LTP</th>
                <th className="py-3 px-2 text-center min-w-[70px]">Put Chg</th>
                <th className="py-3 px-2 text-center min-w-[90px]">Put OI</th>
              </tr>
            </thead>
          </table>
        </div>
        
        {/* Scrollable Body */}
        <div className="overflow-x-auto overflow-y-auto max-h-96" ref={tableRef}>
          <table className="w-full">
            <thead className="invisible">
              <tr className="text-left text-sm text-muted-foreground">
                <th className="py-3 px-2 text-center min-w-[90px]">Call OI</th>
                <th className="py-3 px-2 text-center min-w-[70px]">Call Chg</th>
                <th className="py-3 px-2 text-center min-w-[90px]">Call LTP</th>
                <th className="py-3 px-2 text-center min-w-[80px]">Strike</th>
                <th className="py-3 px-2 text-center min-w-[90px]">Put LTP</th>
                <th className="py-3 px-2 text-center min-w-[70px]">Put Chg</th>
                <th className="py-3 px-2 text-center min-w-[90px]">Put OI</th>
              </tr>
            </thead>
          <tbody>
            {oiData.map((row, index) => {
              // Check if this strike is closest ATM (single strike only)
              const isATM = spotPrice && Math.abs(row.strike - spotPrice) <= 25; // Within 25 points (tighter range)
              
              return (
              <tr 
                key={index} 
                ref={isATM ? atmRowRef : null}
                className={`border-b border-white/5 hover:bg-white/5 ${
                  isATM ? 'bg-green-500/10 border-l-2 border-l-green-500' : ''
                }`}
              >
                {/* Call OI with heatmap */}
                <td className="py-3 text-center">
                  <div 
                    className="px-2 py-1 rounded text-xs font-medium text-white oi-heatmap-cell"
                    style={{ backgroundColor: 'rgba(239, 68, 68, 0.5)' }}
                  >
                    {row.oi.toLocaleString('en-IN')}
                  </div>
                </td>
                
                {/* Call Change */}
                <td className="py-3 text-center">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    row.change > 0 ? 'bg-success-500/20 text-success-500' :
                    row.change < 0 ? 'bg-danger-500/20 text-danger-500' :
                    'bg-gray-500/20 text-gray-300'
                  }`}>
                    {row.change?.toLocaleString('en-IN')}
                  </div>
                </td>
                
                {/* Call LTP */}
                <td className="py-3 text-center text-sm">
                  {row.ltp?.toLocaleString('en-IN', {
                    style: 'currency',
                    currency: 'INR'
                  })}
                </td>
                
                {/* Strike */}
                <td className="py-3 px-2 text-center font-medium">
                  <span className={isATM ? 'text-green-400 font-bold' : ''}>
                    {row.strike.toLocaleString('en-IN')}
                    {isATM && ' 📍'}
                  </span>
                </td>
                
                {/* Put LTP */}
                <td className="py-3 text-center text-sm">
                  {row.put_ltp?.toLocaleString('en-IN', {
                    style: 'currency',
                    currency: 'INR'
                  })}
                </td>
                
                {/* Put Change */}
                <td className="py-3 text-center">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    row.put_change > 0 ? 'bg-success-500/20 text-success-500' :
                    row.put_change < 0 ? 'bg-danger-500/20 text-danger-500' :
                    'bg-gray-500/20 text-gray-300'
                  }`}>
                    {row.put_change?.toLocaleString('en-IN')}
                  </div>
                </td>
                
                {/* Put OI with heatmap */}
                <td className="py-3 text-center">
                  <div 
                    className="px-2 py-1 rounded text-xs font-medium text-white oi-heatmap-cell"
                    style={{ backgroundColor: 'rgba(34, 197, 94, 0.5)' }}
                  >
                    {row.put_oi.toLocaleString('en-IN')}
                  </div>
                </td>
              </tr>
              );
            })}
          </tbody>
        </table>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <div className="font-medium mb-2">Interpretation:</div>
        <div className="text-sm text-muted-foreground space-y-1">
          <div>• 📍 Green highlight indicates ATM (At-The-Money) strike</div>
          <div>• Darker colors indicate higher Open Interest</div>
          <div>• Green changes show OI addition, Red shows OI reduction</div>
          <div>• High Call OI at strikes above spot = Resistance</div>
          <div>• High Put OI at strikes below spot = Support</div>
        </div>
      </div>
    </div>
  );
}
